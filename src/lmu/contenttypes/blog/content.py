# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces.syndication import ISyndicatable
#from plone.dexterity.content import Item
from plone.dexterity.content import Container

from plone.app.discussion.interfaces import IConversation

from zope.interface import implements

from lmu.contenttype.blog.interfaces import IBlogFolder
from lmu.contenttype.blog.interfaces import IBlogEntry

class BlogFolder(Container):
    implements(IBlogFolder, ISyndicatable)

class BlogEntry(Container):
    implements(IBlogEntry)



    def getDiscussionCount(self):
        try:
            # plone.app.discussion.conversation object
            # fetched via IConversation adapter
            conversation = IConversation(self)
        except:
            return 0

        return conversation.total_comments
