from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()
import settings
import photo

urlpatterns = [
    url(r'^', include('photo.urls')),
    url(r'^zzz/photo/album/add/$', photo.views.admin_albums_add, name='photo.views.admin_albums_add'),
    url(r'^zzz/', include(admin.site.urls)),
]
handler400 = photo.views.show_400
handler403 = photo.views.show_403
handler404 = photo.views.show_404
handler500 = photo.views.show_500
