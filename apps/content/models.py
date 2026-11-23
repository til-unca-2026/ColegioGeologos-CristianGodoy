from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.utils.text import slugify
from django.utils import timezone
from core.storage import SupabaseStorage
from .sanitizer import sanitize_html


class Contenido(models.Model):
    class Tipo(models.TextChoices):
        NOTICIA = "NOTICIA", "Noticia"
        COMUNICADO = "COMUNICADO", "Comunicado Oficial"
        EVENTO = "EVENTO", "Evento"
        CAPACITACION = "CAPACITACION", "Capacitación"
        BENEFICIO = "BENEFICIO", "Beneficio"
        CONVOCATORIA = "CONVOCATORIA", "Convocatoria Laboral"
        OTRO = "OTRO", "Otro"

    class EstadoPublicacion(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PROGRAMADO = "PROGRAMADO", "Programado"
        PUBLICADO = "PUBLICADO", "Publicado"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    class Visibilidad(models.TextChoices):
        PUBLICO = "PUBLICO", "Público"
        MATRICULADOS = "MATRICULADOS", "Matriculados"
        INTERNO = "INTERNO", "Interno"

    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        verbose_name="Tipo de contenido",
    )
    titulo = models.CharField(
        max_length=255,
        verbose_name="Título",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="Identificador único para la URL. Se genera automáticamente a partir del título si se deja en blanco.",
    )
    resumen = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Resumen",
        help_text="Texto breve que se muestra en listados y tarjetas (opcional si es afiche o flyer).",
    )
    cuerpo = models.TextField(
        blank=True,
        default="",
        verbose_name="Cuerpo",
        help_text="Contenido completo de la publicación (opcional si la información está en la imagen publicitaria o flyer).",
    )
    estado_publicacion = models.CharField(
        max_length=20,
        choices=EstadoPublicacion.choices,
        default=EstadoPublicacion.BORRADOR,
        verbose_name="Estado de publicación",
    )
    fecha_publicacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de publicación",
        help_text="Vacía si nunca se publicó. Si es a futuro, queda programado.",
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=Visibilidad.choices,
        verbose_name="Visibilidad",
    )

    # Auditoría y fechas
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de última modificación",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contenidos_creados",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contenidos_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "contenidos"
        verbose_name = "Contenido"
        verbose_name_plural = "Contenidos"
        ordering = ["-fecha_publicacion", "-fecha_creacion"]

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza campos de texto, selección y sanitiza el cuerpo.
        """
        if self.tipo:
            self.tipo = str(self.tipo).strip().upper()

        if self.titulo:
            self.titulo = " ".join(self.titulo.split()).strip()

        if self.slug:
            self.slug = slugify(self.slug).lower()

        if self.resumen:
            self.resumen = " ".join(self.resumen.split()).strip()
        else:
            self.resumen = ""

        if self.cuerpo:
            self.cuerpo = sanitize_html(self.cuerpo.strip())
        else:
            self.cuerpo = ""

        if self.visibilidad:
            self.visibilidad = str(self.visibilidad).strip().upper()

    def validar_datos(self):
        """
        Valida que el título tenga longitud adecuada y que los campos requeridos no estén vacíos.
        """
        errores = {}

        if not self.titulo or len(self.titulo) < 3:
            errores["titulo"] = "El título del contenido debe contener al menos 3 caracteres."

        if not self.tipo:
            errores["tipo"] = "Debe seleccionar el tipo de contenido."

        if not self.visibilidad:
            errores["visibilidad"] = "Debe indicar la visibilidad del contenido."

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"

    def determinar_estado_automatico(self):
        """
        Determina el estado de publicación en base a la fecha de publicación:
        - Si está ARCHIVADO manualmente, se preserva dicho estado.
        - fecha_publicacion vacía -> BORRADOR.
        - fecha_publicacion futura -> PROGRAMADO.
        - fecha_publicacion actual o pasada -> PUBLICADO.

        Se incluye un margen de tolerancia (ej. 2 minutos) para evitar que una
        publicación instantánea quede como PROGRAMADO debido a diferencias de
        segundos o desincronización de reloj entre el navegador y el servidor.
        """
        if self.estado_publicacion == self.EstadoPublicacion.ARCHIVADO:
            return self.EstadoPublicacion.ARCHIVADO

        if not self.fecha_publicacion:
            return self.EstadoPublicacion.BORRADOR

        # Margen de 2 minutos para compensar desfases de reloj y latencia
        if self.fecha_publicacion > (timezone.now() + timezone.timedelta(minutes=2)):
            return self.EstadoPublicacion.PROGRAMADO

        return self.EstadoPublicacion.PUBLICADO

    def save(self, *args, **kwargs):
        self.normalizar_datos()

        if not self.slug and self.titulo:
            base_slug = slugify(self.titulo)
            slug = base_slug
            counter = 1
            while Contenido.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Calcular automáticamente el estado de publicación
        self.estado_publicacion = self.determinar_estado_automatico()

        super().save(*args, **kwargs)

    @property
    def esta_publicado(self):
        """Indica si el contenido está en estado publicado y la fecha fijada ya se cumplió."""
        if not self.fecha_publicacion:
            return False
        return self.estado_publicacion == self.EstadoPublicacion.PUBLICADO and self.fecha_publicacion <= timezone.now()

    @property
    def imagen_portada(self):
        """Retorna la imagen designada como portada o la primera de la galería si existe."""
        portada = self.imagenes.filter(es_portada=True).first()
        if not portada:
            portada = self.imagenes.order_by("orden", "id").first()
        return portada

    @property
    def imagen_portada_url(self):
        """
        Retorna la URL de la imagen de portada o la imagen institucional por defecto
        si la publicación no cuenta con imágenes propias.
        """
        portada = self.imagen_portada
        if portada and portada.imagen:
            return portada.imagen.url
        return static("img/contenido/portada_contenido_defecto.jpg")


class ImagenContenido(models.Model):
    contenido = models.ForeignKey(
        Contenido,
        on_delete=models.CASCADE,
        related_name="imagenes",
        verbose_name="Contenido",
    )
    imagen = models.ImageField(
        upload_to="contenidos/",
        storage=SupabaseStorage(),
        verbose_name="Imagen",
    )
    epigrafe = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Epígrafe",
        help_text="Texto visible debajo de la imagen / pie de foto.",
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden de visualización",
    )
    es_portada = models.BooleanField(
        default=False,
        verbose_name="Es portada",
        help_text="Indica si es la imagen principal de la publicación. Solo una por contenido.",
    )

    class Meta:
        db_table = "imagenes_contenido"
        verbose_name = "Imagen de Contenido"
        verbose_name_plural = "Imágenes de Contenido"
        ordering = ["orden", "id"]

    def clean(self):
        super().clean()
        self.normalizar_datos()

    def normalizar_datos(self):
        """
        Normaliza epígrafe de la imagen.
        """
        if self.epigrafe:
            self.epigrafe = " ".join(self.epigrafe.split()).strip()
        else:
            self.epigrafe = ""

    def __str__(self):
        return f"Imagen ({self.id}) de {self.contenido.titulo}"

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        # Si se marca como portada, desmarcar cualquier otra imagen del mismo contenido
        if self.es_portada and self.contenido_id:
            ImagenContenido.objects.filter(
                contenido_id=self.contenido_id,
                es_portada=True,
            ).exclude(pk=self.pk).update(es_portada=False)
        super().save(*args, **kwargs)


class DetalleEvento(models.Model):
    class Modalidad(models.TextChoices):
        PRESENCIAL = "PRESENCIAL", "Presencial"
        VIRTUAL = "VIRTUAL", "Virtual"
        HIBRIDA = "HIBRIDA", "Híbrida"

    contenido = models.OneToOneField(
        Contenido,
        on_delete=models.CASCADE,
        related_name="detalle_evento",
        verbose_name="Contenido",
    )
    inicio = models.DateTimeField(
        verbose_name="Fecha y hora de inicio",
    )
    fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y hora de finalización",
    )
    lugar = models.CharField(
        max_length=255,
        verbose_name="Lugar o plataforma",
        help_text="Lugar físico donde se realiza o enlace de la plataforma.",
    )
    modalidad = models.CharField(
        max_length=20,
        choices=Modalidad.choices,
        verbose_name="Modalidad",
    )
    link_inscripcion = models.URLField(
        blank=True,
        null=True,
        verbose_name="Enlace de inscripción",
        help_text="Enlace externo para la inscripción de participantes.",
    )
    cupo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cupo máximo",
        help_text="Cantidad máxima de participantes (vacío = sin límite).",
    )

    class Meta:
        db_table = "detalles_evento"
        verbose_name = "Detalle de Evento"
        verbose_name_plural = "Detalles de Eventos"

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza lugar, modalidad, link de inscripción y cupo.
        """
        if self.lugar:
            self.lugar = " ".join(self.lugar.split()).strip()
        else:
            self.lugar = ""

        if self.modalidad:
            self.modalidad = str(self.modalidad).strip().upper()

        if self.link_inscripcion:
            link = self.link_inscripcion.strip()
            self.link_inscripcion = link if link else None
        else:
            self.link_inscripcion = None

        if self.cupo is not None and str(self.cupo).strip() == "":
            self.cupo = None

    def validar_datos(self):
        """
        Valida que el lugar sea obligatorio, la coherencia de fechas de inicio/fin y cupo mayor a 0.
        """
        errores = {}

        if not self.lugar or not self.lugar.strip():
            errores["lugar"] = "El lugar o plataforma del evento es obligatorio."

        if self.inicio and self.fin:
            if self.fin < self.inicio:
                errores["fin"] = "La fecha y hora de finalización no puede ser anterior a la de inicio."

        if self.cupo is not None and self.cupo <= 0:
            errores["cupo"] = "El cupo máximo debe ser un número entero mayor a 0."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Detalle de evento: {self.contenido.titulo} ({self.inicio.strftime('%d/%m/%Y %H:%M')})"

