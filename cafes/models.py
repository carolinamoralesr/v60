"""Modelos del catálogo de café de especialidad (método V60).

En el patrón MVC esta capa es el Model: describe los datos, las reglas de
negocio y las relaciones. Django la llama igual.

Criterio de tipos de dato aplicado en todo el archivo:
- CharField para texto corto y acotado (se define siempre max_length).
- PositiveSmallIntegerField para magnitudes enteras que nunca son negativas
  y caben en un rango pequeño (temperatura, gramos de agua, segundos, clicks).
- DecimalField para la dosis de café, porque exige precisión exacta al
  decigramo; FloatField introduciría error de punto flotante en una medida
  que el barista pesa en balanza.
- ImageField (requiere Pillow) para la fotografía del envase.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Cafe(models.Model):
    #Un lote de café tostado por una tostaduría concreta.

    nombre = models.CharField(
        max_length=100,
        help_text="Nombre del lote, finca o variedad. Ej: Bourbon Chiroso Finca La Betania.",
    )
    tostador = models.CharField(
        max_length=100,
        help_text="Tostaduría responsable del tueste.",
    )
    origen = models.CharField(
        max_length=100,
        help_text="Zona y país de origen del grano.",
    )
    imagen = models.ImageField(
        upload_to='cafes/',
        blank=True,
        help_text="Fotografía del envase. Se procesa y valida con Pillow.",
    )

    class Meta:
        verbose_name = "café"
        verbose_name_plural = "cafés"
        ordering = ['tostador', 'nombre']
        # Una tostaduría no repite el mismo nombre de lote en el catálogo.
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'tostador'],
                name='lote_unico_por_tostador',
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.tostador}"


class Receta(models.Model):
    """Receta de filtrado en V60 asociada a un café del catálogo."""

    # Relación 1:N. related_name='recetas' permite recorrer cafe.recetas.all
    # en el template; CASCADE porque una receta no tiene sentido sin su café.
    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.CASCADE,
        related_name='recetas',
        help_text="Café sobre el que se aplica esta receta.",
    )
    autor = models.CharField(
        max_length=50,
        default="Anónimo",
        help_text="Barista que firma la receta.",
    )

    # --- Dosis y agua ---
    gramos_cafe = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('15.0'),
        validators=[MinValueValidator(Decimal('5.0')), MaxValueValidator(Decimal('60.0'))],
        help_text="Dosis de café molido en gramos.",
    )
    agua_total = models.PositiveSmallIntegerField(
        default=250,
        validators=[MinValueValidator(80), MaxValueValidator(1000)],
        help_text="Agua total vertida en mililitros.",
    )
    ratio = models.CharField(
        max_length=20,
        help_text="Proporción café:agua declarada por el barista. Ej: 1:16.",
    )
    temperatura = models.PositiveSmallIntegerField(
        # Bajo 85 °C la extracción queda subextraída y sobre 96 °C se quema.
        validators=[MinValueValidator(85), MaxValueValidator(96)],
        help_text="Temperatura del agua en grados Celsius (85-96).",
    )

    # --- Molienda ---
    molienda = models.CharField(
        max_length=50,
        help_text="Descripción táctil de la molienda. Ej: media (sal gruesa).",
    )
    molino = models.CharField(
        max_length=50,
        default="Comandante C40",
        help_text="Marca y modelo del molino usado como referencia.",
    )
    clicks_molino = models.PositiveSmallIntegerField(
        default=26,
        validators=[MaxValueValidator(60)],
        help_text="Clicks desde cero del molino indicado.",
    )

    # --- Pre-infusión (bloom) ---
    bloom_agua = models.PositiveSmallIntegerField(
        default=45,
        help_text="Agua del bloom en gramos (2 a 3 veces la dosis).",
    )
    bloom_segundos = models.PositiveSmallIntegerField(
        default=40,
        validators=[MaxValueValidator(90)],
        help_text="Duración de la pre-infusión en segundos.",
    )

    # --- Perfil de extracción ---
    vertidos = models.CharField(
        max_length=200,
        blank=True,
        help_text="Etapas del vertido. Ej: 0:00 45g, 0:40 140g, 1:20 240g.",
    )
    tiempo_total = models.CharField(
        max_length=10,
        default="3:00",
        help_text="Tiempo objetivo de extracción en formato mm:ss.",
    )

    class Meta:
        verbose_name = "receta"
        verbose_name_plural = "recetas"
        ordering = ['cafe', 'autor']

    def __str__(self):
        return f"Receta V60 de {self.autor} para {self.cafe.nombre}"

    @property
    def ratio_calculado(self):
        """Ratio real obtenido dividiendo el agua por la dosis.

        Sirve para contrastar el ratio declarado con el que producen los
        gramos efectivamente cargados en la receta.
        """
        if not self.gramos_cafe:
            return "—"
        proporcion = Decimal(self.agua_total) / self.gramos_cafe
        return f"1:{proporcion.quantize(Decimal('0.1'))}"
