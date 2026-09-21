# Catálogo V60 · Directorio de Café de Especialidad

Aplicación web desarrollada con Django que funciona como directorio de cafés de
especialidad chilenos y de sus recetas de filtrado en **Hario V60**. Cada café del
catálogo se muestra como una boleta colgada de un hilo; al abrirla se despliega la
receta técnica completa (dosis, ratio, temperatura, clicks de molino, bloom,
estructura de vertidos y tiempo objetivo) junto a la fotografía del envase.

El frontend (plantillas, CSS y JavaScript) y el archivo JSON de datos de prueba
se elaboraron **con apoyo de inteligencia artificial**, tal como lo pide el
módulo. El backend, los modelos, las vistas y la configuración se revisaron,
adaptaron y validaron a mano. El detalle está en las secciones de los
indicadores 10 y 11.

## Patrón MVC y su equivalente MVT en Django (indicador 5)

La rúbrica evalúa el **Modelo Vista-Controlador (MVC)**. Django implementa ese
mismo patrón bajo el nombre **MVT** (Model-View-Template). No son dos
arquitecturas distintas: cambian los nombres de dos capas.

| Rol en MVC | Nombre en Django (MVT) | Archivo en este proyecto | Qué hace aquí |
| --- | --- | --- | --- |
| **Model** | Model | `cafes/models.py` | Datos, validadores y la relación 1:N `Cafe` → `Receta`. |
| **Controlador** | View | `cafes/views.py` | Recibe el `HttpRequest`, filtra con `request.GET` y arma el contexto. |
| **Vista** | Template | `cafes/templates/` | Presenta el HTML. No consulta la base de datos por su cuenta. |
| Despachador | URLconf | `cafes/urls.py` + `catalogo_cafe/urls.py` | Traduce la URL al Controlador (`catalogo_cafes`). |

Esta separación se aplica de forma consistente: la plantilla nunca ejecuta
consultas extra, la vista nunca pinta HTML a mano y el modelo no conoce el
navegador. Por eso la app se puede mantener y escalar: cambiar el diseño no
exige tocar el modelo, y agregar un filtro no exige reescribir las boletas.

La plantilla base (`base.html`) concentra el esqueleto y los estilos; el
catálogo (`cafes/catalogo.html`) solo rellena bloques; los parciales
(`_boleta.html`, `_modal_receta.html`, `_receta.html`, `_linea.html`,
`_polaroid.html`) se reutilizan en la tarjeta y en el modal.

## Estructura del proyecto

```
backend/
├── catalogo_cafe/          # Configuración del proyecto (settings, urls, wsgi)
├── cafes/                  # App principal
│   ├── models.py           # Capa Model (MVC)
│   ├── views.py            # Capa Controlador (MVC) / View (MVT)
│   ├── urls.py             # Despachador de la app (app_name = 'cafes')
│   ├── admin.py            # Panel de administración con inline de recetas
│   ├── tests.py            # Validación de los datos e interfaz generados con IA
│   └── templates/          # Capa Vista (MVC) / Template (MVT)
│       ├── base.html
│       └── cafes/
│           ├── catalogo.html
│           └── partials/
├── fixtures/datos.json     # Datos de prueba generados con IA (5 cafés, 7 recetas)
├── media/cafes/            # Fotografías de los envases
├── .env.example            # Plantilla de variables de entorno (hosting / DNS)
└── requirements.txt
```

## Justificación de los paquetes externos (indicador 3)

El archivo `requirements.txt` lista **solo las dependencias directas**. Las librerías
`asgiref` y `sqlparse` no se declaran porque `pip` las instala automáticamente como
dependencias internas de Django.

### Django 6.1.1

Framework web del proyecto. Se elige por sobre alternativas como Flask porque trae
resuelto todo lo que esta aplicación necesita sin sumar librerías extra: ORM con
migraciones para modelar la relación café–receta, sistema de plantillas con herencia
e inclusión, panel de administración automático, carga de datos de prueba mediante
fixtures y un servidor de desarrollo con recarga automática.

