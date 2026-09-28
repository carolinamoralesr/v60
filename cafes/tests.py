"""Validación de los datos y de la interfaz generados con IA.

El JSON de fixtures/datos.json y el frontend se produjeron con apoyo de
inteligencia artificial, según lo pide el módulo. Estas pruebas no son un
extra: comprueban que esos artefactos cumplen las reglas del modelo y que
el catálogo responde como se espera. Cubren dos frentes:

1. Validar el fixture (temperaturas, ratios, relación 1:N, full_clean).
2. Validar la vista, las URLs y los templates reutilizables.
"""

import re

from django.conf import settings
from django.contrib.auth.models import Group, User
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
        """Dos consultas de datos (café + recetas). Los SAVEPOINT extra son ATOMIC_REQUESTS."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse('cafes:catalogo'))
        datos = [
            q['sql'] for q in ctx.captured_queries
            if 'SAVEPOINT' not in q['sql'] and 'RELEASE' not in q['sql']
        ]
        self.assertEqual(len(datos), 2)

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


class AutenticacionYSesionTest(TestCase):
    """Indicadores 4 y 5: rutas protegidas y cookie de sesión HttpOnly."""

    def setUp(self):
        self.grupo = Group.objects.get_or_create(name='Baristas')[0]
        self.barista = User.objects.create_user('barista', password='ClaveSegura123')
        self.barista.groups.add(self.grupo)

    def test_anonimo_no_entra_al_crud(self):
        respuesta = self.client.get(reverse('cafes:receta_crear'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('cafes:login'), respuesta.url)

    def test_login_crea_sesion_httponly(self):
        respuesta = self.client.post(
            reverse('cafes:login'),
            {'username': 'barista', 'password': 'ClaveSegura123'},
        )
        self.assertEqual(respuesta.status_code, 302)
        cookie = respuesta.cookies.get('sessionid')
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie['httponly'])
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertEqual(settings.SESSION_COOKIE_AGE, 3600)

    def test_registro_asigna_grupo_baristas(self):
        respuesta = self.client.post(reverse('cafes:registro'), {
            'username': 'nueva',
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        })
        self.assertEqual(respuesta.status_code, 302)
        usuario = User.objects.get(username='nueva')
        self.assertTrue(usuario.groups.filter(name='Baristas').exists())


class RecetaCrudTest(TestCase):
    """Indicador 3: Create, Read, Update, Delete con dueño y validación."""

    fixtures = ['datos.json']

    def setUp(self):
        self.grupo = Group.objects.get_or_create(name='Baristas')[0]
        self.dueno = User.objects.create_user('dueno', password='ClaveSegura123')
        self.otro = User.objects.create_user('otro', password='ClaveSegura123')
        self.dueno.groups.add(self.grupo)
        self.otro.groups.add(self.grupo)
        self.cafe = Cafe.objects.first()

    def _datos_receta(self, **extra):
        datos = {
            'cafe': self.cafe.pk,
            'autor': 'Dueno',
            'gramos_cafe': '15.0',
            'agua_total': 240,
            'ratio': '1:16',
            'temperatura': 92,
            'molienda': 'Media',
            'molino': 'Comandante C40',
            'clicks_molino': 26,
            'bloom_agua': 45,
            'bloom_segundos': 40,
            'vertidos': '0:00 45g, 0:40 240g',
            'tiempo_total': '3:00',
            'publicada': True,
        }
        datos.update(extra)
        return datos

    def test_crear_receta_autenticado(self):
        self.client.login(username='dueno', password='ClaveSegura123')
        respuesta = self.client.post(reverse('cafes:receta_crear'), self._datos_receta())
        self.assertEqual(respuesta.status_code, 302)
        receta = Receta.objects.get(autor='Dueno', creado_por=self.dueno)
        self.assertEqual(receta.cafe, self.cafe)

    def test_bloom_invalido_no_se_guarda(self):
        self.client.login(username='dueno', password='ClaveSegura123')
        respuesta = self.client.post(
            reverse('cafes:receta_crear'),
            self._datos_receta(bloom_agua=10),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Receta.objects.filter(autor='Dueno', creado_por=self.dueno).exists())

    def test_otro_usuario_no_edita(self):
        receta = Receta.objects.create(
            cafe=self.cafe,
            autor='Dueno',
            creado_por=self.dueno,
            gramos_cafe='15.0',
            agua_total=240,
            ratio='1:16',
            temperatura=92,
            molienda='Media',
            clicks_molino=26,
            bloom_agua=45,
            bloom_segundos=40,
            tiempo_total='3:00',
        )
        self.client.login(username='otro', password='ClaveSegura123')
        respuesta = self.client.post(
            reverse('cafes:receta_editar', args=[receta.pk]),
            self._datos_receta(autor='Intruso'),
        )
        self.assertEqual(respuesta.status_code, 403)
        receta.refresh_from_db()
        self.assertEqual(receta.autor, 'Dueno')

    def test_dueno_elimina(self):
        receta = Receta.objects.create(
            cafe=self.cafe,
            autor='Dueno',
            creado_por=self.dueno,
            gramos_cafe='15.0',
            agua_total=240,
            ratio='1:16',
            temperatura=92,
            molienda='Media',
            clicks_molino=26,
            bloom_agua=45,
            bloom_segundos=40,
            tiempo_total='3:00',
        )
        self.client.login(username='dueno', password='ClaveSegura123')
        respuesta = self.client.post(reverse('cafes:receta_eliminar', args=[receta.pk]))
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Receta.objects.filter(pk=receta.pk).exists())

    def test_staff_crea_cafe(self):
        User.objects.create_user('jefe', password='ClaveSegura123', is_staff=True)
        self.client.login(username='jefe', password='ClaveSegura123')
        respuesta = self.client.post(reverse('cafes:cafe_crear'), {
            'nombre': 'Lote Staff',
            'tostador': 'Tostaduría Staff',
            'origen': 'Putaendo, Chile',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Cafe.objects.filter(nombre='Lote Staff').exists())

    def test_barista_no_crea_cafe(self):
        self.client.login(username='dueno', password='ClaveSegura123')
        respuesta = self.client.get(reverse('cafes:cafe_crear'))
        self.assertEqual(respuesta.status_code, 403)
