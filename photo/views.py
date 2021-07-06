from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from gallery.settings import MEDIA_URL
from photo.settings import UPLOAD_PATH, MIN_IMG_SIZE_SUM, SEARCH_COLUMNS, ALBUMS_PER_PAGE, URL_SRCH_DLMTR, STRIP_EXIF_COMMAND, STRIP_EXIF_DATA, SHOW_ALBUMS_STYLE_FULL, IMG_URL_REPLACE, PRESERVE_FILENAME, ALBUM_DESCR_NAME, ALBUM_INITIAL_NAME, DEFAULT_PARENT_TAG, SHOW_VIEWSTYLE_ICONS, UPLOAD_BY, MAX_ALBUM_NAME_LENGTH, MAX_TAG_NAME_LENGTH, IMAGE_NAME_PREFIX_LENGTH, SHOW_ALBUM_BOTTOM_TAGS, SHOW_CATEGORIES_SEARCH_TAGS_MAX, MAIN_PAGE_TITLE, SHOW_CATEGORIES_SHOW_ALL, SHOW_PARENT_TAG_SHOW_ALL, CONTACTFORM_SUBJECT_PREFIX, CONTACTFORM_RECIPIENTS, CONTACTFORM_MESSAGE_SUCCESS, CONTACTFORM_MESSAGE_ERROR, CONTACTFORM_ENABLED, CONTACTFORM_MESSAGE, SHOW_ALBUM_SIMILAR_ALBUMS_FAST, EXTERNAL_LINKS, GALLERY_NAME, SHOW_ALBUMS_META_DESCRIPTION, SHOW_ALBUMS_META_DESCRIPTION_TAGGED, SHOW_ALBUM_SIMILAR_ALBUMS_HEADER, ALL_TAGS_PAGE_ENABLED, SHOW_ALBUMS_ADS_PER_PAGE, SHOW_ALBUMS_PAGINATION_MAXPAGE, PAGINATION_BTN_TEXT, SPECIAL_BUTTON, SHOWALBUM_IMAGE_LINK, SHOW_ALBUM_VIEWS_COUNT, SHOW_ALBUM_VIEWS_COUNT_BOTS, SHOW_ALBUM_GVIEWS_COUNT, SHOW_ALBUM_DEFAULT_DESCRIPTION

from photo.models import *
from photo.lib import get_pages_list, get_tag_tree, get_similar_albums, get_similar_albums_fast, MyPaginator
import re
from django.core.mail import send_mail
from random import randint
from django.db.models import F
from django.views.decorators.cache import cache_page

#AdminCP
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.datastructures import MultiValueDictKeyError
from os import walk, listdir
from os.path import join, isdir, basename, splitext
import urllib2
from PIL import Image as PImage
from cStringIO import StringIO
from urlparse import urljoin, urlsplit
from tempfile import mkdtemp
from django.core.files import File
from os import remove, rmdir, system
from threading import Thread
from photo.forms import AddAlbumForm, ContactForm
from json import load
from datetime import datetime
from django.utils.text import slugify

