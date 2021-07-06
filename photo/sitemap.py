from os.path import join
from urlparse import urljoin
from itertools import combinations
from django.core.urlresolvers import reverse
import re, os, datetime
#from django.core.paginator import Paginator
from photo.settings import WWW_ROOT, SITEMAP_DIR, SITEMAP_FILES, SITEMAP_INDEX_FILE, SITE_URL, ALBUMS_PER_PAGE, SHOW_PARENT_TAG_SHOW_ALL, SHOW_ALBUMS_PAGINATION_MAXPAGE
from photo.models import Album, Tag
import gzip
from photo.lib import MyPaginator

class Sitemap:
    _HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" 
  xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
"""
    _FOOTER = """</urlset>
"""
    _FILE_MAX_URLS = 50000

    def __init__(self):
        self.filenumber = 0
        self.sitemapdir = join(WWW_ROOT, SITEMAP_DIR)
        if not os.path.exists(self.sitemapdir): os.makedirs(self.sitemapdir)

    def _init_file(self):
        self.urlcounter = 0
        self.filenumber += 1
        self.filename = join(self.sitemapdir, SITEMAP_FILES.format(self.filenumber))
        self.f = gzip.open(self.filename, 'w')
        self._write_header()

    def _close_file(self):
        self._write_footer()
        self.f.close()

    def _write(self, data):
        count = data.count('<url>')
        if self.urlcounter + count > self._FILE_MAX_URLS:
            self._close_file()
            self._init_file()
        self.urlcounter += count
        self.f.write(data)

    def _write_header(self):
        self._write(self._HEADER)

    def _write_footer(self):
        self._write(self._FOOTER)

    def _write_image(self, i):
        s = """  <image:image>
    <image:loc>{0}</image:loc>
    <image:caption>{1}</image:caption>
    <image:title>{2}</image:title>
  </image:image>
"""
        try: i_name = i.name.split('-', 1)[1]
        except: i_name = i.name
        i_name = re.sub('[^a-zA-Z0-9 ,_\-]+', '', i_name) #! make var, change everywhere
        i_title = i_name
        self._write(s.format(urljoin(SITE_URL, i.image.url), i_name, i_title))

    def _write_album(self, a):
        a_head = """  <url>
  <loc>{0}</loc>
  <lastmod>{1}</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
"""
        a_footer = """  </url>
"""
        a_url = urljoin(SITE_URL, a.get_absolute_url())
        a_date = a.pub_date.strftime('%Y-%m-%d')
        self._write(a_head.format(a_url, a_date))
        for i in a.image_set.all(): self._write_image(i)
        self._write(a_footer.format())

    def _write_albums(self):
        self._init_file()
        for a in Album.objects.filter(public=True): self._write_album(a)
        self._close_file()

    def _write_tag(self, t):
        s = """  <url>
  <loc>{0}</loc>
  <changefreq>daily</changefreq>
  </url>
"""
        t_url = urljoin(SITE_URL, t.get_absolute_url())
        self._write(s.format(t_url))
        if t.is_root_node():
            items = t.get_descendants(include_self=False)
            if not SHOW_PARENT_TAG_SHOW_ALL: items = items.filter(featured=True)
        else: items = t.album_set.all()
        items = items.filter(public=True)
        paginator = MyPaginator(items, ALBUMS_PER_PAGE)
        if paginator.num_pages > SHOW_ALBUMS_PAGINATION_MAXPAGE: paginator.num_pages = SHOW_ALBUMS_PAGINATION_MAXPAGE
        if paginator.num_pages > 1:
            for c in range(2, paginator.num_pages + 1):
                t_base_url = reverse('photo.views.show_albums', kwargs = {'filter': t.name})
                t_rel_url = '{0}{1}/'.format(t_base_url, c)
                t_url = urljoin(SITE_URL, t_rel_url)
                self._write(s.format(t_url))

    def _write_tags(self):
        self._init_file()
        for t in Tag.objects.filter(public=True): self._write_tag(t)
        self._close_file()

    def _write_root(self):
        s = """  <url>
  <loc>{0}</loc>
  <changefreq>daily</changefreq>
  </url>
"""
        self._init_file()
        r_url = SITE_URL
        self._write(s.format(r_url))
        items = Album.objects.filter(public=True)
        paginator = MyPaginator(items, ALBUMS_PER_PAGE)
        if paginator.num_pages > SHOW_ALBUMS_PAGINATION_MAXPAGE: paginator.num_pages = SHOW_ALBUMS_PAGINATION_MAXPAGE
        if paginator.num_pages > 1:
            for c in range(2, paginator.num_pages + 1):
                r_base_url = reverse('photo.views.show_albums')
                r_rel_url = '{0}{1}/'.format(r_base_url, c)
                r_url = urljoin(SITE_URL, r_rel_url)
                self._write(s.format(r_url))
        self._close_file()

    def _write_sitemapindex(self):
        sm_header = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
        s = """<sitemap>
<loc>{0}</loc>
<lastmod>{1}</lastmod>
</sitemap>
"""
        sm_footer = """</sitemapindex>
"""
        fname = join(WWW_ROOT, SITEMAP_INDEX_FILE)
        f = gzip.open(fname, 'w')
        f.write(sm_header)
        for c in range(1, self.filenumber+1):
            path = join(SITEMAP_DIR, SITEMAP_FILES.format(c))
            url = urljoin(SITE_URL, path)
            dt = datetime.datetime.now().strftime('%Y-%m-%d')
            f.write(s.format(url, dt))
        f.write(sm_footer)

    def _write_cats(self):
        self._init_file()
        MIN_TAG_COUNTER = 100     # increase if too many queries
        MAX_QUERY_LENGTH = 3      # decrease if too many queries
        MIN_RESULTS_ON_PAGE = 10  # increase if too many results
        cats = Tag.objects.filter(public=True).exclude(parent__isnull=True).filter(counter__gte=MIN_TAG_COUNTER)
        c = [cat.name for cat in cats]
        for l in range(2, MAX_QUERY_LENGTH+1):
            for (counter,subset) in enumerate(combinations(c, l)):
                items = reduce(lambda album_filter, x: album_filter.filter(tags__name=x), subset, Album.objects.filter(public=True))
                if len(items) >= MIN_RESULTS_ON_PAGE:
                    print '{0} == {1} => {2}'.format(counter, subset, len(items))
                #if counter > 1000: break
        self._close_file()

    def create(self):
        self._write_root()
        self._write_albums()
        self._write_tags()
        #self._write_cats()
        self._write_sitemapindex()
