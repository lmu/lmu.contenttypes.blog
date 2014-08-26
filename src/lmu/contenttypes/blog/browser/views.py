# -*- coding: utf-8 -*-
from Acquisition import aq_inner

from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from zope.component import getMultiAdapter

from lmu.contenttypes.blog.interfaces import IBlogFolder



def str2bool(v):
    return not (v != None and v.lower not in ['True', '1'])


#class ListingView(BrowserView):

    #template = ViewPageTemplateFile('templates/listing_view.pt')



class FrontPageView(BrowserView):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        omit = self.request.get('omit')
        self.omit = str2bool(omit)

    def update(self):
        """
        """
        # Hide the editable-object border
        context = self.context
        request = self.request
        request.set('disable_border', True)

    def __call__(self):
        return self.template()

    def entries(self):
        #import ipdb; ipdb.set_trace()
        entries = []
        if IBlogFolder.providedBy(self.context):
            content_filter={
                'portal_type' : 'Blog Entry',
                }
            if self.request.get('author'):
                content_filter['Creator'] = self.request.get('author')




            entries = self.context.listFolderContents(
                contentFilter=content_filter
                )
        
        #import ipdb; ipdb.set_trace()
        return entries

    def get_item_image(self, item, scale='mini'):
        #import ipdb; ipdb.set_trace()
        scales = getMultiAdapter((item, self.request), name='images')
        scale = scales.scale('image', scale=scale)
        imageTag = None
        if scale is not None:
           imageTag = scale.tag()
        return imageTag

    def omit(self):
        return self.omit

#class EntryView(BrowserView):

    #template = ViewPageTemplateFile('templates/entry_view.pt')