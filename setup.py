#!/usr/bin/env python
import codecs

from setuptools import find_packages, setup

import easy_thumbnails


def read_files(*filenames):
    """
    Output the contents of one or more files to a single concatenated string.
    """
    output = []
    for filename in filenames:
        f = codecs.open(filename, encoding="utf-8")
        try:
            output.append(f.read())
        finally:
            f.close()
    return "\n\n".join(output)


setup(
    name="easy-thumbnails",
    version=easy_thumbnails.get_version(),
    url="http://github.com/SmileyChris/easy-thumbnails",
    description="Easy thumbnails for Django",
    long_description=read_files("README.rst", "CHANGES.rst"),
    author="Chris Beaven",
    author_email="smileychris@gmail.com",
    platforms=["any"],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=2.2",
        "pillow",
        "svglib",
        "reportlab",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=False,
)
