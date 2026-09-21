#Configuración del panel de administración de la app cafes.

from django.contrib import admin

from .models import Cafe, Receta


class RecetaInline(admin.TabularInline):
   # Edita las recetas desde la ficha del café al que pertenecen.

    model = Receta
    extra = 1


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tostador', 'origen', 'cantidad_recetas')
    list_filter = ('tostador',)
    search_fields = ('nombre', 'tostador', 'origen')
    inlines = [RecetaInline]

    def get_queryset(self, request):
        # Evita una consulta por fila al contar las recetas del listado.
        return super().get_queryset(request).prefetch_related('recetas')

    @admin.display(description="recetas")
    def cantidad_recetas(self, cafe):
        return cafe.recetas.count()


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ('autor', 'cafe', 'gramos_cafe', 'ratio', 'temperatura', 'tiempo_total')
    list_filter = ('molino', 'temperatura')
    search_fields = ('autor', 'cafe__nombre')
    list_select_related = ('cafe',)
