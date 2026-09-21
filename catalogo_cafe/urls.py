"""Rutas raíz del proyecto catalogo_cafe.

El proyecto solo enruta: delega las direcciones de la app en cafes/urls.py
mediante include(), de modo que la app pueda montarse en otra URL o en otro
proyecto sin tocar su código.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('cafes.urls')),
]

# En desarrollo Django sirve los archivos subidos por el usuario (MEDIA).
# En producción esto lo hace el servidor web o el hosting, nunca Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
