from django import template
from photo.settings import GA_ENABLED, GA_ID, GA_SITE

register = template.Library()

register.simple_tag(lambda: GA_ID, name='photo_ga_id')
register.simple_tag(lambda: GA_SITE, name='photo_ga_site')

register.assignment_tag(lambda: GA_ENABLED, name='photo_ga_enabled')
