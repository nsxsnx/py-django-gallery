from django import template
from photo.settings import MENU_MAIN, MENU_FOOTER

register = template.Library()

register.assignment_tag(lambda: MENU_MAIN, name='photo_menu_main_as')
register.assignment_tag(lambda: MENU_FOOTER, name='photo_menu_footer_as')
