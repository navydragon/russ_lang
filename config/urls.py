"""
URL configuration for russ_lang project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from courses.test_launcher import test_launcher, set_review_confirmation
from courses.author_review import author_assignments

urlpatterns = [
    path('dev/tasks/', test_launcher, name='test_launcher'),
    path('dev/tasks/confirmation/', set_review_confirmation, name='set_review_confirmation'),
    path('authors/assignments/', author_assignments, name='author_assignments'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('config.task_pages')),
    path('', include('students.urls')),
    path('', include('users.urls')),
]

# Раздача /media/ (уроки tasks). На проде предпочтителен nginx alias на MEDIA_ROOT.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]

