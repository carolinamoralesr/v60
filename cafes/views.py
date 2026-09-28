"""Vistas de la app cafes.

En el patrón MVC esta capa es el Controlador: recibe la petición HTTP,
consulta el Model y elige el Template (la Vista) que se va a renderizar.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CafeForm, RecetaForm, RegistroBaristaForm
from .mixins import BaristaRequiredMixin, RecetaOwnerMixin, StaffRequiredMixin
from .models import Cafe, Receta


def catalogo_cafes(request):
    """Catálogo público: solo recetas marcadas como publicadas.

    Recibe GET con ?q= opcional. prefetch_related evita el problema N+1.
    """
    busqueda = request.GET.get('q', '').strip()
    recetas_publicas = Prefetch(
        'recetas',
        queryset=Receta.objects.filter(publicada=True).select_related('creado_por'),
    )
    catalogo = Cafe.objects.prefetch_related(recetas_publicas)

    if busqueda:
        catalogo = catalogo.filter(
            Q(nombre__icontains=busqueda)
            | Q(tostador__icontains=busqueda)
            | Q(origen__icontains=busqueda)
        )

    cafes = list(catalogo)
    total_recetas = sum(len(cafe.recetas.all()) for cafe in cafes)

    contexto = {
        'cafes': cafes,
        'busqueda': busqueda,
        'total_cafes': len(cafes),
        'total_recetas': total_recetas,
    }
    return render(request, 'cafes/catalogo.html', contexto)


class RegistroBaristaView(CreateView):
    """Crea un usuario, lo asigna al grupo Baristas e inicia sesión."""

    form_class = RegistroBaristaForm
    template_name = 'registration/registro.html'
    success_url = reverse_lazy('cafes:mis_recetas')

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        grupo, _ = Group.objects.get_or_create(name='Baristas')
        self.object.groups.add(grupo)
        login(self.request, self.object)
        messages.success(self.request, 'Cuenta creada. Ya puedes publicar recetas V60.')
        return respuesta


class MisRecetasView(BaristaRequiredMixin, ListView):
    """Listado de recetas del usuario autenticado (Read del CRUD)."""

    model = Receta
    template_name = 'cafes/mis_recetas.html'
    context_object_name = 'recetas'

    def get_queryset(self):
        qs = Receta.objects.select_related('cafe')
        if self.request.user.is_staff:
            return qs
        return qs.filter(creado_por=self.request.user)


class RecetaCreateView(BaristaRequiredMixin, CreateView):
    """Create del CRUD, envuelto en transacción atómica."""

    model = Receta
    form_class = RecetaForm
    template_name = 'cafes/receta_form.html'
    success_url = reverse_lazy('cafes:mis_recetas')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                receta = form.save(commit=False)
                receta.creado_por = self.request.user
                if not receta.autor or receta.autor == 'Anónimo':
                    receta.autor = self.request.user.get_username()
                receta.save()
                self.object = receta
        except IntegrityError:
            messages.error(self.request, 'No se pudo guardar la receta. Revisa los datos.')
            return self.form_invalid(form)
        messages.success(self.request, 'Receta publicada en la barra.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['titulo_formulario'] = 'Nueva receta V60'
        return contexto


class RecetaUpdateView(RecetaOwnerMixin, UpdateView):
    """Update del CRUD: solo el dueño o staff."""

    model = Receta
    form_class = RecetaForm
    template_name = 'cafes/receta_form.html'
    success_url = reverse_lazy('cafes:mis_recetas')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            messages.error(self.request, 'No se pudo actualizar la receta.')
            return self.form_invalid(form)
        messages.success(self.request, 'Receta actualizada.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['titulo_formulario'] = 'Editar receta V60'
        return contexto


class RecetaDeleteView(RecetaOwnerMixin, DeleteView):
    """Delete del CRUD, con plantilla de confirmación."""

    model = Receta
    template_name = 'cafes/receta_confirm_delete.html'
    success_url = reverse_lazy('cafes:mis_recetas')

    def form_valid(self, form):
        messages.success(self.request, 'Receta eliminada.')
        return super().form_valid(form)


class CafeCreateView(StaffRequiredMixin, CreateView):
    """Gestión de colecciones: alta de un lote (staff)."""

    model = Cafe
    form_class = CafeForm
    template_name = 'cafes/cafe_form.html'
    success_url = reverse_lazy('cafes:catalogo')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            messages.error(self.request, 'Ese lote ya existe para esa tostaduría.')
            return self.form_invalid(form)
        messages.success(self.request, 'Café agregado a la colección.')
        return redirect(self.success_url)
