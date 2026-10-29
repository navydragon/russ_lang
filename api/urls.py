from django.urls import path

from . import views
from . import dictation_views, university_question_views

urlpatterns = [
    path('university-questions/start', university_question_views.start),
    path('university-questions/state', university_question_views.state),
    path('university-questions/answer', university_question_views.answer),
    path('dictation/start', dictation_views.start, name='dictation_start'),
    path('dictation/state', dictation_views.state, name='dictation_state'),
    path('dictation/answer', dictation_views.answer, name='dictation_answer'),
    path('quiz_result', views.quiz_result, name='quiz_result'),
    path('neighborhood-verbs/check', views.neighborhood_verbs_check),
    path('story/check', views.story_check, name='story_check'),
    path('retelling/check', views.retelling_check, name='retelling_check'),
    path('speaking/check', views.speaking_check, name='speaking_check'),
    path('speaking/complete', views.speaking_complete, name='speaking_complete'),
    path('reading/check', views.reading_check, name='reading_check'),
    path('reading/complete', views.reading_complete, name='reading_complete'),
]
