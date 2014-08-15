# -*- coding: utf-8 -*-

#from plone.directives import dexterity
from plone.directives import form
from plone.namedfile.interfaces import IImageScaleTraversable

#from plone.supermodel import model
from plone.theme.interfaces import IDefaultPloneLayer

#from zope import schema

#from zope.interface import Attribute
#from zope.interface import Interface

from lmu.contenttype.blog import MessageFactory as _

class IBlogFolder(form.Schema, IImageScaleTraversable):
    """
    Folder for Blog Entries with special views and restrictions
    """
    form.model("models/blog_folder.xml")

class IBlogEntry(form.Schema, IImageScaleTraversable):
    """
    Blog Entry with folder support for files and images
    """
    form.model("models/blog_entry.xml")

class IBlogLayer(IDefaultPloneLayer):
    """ A layer specific to this product. 
        Is registered using browserlayer.xml
    """

