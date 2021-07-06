from django import template
from photo.settings import SITE_URL, SHOW_ALBUM_SHARE_BUTTONS_TOP, SHOW_ALBUM_SHARE_BUTTONS_BOTTOM
from urlparse import urljoin
from cgi import escape

TEMPLATE_BASE = '<ul class="share-buttons">{0}</ul>'
TEMPLATE_URL = '<li><a rel="nofollow" href="{0}" target="_blank"><img src="/static/share-icons/{1}" alt="Share {2}" /></a></li>'

FACEBOOK = ('https://www.facebook.com/sharer/sharer.php?u={0}&t={1}', 'Facebook.png', 'on Facebook')
TWITTER = ('https://twitter.com/intent/tweet?text={1}:+{0}', 'Twitter.png', 'on Twitter')
GOOGLE = ('https://plus.google.com/share?url={0}', 'Google+.png', 'on Google+')
PINTEREST = ('http://pinterest.com/pin/create/button/?url={0}&description={1}&media={2}', 'Pinterest.png', 'on Pinterest')
TUMBLR = ('http://www.tumblr.com/share', 'Tumblr.png', 'on Tumblr')
MAIL = ('mailto:?subject={1}&body={1}:%20{0}', 'Email.png', 'by Email')

ENABLED_BUTTONS = [FACEBOOK, TWITTER, GOOGLE, PINTEREST, TUMBLR, MAIL]

for i, item in enumerate(ENABLED_BUTTONS):
    ENABLED_BUTTONS[i] = TEMPLATE_URL.format(escape(item[0]), item[1], item[2]) 

def photo_share_buttons(url, text, img):
    if url.startswith('/'): url = urljoin(SITE_URL, url)
    if img.startswith('/'): img = urljoin(SITE_URL, img)
    links = []
    for button in ENABLED_BUTTONS:
        links += button.format(url, text, img)
    code = TEMPLATE_BASE.format(''.join(links))
    return code

register = template.Library()

register.simple_tag(photo_share_buttons, name='photo_share_buttons')

register.assignment_tag(lambda: SHOW_ALBUM_SHARE_BUTTONS_TOP, name='sb_top_as')
register.assignment_tag(lambda: SHOW_ALBUM_SHARE_BUTTONS_BOTTOM, name='sb_bottom_as')
