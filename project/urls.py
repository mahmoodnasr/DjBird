
from project import views
from django.conf.urls import url


urlpatterns = [
    url(r'^$', views.feeds, name='feeds'),
    url(r'post/$', views.post, name='post'),
    url(r'like/$', views.like, name='like'),
    url(r'comment/$', views.comment, name='comment'),
    url(r'load/$', views.load, name='load'),
    url(r'remove/$', views.remove, name='remove_feed'),
    url(r'(\d+)/$', views.feed, name='feed'),

]