### Pillow 12.3.0

Es el requisito obligatorio del campo `models.ImageField`, usado en `Cafe.imagen`
para la fotografía del envase. Sin Pillow instalado, `python manage.py check` falla
con el error `fields.E210: Cannot use ImageField because Pillow is not installed`.

Se elige `ImageField` en vez de un simple `CharField` con la URL de la imagen porque
Pillow **verifica que el archivo subido sea realmente una imagen válida** y expone sus
dimensiones (`width`/`height`), lo que evita guardar archivos corruptos o de otro tipo
desde el panel de administración. Además, `ImageField` entrega el atributo `.url`, que
el template usa directamente con `{{ cafe.imagen.url }}`.

### python-decouple 3.8

Separa la configuración del código fuente siguiendo la metodología *Twelve-Factor App*.
Los valores que cambian entre el entorno local y el de producción —
`SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` — se leen desde un archivo `.env` que
**nunca se versiona**, en lugar de estar escritos dentro de `settings.py`.

Se elige por sobre leer `os.environ` directamente porque entrega tres cosas que el
código manual no tiene: valores por defecto para que el proyecto siga funcionando si
falta alguna variable opcional, conversión de tipos mediante `cast` (aquí `Csv()` y
`bool`), y una búsqueda automática del `.env` sin necesidad de exportar variables a
mano en cada terminal. Gracias a esto, desplegar en otro hosting o publicar el
código en un repositorio GitHub **no exige dejar secretos en el código**: basta
con el `.env` local o las variables del panel del PaaS.

## Tecnologías del lado del servidor y soluciones pertinentes (indicador 9)

El proyecto integra las piezas del lado del servidor que Django ya entrega y,
donde hay más de un camino, **elige el pertinente** y lo deja documentado.

| Necesidad | Solución elegida | Alternativa descartada | Por qué esta |
| --- | --- | --- | --- |
| Framework | Django | Flask | ORM, admin, fixtures y plantillas vienen juntos. |
| Base de datos local | SQLite | PostgreSQL en desarrollo | Cero instalación; en producción sí se migraría a PostgreSQL. |
| Fotos de envases | `ImageField` + Pillow | `CharField` con una URL | Pillow valida que el archivo sea una imagen real. |
| Configuración de despliegue | `python-decouple` + `.env` | Secretos en `settings.py` | La `SECRET_KEY` no se sube a un GitHub público. |
| Consulta del catálogo | GET `?q=` | POST | GET no modifica datos; la URL se puede compartir. |
| Relación café–recetas en la vista | `prefetch_related('recetas')` | `Cafe.objects.all()` suelto | Evita el problema N+1: siempre 2 consultas SQL. |
| Hosting de producción | Render o PythonAnywhere | Un VPS armado a mano | PaaS nativas para Python; ver indicador 12. |
| Archivos de `media/` en local | Django + `DEBUG` | Un Nginx en el notebook | En desarrollo basta Django; en producción lo sirve el hosting. |

El ORM, el `URLconf`, el sistema de plantillas, el admin y WSGI
(`catalogo_cafe/wsgi.py`) son tecnologías del lado del servidor ya integradas
en el flujo: el cliente pide, el servidor consulta, valida y responde.

## Instalación y puesta en marcha (indicador 6)

Requisito previo: **Python 3.12 o superior** (el proyecto se desarrolló en 3.14).

### 1. Clonar o descargar el proyecto y entrar a la carpeta

```bash
cd backend
```

### 2. Crear el entorno virtual

El entorno virtual aísla las dependencias de este proyecto de las del sistema.

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

