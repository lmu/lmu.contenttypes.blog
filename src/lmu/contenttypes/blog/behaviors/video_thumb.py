# -*- coding: utf-8 -*-
from lmu.contenttypes.blog import MESSAGE_FACTORY as _
from logging import getLogger
from plone import api
from plone.app.blob.utils import openBlob
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior import AnnotationStorage
from plone.namedfile import field as namedfile
from plone.namedfile import NamedBlobImage
from plone.supermodel import model
from zope.interface import Interface
from zope.interface import provider

import subprocess
import tempfile


logger = getLogger(__name__)


@provider(IFormFieldProvider)
class IVideoThumb(model.Schema):

    directives.omitted('video_thumb')
    video_thumb = namedfile.NamedBlobImage(
        title=_('label_video_thumb', default=u'Video thumbnail'),
        description=u'',
        required=False,
    )


class IVideoThumbAware(Interface):
    ''' Marker interface for an object that is aware of video thumbnails
    '''


class VideoThumbStorage(AnnotationStorage):
    ''' Add additional methods to this behavior
    '''

    def generate(self, force=False):
        ''' Generate the preview from the file attribute

        It tries to spare cpu cycles by generating the thumbnail only if the
        file is actually changed.
        For this reason a _video_size parameter on the video_thumb is set
        '''
        mtr = api.portal.get_tool('mimetypes_registry')
        video = self.schema.file

        try:
            mime_type_description = mtr.lookup(video.contentType)[0].id
        except:
            logger.exception('Cannot check mimetype')
            mime_type_description = ''

        if not mime_type_description == 'MPEG-4 video':
            self.schema.video_thumb = None
            return

        if not force:
            cached_size = getattr(self.schema.video_thumb, '_video_size', None)
            if cached_size == video.size:
                # Highly improbable that a new video with the same size
                # replaced the old one. We have nothing to do here
                return

        fd, tmpfile = tempfile.mkstemp()

        with openBlob(video) as f:
            cmd = 'ffmpegthumbnailer -s 0 -i {infile} -o {oufile}'.format(
                infile=f.name,
                oufile=tmpfile,
            )
            try:
                subprocess.call(cmd.split())
            except:
                self.schema.video_thumb = None
                logger.exception('Error running command %r', cmd)
                return

        thumb_name = video.filename.rpartition('.')[0] + u'.png'

        with open(tmpfile, 'rb') as thumb:
            nbi = NamedBlobImage(
                thumb.read(),
                filename=thumb_name,
            )
            nbi._video_size = video.size
            self.schema.video_thumb = nbi
