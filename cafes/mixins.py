"""Mixins de autorización: sesiones y roles (indicador 5)."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class BaristaRequiredMixin(LoginRequiredMixin):
    """Exige sesión activa y rol de barista o staff."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        es_barista = request.user.groups.filter(name='Baristas').exists()
        if not (request.user.is_staff or es_barista):
            raise PermissionDenied('Solo baristas o administradores pueden gestionar recetas.')
        return super().dispatch(request, *args, **kwargs)


class RecetaOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Solo el dueño o un staff pueden editar o borrar la receta."""

    def test_func(self):
        receta = self.get_object()
        return receta.puede_gestionar(self.request.user)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """La colección de cafés la gestiona solo el personal."""

    def test_func(self):
        return self.request.user.is_staff
