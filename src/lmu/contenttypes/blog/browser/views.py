# -*- coding: utf-8 -*-

from Products.CMFCore import permissions
from Products.CMFPlone.PloneBatch import Batch
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import json
from collective.quickupload.portlet.quickuploadportlet import Assignment
from collective.quickupload.portlet.quickuploadportlet import Renderer
from datetime import datetime
from plone import api
from plone.app.discussion.browser.comments import CommentsViewlet
from plone.app.z3cform.templates import RenderWidget
#from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser import edit
from plone.dexterity.browser import add
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import INPUT_MODE
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

#from lmu.contenttypes.blog.interfaces import IBlogEntry
from lmu.contenttypes.blog.interfaces import IBlogFolder
from lmu.contenttypes.blog.interfaces import IBlogCommentFormLayer

from lmu.contenttypes.blog import MESSAGE_FACTORY as _
#from lmu.contenttypes.blog import logger
from lmu.policy.base.browser import _AbstractLMUBaseContentView
from lmu.policy.base.browser import _FrontPageIncludeMixin
from lmu.policy.base.browser import _EntryViewMixin
from lmu.policy.base.browser import str2bool

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


class EntryContentView(_AbstractLMUBaseContentView):

    template = ViewPageTemplateFile('templates/entry_content_view.pt')

    def __call__(self):
        omit = self.request.get('full')
        self.omit = not str2bool(omit)
        return self.template()

    def content(self, mode='files'):
        if mode == 'images':
            type_test = lambda typ: typ == 'Image'
        else:
            plone_layout = getMultiAdapter((self.context, self.request),
                                           name='plone_layout')
            type_test = lambda typ: typ != 'Image'
        items = []
        previous = -1
        for current, obj in enumerate(self.context.objectValues()):
            if type_test(obj.portal_type):
                item = {'url': obj.absolute_url(),
                        'id': obj.getId(),
                        'title': obj.Title()}
                if mode == 'files':
                    item['tag'] = plone_layout.getIcon(obj).html_tag()
                    item['type'] = self.getFileType(obj)
                    item['size'] = self.getFileSize(obj)
                elif mode == 'images':
                    scales = api.content.get_view(
                        context=obj,
                        request=self.request,
                        name='images')
                    item['tag'] = scales.tag('image', width=80, height=80,
                                             direction='down')
                if previous > -1:
                    item['delta_up'] = previous - current
                items.append(item)
                previous = current
            else:
                items.append({})
        previous = -1
        for current, obj in enumerate(reversed(self.context.objectValues())):
            if type_test(obj.portal_type):
                if previous > -1:
                    items[-1 - current]['delta_down'] = current - previous
                previous = current
        return [i for i in items if i]

    def render_quickupload(self):
        ass = Assignment(header=_(''))
        renderer = CustomUploadRenderer(
            self.context, self.request, self, None, ass)
        renderer.update()
        return renderer.render()

    def timestamp(self):
        return datetime.now().isoformat()

    def subset_ids(self):
        return json.dumps(self.context.objectIds())

    def mode_label(self):
        return self.mode[0].upper() + self.mode[1:]

    def content_sortinfo(self):
        return self.content(mode=self.mode)


class EntrySortFilesView(EntryContentView):

    template = ViewPageTemplateFile('templates/entry_sort_images_view.pt')
    mode = 'files'

    def __call__(self):
        return self.template()


class EntrySortImagesView(EntryContentView):

    template = ViewPageTemplateFile('templates/entry_sort_images_view.pt')
    mode = 'images'

    def __call__(self):
        return self.template()


class CustomUploadRenderer(Renderer):
    def javascript(self):
        return ''


class RichTextWidgetConfig(object):
    allow_buttons = ('style',
                     'bold',
                     'italic',
                     'numlist',
                     'bullist',
                     'link',
                     'unlink',
                     )
    redefine_parastyles = True
    parastyles = (_('Heading') + '|h2|',
                  _('Subheading') + '|h3|',
                  )


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


