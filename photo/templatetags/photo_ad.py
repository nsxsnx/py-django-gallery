from django import template
from photo.settings import SHOWALBUM_AD_CONTENT_ABOVE, SHOWALBUM_AD_CONTENT_BELOW, SHOWALBUM_AD_CONTENT_INSIDE, SHOWALBUM_AD_FOOTER, ERROR_AD_CONTENT_ABOVE, ERROR_AD_CONTENT_INSIDE, ERROR_AD_CONTENT_BELOW, ERROR_AD_FOOTER
from photo.settings import SHOWALBUMS_AD_CONTENT_ABOVE, SHOWALBUMS_AD_CONTENT_BELOW, SHOWALBUMS_AD_CONTENT_INSIDE, SHOWALBUMS_AD_FOOTER
from photo.settings import ALERT, POPUP, HIST_LINK
from random import shuffle, choice
from django.utils.safestring import mark_safe

HTML_TEMPLATE = """    <div class="carousel slide inline {2}" data-ride="carousel">
                 <ol class="carousel-indicators">{0} 
                 </ol>
                 <div class="carousel-inner">{1} 
                 </div>
             </div>\n"""

HTML_ITEM = """\n                     <div class="item">{0}</div>"""
HTML_ITEM_FIRST ="""\n                     <div class="item active">{0}</div>"""
HTML_LI = """\n                     <li data-target="#{0}" data-slide-to="{1}"></li>"""
HTML_LI_FIRST = """\n                     <li data-target="#{0}" data-slide-to="0" class="active"></li>"""
ADS_SHOWALBUM = {
        'bd_ca':  SHOWALBUM_AD_CONTENT_ABOVE,
        'bd_cb':  SHOWALBUM_AD_CONTENT_BELOW,
        'bd_foo': SHOWALBUM_AD_FOOTER,
        'bd_ci_sa': SHOWALBUM_AD_CONTENT_INSIDE,
      }
ADS_SHOWALBUMS = {
        'bd_ca':  SHOWALBUMS_AD_CONTENT_ABOVE,
        'bd_cb':  SHOWALBUMS_AD_CONTENT_BELOW,
        'bd_foo': SHOWALBUMS_AD_FOOTER,
        'bd_ci_sas': SHOWALBUMS_AD_CONTENT_INSIDE,
      }
ADS_SHOWERROR = {
        'bd_ca':  ERROR_AD_CONTENT_ABOVE,
        'bd_cb':  ERROR_AD_CONTENT_BELOW,
        'bd_foo': ERROR_AD_FOOTER,
        'bd_ci': ERROR_AD_CONTENT_INSIDE,
      }

HTML_TEMPLATE_SIMPLE = """<div class="centered {0}">\n{1}\n</div>"""

def photo_ad(id, view_name = ''):
    RANDOM = False
    if view_name == 'show_album': ADS = ADS_SHOWALBUM
    elif view_name == 'show_albums': ADS = ADS_SHOWALBUMS
    elif view_name == 'show_error': ADS = ADS_SHOWERROR
    else: ADS = {}
    try: ad = ADS[id]
    except KeyError: ad = ''
    if not ad: return ''
    if isinstance(ad, basestring): return mark_safe(HTML_TEMPLATE_SIMPLE.format(id, ad))
    if len(ad) == 1: return mark_safe(HTML_TEMPLATE_SIMPLE.format(id, ad[0]))
    if isinstance(ad, tuple): RANDOM = True
    ad = [a for a in ad if a]
    if not ad: return ''
    if RANDOM: 
        ad = choice(ad)
        return mark_safe(HTML_TEMPLATE_SIMPLE.format(id, ad))
    shuffle(ad)
    html_li = [HTML_LI_FIRST.format(id, 0)]
    html_inner = [HTML_ITEM_FIRST.format(ad[0])]
    for i, item in enumerate(ad[1:], start=1):
        html_li.append(HTML_LI.format(id, i))
        html_inner.append(HTML_ITEM.format(item))
    return mark_safe(HTML_TEMPLATE.format(''.join(html_li), ''.join(html_inner), id))

register = template.Library()
register.simple_tag(photo_ad, name='photo_ad')
register.assignment_tag(lambda: ALERT, name='photo_alert_as')
register.assignment_tag(lambda: POPUP, name='photo_popup_as')
register.assignment_tag(lambda: HIST_LINK,  name='photo_hist_link_as')
