# coding=utf-8
from lmu.contenttypes.blog.behaviors.video_thumb import IVideoThumb
from logging import getLogger
from plone import api


logger = getLogger(__name__)


def enable_video_thumb(context):
    ''' We have a new behavior to extract video thumbnails
    '''
    identifier = IVideoThumb.__identifier__
    candidate_types = ('File', )
    pt = api.portal.get_tool('portal_types')
    for candidate_type in candidate_types:
        fti = pt.get(candidate_type)
        if fti and identifier not in fti.behaviors:
            # Add the behavior for our selected types if missing
            fti.behaviors += (identifier, )

    # Try to generate the thumbnails for the existing content
    [
        IVideoThumb(b.getObject()).generate()
        for b in api.content.find(portal_type='File')
    ]
