"""Rutas propias de la app cafes.

El URLconf es el despachador del patrón MVC: traduce la URL de la petición
HTTP en la función Controlador que debe atenderla.
"""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = 'cafes'

urlpatterns = [
    path('', views.catalogo_cafes, name='catalogo'),
    path('ingresar/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('salir/', LogoutView.as_view(), name='logout'),
    path('registro/', views.RegistroBaristaView.as_view(), name='registro'),
    path('recetas/', views.MisRecetasView.as_view(), name='mis_recetas'),
    path('recetas/nueva/', views.RecetaCreateView.as_view(), name='receta_crear'),
    path('recetas/<int:pk>/editar/', views.RecetaUpdateView.as_view(), name='receta_editar'),
    path('recetas/<int:pk>/eliminar/', views.RecetaDeleteView.as_view(), name='receta_eliminar'),
    path('cafes/nuevo/', views.CafeCreateView.as_view(), name='cafe_crear'),
]