@cache_page(86400)
def show_albums(request, page_id = '1', filter = ''):
    view_name = 'show_albums'
    page = int(page_id)
    template = 'show_albums.html'
    menu_tag = None
    items = Album.objects.none()
    # tags pages:
    if filter: 
        tags = filter.split(URL_SRCH_DLMTR)[:SHOW_CATEGORIES_SEARCH_TAGS_MAX]
        l = len(tags)
        if l == 1: 
            try: node = Tag.objects.get(name=filter, public = True)
            except: node = False
            if node:
                menu_tag = node
                # parent tag - descendants (tags):
                if node.parent_id is None:
                    items = node.get_descendants(include_self=False)
                    if not SHOW_PARENT_TAG_SHOW_ALL: items = items.filter(featured=True)
                    template = 'show_parent_tag.html'
                #single tag (albums):
                else: items = node.album_set.all()
        # multi tag (albums):
        else:   
            tags = Tag.objects.filter(name__in=tags, public = True)
            if len(tags) == l: items = reduce(lambda album_filter, x: album_filter.filter(tags=x), tags, Album.objects)
    # albums pages:
    else: items = Album.objects.all()
    items = items.filter(public=True).select_related('cover')
    paginator = MyPaginator(items, ALBUMS_PER_PAGE)
    # try to avoid count(*) query, using precalculated value:
    if filter: # on tag page(incl. parent tag)
        try: paginator._count = node.counter
        except: pass
    else: # on show_album
        try: paginator._count = Album.objects.latest('id').id
        except: paginator._count = 0
    if paginator.num_pages > SHOW_ALBUMS_PAGINATION_MAXPAGE: paginator.num_pages = SHOW_ALBUMS_PAGINATION_MAXPAGE
    if page > paginator.num_pages:
        if filter: return HttpResponseRedirect(reverse('photo.views.show_albums', kwargs={'filter':filter}))
        else: return HttpResponseRedirect(reverse('photo.views.show_albums'))
    items = paginator.page(page)
    #items.show_pages = get_pages_list(page, paginator.num_pages)
    menu = get_tag_tree(menu=True)
    # ad_pos:
    grp_len = ALBUMS_PER_PAGE/SHOW_ALBUMS_ADS_PER_PAGE
    rpos = randint(1, grp_len)
    # to set AD at the end (5th position) of random string:
    rpos = randint(1, 5)*5
    if rpos == 25: rpos = rpos-1 # last string has 4 elements
    #
    ad_pos = [rpos + i*grp_len  for i in range(0, ALBUMS_PER_PAGE/grp_len)]
    # title, description:
    if filter:
        t_filter = filter.replace('-', ' ').replace('_', ' ').replace(URL_SRCH_DLMTR, ' ')
        if page == 1: title = '{0} - {1}'.format(t_filter, GALLERY_NAME)
        else: title = '{0} | Page {1} - {2}'.format(t_filter, str(page), GALLERY_NAME)
        keywords = filter.replace(URL_SRCH_DLMTR, ', ')
        description = SHOW_ALBUMS_META_DESCRIPTION_TAGGED.format(keywords)
        page_h1 = '{0} - {1}'.format(t_filter, GALLERY_NAME)
    else: 
        if page == 1: title = MAIN_PAGE_TITLE
        else: title = '{0} | Page {1}'.format(GALLERY_NAME, str(page))
        #k_list = Tag.objects.filter(album__in = items).values_list('name', flat=True)
        #k_list = sorted(set(k_list[:20]))
        #keywords = ', '.join(k_list)
        description = SHOW_ALBUMS_META_DESCRIPTION
        page_h1 = GALLERY_NAME
    return render(request, template, 
            {'page': page, 'albums':items, 'tags':items, 'media_url':MEDIA_URL, 'menu':menu, 'ad_pos':ad_pos, 'filter':filter, 'menu_tag':menu_tag, 'style_full':SHOW_ALBUMS_STYLE_FULL, 'show_icons': SHOW_VIEWSTYLE_ICONS, 'bottom_tags': SHOW_ALBUM_BOTTOM_TAGS, 'title': title, 'description': description, 'page_h1': page_h1, 'view_name': view_name, 'pagination_btn_text': PAGINATION_BTN_TEXT, 'special_button': SPECIAL_BUTTON}
    )
    