```bash
# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

La consola debe mostrar el prefijo `(venv)`.

### 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 5. Crear el archivo de variables de entorno

El repositorio incluye una plantilla `.env.example` (sí se sube a GitHub).
Se copia a `.env`, que es el archivo real que lee `python-decouple` y que
**nunca se versiona**. Ahí vive la `SECRET_KEY` de Django: no es una API key
de un servicio externo, pero **sí es un secreto** (firma cookies de sesión y
tokens CSRF). En un repo público no puede ir en `settings.py`.

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Este paso **no se puede omitir**: sin `SECRET_KEY` en el `.env` Django no arranca.
El valor de ejemplo sirve para evaluar el proyecto en local; en un hosting real
se genera otra clave y se carga como variable de entorno del panel.

### 6. Aplicar las migraciones

Crea la base de datos SQLite con las tablas de `Cafe` y `Receta`.

```bash
python manage.py migrate
```

### 7. Cargar los datos de prueba

```bash
python manage.py loaddata datos.json
```

Funciona sin indicar la ruta porque `settings.py` declara
`FIXTURE_DIRS = [BASE_DIR / 'fixtures']`.

### 8. Levantar el servidor de desarrollo

```bash
python manage.py runserver
```

El catálogo queda disponible en <http://127.0.0.1:8000/>.

### Comandos adicionales

```bash
python manage.py test              # Valida los datos e interfaz generados con IA
python manage.py check             # Valida la configuración
python manage.py createsuperuser   # Crea un usuario para /admin/
```

## Uso de inteligencia artificial (indicador 10)

El módulo pide usar IA como apoyo al **diseño de interfaces** y a la **generación
de datos de prueba**. Ese fue el encargo del profesor y así se hizo. No se
aceptó el resultado a ciegas: cada entrega se evaluó, se adaptó y se validó.

| Artefacto | Qué hizo la IA | Qué se aceptó | Qué se corrigió o rechazó | Cómo se validó |
| --- | --- | --- | --- | --- |
| Frontend (`catalogo.html`, `base.html`, CSS, JS) | Maquetó el hero con SVG, el protocolo V60, las boletas, el carrusel y los modales. | Estética indie/line-art, boleta colgada, Polaroid y modal nativo `<dialog>`. | La primera versión cambió las boletas por tarjetas resumen con botón «Ver Receta». Se rechazó y se volvió al formato boleta clickeable. Las modales estaban *dentro* del carrusel y rompían la inclinación; se movieron fuera. | El catálogo responde `200`, las plantillas se renderizan sin tags sueltos y `assertTemplateUsed` comprueba que se reutilizan los parciales. |
| Datos (`fixtures/datos.json`) | Propuso 5 tostadurías chilenas, orígenes y recetas V60. | Tostadurías reales y premiadas (Holaste!, Eco Mapu, Wake Up, Micelio, Folks) y orígenes verificables. | Se rechazó tratar como receta oficial de cada local los parámetros de vertido. Esos números son reconstrucciones técnicas plausibles, no fichas publicadas por las cafeterías. Se agregaron 2 recetas extra para que la relación 1:N no se viera como 1:1. | `loaddata` + `full_clean()` + pruebas de rango (85–96 °C), formato de ratio y coincidencia del ratio calculado. |
| Fotos de Polaroid | Buscó imágenes de los envases en las tiendas. | Bolsas reales de Holaste, Micelio y Folks. | Eco Mapu y Wake Up no publican su bolsa. Se rechazó una foto genérica haciéndola pasar por suya; se usó material auténtico de cada marca y se dejó constancia de la limitación. | Las cinco URLs `/media/cafes/` responden `200`. |
| Vista del catálogo | Escribió `Cafe.objects.all()`. | El flujo GET → vista → template. | Eso provocaba el problema N+1 (una consulta SQL por café). Se adaptó a `prefetch_related('recetas')`. | `assertNumQueries(2)`. |
| Tests (`cafes/tests.py`) | Generó la batería de comprobaciones. | Usarlos para **validar** el JSON y el frontend producidos con IA, no como un extra fuera de rúbrica. | Se reencuadraron como evidencia de los indicadores 10 y 11. | `python manage.py test` → 15 pruebas en verde. |

La IA se usó de forma estratégica: acelera la interfaz y los datos, y el criterio
humano decide qué entra al proyecto. Evaluar, adaptar y validar es exactamente
el nivel Destacado de este indicador.

## Datos de prueba variados, representativos y validados (indicador 11)

El fixture `fixtures/datos.json` se **generó con IA** y luego se contrastó con
fuentes reales. Quedó así:

| Qué es real y verificable | Qué es una reconstrucción técnica (plausible, no oficial) |
| --- | --- |
| Las 5 tostadurías chilenas y sus nombres comerciales. | Los nombres de los baristas. |
| Los orígenes de lote (país / zona) alineados con lo que esas marcas tuestan. | Los clicks exactos, los vertidos y los tiempos al segundo. |
| Las fotos de envase de Holaste, Micelio y Folks. | — |

Los datos son **variados**: 5 tostadurías, 5 países de origen (Colombia, Etiopía,
México, Guatemala y un segundo lote colombiano), 3 molinos (Comandante C40,
Timemore C2, 1Zpresso JX-Pro) y temperaturas entre 88 °C y 94 °C. Son
**representativos** de un V60 profesional: dosis, ratio, bloom y estructura de
vertidos. La relación 1:N se demuestra con Holaste y Wake Up, que tienen **dos
recetas** cada uno (7 recetas en total para 5 cafés).

**Validación para pruebas completas.** No basta con que el JSON cargue. El
archivo `cafes/tests.py` —también producido con IA y revisado— ejecuta esas
comprobaciones:

- `full_clean()` sobre cada café y cada receta (corre los validadores del modelo).
- Temperaturas dentro de 85–96 °C, ratio con formato `1:NN` y tiempo `m:ss`.
- Al menos 4 países y 3 molinos distintos; al menos un café con más de una receta.
- El ratio declarado no se aleja más de 1.5 del ratio real (`agua / gramos`).
- La vista usa las plantillas reutilizables, filtra por `?q=` y evita el N+1.

```bash
python manage.py test
```

## Problemas encontrados y cómo se resolvieron (indicador 6)

Registro de los errores reales que aparecieron durante el desarrollo y su solución,
por si se repiten al montar el entorno en otro equipo.

| Problema | Causa | Solución aplicada |
| --- | --- | --- |
| Las fotos de los envases no cargaban (`404`) | Faltaba configurar el almacenamiento de archivos subidos | Se definieron `MEDIA_URL` y `MEDIA_ROOT` en `settings.py` y se agregó `static(settings.MEDIA_URL, ...)` a `urls.py` bajo `if settings.DEBUG`. |
| `Invalid HTTP_HOST header: 'testserver'` | `ALLOWED_HOSTS` no incluía el host usado por el cliente de pruebas | Las pruebas se ejecutan con `python manage.py test`, que agrega `testserver` automáticamente; para desarrollo se declararon `127.0.0.1` y `localhost`. |
| `makemigrations` se detenía preguntando por un valor por defecto | Se cambió `imagen` de `null=True` a `blank=True` y la columna ya tenía filas | Se entregó `''` como valor único de relleno, que es el valor vacío estándar de un `ImageField`. |
| El catálogo lanzaba una consulta SQL por cada café (problema N+1) | El template recorre `cafe.recetas.all` dentro del bucle de cafés | Se agregó `prefetch_related('recetas')` en la vista: ahora son siempre 2 consultas, verificado en `test_evita_el_problema_n_mas_1`. |
| Primera versión del frontend sin boletas | La IA propuso tarjetas resumen y un botón «Ver Receta» | Se rechazó esa recomendación y se restauró la boleta clickeable que abre el modal. |

## Infraestructura y Despliegue (HTTP, DNS y Hosting)

Este proyecto se sostiene sobre la arquitectura **cliente-servidor**: el navegador
(cliente) solicita un recurso y Django (servidor) lo procesa y responde. En ese
intercambio se articulan los tres conceptos. **El protocolo HTTP define las reglas del
intercambio web** (ej. el buscador usa GET para solicitar información sin modificar
datos). **El sistema DNS traducirá el dominio legible a la dirección IP numérica del
servidor en la red**, de modo que el usuario escriba un nombre y no una IP. **El Hosting
proveerá el almacenamiento y capacidad de cómputo para hospedar la app**, manteniéndola
disponible las 24 horas, algo que un computador personal no garantiza. El proyecto ya
está **preparado para producción mediante `python-decouple`**: la lista de dominios
autorizados no está escrita en el código, sino que se lee del entorno con
`ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1, localhost', cast=Csv())`,
así que cambiar de servidor o de dominio solo requiere editar el archivo `.env`. Como
alternativas pertinentes se proponen plataformas **PaaS nativas para Python**:
**Render**, que despliega directamente desde el repositorio ejecutando Gunicorn sobre
la interfaz WSGI y entrega certificado HTTPS automático, o **PythonAnywhere**, que
ofrece un panel específico para Django con un subdominio incluido y la opción de
apuntar un dominio propio mediante un registro `CNAME` en el DNS. Ambas están ya
contempladas en `.env.example` con los sufijos `.render.com` y `.pythonanywhere.com`.

