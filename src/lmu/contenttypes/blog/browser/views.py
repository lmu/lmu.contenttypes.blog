# -*- coding: utf-8 -*-
from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from lmu.contenttypes.blog





#class ListingView(BrowserView):

    #template = ViewPageTemplateFile('templates/listing_view.pt')



class FrontPageView(BrowserView):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')

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

    def __call__(self):
        return self.template()

    def entries(self):
    	import ipdb; ipdb.set_trace()
    	if not self.context:
    		pass
    	entries = context.
    	return []


#class EntryView(BrowserView):

    #template = ViewPageTemplateFile('templates/entry_view.pt')