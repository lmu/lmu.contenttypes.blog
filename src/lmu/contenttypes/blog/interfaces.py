# -*- coding: utf-8 -*-

from plone.namedfile.interfaces import IImageScaleTraversable
from plone.theme.interfaces import IDefaultPloneLayer
#from zope import schema
from zope.interface import Interface

#from lmu.contenttypes.blog import MESSAGE_FACTORY as _


class IBlogFolder(Interface, IImageScaleTraversable):
    """
    Folder for Blog Entries with special views and restrictions
    """
    #form.model("models/blog_folder.xml")


class IBlogEntry(Interface, IImageScaleTraversable):
    """
    Blog Entry with folder support for files and images
    """
    #form.model("models/blog_entry.xml")


class IBlogLayer(IDefaultPloneLayer):
    """ A layer specific to this product.
        Is registered using browserlayer.xml
    """


# class IBlogReportForm(Interface):

#     name = schema.TextLine(
#         title=_(u"Name of Reporter"),
#         description=_(u"Name of the Person reporting this issue, will be filled by System.")
#     )

#     url = schema.URI(
#         title=_(u"Reported URL"),
#         description=_(u"The Reported URL of the Blog Entry.")
#     )

#     message = schema.Text(
#         title=_(u"Report Message"),
#         description=_(u"Please describe why you report this Blog Entry")
#     )
