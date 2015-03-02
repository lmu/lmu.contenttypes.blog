# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces.syndication import ISyndicatable

from Products.statusmessages.interfaces import IStatusMessage

#from plone.dexterity.content import Item
from plone.dexterity.content import Container

#from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.discussion.interfaces import IConversation
from plone.directives import form

from zope.interface import implements

from z3c.form import button

from lmu.contenttypes.blog.interfaces import IBlogFolder
from lmu.contenttypes.blog.interfaces import IBlogEntry
from lmu.contenttypes.blog.interfaces import IBlogReportForm

from lmu.contenttypes.blog import MessageFactory as _


class BlogFolder(Container):
    implements(IBlogFolder, ISyndicatable)


class BlogEntry(Container):
    implements(IBlogEntry)

    def getDiscussionCount(self):
        try:
            # plone.app.discussion.conversation object
            # fetched via IConversation adapter
            conversation = IConversation(self)
        except:
            return 0
        return conversation.total_comments


class BlogReportForm(form.SchemaForm):
    implements(IBlogReportForm)

    schema = IBlogReportForm
    ignoreContext = True

    label = _(u"Report a Blog Entry")
    description = _(u"Report a Blog Entry that violates the Blog rules.")

    @button.buttonAndHandler(_(u"Report Blog Entry"), name="report")
    def handle_report(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # Do something with valid data here

        # Set status on this form page
        # (this status message is not bind to the session
        # and does not go thru redirects)
        self.status = _(u"Thank you for your Report. E-Mail send to Webmaster.")
        IStatusMessage(self.request).addStatusMessage(
            _(u"Thank you for your Report. E-Mail send to Webmaster."),
            'info')
        redirect_url = self.context.absolute_url()
        self.request.response.redirect(redirect_url)

    @button.buttonAndHandler(u"Cancel")
    def handle_cancel(self, action):
        """User cancelled. Redirect back to the front page.
        """
        IStatusMessage(self.request).addStatusMessage(
            "Notting Reported",
            'info')
        redirect_url = self.context.absolute_url()
        self.request.response.redirect(redirect_url)

    def updateActions(self):
        super(BlogReportForm, self).updateActions()
        self.actions['cancel'].addClass("button")
        self.actions['report'].addClass("button")

#    def updateFields(self):
#        super(BlogReportForm, self).updateFields()
#        self.fields['url'].value = self.context.absolute_url()
