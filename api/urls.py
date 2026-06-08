from django.urls import path

from . import views

urlpatterns = [
    path('quiz_result', views.quiz_result, name='quiz_result'),
]
