from photo.models import Tag, Album, Image
import string
from random import SystemRandom
import collections
from zlib import crc32
from itertools import chain, ifilter
from photo.settings import HOME_SHOW_ADJACENT_PAGES, SHOW_ALBUM_SIMILAR_RANDOM_PROPORTION, SHOW_ALBUM_SIMILAR_ALBUMS, PARENT_TAGS_IDS, UPLOAD_PATH, MAILSTAT_ENABLED, MAILSTAT_RECIPIENTS, MAILSTAT_SUBJECT, MAILSTAT_SENDER

from sys import stdout
from django.core.paginator import Paginator, Page
import datetime, os
from django.core.mail import send_mail


def get_pages_list(page, pages):
	if pages == 1: return []
	show_adjacent = HOME_SHOW_ADJACENT_PAGES
	res = []
	cnt = show_adjacent
	while cnt:
		if page - cnt > 1: res += [page - cnt]
		cnt -= 1
	res += [page]
	cnt = 1
	while cnt <= show_adjacent:
		if page + cnt < pages: res += [page + cnt]
		cnt += 1
	if res[0] != 1: 
		if res[0] != 2: res = [0] + res
		res = [1] + res
	if res[-1] != pages: 
		if res[-1] != pages - 1: res += [0]
		res += [pages] 
	return res

def get_tag_tree(menu=False, album_id=None, featured=False):
    res = []
    try: root_nodes = Tag.objects.filter(pk__in = PARENT_TAGS_IDS, public = True).order_by()
    except: root_nodes = Tag.objects.root_nodes()
    for node in root_nodes:
        if not node.public: continue
        t = node.get_descendants(include_self=True).filter(public=True)
        #t = Tag.objects.filter(parent_id = node.id, public=True)
        if menu:     t = t.filter(menu=True)
        if featured: t = t.filter(featured=True)
        if album_id: 
            #t = list(chain(t.filter(pk = node.id), t.filter(album__id__exact=album_id)))
            t = list(chain((node,), t.filter(album__id=album_id)))
            if len(t) < 2: t = Tag.objects.none() # if parent tag has no children to be returned its not returned either
        #t = list(chain((node,), t)) # added when fast version was created
        if len(t): res += [t]
    return res

def find_duplicates(delete = False, verbose = False):
	if verbose: print 'Stage {0} started.'.format(1)
	names = []
	count = Image.objects.all().count()
	images_all = Image.objects.defer('thumbnail')
	bool(images_all)
	for i in images_all: names.append(i.name.split('-', 1)[1])
	dupl_names = [x for x, y in collections.Counter(names).items() if y > 1]
	dupl_names = sorted(dupl_names)
	if verbose: print 'Stage {0} completed. Found {1} groups of similar items by {2}'.format(1, len(dupl_names), 'name.')
	if verbose: print 'Stage {0} started.'.format(2)
	d = {}
	dupl_name_size = {}
	cnt = 0
	total = len(dupl_names)
	for dup in dupl_names:
		dupls = []
		for i in images_all.filter(name__endswith = '-' + dup):
			with i.image.file as f: dupls.append((i.name.split('-', 1)[1], str(f.size)))
		dupls = [x for x, y in collections.Counter(dupls).items() if y > 1]
		dupls = sorted(dupls, key=lambda e: (e[0], e[1]))
		if len(dupls): dupl_name_size[dup] = dupls
		cnt = cnt + 1 
		if verbose: 
			stdout.write('\rStep {0} of {1} completed ({2:05.2f}%).'.format(cnt, total, float(cnt)/total*100))
			stdout.flush()
	#for k,v in dupl_name_size.items(): print '{0} => {1}'.format(k ,v)
	if verbose: print 'Stage {0} completed. Found {1} groups of similar items by {2}'.format(2, len(dupl_name_size), 'name and size.')
	
	if verbose: print 'Stage {0} started.'.format(3)
	dupl_name_size_crc = {}
	ids_nsc = {}
	cnt = 0
	total = len(dupl_name_size)
	for name, similars in dupl_name_size.items():
		for sim in similars:
			dupls = []
			for i in images_all.filter(name__endswith = '-' + name):
				with i.image.file as f: 
					s = (i.name.split('-', 1)[1], str(f.size))
					if s == sim:
						#print 'duplicate image: {0} | {1} | album {2}'.format(i.name, f.size, i.album.id)
						crc = str(crc32(f.read()))
						dupls.append(s + (crc,))
						key = '|'.join(s + (crc,))
						try: ids_nsc[key].append(i.album.id)
						except KeyError: ids_nsc[key] = [i.album.id]
			dupls = [x for x, y in collections.Counter(dupls).items() if y > 1]
			dupls = sorted(dupls, key=lambda e: (e[0], e[1], e[2]))
			if len(dupls): dupl_name_size_crc['|'.join(sim)] = dupls
			#print '---'
		cnt = cnt + 1 
		if verbose: 
			stdout.write('\rStep {0} of {1} completed ({2:05.2f}%).'.format(cnt, total, float(cnt)/total*100))
			stdout.flush()
	if verbose: print '\nStage {0} completed. Found {1} groups of similar items by {2}'.format(3, len(dupl_name_size_crc), 'name, size and crc.')

	for name, similars in dupl_name_size_crc.items():
		for sim in similars:
			print '{0}:'.format(sim[0])
			for id in sorted(ids_nsc['|'.join(sim)])[1:]:
				print '    deletng album {0}'.format(id)
				if delete: Album.objects.get(id = id).delete()

