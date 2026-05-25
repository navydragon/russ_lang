from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('my-groups/', views.MyGroupsView.as_view(), name='my_groups'),
    path('group-results/<int:group_id>/', views.GroupResultsView.as_view(), name='group_results'),
    path('student-lesson-results/<int:student_id>/<int:lesson_id>/', views.StudentLessonResultsView.as_view(), name='student_lesson_results'),
    # Управление группами (CRUD)
    path('groups/', views.GroupManagementView.as_view(), name='group_management'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),
    path('groups/<int:group_id>/students/', views.GroupStudentsView.as_view(), name='group_students'),
    path('groups/<int:group_id>/students/<int:student_id>/remove/', views.RemoveStudentFromGroupView.as_view(), name='remove_student_from_group'),
]

