"""Configuración del panel de administración de la app cafes.

Se personaliza y se extiende el Admin para la gestión de colecciones
(indicador 2 Destacado): fieldsets, autocomplete, acciones masivas y
asignación del usuario que guarda.
"""

from django.contrib import admin

from .models import Cafe, Receta


class RecetaInline(admin.TabularInline):
    model = Receta
    extra = 1
    autocomplete_fields = ('creado_por',)
    fields = (
        'autor', 'creado_por', 'gramos_cafe', 'ratio', 'temperatura',
        'tiempo_total', 'publicada',
    )


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tostador', 'origen', 'cantidad_recetas')
    list_filter = ('tostador',)
    search_fields = ('nombre', 'tostador', 'origen')
    inlines = [RecetaInline]
    fieldsets = (
        ('Colección', {'fields': ('nombre', 'tostador', 'origen')}),
        ('Fotografía', {'fields': ('imagen',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('recetas')

    @admin.display(description="recetas")
    def cantidad_recetas(self, cafe):
        return cafe.recetas.count()


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = (
        'autor', 'cafe', 'gramos_cafe', 'ratio', 'temperatura',
        'tiempo_total', 'publicada',
    )
    list_display_links = ('autor',)
    list_editable = ('temperatura', 'publicada')
    list_filter = ('molino', 'publicada', 'temperatura')
    search_fields = ('autor', 'cafe__nombre', 'creado_por__username')
    autocomplete_fields = ('cafe', 'creado_por')
    list_select_related = ('cafe', 'creado_por')
    readonly_fields = ('ratio_calculado', 'creado_en', 'actualizado_en')
    actions = ('publicar_recetas', 'ocultar_recetas')
    fieldsets = (
        ('Colección', {'fields': ('cafe', 'autor', 'creado_por', 'publicada')}),
        ('Dosis y agua', {'fields': ('gramos_cafe', 'agua_total', 'ratio', 'ratio_calculado', 'temperatura')}),
        ('Molienda', {'fields': ('molienda', 'molino', 'clicks_molino')}),
        ('Bloom y vertidos', {'fields': ('bloom_agua', 'bloom_segundos', 'vertidos', 'tiempo_total')}),
        ('Auditoría', {'fields': ('creado_en', 'actualizado_en'), 'classes': ('collapse',)}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        if not obj.autor or obj.autor == 'Anónimo':
            obj.autor = request.user.get_username()
        super().save_model(request, obj, form, change)

    @admin.action(description="Publicar recetas seleccionadas")
    def publicar_recetas(self, request, queryset):
        actualizadas = queryset.update(publicada=True)
        self.message_user(request, f'{actualizadas} receta(s) visibles en el catálogo.')

    @admin.action(description="Ocultar recetas seleccionadas")
    def ocultar_recetas(self, request, queryset):
        actualizadas = queryset.update(publicada=False)
        self.message_user(request, f'{actualizadas} receta(s) ocultas del catálogo.')
