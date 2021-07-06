from django.db import models
from os.path import join, splitext, basename, dirname, exists
from urlparse import urljoin
from os import rmdir, remove, chmod
from PIL import Image as PImage
from gallery.settings import MEDIA_ROOT, FILE_UPLOAD_PERMISSIONS
from django.core.files import File
from tempfile import NamedTemporaryFile
from photo.settings import APP_NAME, THUMB_SIZE, ADMINCP_IMG_TMPL, ALBUM_DESCR_NAME, SHOW_ALBUMS_STYLE_FULL, URL_SRCH_DLMTR, ALBUM_VIEW_DEFAULT_FULL, MAX_ALBUM_NAME_LENGTH, MAX_TAG_NAME_LENGTH, SHOW_PARENT_TAG_SHOW_ALL, SAVE_ALBUM_DESCRIPTION, VIVID_COUNTERS, SITE_URL
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from time import strftime
from django.core.urlresolvers import reverse
from mptt.models import MPTTModel, TreeForeignKey
from django.template.defaultfilters import slugify
from json import dump
from django.db.models.signals import m2m_changed

class Tag(MPTTModel):
	class Meta:
		index_together = [
			['public', 'menu'],
			['public', 'featured'],
		]
	name = models.CharField(max_length=MAX_TAG_NAME_LENGTH, unique=True, db_index=True)
	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.PROTECT)
	cover = models.ForeignKey('Image', related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
	public = models.BooleanField(default=False)
	menu = models.BooleanField('Show in menu', default=False, db_index=True)
	counter = models.PositiveIntegerField(null=True, editable=False, default=0, verbose_name='#')
	featured = models.BooleanField(default=False, db_index=True)
	def recount(self):
		if self.is_root_node(): 
			if SHOW_PARENT_TAG_SHOW_ALL: self.counter = self.get_descendants().filter(public=True).count()
			else: self.counter = self.get_descendants().filter(public=True, featured=True).count()
		else: self.counter = Album.objects.filter(tags__id = self.id, public=True).count()
		self.save(update_fields=['counter'])
	def cover_(self):
		if self.cover: return ADMINCP_IMG_TMPL % (self.cover.image.name, self.cover.thumbnail.name)
		else: return '(None)'
	cover_.allow_tags = True 
	def __unicode__(self):
		return '%s%s' % ('-' * self.level, self.name)
	class MPTTMeta:
		order_insertion_by = ['name']
	def get_absolute_url(self):
		return reverse('photo.views.show_albums', args=[self.name])
	def counter_(self):
		return '<a href="{0}"><b>{1}</b></a>'.format(self.get_absolute_url(), self.counter)
	counter_.allow_tags = True 
	counter_.short_description = '#'
	def vivid_counter(self):
		cnt = self.counter
		if not VIVID_COUNTERS: return cnt
		if cnt < 1000: return cnt
		if cnt < 10000: return '{:.1f}K'.format(float(cnt)/1000)
		if cnt < 1000000: return '{:.0f}K'.format(float(cnt)/1000)
		if cnt < 10000000: return '{:.1f}M'.format(float(cnt)/1000000)
		else: return '{:.0f}M'.format(float(cnt)/1000000)
	def save(self, *args, **kwargs):
		super(Tag, self).save(*args, **kwargs)
		try: self.name.index(URL_SRCH_DLMTR)
		except: pass
		else:
			self.name = self.name.replace(URL_SRCH_DLMTR, '-')
			super(Tag, self).save(*args, **kwargs)

class Album(models.Model):
	class Meta:
		ordering = ['-id']
	name = models.CharField(max_length=MAX_ALBUM_NAME_LENGTH, blank=True, db_index=True)
	url = models.SlugField(max_length=255, blank=True, editable = False)
	description = models.TextField(blank=True)
	cover = models.OneToOneField('Image', related_name='+', null=True, on_delete=models.SET_NULL)
	tags = models.ManyToManyField(Tag, blank=True)
	pub_date = models.DateTimeField(auto_now_add=True)
	public = models.BooleanField(default=False, db_index=True)
	featured = models.BooleanField(default=False, db_index=True)
	no_watermark = models.BooleanField(default=False)
	counter = models.PositiveSmallIntegerField(null=True, editable=False, default=0, verbose_name='#Images')
	views = models.PositiveIntegerField(editable=False, default=0, verbose_name='#Views')
	gviews = models.PositiveIntegerField(editable=False, default=0, verbose_name='GViews')
	def recount(self):
		self.counter = self.image_set.count()
		self.save(update_fields=['counter'])
	def __unicode__(self):
		return self.name
	def tags_(self):
		return ', '.join([t.name for t in self.tags.all()])
	def tags_as_list(self):
		return self.tags.filter(public=True).values_list('name', flat=True)
	def tags_as_str(self):
		return ', '.join(self.tags_as_list())
	def pub_date_(self):
		return self.pub_date.strftime('%Y-%m-%d %I:%M:%S %p')
		pub_date_.admin_order_field = 'pub_date'
		pub_date_.short_description = 'date'
	def cover_(self):
		if self.cover: return ADMINCP_IMG_TMPL % (self.cover.image.name, self.cover.thumbnail.name)
		else: return '(None)'
	cover_.allow_tags = True 
	def counter_(self):
		return '<a href="{0}"><b>{1}</b></a>'.format(self.get_absolute_url(), self.counter)
	counter_.allow_tags = True 
	counter_.short_description = '#'
	def _get_image_path(self):
		return join(MEDIA_ROOT, dirname(self.image_set.first().image.name))
	def _get_absolute_url(self, view):
		return reverse('photo.views.show_album', args=[view, str(self.id)]) + self.url
	def get_absolute_url_f(self):
		return self._get_absolute_url('f')
	def get_absolute_url_t(self):
		return self._get_absolute_url('t')
	def get_absolute_url(self):
		if SHOW_ALBUMS_STYLE_FULL or ALBUM_VIEW_DEFAULT_FULL: return self._get_absolute_url('f')
		else: return self._get_absolute_url('t')
	def get_full_absolute_url(self):
		return urljoin(SITE_URL, self.get_absolute_url())
	def save(self, *args, **kwargs):
		self.name = self.name[0].upper() + self.name[1:]
		super(Album, self).save(*args, **kwargs)
		if 'update_fields' not in kwargs:
			self.url = slugify(self.name)
			super(Album, self).save(*args, **kwargs)
			save_album_description(sender = None, instance = self)
      
def save_album_description(sender, **kwargs):
	if not SAVE_ALBUM_DESCRIPTION: return
	album = kwargs['instance']
	try: fn = join(album._get_image_path(),  ALBUM_DESCR_NAME)
	except: pass
	else: 
		d = {'id': album.id, 'name': album.name, 'tags': album.tags_(), 'public': album.public, 'featured': album.featured, 'pub_date': album.pub_date.strftime("%Y-%m-%d %H:%M:%S"), 'no_watermark': album.no_watermark, 'description': album.description}
		d['cover'] = basename(album.cover.image.name)
		with open(fn, 'wb') as f: dump(d, f, sort_keys=True)
		chmod(fn, FILE_UPLOAD_PERMISSIONS)

m2m_changed.connect(save_album_description, sender=Album.tags.through)

#def upload_path(p):
	#return lambda instance, filename: '/'.join([APP_NAME, p, strftime('%y%m/%d'), str(instance.album.id).zfill(5), filename])
def upload_path_i(instance, filename):
	return '/'.join([APP_NAME, 'i', strftime('%y%m/%d'), str(instance.album.id).zfill(5), filename])
def upload_path_t(instance, filename):
	return '/'.join([APP_NAME, 't', strftime('%y%m/%d'), str(instance.album.id).zfill(5), filename])

class Image(models.Model):
	album = models.ForeignKey(Album, on_delete=models.CASCADE)
	name = models.CharField(max_length=128, blank=True, db_index=True)
	#image = models.ImageField(max_length=255, upload_to=upload_path('i'), blank=True)
	#thumbnail = models.ImageField(max_length=255, upload_to=upload_path('t'), blank=True)
	image = models.ImageField(max_length=255, upload_to=upload_path_i, blank=True)
	thumbnail = models.ImageField(max_length=255, upload_to=upload_path_t, blank=True)
	def __unicode__(self):
		return basename(self.image.name)
	def thumbnail_html(self):
		return ADMINCP_IMG_TMPL % ((self.image.name, self.thumbnail.name))
	thumbnail_html.allow_tags = True
	thumbnail_html.short_description = 'Thumbnail'
	def get_full_image_url(self):
		return urljoin(SITE_URL, self.image.url)
	def save(self, *args, **kwargs):
		super(Image, self).save(*args, **kwargs)
		if not self.thumbnail: self.create_thumbnail(*args, **kwargs)
	def create_thumbnail(self, *args, **kwargs):
		if self.image:
			im = PImage.open(join(MEDIA_ROOT, self.image.name))
			im.thumbnail(THUMB_SIZE, PImage.ANTIALIAS)
			if self.thumbnail:
				thumb_fn = basename(self.thumbnail.name)
				# Preserve old path before delete():
				thumb_fn_full = self.thumbnail.name
				# Redefine generate_filename to preserve old path:
				self.thumbnail.field.generate_filename = lambda i, n: thumb_fn_full
				self.thumbnail.delete(save=False)
			else: thumb_fn = basename(self.image.name)
			tempfile = NamedTemporaryFile()
			im.save(tempfile.name, "JPEG")
			self.thumbnail.save(thumb_fn, File(open(tempfile.name)))
			tempfile.close()

#delete ImageField file:
@receiver(pre_delete, sender=Image)
def image_delete_handler(sender, instance, **kwargs):
	files = [instance.image.path, instance.thumbnail.path]
	for file in files:
		instance.image.storage.delete(file)
		instance.thumbnail.storage.delete(file)

@receiver(post_delete, sender=Image)
def image_post_delete_handler(sender, instance, **kwargs):
	instance.album.recount()
	if not instance.album.cover:
		try:
			instance.album.cover = instance.album.image_set.first()
			instance.album.save()
		except: pass

#delete JSON description:
@receiver(pre_delete, sender=Album)
def album_delete_handler(sender, instance, **kwargs):
	try: path = instance._get_image_path()
	except: pass
	else: 
		f = join(path, ALBUM_DESCR_NAME)
		if exists(f): remove(f)
		if exists (path): rmdir(path)

