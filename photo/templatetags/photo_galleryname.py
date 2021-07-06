from django import template
from photo.settings import GALLERY_NAME

register = template.Library()

register.simple_tag(lambda: GALLERY_NAME, name='photo_galleryname')