def _get_albums(tags=[], quantity=0):
    items = Album.objects.filter(public=True)
    if tags: 
        if len(tags) > quantity: tags = SystemRandom().sample(tags, quantity)
        items = items.filter(tags__name__in=tags).distinct()
    icnt = items.count()
    if quantity > icnt: quantity = icnt
    start_index = SystemRandom().randint(0, icnt-quantity)
    return items[start_index:start_index+quantity]

def get_similar_albums(tags=[], quantity=SHOW_ALBUM_SIMILAR_ALBUMS, randomness=SHOW_ALBUM_SIMILAR_RANDOM_PROPORTION):
    if not quantity: return Album.objects.none()
    if tags: 
        tqu = quantity - int(round(quantity*randomness, 0))
        res1 = _get_albums(tags=tags, quantity=tqu)
        res2 = _get_albums(quantity=quantity)
        res1_ids = res1.values_list('id', flat=True) 
        res2 = ifilter(lambda x: x.id not in res1_ids, res2)
        res = list(chain(res1, res2))[:quantity]
        return res
    else: return _get_albums(quantity=quantity)

def get_similar_albums_fast(quantity=SHOW_ALBUM_SIMILAR_ALBUMS):
    if not quantity: return Album.objects.none()
    icnt = Album.objects.latest('id').id
    if quantity > icnt: quantity = icnt
    res = Album.objects.none()
    cnt = 0
    GREEDYNESS = 25
    MAXQUERIES = 4
    while len(res) < quantity:
        start_index = SystemRandom().randint(0, icnt)
        a = Album.objects.filter(public=True, id__gt=start_index, id__lt=start_index+quantity*GREEDYNESS).select_related('cover')
        res = list(chain(res, a))
        cnt += 1
        if cnt >= MAXQUERIES: break
    if len(res) > quantity: res = SystemRandom().sample(res, quantity)
    return res

class MyPaginator(Paginator):
    def _get_page(self, *args, **kwargs):
        ids = set(args[0].values_list('id', flat=True))
        if args[0].query.select_related: object_list = self.object_list.model.objects.filter(pk__in=ids).select_related(*args[0].query.select_related)
        else: object_list = self.object_list.model.objects.filter(pk__in=ids)
        return Page(object_list, *args[1:], **kwargs)

    num_pages = property(lambda self: super(MyPaginator, self).num_pages)
    @num_pages.setter
    def num_pages(self, value):
        self._num_pages = value

def get_stats():
    EXC_FS = ['rootfs', 'sysfs', 'proc', 'devtmpfs', 'devpts', 'tmpfs', 'securityfs', 'cgroup', 'pstore', 'hugetlbfs', 'mqueue', 'debugfs', 'autofs', 'binfmt_misc', 'tracefs',] 
    res = 'Albums: \n'
    res += '    Overall (public / total): {0} / {1}\n    Added today (public / total): {2} / {3}\n    Waiting upload: {4}\n'.format(
    Album.objects.filter(public=True).count(),
    Album.objects.all().count(),
    Album.objects.filter(public=True, pub_date__gte=datetime.date.today()).count(),
    Album.objects.filter(pub_date__gte=datetime.date.today()).count(),
    len(os.listdir(UPLOAD_PATH)))
    res += '\nFile systems:\n'
    with open('/proc/mounts') as f:
        for line in f:
            dev, mount_point, fstype = line.split()[0:3]
            if fstype in EXC_FS: continue
            statvfs = os.statvfs(mount_point)
            res += '    {0} {1} Mb of {2} Mb free\n'.format( mount_point, statvfs.f_frsize * statvfs.f_bavail / 1024 / 1024, statvfs.f_frsize * statvfs.f_blocks / 1024 / 1024 )
    return res

def cron_mail_stats():
    if MAILSTAT_ENABLED: send_mail(MAILSTAT_SUBJECT, get_stats(), MAILSTAT_SENDER, MAILSTAT_RECIPIENTS)
