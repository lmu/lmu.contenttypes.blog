# -*- coding: utf-8 -*-

from Products.CMFCore import permissions
from Products.CMFPlone.browser.ploneview import Plone
from Products.CMFPlone.PloneBatch import Batch
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import json
from collective.quickupload.portlet.quickuploadportlet import Assignment
from collective.quickupload.portlet.quickuploadportlet import Renderer
from datetime import datetime
from plone import api
from plone.app.discussion.browser.comments import CommentsViewlet
from plone.app.textfield.interfaces import ITransformer
from plone.app.z3cform.templates import RenderWidget
#from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser import edit
from plone.dexterity.browser import add
#from plone.z3cform.fieldsets.utils import move
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import INPUT_MODE
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
#from zope.schema import getFieldsInOrder


#from lmu.contenttypes.blog.interfaces import IBlogEntry
from lmu.contenttypes.blog.interfaces import IBlogFolder
from lmu.contenttypes.blog.interfaces import IBlogCommentFormLayer

from lmu.contenttypes.blog import MESSAGE_FACTORY as _
#from lmu.contenttypes.blog import logger

from Products.CMFPlone.utils import transaction_note
from AccessControl import Unauthorized
from Acquisition import aq_parent
from logging import getLogger

logging = getLogger(__name__)


def str2bool(v):
    return v is not None and v.lower() in ['true', '1']


class _AbstractBlogView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_memberdata(self, item):
        pmt = api.portal.get_tool(name='portal_membership')
        member_id = item.Creator()
        member = pmt.getMemberById(member_id)
        return member

    def strip_text(self, item, length=500):
        transformer = ITransformer(item)
        transformedValue = transformer(item.text, 'text/plain')
        striped_length = len(transformedValue)
        if striped_length > length:
            striped_length = transformedValue.rfind(' ', 0, length)
            transformedValue = transformedValue[:striped_length] + '...'
        return transformedValue

    def _strip_text(self, item, length=500, ellipsis='...'):
        transformer = ITransformer(item)
        transformedValue = transformer(item.text, 'text/plain')
        return Plone.cropText(transformedValue, length=length, ellipsis=ellipsis)

    def images(self):
        #image_brains = api.content.find(context=self.context, depth=1, portal_type='Image')
        #images = [item.getObject() for item in image_brains]
        #import ipdb; ipdb.set_trace()
        images = [item for item in self.context.values() if item.portal_type == 'Image']
        if None in images:
            images.remove(None)
        return images

    def files(self):
        files = [item for item in self.context.values() if item.portal_type == 'File']
        if None in files:
            files.remove(None)
        #import ipdb; ipdb.set_trace()
        return files

    def getFileSize(self, fileobj):
        size = fileobj.file.getSize()
        if size < 1000:
            size = str(size) + ' Byte'
        elif size > 1024 and size/1024 < 1000:
            size = str(fileobj.file.getSize() / 1024) + ' KB'
        else:
            size = str(fileobj.file.getSize() / 1024 / 1024) + ' MB'
        return size

    def getFileType(self, fileobj):
        ctype = fileobj.file.contentType
        ctype = ctype.split('/')
        return str.upper(ctype[1])

    def _check_permission(self, permission, item):
        pmt = api.portal.get_tool(name='portal_membership')
        return pmt.checkPermission(permission, item)


