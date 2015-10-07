import logging
from zope.i18nmessageid import MessageFactory

# Set up the i18n message factory for our package
MESSAGE_FACTORY = MessageFactory('lmu.contenttypes.blog')

logger = logging.getLogger('lmu.contenttypes.blog')
