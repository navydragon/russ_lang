from django.urls import include, path

urlpatterns = [path('', include('students.urls')), path('', include('users.urls'))]