class _AbstractBlogListingView(_AbstractBlogView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

        limit_display = getattr(self.request, 'limit_display', None)
        limit_display = int(limit_display) if limit_display is not None else 20
        b_size = getattr(self.request, 'b_size', None)
        self.b_size = int(b_size) if b_size is not None else limit_display
        b_start = getattr(self.request, 'b_start', None)
        self.b_start = int(b_start) if b_start is not None else 0

        self.content_filter = {
            'portal_type': 'Blog Entry',
        }

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
        return api.user.has_permission('lmu.contenttypes.blog: Add Blog Entry',
                                       #     permissions.AddPortalContent,
                                       obj=self.context)


class ListingView(_AbstractBlogListingView):

    template = ViewPageTemplateFile('templates/listing_view.pt')

    def __call__(self):
        return self.template()


class FrontPageIncludeView(_AbstractBlogListingView):

    template = ViewPageTemplateFile('templates/frontpage_view.pt')

    def update(self):
        """
        """
        # Hide the editable-object border
        request = self.request
        request.set('disable_border', True)

    def __call__(self):
        omit = self.request.get('full')
        self.omit = not str2bool(omit)
        author = self.request.get('author')
        self.author = bool(author)
        if 'b_size' not in self.request:
            self.request.set('b_size', '3')
        if self.omit:
            REQUEST = self.context.REQUEST
            RESPONSE = REQUEST.RESPONSE
            RESPONSE.setHeader('Content-Type', 'text/xml;charset=utf-8')
        # import ipdb; ipdb.set_trace()
        return self.template()


class EntryView(_AbstractBlogView):

    template = ViewPageTemplateFile('templates/entry_view.pt')

    def __call__(self):
        return self.template()

    def can_see_history(self):
        return True

    def can_edit(self):
        return api.user.has_permission(permissions.ModifyPortalContent, obj=self.context)

    def can_remove(self):
        """Only show the delete-button if the user has the permission to delete
        items and the workflow_state fulfills a condition.
        """
        state = api.content.get_state(obj=self.context)
        can_delete = api.user.has_permission(
            permissions.DeleteObjects, obj=self.context)
        if can_delete and state not in ['banned']:
            return True

    def can_publish(self):
        return api.user.has_permission(permissions.ReviewPortalContent, obj=self.context)

    def can_set_private(self):
        return api.user.has_permission(permissions.ReviewPortalContent, obj=self.context)

    def can_lock(self):
        return api.user.has_permission(permissions.ReviewPortalContent, obj=self.context)

    def isOwner(self):
        user = api.user.get_current()
        return 'Owner' in user.getRolesInContext(self.context)

    def isReviewer(self):
        user = api.user.get_current()
        return 'Reviewer' in user.getRolesInContext(self.context)

    def isManager(self):
        user = api.user.get_current()
        return any(role in user.getRolesInContext(self.context) for role in ['Manager', 'SiteAdmin'])


class EntryContentView(_AbstractBlogView):

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
        for current, obj in enumerate(reversed(self.context.objectValues())):
            if type_test(obj.portal_type):
                item = {'url': obj.absolute_url(),
                        'id': obj.getId(),
                        'title': obj.Title()}
                if mode == 'files':
                    item['tag'] = plone_layout.getIcon(obj).html_tag()
                if previous > -1:
                    item['delta_up'] = current - previous
                items.append(item)
                previous = current
            else:
                items.append({})
        previous = -1
        for current, obj in enumerate(self.context.objectValues()):
            if type_test(obj.portal_type):
                if previous > -1:
                    items[-1 - current]['delta_down'] = previous - current
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


class EntrySortFilesView(_AbstractBlogView):

    template = ViewPageTemplateFile('templates/entry_content_view.pt')

    def __call__(self):
        return self.template()


class EntrySortImagesView(_AbstractBlogView):

    template = ViewPageTemplateFile('templates/entry_content_view.pt')

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
    description = _(u'Geben Sie zunächst den Titel und Text Ihres Blog-Beitrags an, und klicken Sie auf "Weiter". Danach können Sie Bilder und / oder Dateien hinzufügen.')

    def __call__(self):
        self.updateWidgets()

        text = self.schema.get('text')
        text.widget = RichTextWidgetConfig()

        self.updateFields()
        fields = self.fields

        cn = fields.get('IVersionable.changeNote')
        cn.omitted = True
        cn.mode = HIDDEN_MODE

        return super(BlogEntryAddForm, self).__call__()


class BlogEntryAddView(add.DefaultAddView):
    form = BlogEntryAddForm


class BlogEntryEditForm(edit.DefaultEditForm):
    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    description = None

    portal_type = 'Blog Entry'

    def __call__(self):
        fields_to_show = ['file']
        fields_to_input = ['title', 'description']
        fields_to_hide = []
        fields_to_omit = ['IPublication.effective', 'IPublication.expires', 'IVersionable.changeNote']

        self.updateWidgets()

        text = self.schema.get('text')
        text.widget = RichTextWidgetConfig()

        self.updateFields()
        fields = self.fields

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

        for group in self.groups:
            for field in group.fields.values():
                if field.__name__ in fields_to_omit:
                    field.field.omitted = True
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
            if group.__name__ in ['dates']:
                group.omitted = True

        #self.updateActions()
        #actions = self.actions

        buttons = self.buttons

        import ipdb; ipdb.set_trace()
        for button in buttons.values():
            button.klass = u' button large round'

        return super(BlogEntryEditForm, self).__call__()


class BlogFileEditForm(edit.DefaultEditForm):

    description = None

    portal_type = 'File'

    def __call__(self):
        fields_to_show = ['file']
        fields_to_input = ['title', 'description']
        fields_to_hide = []

        self.updateWidgets()

        self.updateFields()
        fields = self.fields

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

        for group in self.groups:
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

        return super(BlogFileEditForm, self).__call__()

    def label(self):
        return None


class BlogImageEditForm(edit.DefaultEditForm):

    description = None
    portal_type = 'Image'

    def __call__(self):
        fields_to_show = ['image']
        fields_to_input = ['title', 'description']
        fields_to_hide = []
        fields_to_omit = []

        self.updateWidgets()

        self.updateFields()
        fields = self.fields

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

        for group in self.groups:
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
        #import ipdb; ipdb.set_trace()
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
