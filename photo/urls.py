from django.conf.urls import include, url
from photo.settings import URL_SRCH_DLMTR
from photo import views

urlpatterns = [
    url(r'^$', views.show_albums, name='photo.views.show_albums'),
    url(r'^(?P<page_id>\d+)/$', views.show_albums, name='photo.views.show_albums'),
    url(r'^t/(?P<filter>[\w\-\_{0}]+)/$'.format(URL_SRCH_DLMTR), views.show_albums, name='photo.views.show_albums'),
    url(r'^t/(?P<filter>[\w\-\_{0}]+)/(?P<page_id>\d+)/$'.format(URL_SRCH_DLMTR), views.show_albums, name='photo.views.show_albums'),
    url(r'^a/(?P<view>f|t)/(?P<album_id>\d+)/.*$', views.show_album, name='photo.views.show_album'),
    url(r'^a/c/(?P<album_id>\d+)/dumb.js$', views.count_album, name='photo.views.count_album'),
    url(r'^g/(?P<link_name>[\w\-\_]+)/$', views.show_go, name='photo.views.show_go'),
    url(r'^categories/$', views.show_categories, name='photo.views.show_categories'),
    url(r'^contact/$', views.show_contact, name='photo.views.show_contact'),
    url(r'^t/$', views.show_all_tags, name='photo.views.show_all_tags'),
]

