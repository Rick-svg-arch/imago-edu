from django.urls import path
from .views import (
    PublicacionListView, 
    PublicacionCreateView, 
    PublicacionUpdateView, 
    PublicacionDeleteView,
    gestionar_bloque_ajax,
    anclar_publicacion_ajax,
    editar_publicacion_ajax
)

app_name = 'comunicaciones'

urlpatterns = [
    path('', PublicacionListView.as_view(), name='lista_publicaciones'),
    path('crear/', PublicacionCreateView.as_view(), name='crear_publicacion'),
    path('<int:pk>/editar/', PublicacionUpdateView.as_view(), name='editar_publicacion'),
    path('<int:pk>/borrar/', PublicacionDeleteView.as_view(), name='borrar_publicacion'),
    path('ajax/publicacion/<int:pub_pk>/bloque/', gestionar_bloque_ajax, name='crear_bloque_ajax'),
    path('ajax/bloque/<int:bloque_pk>/', gestionar_bloque_ajax, name='gestionar_bloque_ajax'),
    path('ajax/publicacion/<int:pub_pk>/reordenar/', gestionar_bloque_ajax, name='reordenar_bloques_ajax'),
    path('ajax/publicacion/<int:pub_pk>/titulo/', gestionar_bloque_ajax, name='guardar_titulo_ajax'),
    path('ajax/publicacion/<int:pk>/', editar_publicacion_ajax, name='editar_publicacion_ajax'),
    path('ajax/bloque/<int:bloque_pk>/upload-image/', gestionar_bloque_ajax, name='upload_bloque_image_ajax'),
    path('ajax/publicacion/<int:pk>/anclar/', anclar_publicacion_ajax, name='anclar_publicacion_ajax'),
]