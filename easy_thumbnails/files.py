import os

from .django_images import get_image_dimensions

from .django_module_loading import import_string

from easy_thumbnails import engine, exceptions, utils
from easy_thumbnails.alias import aliases
from easy_thumbnails.conf import settings
from easy_thumbnails.options import ThumbnailOptions


def get_thumbnailer(obj, relative_name=None):
    """
    Get a :class:`Thumbnailer` for a source file.

    The ``obj`` argument is usually either one of the following:

        * ``FieldFile`` instance (i.e. a model instance file/image field
          property).

        * A string, which will be used as the relative name (the source will be
          set to the default storage).

        * ``Storage`` instance - the ``relative_name`` argument must also be
          provided.

    Or it could be:

        * A file-like instance - the ``relative_name`` argument must also be
          provided.

          In this case, the thumbnailer won't use or create a cached reference
          to the thumbnail (i.e. a new thumbnail will be created for every
          :meth:`Thumbnailer.get_thumbnail` call).

    If ``obj`` is a ``Thumbnailer`` instance, it will just be returned. If it's
    an object with an ``easy_thumbnails_thumbnailer`` then the attribute is
    simply returned under the assumption it is a Thumbnailer instance)
    """
    if hasattr(obj, 'easy_thumbnails_thumbnailer'):
        return obj.easy_thumbnails_thumbnailer
    if isinstance(obj, Thumbnailer):
        return obj

    source_storage = None

    if isinstance(obj, str):
        relative_name = obj
        obj = None

    if not relative_name:
        raise ValueError(
            "If object is not a FieldFile or Thumbnailer instance, the "
            "relative name must be provided")

    return Thumbnailer(
        file=obj, name=relative_name, source_storage=source_storage,
        remote_source=obj is not None)


def generate_all_aliases(fieldfile, include_global):
    """
    Generate all of a file's aliases.

    :param fieldfile: A ``FieldFile`` instance.
    :param include_global: A boolean which determines whether to generate
        thumbnails for project-wide aliases in addition to field, model, and
        app specific aliases.
    """
    all_options = aliases.all(fieldfile, include_global=include_global)
    if all_options:
        thumbnailer = get_thumbnailer(fieldfile)
        for key, options in all_options.items():
            options['ALIAS'] = key
            thumbnailer.get_thumbnail(options)


def database_get_image_dimensions(file, close=False, dimensions=None):
    """
    Returns the (width, height) of an image, given ThumbnailFile.  Set
    'close' to True to close the file at the end if it is initially in an open
    state.

    Will attempt to get the dimensions from the file itself if they aren't
    in the db.
    """
    dimensions = get_image_dimensions(file, close=close)
    return dimensions


