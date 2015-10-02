# -*- coding: utf-8 -*-

from Products.CMFCore import permissions
from Products.CMFPlone.PloneBatch import Batch
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api
#from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser import add

#from lmu.contenttypes.blog.interfaces import IBlogEntry
from lmu.contenttypes.blog.interfaces import IBlogFolder

from lmu.contenttypes.blog import MESSAGE_FACTORY as _
#from lmu.contenttypes.blog import logger
from lmu.policy.base.browser import _AbstractLMUBaseContentEditForm
from lmu.policy.base.browser import _AbstractLMUBaseContentView
from lmu.policy.base.browser import _FrontPageIncludeMixin
from lmu.policy.base.browser import _EntryViewMixin
from lmu.policy.base.browser import RichTextWidgetConfig
from lmu.policy.base.browser import formHelper

from logging import getLogger

logging = getLogger(__name__)


class _AbstractBlogListingView(_AbstractLMUBaseContentView):

    DEFAULT_LIMIT = 10

    def __init__(self, context, request):
        self.context = context
        self.request = request
        limit_display = getattr(self.request, 'limit_display', None)
        limit_display = int(limit_display) if limit_display is not None else \
            self.DEFAULT_LIMIT
        b_size = getattr(self.request, 'b_size', None)
        self.b_size = int(b_size) if b_size is not None else limit_display
        b_start = getattr(self.request, 'b_start', None)
        self.b_start = int(b_start) if b_start is not None else 0

        self.content_filter = {'portal_type': 'Blog Entry'}
        self.pcatalog = self.context.portal_catalog

        if IBlogFolder.providedBy(self.context):

            if self.request.get('author'):
                self.content_filter['Creator'] = self.request.get('author')

    def absolute_length(self):
        return len(self.pcatalog.searchResults(self.content_filter))

    def entries(self):
        entries = []
        if IBlogFolder.providedBy(self.context):

            entries = self.pcatalog.searchResults(
                self.content_filter,
                sort_on='effective', sort_order='reverse',
            )

        return entries

    def batch(self):
        batch = Batch(
            self.entries(),
            size=self.b_size,
            start=self.b_start,
            orphan=1
        )
        return batch

    def can_add(self):
        return api.user.has_permission(permissions.AddPortalContent,
                                       #'lmu.contenttypes.blog: Add Blog Entry',
                                       obj=self.context)


class ListingView(_AbstractBlogListingView):

    template = ViewPageTemplateFile('templates/listing_view.pt')

    def __call__(self):
        return self.template()


class FrontPageIncludeView(_AbstractBlogListingView, _FrontPageIncludeMixin):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')
    DEFAULT_LIMIT = 3


class EntryView(_AbstractLMUBaseContentView, _EntryViewMixin):

    template = ViewPageTemplateFile('templates/entry_view.pt')

    def __call__(self):
        return self.template()


class BlogEntryAddForm(add.DefaultAddForm):
    template = ViewPageTemplateFile('templates/blog_entry_add.pt')

    portal_type = 'Blog Entry'
    label = None
    description = _(u'Geben Sie zunächst den Titel und Text Ihres Blog-Beitrags an, und klicken Sie auf "Weiter". Danach können Sie Bilder und andere Dateien hinzufügen.')

    def update(self):
        self.updateWidgets()

        text = self.schema.get('text')
        text.widget = RichTextWidgetConfig()

        formHelper(self,
                   fields_to_show=[],
                   fields_to_input=['title', 'description'],
                   fields_to_hide=['IPublication.effective', 'IPublication.expires', ],
                   fields_to_omit=['IPublication.effective', 'IPublication.expires', 'IVersionable.changeNote'])

        buttons = self.buttons
        for button in buttons.values():
            #button.klass = u' button large round'
            if button.__name__ == 'save':
                button.title = _(u'Next')

        return super(BlogEntryAddForm, self).update()


class BlogEntryAddView(add.DefaultAddView):
    form = BlogEntryAddForm
    widgets = form.widgets
    groups = form.groups


class BlogEntryEditForm(_AbstractLMUBaseContentEditForm):
    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    description = _(u'Bearbeiten Sie Ihren Blog-Beitrag. Klicken Sie anschließend auf "Vorschau", um die Eingaben zu überprüfen und den Blog-Eintrag zu veröffentlichen.')

    portal_type = 'Blog Entry'
