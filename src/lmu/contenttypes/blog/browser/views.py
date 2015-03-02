# -*- coding: utf-8 -*-
from Acquisition import aq_inner

from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.textfield.interfaces import ITransformer
from zope.component import getMultiAdapter

from lmu.contenttypes.blog.interfaces import IBlogFolder



def str2bool(v):
    return v != None and v.lower() in ['true', '1']

class _AbstractBlogView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_memberdata(self, item):
        pm = getToolByName(self.context, 'portal_membership')
        member_id = item.Creator()
        member = pm.getMemberById(member_id)
        return member

    def strip_text(self, item, length=500):
        transformer = ITransformer(item)
        transformedValue = transformer(item.text, 'text/plain')
        striped_length = len(transformedValue)
        if striped_length > length:
            striped_length = transformedValue.rfind(' ',0,length)
            transformedValue = transformedValue[:striped_length] + '...'
        return transformedValue


class _AbstractBlogListingView(_AbstractBlogView):


    def entries(self):
        entries = []
        if IBlogFolder.providedBy(self.context):
            content_filter={
                'portal_type' : 'Blog Entry',
                'review_state' : 'published',
                }
            if self.request.get('author'):
                content_filter['Creator'] = self.request.get('author')

            pcatalog = self.context.portal_catalog

            entries = pcatalog.searchResults(
                content_filter, 
                sort_on='modified', sort_order='reverse',
                b_size=int(self.request.get('b_size', '20')),
                b_start=int(self.request.get('b_start', '0'))
                )
        
        return entries

class ListingView(_AbstractBlogListingView):

    template = ViewPageTemplateFile('templates/listing_view.pt')

    def __call__(self):
        return self.template()


class FrontPageView(_AbstractBlogListingView):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')


    def update(self):
        """
        """
        # Hide the editable-object border
        context = self.context
        request = self.request
        request.set('disable_border', True)


    def __call__(self):

        omit = self.request.get('omit')
        self.omit = str2bool(omit)
        return self.template()



    def omit(self):
        return self.omit


class EntryView(_AbstractBlogView):

    template = ViewPageTemplateFile('templates/entry_view.pt')


    def __call__(self):
        return self.template()


    def canSeeHistory(self):
        return True


    def canEdit(self):
        return True


    def canRemove(self):
        return True