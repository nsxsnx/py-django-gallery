from photo.models import Tag, Album, Image
from django.contrib import admin
from datetime import datetime
from django import forms
from django.core.files import File
from photo.forms import AddTagForm, RenameForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from photo.settings import TAG_VISIBLE_COUNTER_LIMIT

def update_counters_admin_action(modeladmin, request, queryset):
    for object in queryset: object.recount()
update_counters_admin_action.short_description = 'Recount'

def set_menu(modeladmin, request, queryset):
    rows_updated = queryset.update(menu = True)
    if rows_updated == 1: message_bit = '1 item was'
    else: message_bit = '%s items were' % rows_updated
    modeladmin.message_user(request, '%s successfully set to be shown in menu' % message_bit)
set_menu.short_description = 'Set Menu'

def set_featured(modeladmin, request, queryset):
    rows_updated = queryset.update(featured = True)
    if rows_updated == 1: message_bit = '1 item was'
    else: message_bit = '%s items were' % rows_updated
    modeladmin.message_user(request, '%s successfully featured' % message_bit)
set_featured.short_description = 'Set Featured'

def set_public(modeladmin, request, queryset):
    if queryset.model is Album:
        rows_updated = queryset.update(public = True, pub_date = datetime.now())
    else:
        rows_updated = queryset.update(public = True)
    if rows_updated == 1: message_bit = '1 item was'
    else: message_bit = '%s items were' % rows_updated
    modeladmin.message_user(request, '%s successfully published' % message_bit)
set_public.short_description = 'Publish'

def rename(self, request, queryset):
    if 'submit' in request.POST:
        form = RenameForm(request.POST)
        if form.is_valid():
            find_str, replace_str, items = form.cleaned_data['find'], form.cleaned_data['replace'], queryset
            cnt = 0
            for i in items:
                if find_str in i.name:
                    i.name = i.name.replace(find_str, replace_str).strip()
                    if not i.name: 
                        self.message_user(request, 'empty new name, skipping')
                        continue
                    if form.cleaned_data['only_name']: i.save(update_fields=['name'])
                    else: i.save()
                    cnt += 1
            self.message_user(request, '%s item(s) successfully renamed' % (cnt))
        else:
            self.message_user(request, 'Invalid parameters')
        return HttpResponseRedirect(request.get_full_path())
    else:
        form = RenameForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'admin_action_rename.html', {'form': form})


class TagForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        inner_qs = Album.objects.filter(tags=self.instance.pk).values('id')
        self.fields['cover'].queryset = Image.objects.filter(album__in=inner_qs)
        self.fields['cover'].widget.can_add_related = False

class TagAdmin(admin.ModelAdmin):
    def tag_maintainance(modeladmin, request, queryset):
        for t in Tag.objects.all(): 
            #t.recount()
            if not t.is_root_node() and (t.counter < TAG_VISIBLE_COUNTER_LIMIT or not t.cover):
                t.public = False
                t.save()
            if not t.cover:
                try: t.cover = Album.objects.filter(tags__id = t.id, public=True).order_by('?')[0].image_set.first()
                except: 
                    t.cover = None
                    if not t.is_root_node(): t.public = False
                t.save()
    tag_maintainance.short_description = "All Tags Maintainance"

    def set_random_cover(self, request, queryset):
        for t in queryset: 
            try: t.cover = Album.objects.filter(tags__id = t.id, public=True).order_by('?')[0].image_set.first()
            except: 
                t.cover = None
                t.public = False
            t.save()
    set_random_cover.short_description = "Set Random Cover"

    list_display = ['name', 'parent', 'public', 'menu', 'featured', 'cover_', 'counter_', 'counter']
    list_editable = ['public', 'menu', 'featured']
    list_filter = ['public', 'menu', 'featured']
    search_fields = ['name']
    readonly_fields = ('cover_', 'counter')
    actions = [rename, 'tag_maintainance', 'set_random_cover', set_menu, set_featured, update_counters_admin_action, set_public]
    actions_on_bottom = True
    form = TagForm

class AlbumForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AlbumForm, self).__init__(*args, **kwargs)
        self.fields['cover'].queryset = Image.objects.filter(album=self.instance.pk)
        self.fields['cover'].widget.can_add_related = False

class AlbumAdmin(admin.ModelAdmin):
    list_display = ['name', 'tags_', 'public', 'featured', 'cover_', 'counter_', 'views', 'gviews']
    list_editable = ['public', 'featured']
    list_filter = ['public', 'pub_date', 'featured']
    search_fields = ['name', 'id']
    actions = [rename, 'add_tags', 'clear_views', set_featured, update_counters_admin_action, set_public]
    actions_on_bottom = True
    list_per_page = 500
    filter_horizontal = ['tags']
    date_hierarchy = 'pub_date'
    save_on_top = True
    form = AlbumForm

    def add_tags(self, request, queryset):
        if 'submit' in request.POST:
            form = AddTagForm(request.POST)
            if form.is_valid():
                tags, action, albums = form.cleaned_data['tags'], form.cleaned_data['act'], queryset
                for album in albums:
                    for tag in tags:
                        if action == 'add': album.tags.add(tag)
                        else: album.tags.remove(tag)
                    album.save()
                self.message_user(request, '%s tag(s) successfully added/removed, %s album(s) affected' % (len(tags), len(albums)))
            else:
                self.message_user(request, 'no tags chosen')
            return HttpResponseRedirect(request.get_full_path())
        else:
            form = AddTagForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            return render(request, 'admin_action_add_tag.html', {'items': queryset,'form': form})
    add_tags.short_description = 'Add/Remove Tags'
      
    def clear_views(self, request, queryset):
        rows_updated = queryset.update(views = 0)
        self.message_user(request, '%s item(s) was/were successfully updated' % rows_updated)

    """def album_join(self, request, queryset):
       la = queryset[1]
       for a in queryset[1:]:
          for i in a.image_set.all():
             i.album = la
             i.save()
             tmpfile = File(open(i.image.path, 'rb'))
             i.image.save(i.image.name, tmpfile)


    album_join.short_description = 'Join selected items'"""
             

       #rows_updated = queryset.update(public = True, pub_date = datetime.now())
       #if rows_updated == 1: message_bit = '1 album was'
       #else: message_bit = '%s albums were' % rows_updated
       #self.message_user(request, '%s successfully published' % message_bit)

class ImageAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'name', 'thumbnail_html']
    search_fields = ['name']

admin.site.register(Image, ImageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Album, AlbumAdmin)

