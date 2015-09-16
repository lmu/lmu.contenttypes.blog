# -*- coding: utf-8 -*-

from Products.CMFCore import permissions
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import json
from collective.quickupload.portlet.quickuploadportlet import Assignment
from collective.quickupload.portlet.quickuploadportlet import Renderer
from datetime import datetime
from plone import api
from plone.app.textfield.interfaces import ITransformer
#from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser import edit
from plone.dexterity.browser import add
from z3c.form.interfaces import HIDDEN_MODE
#from z3c.form.interfaces import DISPLAY_MODE
#from z3c.form.interfaces import INPUT_MODE
from zope.component import getMultiAdapter
#from zope.schema import getFieldsInOrder


#from lmu.contenttypes.blog.interfaces import IBlogEntry
from lmu.contenttypes.blog.interfaces import IBlogFolder

from lmu.contenttypes.blog import MESSAGE_FACTORY as _
#from lmu.contenttypes.blog import logger


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

    def images(self):
        #image_brains = api.content.find(context=self.context, depth=1, portal_type='Image')
        #images = [item.getObject() for item in image_brains]
        #import ipdb; ipdb.set_trace()
        images = [item for item in self.context.values()if item.portal_type == 'Image']
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

    def entries(self):
        entries = []
        if IBlogFolder.providedBy(self.context):
            content_filter = {
                'portal_type': 'Blog Entry',
                #'review_state': ['published', 'internal-published', 'internally_published'],
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

    def can_add(self):
        #current_user = api.user.get_current()
        #import ipdb; ipdb.set_trace()
        #return api.user.has_permission(permissions.AddPortalContent, user=current_user, obj=self.context)
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
        #import ipdb; ipdb.set_trace()
        return self.template()


class EntryView(_AbstractBlogView):

    template = ViewPageTemplateFile('templates/entry_view.pt')

    def __call__(self):
        #import ipdb; ipdb.set_trace()
        return self.template()

    def can_see_history(self):
        return True

    def can_edit(self):
        #import ipdb; ipdb.set_trace()
        return api.user.has_permission(permissions.ModifyPortalContent, obj=self.context)

    def can_remove(self):
        return api.user.has_permission(permissions.DeleteObjects, obj=self.context)

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
        #import ipdb; ipdb.set_trace()
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
    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    portal_type = 'Blog Entry'

    def __call__(self):
        #import ipdb; ipdb.set_trace()
        self.updateWidgets()

        text = self.schema.get('text')
        text.widget = RichTextWidgetConfig()

        self.updateFields()
        fields = self.fields

        cn = fields.get('IVersionable.changeNote')
        cn.omitted = True
        cn.mode = HIDDEN_MODE

        return super(BlogEntryAddForm, self).__call__()


class BlogEntryEditForm(edit.DefaultEditForm):
    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    description = None

    portal_type = 'Blog Entry'

    def __call__(self):

        self.updateWidgets()
        #import ipdb; ipdb.set_trace()
        #self.portal_type = self.context.portal_type
        text = self.schema.get('text')
        text.widget = RichTextWidgetConfig()

        self.updateFields()
        fields = self.fields

        cn = fields.get('IVersionable.changeNote')
        cn.omitted = True
        cn.mode = HIDDEN_MODE

        self.updateActions()
        actions = self.actions

        for action in actions.values():
            action.klass = action.klass + u' button large round'

        return super(BlogEntryEditForm, self).__call__()


class BlogFileEditForm(edit.DefaultEditForm):

    description = None

    def __call__(self):
        fields_to_show = ['title', 'description']

        self.portal_type = self.context.portal_type

        self.updateFields()
        fields = self.fields

        for field in fields.values():
            if field.__name__ not in fields_to_show:
                field.omitted = True
                field.mode = HIDDEN_MODE

        for group in self.groups:
            for field in group.fields.values():
                if field.__name__ not in fields_to_show:
                    field.omitted = True
                    field.mode = HIDDEN_MODE

        self.updateWidgets()
        return super(BlogFileEditForm, self).__call__()

    def label(self):
        return None


class BlogImageEditForm(edit.DefaultEditForm):

    description = None

    def __call__(self):
        fields_to_show = ['title', 'description']

        self.portal_type = self.context.portal_type

        self.updateFields()
        fields = self.fields

        for field in fields.values():
            if field.__name__ not in fields_to_show:
                field.omitted = True
                field.mode = HIDDEN_MODE

        for group in self.groups:
            for field in group.fields.values():
                if field.__name__ not in fields_to_show:
                    field.omitted = True
                    field.mode = HIDDEN_MODE

        self.updateWidgets()
        return super(BlogImageEditForm, self).__call__()

    def label(self):
        return None


class BlogCommentAddForm(add.DefaultAddForm):

    template = ViewPageTemplateFile('templates/blog_entry_edit.pt')

    def __call__(self):
        self.portal_type = self.context.portal_type
        text = self.schema.get('text')
        #import ipdb; ipdb.set_trace()
        text.widget = RichTextWidgetConfig()
        self.updateWidgets()
        return super(BlogCommentAddForm, self).__call__()
