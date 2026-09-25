from django.urls import path

from . import views

urlpatterns = [
    path('quiz_result', views.quiz_result, name='quiz_result'),
    path('story/check', views.story_check, name='story_check'),
    path('speaking/check', views.speaking_check, name='speaking_check'),
    path('speaking/complete', views.speaking_complete, name='speaking_complete'),
    path('reading/check', views.reading_check, name='reading_check'),
    path('reading/complete', views.reading_complete, name='reading_complete'),
]