@cache_page(3600)
def show_album(request, album_id, view = 't'):
    view_name = 'show_album'
    album_id = int(album_id)
    album = get_object_or_404(Album, pk=album_id)
    if not album.public and not request.user.is_superuser: raise Http404
    images = album.image_set.all()
    menu = get_tag_tree(menu=True)
    tags = get_tag_tree(album_id = album_id)
    if SHOW_ALBUM_SIMILAR_ALBUMS_FAST: similar_albums = get_similar_albums_fast()
    else: 
        album_tags_list = album.tags_as_list()
        similar_albums = get_similar_albums(album_tags_list)
    title = '{0} - {1}'.format(album.name, GALLERY_NAME)
    #keywords = ''
    #for tree in tags: keywords = ', '.join([keywords] + [t.name for t in tree[1:]])
    description = album.name
    similar_albums_header = SHOW_ALBUM_SIMILAR_ALBUMS_HEADER
    ad_pos = [1, 11]
    if not album.description:
        album.description = SHOW_ALBUM_DEFAULT_DESCRIPTION
        if '{0}' in album.description: album.description = album.description.format(album.name)
    if '{0}' in similar_albums_header: similar_albums_header = similar_albums_header.format(album.name)
    return render(request, 'show_album.html', 
            {'album': album, 'images': images, 'tags':tags, 'view': view, 'media_url': MEDIA_URL, 'menu':menu, 'ad_pos': ad_pos, 'show_icons': SHOW_VIEWSTYLE_ICONS, 'similar_albums': similar_albums, 'similar_albums_header': similar_albums_header, 'title': title, 'description': description, 'view_name': view_name, 'pagination_btn_text': PAGINATION_BTN_TEXT, 'special_button': SPECIAL_BUTTON, 'image_link': SHOWALBUM_IMAGE_LINK, 'views_count': SHOW_ALBUM_VIEWS_COUNT},
    )

def count_album(request, album_id):
    if SHOW_ALBUM_VIEWS_COUNT:
        if SHOW_ALBUM_VIEWS_COUNT_BOTS or 'http://' not in request.META['HTTP_USER_AGENT']:
            Album.objects.filter(pk=album_id).update(views = F('views') + 1)
    if SHOW_ALBUM_GVIEWS_COUNT:
        if 'Googlebot' in request.META['HTTP_USER_AGENT']:
            Album.objects.filter(pk=album_id).update(gviews = F('gviews') + 1)
    return HttpResponse('')

@cache_page(86400)
def show_categories(request):
    ptags = request.POST.getlist('tag')[:SHOW_CATEGORIES_SEARCH_TAGS_MAX]
    if ptags:
        filter = URL_SRCH_DLMTR.join(ptags)
        return HttpResponseRedirect(reverse('photo.views.show_albums', kwargs={'filter':filter}))
    menu = get_tag_tree(menu=True)
    if SHOW_CATEGORIES_SHOW_ALL: tags = get_tag_tree()
    else: tags = get_tag_tree(featured=True)
    return render(request, 'show_categories.html', {'menu':menu, 'tags':tags, 'cols': SEARCH_COLUMNS}, )

@cache_page(86400)
def show_all_tags(request):
    if not ALL_TAGS_PAGE_ENABLED: raise Http404
    menu = get_tag_tree(menu=True)
    tags = get_tag_tree()
    return render(request, 'show_all_tags.html', {'menu':menu, 'tags':tags, 'cols': SEARCH_COLUMNS}, )

def show_contact(request):
    if not CONTACTFORM_ENABLED: raise Http404
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            subject = CONTACTFORM_SUBJECT_PREFIX + form.cleaned_data['subject']
            message = CONTACTFORM_MESSAGE.format(name, form.cleaned_data['message'])
            sender = form.cleaned_data['email']
            recipients = CONTACTFORM_RECIPIENTS
            try: send_mail(subject, message, sender, recipients)
            except: return HttpResponse(CONTACTFORM_MESSAGE_ERROR)
            return HttpResponse(CONTACTFORM_MESSAGE_SUCCESS)
    else: form = ContactForm()
    menu = get_tag_tree(menu=True)
    return render(request, 'show_contact.html', {'menu': menu, 'form':form}, )

def show_go(request, link_name = ''):
    try: url = EXTERNAL_LINKS[link_name]
    except KeyError: raise Http404
    return HttpResponseRedirect(url)

def show_error(request, status_code, status_message, status_description = ''):
    view_name = 'show_error'
    menu = get_tag_tree(menu=True)
    similar_albums = get_similar_albums_fast()
    ad_pos = [1, 11]
    response = render(request, 'show_error.html',
            {'status': status_code, 'message': status_message, 'menu': menu, 'similar_albums': similar_albums, 'ad_pos': ad_pos, 'view_name': view_name, 'pagination_btn_text': PAGINATION_BTN_TEXT, 'special_button': SPECIAL_BUTTON, 'description': status_description},
            )
    response.status_code = status_code
    return response

    
