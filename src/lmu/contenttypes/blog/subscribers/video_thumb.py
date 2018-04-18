# coding=utf-8
from lmu.contenttypes.blog.behaviors.video_thumb import IVideoThumb


def generate(obj, event=None):
    ''' Create a video thumb if needed
    '''
    IVideoThumb(obj).generate()
