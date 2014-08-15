# -*- coding: utf-8 -*-
from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class ListingView(BrowserView):

    template = ViewPageTemplateFile('templates/listing_view.pt')



class FrontPageView(BrowserView):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')


class EntryView(BrowserView):

    template = ViewPageTemplateFile('templates/entry_view.pt')