def show_400(request): return show_error(request, 400, 'Bad request', 'Something went wrong =( Please reload the page or try again later')
def show_403(request): return show_error(request, 403, 'Permission denied', 'You are not allowed to access this page')
def show_404(request): return show_error(request, 404, 'Page not found', 'We could not find the page you were looking for on our servers')
def show_500(request): return show_error(request, 500, 'Server error', 'Something went wrong =( Please reload the page or try again later')


#AdminCP
@staff_member_required
def admin_albums_add(request):
    form = None
    err = ''
    if request.method == 'GET':
        form = AddAlbumForm(initial={'path': UPLOAD_PATH})
        return render(request, 'admin_albums_add.html', {'upload_path':UPLOAD_PATH, 'form':form})
    form = AddAlbumForm(request.POST)
    if form.is_valid():
        res = admin_albums_add_worker(form.cleaned_data['path'], form.cleaned_data['url'])
        if isinstance(res, str): err = res
        else:
            message = res[1]
            return render(request, 'admin_albums_add_result.html', {'message':message})
    return render(request, 'admin_albums_add.html', {'upload_path':UPLOAD_PATH, 'form':form, 'error_message':err})

def admin_albums_add_worker(path, url='', upload_by=UPLOAD_BY):
   message = ''
   #Get from web:
   def req_with_headers(url):
      surl = urlsplit(url)
      host = '{0}://{1}/'.format(surl[0], surl[1])
      req = urllib2.Request(url)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:29.0) Gecko/20100101 Firefox/29.0')
      req.add_header('Accept-Language', 'en;q=0.5')
      req.add_header('Referer', host)
      return urllib2.urlopen(req)

   if url: 
      if url[:7] != 'http://': url = 'http://' + url
      html = req_with_headers(url).read()
      try:
         r_head = '< *head *>(.*?)< */ *head *>'
         m = re.search(r_head, html, flags=re.DOTALL | re.IGNORECASE)
         html_head = m.group(1).lower()
         r_charset = 'charset=(.*?)["\' ]'
         m = re.search(r_charset, html_head)
         html_charset = m.group(1)
      except AttributeError: html_charset = 'utf8' #!! field to choose charset
      if not html_charset: html_charset = 'utf8' #!! field to choose charset
      html = html.decode(html_charset)

      r_qu = '(?:\'|")'
      r_imgsrc = '< *img [^>]*?src *= *' + r_qu
      r_ahref = '< *a [^>]*?href *= *' + r_qu
      r_ext = '(?:jpg|jpeg)'
      r = '(?:' + r_ahref + '|' + r_imgsrc + ')' + '([^>]+?\.' + r_ext + ') *' + r_qu

      m = re.findall(r, html, flags=re.DOTALL | re.IGNORECASE)
      cnt = 0
      if not len(m):
         return 'No images found at the given url'
      else:
         dir = mkdtemp(dir = path)

         def http_get_image_thread(dir, url, img_url, cnt):
            surl = urlsplit(url)
            host = '{0}://{1}/'.format(surl[0], surl[1])
            if img_url[:7] != 'http://': img_url = urljoin(host, img_url)
            host_short = re.sub('^www.', '', surl[1]).split(':')[0]
            if IMG_URL_REPLACE.has_key(host_short):
                img_url = re.sub(IMG_URL_REPLACE[host_short][0], IMG_URL_REPLACE[host_short][1], img_url)
            img = StringIO(req_with_headers(img_url).read())
            pimg = PImage.open(img)
            s1, s2 = pimg.size
            if s1 + s2 > MIN_IMG_SIZE_SUM:
               pimg.save(join(dir, 'img_' + str(cnt).zfill(3) + '.jpg'))
            
         threads = []
         for img_url in m:
            cnt += 1
            threads.append(Thread(target=http_get_image_thread, args=(dir, url, img_url, cnt)))
         [t.start() for t in threads]
         [t.join() for t in threads]

   #Upload from path:
   if not path: return 'No path given'
   if not listdir(path): return 'No files found in the upload path'
   albums, descrs = {}, {}
   for entry in listdir(path)[:upload_by]:
      entry = join(path, entry)
      if isdir(entry) and listdir(entry):
         images = []
	 for file in listdir(entry):
            lfile = join(entry, file)
            if file == ALBUM_DESCR_NAME:
               descrs[entry] = load(open(lfile))
               #remove(lfile)
               continue
            try: PImage.open(lfile).verify()
            except:
               remove(lfile)
               continue
            images += [lfile]
         albums[entry] = sorted(images)

   #Create albums:
   for dir in albums.iterkeys():
      if dir in descrs: descr = descrs[dir]
      else: descr = None
      album_name = ALBUM_INITIAL_NAME 
      try:
	      if descr['descr']: album_name = descr['descr']
      except (KeyError, TypeError): pass
      try:
         if descr['name']: album_name = descr['name']
      except (KeyError, TypeError): pass
      alb_name_len = MAX_ALBUM_NAME_LENGTH-IMAGE_NAME_PREFIX_LENGTH-1
      album_name = album_name[:alb_name_len]
      a = Album(name = album_name)
      a.save()
      if album_name == ALBUM_INITIAL_NAME[:alb_name_len]: a.name = album_name[:alb_name_len-6]+ '_' + str(a.id).zfill(5)
      imgs = albums[dir]

      def save_image_thread(i, file):
         pref = str(i.id).zfill(IMAGE_NAME_PREFIX_LENGTH) + '-'
         i.name = pref + i.name
         i.save()
	 if STRIP_EXIF_DATA: system(STRIP_EXIF_COMMAND + ' ' + file)
	 if PRESERVE_FILENAME: filename = pref + splitext(basename(file))[0]
	 else: filename = slugify(i.name.decode('utf-8'))
	 filename += '.jpg'
         i.image.save(filename, File(open(file)))
         remove(file)

      threads = []
      for file in imgs:
         i = Image(album = a, name = a.name)
         i.save()
         try:
            if descr['cover'] and file.endswith('/' + descr['cover']): a.cover = i
         except (KeyError, TypeError): pass
         save_image_thread(i, file)
         #threads.append(Thread(target=save_image_thread, args=(i, file)))
      #[t.start() for t in threads]
      #[t.join() for t in threads]

      try: remove(join(dir, ALBUM_DESCR_NAME))
      except: pass
      rmdir(dir)   
      if not a.cover: a.cover = a.image_set.first()
      
      try:
         if descr['tags']: tags = descr['tags'].split(',')
      except (KeyError, TypeError): pass
      else:
         for tag in tags:
            tag = tag.replace(URL_SRCH_DLMTR, '-').lower()[:MAX_TAG_NAME_LENGTH]
            t, cr = Tag.objects.get_or_create(name = tag.strip())
            if cr: t.save()
            a.tags.add(t)
            if cr or not t.cover: t.cover = a.image_set.first()
            t.parent, cr2 = Tag.objects.get_or_create(name = DEFAULT_PARENT_TAG)
	    t.save()
      for name in ['description', 'featured', 'no_watermark', 'public']:
         try:
            if descr[name]: 
	       if name == 'descr': a.__setattr__(self, 'name', descr[name])
	       else: a.__setattr__(name, descr[name])
         except (KeyError, TypeError): pass
      try:
         if descr['pub_date']: a.pub_date = datetime.strptime(descr['pub_date'], "%Y-%m-%d %H:%M:%S")
      except (KeyError, TypeError): pass

      a.save()
      a.recount()
      message += a.name + ' - ' + str(len(imgs)) + ' images <br/>'
   for d in listdir(path)[:upload_by]:
      try: rmdir(join(path, d))
      except: pass
   if not message: message = 'No albums created'
   return None, message
