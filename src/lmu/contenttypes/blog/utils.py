# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
#from plone.app.contenttypes.indexer import _unicode_save_string_concat(*args)
from plone.indexer.decorator import indexer

from lmu.contenttypes.blog.interfaces import IBlogFolder
from lmu.contenttypes.blog.interfaces import IBlogEntry


@indexer(IBlogFolder)
def SearchableText_blogfolder(obj):

    return u" ".join((
        safe_unicode(obj.id),
        safe_unicode(obj.title) or u"",
        safe_unicode(obj.description) or u"",
    ))


@indexer(IBlogEntry)
def SearchableText_blogentry(obj):
    return u" ".join((
        safe_unicode(obj.id),
        safe_unicode(obj.title) or u"",
        safe_unicode(obj.description) or u"",
        safe_unicode(obj.text.output) or u"",
    ))
