"""NU URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.contrib.auth import views as auth_views
from django.conf.urls import url,include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from project import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',views.home,name='home'),
    url(r'^accounts/profile/$',views.home,name='home'),

    url(r'login', auth_views.login, {'template_name': 'project/cover.html'},name='login'),
    url(r'logout', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'signup/$', views.signup, name='signup'),

    url(r'settings/$', views.settings, name='settings'),
    url(r'settings/picture/$', views.picture, name='picture'),
    url(r'settings/upload_picture/$', views.upload_picture,name='upload_picture'),
    url(r'settings/save_uploaded_picture/$', views.save_uploaded_picture,name='save_uploaded_picture'),
    url(r'settings/password/$', views.password, name='password'),
    url(r'network/$', views.network, name='network'),

    url(r'^feeds/',include('project.urls')),

    url(r'notifications/$', views.notifications,name='notifications'),

    url(r'search/$', views.search, name='search'),
    url(r'^(?P<username>[^/]+)/$', views.profile, name='profile'),
    url(r'^(?P<user_id>[0-9]+)/follow/$', views.follow, name='follow'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)