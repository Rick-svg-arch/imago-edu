from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('panel/', views.DashboardView.as_view(), name='dashboard'),
    path('panel/profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('panel/clases/crear/', views.ClassCreateView.as_view(), name='class_create'),
    path('panel/clases/find-students/', views.FindStudentsByIdView.as_view(), name='find_students_by_id'),
    path('panel/clases/preview-csv/', views.PreviewStudentsFromCSVView.as_view(), name='preview_students_csv'),
    path('panel/clases/<int:pk>/editar/', views.ClassUpdateView.as_view(), name='class_edit'),
    path('panel/manage-roles/', views.UserListView.as_view(), name='manage_users_list'),
    path('panel/manage-roles/<int:pk>/edit/', views.UserGroupUpdateView.as_view(), name='manage_user_edit'),
    path('panel/clases/<int:pk>/', views.ClaseDetailView.as_view(), name='clase_detail'),
    path('panel/manage-preregistros/', views.PreRegistroManagerView.as_view(), name='manage_preregistros_list'),
    path('panel/manage-preregistros/<int:pk>/editar/', views.PreRegistroUpdateView.as_view(), name='preregistro_edit'),
    path('panel/manage-preregistros/<int:pk>/borrar/', views.PreRegistroDeleteView.as_view(), name='preregistro_delete'),
    path('panel/manage-roles/<int:pk>/reset-password/', views.PasswordResetByAdminView.as_view(), name='manage_user_reset_password'),
    path('panel/change-password/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('panel/change-password/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
]