### Detalle técnico de cada capa

**HTTP.** Todo lo que se ve en pantalla es la respuesta a una petición HTTP. Cuando el
navegador pide `http://127.0.0.1:8000/?q=guatemala`, envía una petición con el método
**GET** que Django entrega al `URLconf`; este la enruta hacia la vista
`catalogo_cafes()`, que recibe un objeto `HttpRequest`, lee los parámetros de la URL
con `request.GET`, consulta la base de datos y devuelve un `HttpResponse` con el HTML
renderizado y el código de estado **200 OK**. El buscador del catálogo usa GET —y no
POST— justamente porque solo consulta información: el filtro queda visible en la URL,
se puede compartir y el navegador puede cachearlo. POST se reserva para peticiones que
modifican datos, y en ese caso Django exige el token CSRF. Otros códigos de estado del
mismo protocolo ya aparecen en el proyecto: **404** cuando se pide una ruta inexistente
y **400** si llega una cabecera `Host` no autorizada.

**DNS.** En desarrollo se escribe `127.0.0.1` o `localhost`, que el sistema operativo
resuelve localmente sin salir a internet. Al desplegar, el sitio vive en un servidor con
una dirección IP pública, y como nadie memoriza direcciones IP se contrata un dominio
(por ejemplo `catalogov60.cl`). El **DNS** es el servicio que traduce ese nombre a la IP
del servidor: se crea un registro `A` que apunta el dominio a la IP, o un `CNAME` que lo
apunta al nombre del hosting. Ese dominio debe quedar además dentro de `ALLOWED_HOSTS`
—que ahora se configura desde el `.env`—, porque Django rechaza con un **400** cualquier
petición cuyo encabezado `Host` no esté en esa lista; es una defensa contra ataques de
cabecera Host envenenada. Por eso `.env.example` usa comodines de subdominio como
`.render.com`: cubren el subdominio que la plataforma asigne al desplegar.

**Hosting.** El servidor de `runserver` es solo para desarrollo: es de un solo proceso y
no está pensado para tráfico real. En un hosting (PythonAnywhere, Render, Railway, un VPS
con Nginx y Gunicorn, etc.) la aplicación se ejecuta detrás de un servidor de aplicaciones
que habla con Django mediante **WSGI** —la interfaz que ya está declarada en
`catalogo_cafe/wsgi.py`— mientras un servidor web entrega los archivos estáticos y las
imágenes de `media/`, tarea que en producción Django no realiza. El despliegue implica
además cambiar `DEBUG = False` en el `.env` del hosting, ejecutar `collectstatic` y, normalmente, migrar de SQLite
a PostgreSQL. Encadenando las tres piezas:
el usuario escribe el **dominio**, el **DNS** lo traduce a la IP del **hosting**, y allí el
servidor recibe la petición **HTTP** y se la pasa a Django, que responde con el catálogo.

`SECRET_KEY` y `DEBUG` ya se leen del entorno con el mismo `python-decouple`. En el
repo público de GitHub solo queda `.env.example` (un placeholder). El `.env` real,
`venv/`, `db.sqlite3` y `RUBRICA.pdf` están en `.gitignore` y no deben subirse.
