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
    path('ajax/comentario/<int:pk>/editar/', views.editar_comentario_ajax, name='editar_comentario_ajax'),
    path('ajax/comentario/<int:pk>/borrar/', views.borrar_comentario_ajax, name='borrar_comentario_ajax'),
    path('ajax/documento/<int:pk>/calificar/', views.calificar_documento_ajax, name='calificar_documento_ajax'),
    path('ajax/documento/<int:pk>/guardar/', views.guardar_documento_ajax, name='guardar_documento_ajax'),
    path('ajax/documento/<int:pk>/subir/<str:field_name>/', views.subir_archivo_ajax, name='subir_archivo_ajax'),
]