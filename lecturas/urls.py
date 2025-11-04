from django.urls import path
from . import views

app_name = 'lecturas'

urlpatterns = [
    path('subir/', views.subir_documento, name='subir_documento'),
    path('', views.DocumentoListView.as_view(), name='lista_documentos_base'),
    path('detalle/<int:pk>/', views.DocumentoDetailView.as_view(), name='detalle_documento'),
    path('detalle/<int:pk>/file/', views.serve_file, name='serve_file'),
    path('detalle/<int:pk>/comentar/', views.anadir_comentario, name='anadir_comentario'),
    path('<str:idioma>/<str:grado>/', views.DocumentoListView.as_view(), name='lista_documentos_filtrada'),
    path('<str:idioma>/', views.DocumentoListView.as_view(), name='lista_por_idioma'),
    path('detalle/<int:pk>/editar/', views.DocumentoUpdateView.as_view(), name='editar_documento'),
    path('detalle/<int:pk>/borrar/', views.DocumentoDeleteView.as_view(), name='borrar_documento'),
    path('comentario/<int:pk>/editar/', views.ComentarioUpdateView.as_view(), name='editar_comentario'),
    path('comentario/<int:pk>/borrar/', views.ComentarioDeleteView.as_view(), name='borrar_comentario'),
]