# -*- coding: utf-8 -*-
from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile







#class ListingView(BrowserView):

    #template = ViewPageTemplateFile('templates/listing_view.pt')



class FrontPageView(BrowserView):

    index = ViewPageTemplateFile('templates/frontpage_view.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    #def __call__(self):
    #    return render(self.template)

    def update(self):
        """
        """
        # Hide the editable-object border
        context = self.context
        request = self.request
        request.set('disable_border', True)
        
    def render(self):
        return self.index()

    def __call__(self):
        return self.render()
#class EntryView(BrowserView):

    #template = ViewPageTemplateFile('templates/entry_view.pt')