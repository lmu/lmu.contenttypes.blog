# -*- coding: utf-8 -*-

from plone.dexterity.content import Item
from plone.dexterity.content import Container

from zope.interface import implements

from Products.CMFPlone.interfaces.syndication import ISyndicatable


class BlogFolder(Container):
    implements(IBlogFolder, ISyndicatable)

class BlogEntry(Container):
    implements(IBlogEntry)
    