class BlogFileEditForm(edit.DefaultEditForm):

    description = None

    portal_type = 'File'

    def __call__(self):
        formHelper(self,
                   fields_to_show=['image'],
                   fields_to_input=['title', 'description'],
                   fields_to_hide=['IPublication.effective',
                                   'IPublication.expires',
                                   'ICategorization.subjects',
                                   'ICategorization.language',
                                   'IRelatedItems.relatedItems',
                                   'IOwnership.creators',
                                   'IOwnership.contributors',
                                   'IOwnership.rights',
                                   'IAllowDiscussion.allow_discussion',
                                   'IExcludeFromNavigation.exclude_from_nav',
                                   ],
                   fields_to_omit=['IVersionable.changeNote'])

        buttons = self.buttons
        for button in buttons.values():
            #button.klass = u' button large round'
            if button.__name__ == 'save':
                button.title = _(u'Save')
        return super(BlogFileEditForm, self).__call__()

    def label(self):
        return None


class BlogImageEditForm(edit.DefaultEditForm):

    description = None
    portal_type = 'Image'

    def __call__(self):
        formHelper(self,
                   fields_to_show=['image'],
                   fields_to_input=['title', 'description'],
                   fields_to_hide=['IPublication.effective',
                                   'IPublication.expires',
                                   'ICategorization.subjects',
                                   'ICategorization.language',
                                   'IRelatedItems.relatedItems',
                                   'IOwnership.creators',
                                   'IOwnership.contributors',
                                   'IOwnership.rights',
                                   'IAllowDiscussion.allow_discussion',
                                   'IExcludeFromNavigation.exclude_from_nav',
                                   ],
                   fields_to_omit=['IVersionable.changeNote'])

        buttons = self.buttons
        for button in buttons.values():
            #button.klass = u' button large round'
            if button.__name__ == 'save':
                button.title = _(u'Save')

        return super(BlogImageEditForm, self).__call__()

    def label(self):
        return None


class BlogCommentAddForm(add.DefaultAddForm):

    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    def __init__(self, context, request, ti=None):
        alsoProvides(self.request, IBlogCommentFormLayer)
        super(BlogCommentAddForm, self).__init__(context, request, ti=ti)

    def __call__(self):
        self.portal_type = self.context.portal_type
        text = self.schema.get('text')
        text.widget = RichTextWidgetConfig()
        self.updateWidgets()
        return super(BlogCommentAddForm, self).__call__()


class BlogRenderWidget(RenderWidget):
    index = ViewPageTemplateFile('templates/widget.pt')


class BlogCommentsViewlet(CommentsViewlet):

    def update(self):
        alsoProvides(self.request, IBlogCommentFormLayer)
        super(BlogCommentsViewlet, self).update()

    def can_reply(self):
        is_blog_entry = (self.context.portal_type == 'Blog Entry')
        is_private = (api.content.get_state(self.context) == 'private')
        if is_blog_entry and is_private:
            return False
        return super(BlogCommentsViewlet, self).can_reply()


def formHelper(form, fields_to_show=[], fields_to_input=[], fields_to_hide=[], fields_to_omit=[]):

    form.updateWidgets()

    form.updateFields()
    fields = form.fields
    groups = form.groups

    for field in fields.values():
        if field.__name__ in fields_to_omit:
            field.omitted = True
        if field.__name__ in fields_to_hide:
            field.omitted = False
            field.mode = HIDDEN_MODE
        if field.__name__ in fields_to_show:
            field.omitted = False
            field.mode = DISPLAY_MODE
        if field.__name__ in fields_to_input:
            field.omitted = False
            field.mode = INPUT_MODE

    for group in groups:
        for field in group.fields.values():
            if field.__name__ in fields_to_omit:
                field.omitted = True
            if field.__name__ in fields_to_hide:
                field.omitted = False
                field.mode = HIDDEN_MODE
            if field.__name__ in fields_to_show:
                field.omitted = False
                field.mode = DISPLAY_MODE
            if field.__name__ in fields_to_input:
                field.omitted = False
                field.mode = INPUT_MODE
