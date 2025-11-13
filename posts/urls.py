from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.lista_categorias, name='lista_categorias'),
    path('crear-categoria/', views.CategoriaCreateView.as_view(), name='crear_categoria'),
    path('<slug:slug_categoria>/', views.lista_temas, name='lista_temas'),
    path('<slug:slug_categoria>/nuevo-tema/', views.crear_tema, name='crear_tema'),
    path('tema/<int:pk>/', views.detalle_tema, name='detalle_tema'),
    path('tema/<int:pk>/editar/', views.TemaUpdateView.as_view(), name='editar_tema'),
    path('tema/<int:pk>/borrar/', views.TemaDeleteView.as_view(), name='borrar_tema'),
    path('respuesta/<int:pk_parent>/get-hijos/', views.get_hijos_respuesta_ajax, name='get_hijos_respuesta'),
    path('ajax/respuesta/<int:pk>/editar/', views.editar_respuesta_ajax, name='editar_respuesta_ajax'),
    path('ajax/respuesta/<int:pk>/borrar/', views.borrar_respuesta_ajax, name='borrar_respuesta_ajax'),
]