class Thumbnailer:
    """
    A file-like object which provides some methods to generate thumbnail
    images.

    You can subclass this object and override the following properties to
    change the defaults (pulled from the default settings):

        * source_generators
        * thumbnail_processors
    """
    #: A list of source generators to use. If ``None``, will use the default
    #: generators defined in settings.
    source_generators = None
    #: A list of thumbnail processors. If ``None``, will use the default
    #: processors defined in settings.
    thumbnail_processors = None

    def __init__(self, file=None, name=None, source_storage=None,
                 thumbnail_storage=None, remote_source=False, generate=True,
                 *args, **kwargs):
        self.file = file
        self.name = name
        self.source_storage = source_storage
        self.thumbnail_storage = thumbnail_storage
        self.remote_source = remote_source
        self.alias_target = None
        self.generate = generate

        # Set default properties. For backwards compatibilty, check to see
        # if the attribute exists already (it could be set as a class property
        # on a subclass) before getting it from settings.
        for default in (
                'basedir', 'subdir', 'prefix', 'quality', 'extension',
                'preserve_extensions', 'transparency_extension',
                'check_cache_miss', 'namer'):
            attr_name = 'thumbnail_%s' % default
            if getattr(self, attr_name, None) is None:
                value = getattr(settings, attr_name.upper())
                setattr(self, attr_name, value)

    def __getitem__(self, alias):
        """
        Retrieve a thumbnail matching the alias options (or raise a
        ``KeyError`` if no such alias exists).
        """
        options = aliases.get(alias, target=self.alias_target)
        if not options:
            raise KeyError(alias)
        options['ALIAS'] = alias
        return self.get_thumbnail(options, silent_template_exception=True)

    def get_options(self, thumbnail_options, **kwargs):
        """
        Get the thumbnail options that includes the default options for this
        thumbnailer (and the project-wide default options).
        """
        if isinstance(thumbnail_options, ThumbnailOptions):
            return thumbnail_options
        args = []
        if thumbnail_options is not None:
            args.append(thumbnail_options)
        opts = ThumbnailOptions(*args, **kwargs)
        if 'quality' not in thumbnail_options:
            opts['quality'] = self.thumbnail_quality
        return opts

    def generate_thumbnail(self, thumbnail_options, silent_template_exception=False):
        """
        Return an unsaved ``ThumbnailFile`` containing a thumbnail image.

        The thumbnail image is generated using the ``thumbnail_options``
        dictionary.
        """
        thumbnail_options = self.get_options(thumbnail_options)
        orig_size = thumbnail_options['size']  # remember original size
        # Size sanity check.
        min_dim, max_dim = 0, 0
        for dim in orig_size:
            try:
                dim = float(dim)
            except (TypeError, ValueError):
                continue
            min_dim, max_dim = min(min_dim, dim), max(max_dim, dim)
        if max_dim == 0 or min_dim < 0:
            msg = "The source image has an invalid size ({0}x{1})"
            raise exceptions.EasyThumbnailsError(msg.format(*orig_size))

        image = engine.generate_source_image(
            self.file, thumbnail_options, self.source_generators,
            fail_silently=silent_template_exception)
        if image is None:
            msg = "The source file does not appear to be an image: '{name}'"
            raise exceptions.InvalidImageFormatError(
                msg.format(name=self.name))

        thumbnail_image = engine.process_image(image, thumbnail_options,
                                               self.thumbnail_processors)
        filename = self.get_thumbnail_name(
            thumbnail_options,
            transparent=utils.is_transparent(thumbnail_image))
        quality = thumbnail_options['quality']
        subsampling = thumbnail_options['subsampling']

        img = engine.save_pil_image(
            thumbnail_image, filename=filename, quality=quality,
            subsampling=subsampling)

        return img

    def get_thumbnail_name(self, thumbnail_options, transparent=False):
        """
        Return a thumbnail filename for the given ``thumbnail_options``
        dictionary and ``source_name`` (which defaults to the File's ``name``
        if not provided).
        """
        thumbnail_options = self.get_options(thumbnail_options)
        path, source_filename = os.path.split(self.name)
        source_extension = os.path.splitext(source_filename)[1][1:].lower()
        preserve_extensions = self.thumbnail_preserve_extensions
        if preserve_extensions is True or isinstance(preserve_extensions, (list, tuple)) and \
                source_extension in preserve_extensions:
            extension = source_extension
        elif transparent:
            extension = self.thumbnail_transparency_extension
        else:
            extension = self.thumbnail_extension
        extension = extension or 'jpg'

        prepared_opts = thumbnail_options.prepared_options()
        opts_text = '_'.join(prepared_opts)

        data = {'opts': opts_text}
        basedir = self.thumbnail_basedir % data
        subdir = self.thumbnail_subdir % data

        if isinstance(self.thumbnail_namer, str):
            namer_func = import_string(self.thumbnail_namer)
        else:
            namer_func = self.thumbnail_namer
        filename = namer_func(
            thumbnailer=self,
            source_filename=source_filename,
            thumbnail_extension=extension,
            thumbnail_options=thumbnail_options,
            prepared_options=prepared_opts,
        )
        filename = '{}{}'.format(self.thumbnail_prefix, filename)

        return os.path.join(basedir, path, subdir, filename)

    def get_thumbnail(self, thumbnail_options, save=True, generate=None,
                      silent_template_exception=False):
        """
        Return a ``ThumbnailFile`` containing a thumbnail.

        If a matching thumbnail already exists, it will simply be returned.

        By default (unless the ``Thumbnailer`` was instanciated with
        ``generate=False``), thumbnails that don't exist are generated.
        Otherwise ``None`` is returned.

        Force the generation behaviour by setting the ``generate`` param to
        either ``True`` or ``False`` as required.

        The new thumbnail image is generated using the ``thumbnail_options``
        dictionary. If the ``save`` argument is ``True`` (default), the
        generated thumbnail will be saved too.
        """
        thumbnail_options = self.get_options(thumbnail_options)
        thumbnail = self.generate_thumbnail(
            thumbnail_options,
            silent_template_exception=silent_template_exception)

        return thumbnail

    def open(self, mode=None):
        if self.closed:
            mode = mode or getattr(self, 'mode', None) or 'rb'
            self.file = self.source_storage.open(self.name, mode)
        else:
            self.seek(0)

    # open() doesn't alter the file's contents, but it does reset the pointer.
    open.alters_data = True
