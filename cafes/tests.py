"""Validación de los datos y de la interfaz generados con IA.

El JSON de fixtures/datos.json y el frontend se produjeron con apoyo de
inteligencia artificial, según lo pide el módulo. Estas pruebas no son un
extra: comprueban que esos artefactos cumplen las reglas del modelo y que
el catálogo responde como se espera. Cubren dos frentes:

1. Validar el fixture (temperaturas, ratios, relación 1:N, full_clean).
2. Validar la vista, las URLs y los templates reutilizables.
"""

import re

from django.test import TestCase
from django.urls import reverse

from .models import Cafe, Receta


class FixtureDatosTest(TestCase):
    """Indicador: datos variados y representativos, validados para pruebas."""

    fixtures = ['datos.json']

    def test_cantidad_de_registros(self):
        self.assertEqual(Cafe.objects.count(), 5)
        self.assertEqual(Receta.objects.count(), 7)

    def test_los_datos_pasan_las_validaciones_del_modelo(self):
        """full_clean() ejecuta los validators de cada campo."""
        for cafe in Cafe.objects.all():
            cafe.full_clean()
        for receta in Receta.objects.all():
            receta.full_clean()

    def test_temperaturas_en_rango_de_filtrado(self):
        for receta in Receta.objects.all():
            self.assertGreaterEqual(receta.temperatura, 85)
            self.assertLessEqual(receta.temperatura, 96)

    def test_formato_de_ratio_y_tiempo(self):
        for receta in Receta.objects.all():
            self.assertRegex(receta.ratio, r'^1:\d{1,2}$')
            self.assertRegex(receta.tiempo_total, r'^\d:[0-5]\d$')

    def test_datos_variados(self):
        """El catálogo no repite tostadurías y cubre varios orígenes y molinos."""
        tostadores = Cafe.objects.values_list('tostador', flat=True)
        self.assertEqual(len(set(tostadores)), 5)
        self.assertGreaterEqual(len(set(Receta.objects.values_list('molino', flat=True))), 3)
        paises = {cafe.origen.split(',')[-1].strip() for cafe in Cafe.objects.all()}
        self.assertGreaterEqual(len(paises), 4)

    def test_relacion_uno_a_muchos(self):
        """Al menos un café tiene más de una receta asociada."""
        con_varias = [c for c in Cafe.objects.prefetch_related('recetas') if c.recetas.count() > 1]
        self.assertTrue(con_varias)
        for cafe in Cafe.objects.all():
            for receta in cafe.recetas.all():
                self.assertEqual(receta.cafe_id, cafe.id)

    def test_todos_los_cafes_tienen_imagen_declarada(self):
        for cafe in Cafe.objects.all():
            self.assertTrue(cafe.imagen.name.startswith('cafes/'))

    def test_ratio_calculado_coincide_con_el_declarado(self):
        """El ratio declarado no puede alejarse del que dan dosis y agua."""
        for receta in Receta.objects.all():
            declarado = int(receta.ratio.split(':')[1])
            real = float(re.sub(r'^1:', '', receta.ratio_calculado))
            self.assertAlmostEqual(declarado, real, delta=1.5)


class CatalogoVistaTest(TestCase):
    """Indicador: vistas y templates organizados, MVT e integración servidor."""

    fixtures = ['datos.json']

    def test_la_url_con_nombre_resuelve_la_vista(self):
        self.assertEqual(reverse('cafes:catalogo'), '/')

    def test_respuesta_y_plantillas_usadas(self):
        respuesta = self.client.get(reverse('cafes:catalogo'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'base.html')
        self.assertTemplateUsed(respuesta, 'cafes/catalogo.html')
        self.assertTemplateUsed(respuesta, 'cafes/partials/_boleta.html')
        self.assertTemplateUsed(respuesta, 'cafes/partials/_modal_receta.html')
        self.assertTemplateUsed(respuesta, 'cafes/partials/_polaroid.html')

    def test_contexto_entregado_al_template(self):
        respuesta = self.client.get(reverse('cafes:catalogo'))
        self.assertEqual(respuesta.context['total_cafes'], 5)
        self.assertEqual(respuesta.context['total_recetas'], 7)

    def test_evita_el_problema_n_mas_1(self):
        """Dos consultas: una de cafés y una de recetas, gracias al prefetch."""
        with self.assertNumQueries(2):
            self.client.get(reverse('cafes:catalogo'))

    def test_filtro_get_por_origen(self):
        respuesta = self.client.get(reverse('cafes:catalogo'), {'q': 'guatemala'})
        self.assertEqual(respuesta.context['total_cafes'], 1)
        self.assertContains(respuesta, 'Café Folks')

    def test_busqueda_sin_resultados(self):
        respuesta = self.client.get(reverse('cafes:catalogo'), {'q': 'no-existe'})
        self.assertEqual(respuesta.context['total_cafes'], 0)
        self.assertContains(respuesta, 'Sin coincidencias')

    def test_cafe_sin_recetas_muestra_el_mensaje_alternativo(self):
        """Comprueba la rama {% else %} del template."""
        Cafe.objects.create(
            nombre='Lote experimental',
            tostador='Tostaduría de prueba',
            origen='Alto Hospicio, Chile',
        )
        respuesta = self.client.get(reverse('cafes:catalogo'), {'q': 'experimental'})
        self.assertContains(respuesta, '¡Sé el primero en experimentar!')
