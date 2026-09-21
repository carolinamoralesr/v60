"""Rutas propias de la app cafes.

El URLconf es el despachador del patrón MVC: traduce la URL de la petición
HTTP en la función Controlador que debe atenderla. Se declara aparte del
urls.py del proyecto y con app_name para que la app sea reutilizable.
"""

from django.urls import path

from . import views

app_name = 'cafes'

urlpatterns = [
    path('', views.catalogo_cafes, name='catalogo'),
]
