"""Vistas de la app cafes.

En el patrón MVC esta capa es el Controlador: recibe la petición HTTP,
consulta el Model y elige el Template (la Vista) que se va a renderizar.
Django llama a este archivo views.py; el rol, sin embargo, es el de
Controlador.
"""

from django.db.models import Q
from django.shortcuts import render

from .models import Cafe


def catalogo_cafes(request):
    """Renderiza el catálogo de cafés con sus recetas V60.

    Recibe una petición HTTP GET y admite el parámetro opcional ?q= para
    filtrar el catálogo por lote, tostaduría u origen.

    prefetch_related('recetas') es clave para la eficiencia: el template
    recorre cafe.recetas.all dentro del bucle de cafés, así que sin él
    Django lanzaría una consulta por cada café (problema N+1). Con el
    prefetch son siempre 2 consultas, sin importar cuántos cafés existan.
    """
    busqueda = request.GET.get('q', '').strip()

    catalogo = Cafe.objects.prefetch_related('recetas')

    if busqueda:
        # Q permite combinar condiciones con OR en una sola consulta SQL.
        catalogo = catalogo.filter(
            Q(nombre__icontains=busqueda)
            | Q(tostador__icontains=busqueda)
            | Q(origen__icontains=busqueda)
        )

    # Se evalúa el queryset una sola vez y se reutiliza en los cálculos.
    cafes = list(catalogo)
    total_recetas = sum(len(cafe.recetas.all()) for cafe in cafes)

    contexto = {
        'cafes': cafes,
        'busqueda': busqueda,
        'total_cafes': len(cafes),
        'total_recetas': total_recetas,
    }
    return render(request, 'cafes/catalogo.html', contexto)
