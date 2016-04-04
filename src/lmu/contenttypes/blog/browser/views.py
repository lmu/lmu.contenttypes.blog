# -*- coding: utf-8 -*-

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.discussion.browser.comments import CommentsViewlet
#from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser import add
from plone.dexterity.browser import edit
from plone.dexterity.events import EditFinishedEvent
from z3c.form import button
from zope.event import notify

from lmu.policy.base.browser.content import _AbstractLMUBaseContentView
from lmu.policy.base.browser.content import _EntryViewMixin
from lmu.policy.base.browser.content import RichTextWidgetConfig
from lmu.policy.base.browser.content import formHelper
from lmu.policy.base.browser.content_listing import _AbstractLMUBaseListingView
from lmu.policy.base.browser.content_listing import _FrontPageIncludeMixin
from lmu.policy.base.browser.utils import isDBReadOnly as uIsDBReadOnly

#from lmu.contenttypes.blog.interfaces import IBlogEntry
from lmu.contenttypes.blog.interfaces import IBlogFolder

from lmu.contenttypes.blog import MESSAGE_FACTORY as _
#from lmu.contenttypes.blog import logger

from logging import getLogger

logging = getLogger(__name__)


class ListingView(_AbstractLMUBaseListingView):

    template = ViewPageTemplateFile('templates/listing_view.pt')

    portal_type = 'Blog Entry'
    container_interface = IBlogFolder
    sort_on = 'effective'

    def __init__(self, context, request):
        super(ListingView, self).__init__(context, request)

        if self.request.get('author'):
            self.content_filter['Creator'] = self.request.get('author')

    def __call__(self):
        return self.template()


class FrontPageIncludeView(_AbstractLMUBaseListingView, _FrontPageIncludeMixin):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')

    DEFAULT_LIMIT = 3
    portal_type = 'Blog Entry'
    container_interface = IBlogFolder
    sort_on = 'effective'


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

    @button.buttonAndHandler(_('Save'), name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            #IStatusMessage(self.request).addStatusMessage(
            #    _(u"Item created"), "info success"
            #)

    def isDBReadOnly(self):
        return uIsDBReadOnly()


class BlogEntryAddView(add.DefaultAddView):
    form = BlogEntryAddForm
    widgets = form.widgets
    groups = form.groups


class BlogEntryEditForm(edit.DefaultEditForm):

    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    description = _(u'Bearbeiten Sie Ihren Blog-Beitrag. Klicken Sie anschließend auf "Vorschau", um die Eingaben zu überprüfen und den Blog-Eintrag zu veröffentlichen.')

    portal_type = 'Blog Entry'

    def __call__(self):
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
            if button.__name__ == 'save':
                button.title = _(u'Preview')

        return super(BlogEntryEditForm, self).__call__()

    def isDBReadOnly(self):
        return uIsDBReadOnly()

    @button.buttonAndHandler(_(u'Save'), name='save')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        #IStatusMessage(self.request).addStatusMessage(
        #    _(u"Changes saved"), "info success"
        #)
        self.request.response.redirect(self.nextURL())
        notify(EditFinishedEvent(self.context))


class BlogCommentsViewlet(CommentsViewlet):
    index = ViewPageTemplateFile('templates/comments.pt')
