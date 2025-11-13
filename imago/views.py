from django.shortcuts import render
from django.db.models import Avg, Count
from lecturas.models import Documento
from posts.models import Categoria

def home_view(request):
    """
    Vista para la nueva landing page inmersiva.
    """
    mejor_valoradas = Documento.objects.annotate(
        avg_rating=Avg('calificaciones__puntuacion')
    ).filter(
        avg_rating__isnull=False
    ).order_by('-avg_rating')[:8]

    recientes = Documento.objects.order_by('-date')[:8]

    foros_destacados = Categoria.objects.annotate(
        num_temas=Count('temas')
    ).order_by('-num_temas')[:4]

    context = {
        'mejor_valoradas': mejor_valoradas,
        'recientes': recientes,
        'foros_destacados': foros_destacados, # Añadimos al contexto
    }
    
    return render(request, 'home.html', context)