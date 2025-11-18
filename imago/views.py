from django.shortcuts import render
from django.db.models import Avg, Count
from lecturas.models import Documento
from posts.models import Categoria
from home.models import HomePageBlock, HeroConfiguration

def home_view(request):
    try:
        hero_config = HeroConfiguration.objects.get()
    except HeroConfiguration.DoesNotExist:
        hero_config = None

    mejor_valoradas = Documento.objects.annotate(
        avg_rating=Avg('calificaciones__puntuacion')
    ).filter(
        avg_rating__isnull=False
    ).order_by('-avg_rating')[:8]
    recientes = Documento.objects.order_by('-date')[:8]
    foros_destacados = Categoria.objects.annotate(
        num_temas=Count('temas')
    ).order_by('-num_temas')[:4]
    bloques_home = HomePageBlock.objects.filter(activo=True).order_by('orden')

    context = {
        'hero_config': hero_config,
        'mejor_valoradas': mejor_valoradas,
        'recientes': recientes,
        'foros_destacados': foros_destacados,
        'bloques_home': bloques_home,
    }
    
    return render(request, 'home.html', context)