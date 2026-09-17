from django.urls import path

from . import views

urlpatterns = [
    path('quiz_result', views.quiz_result, name='quiz_result'),
    path('story/check', views.story_check, name='story_check'),
]
