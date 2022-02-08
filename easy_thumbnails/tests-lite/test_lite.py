# coding: utf-8

from datetime import timedelta
from decimal import Decimal
import json
import time
import unittest

from easy_thumbnails.alias import aliases
from easy_thumbnails.files import get_thumbnailer


class TestLite(unittest.TestCase):
    
    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_0010_aliases(self):
        print("""
          Test aliases.
        """)
                
        print(aliases.all())

    def test_0020_get_thumbnailer(self):
        print("""
          Test get_thumbnailer().
        """)
                
        obj = None
        relative_name = 'test.jpg'
        thumbnailer = get_thumbnailer(obj, relative_name)
        
        print(thumbnailer)

    def test_0030_generate_alias_small(self):
        print("""
          Test generate_alias_small.
        """)
                
        with open('tests-lite/test.jpg', 'rb') as obj:
            relative_name = 'test.jpg'
            thumbnailer = get_thumbnailer(obj, relative_name)
            
            print(thumbnailer['small'])
        
    def test_0040_get_thumbnail_name(self):
        print("""
          Test get_thumbnail_name().
        """)
                
        obj = None
        relative_name = 'test.jpg'
        thumbnailer = get_thumbnailer(obj, relative_name)
        alias = 'small'
        options = aliases.get(alias, target='selforder.Immagine')
        options['ALIAS'] = alias      #this IS needed for namers to work!!!
        
        print(thumbnailer.get_thumbnail_name(options, transparent=False))
        
    def test_0050_get_thumbnail_name_alias(self):
        print("""
          Test get_thumbnail_name(namer=alias).
        """)
                
        obj = None
        relative_name = 'test.jpg'
        thumbnailer = get_thumbnailer(obj, relative_name)
        thumbnailer.thumbnail_namer = 'easy_thumbnails.namers.alias'
        alias = 'small'
        options = aliases.get(alias, target='selforder.Immagine')
        options['ALIAS'] = alias      #this IS needed for namers to work!!!
        
        print(thumbnailer.get_thumbnail_name(options, transparent=False))
        
