from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que hereda de AbstractUser.
    Permite agregar campos adicionales sin perder la estructura base de Django.
    """
    es_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'tienda_usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


GENEROS = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('O', 'Otro'),
    ('P', 'Prefiero no decir'),
]

class Cliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cliente')
    genero = models.CharField(max_length=1, choices=GENEROS)
    acepta_terminos = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cliente: {self.usuario.get_full_name() or self.usuario.username}"

    class Meta:
        db_table = 'tienda_cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Producto(models.Model):
    """
    Modelo de productos disponibles en la tienda.
    Incluye información básica y una imagen opcional.
    """
    MARCAS = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
        ('Puma', 'Puma'),
        ('Reebok', 'Reebok'),
        ('Converse', 'Converse'),
        ('Vans', 'Vans'),
        ('New Balance', 'New Balance'),
        ('Asics', 'Asics'),
        ('Under Armour', 'Under Armour'),
        ('Otra', 'Otra'),
    ]
    
    TALLAS = [
        ('35', '35'),
        ('36', '36'),
        ('37', '37'),
        ('38', '38'),
        ('39', '39'),
        ('40', '40'),
        ('41', '41'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
    ]
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    marca = models.CharField(max_length=50, choices=MARCAS, default='Otra')  # NUEVO
    talla = models.CharField(max_length=10, choices=TALLAS, default='40')    # NUEVO
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.marca} - Talla {self.talla}"

    class Meta:
        db_table = 'tienda_producto'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        

class Pedido(models.Model):
    ESTADOS = (
        ("comprado", "Comprado"),
        ("enviado", "Enviado"),
        ("en_reparto", "En reparto"),
        ("entregado", "Entregado"),
    )
    numero_pedido = models.CharField(max_length=20, unique=True, editable=False)
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pedidos'
    )
    nombre = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    carrito = models.JSONField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="comprado")
    wompi_id = models.CharField(max_length=100, blank=True, null=True)
    referencia_pago = models.CharField(max_length=150, null=True, blank=True)

    # Dentro de la clase Pedido, antes del método save():
    def estado_calculado(self):
        """Calcula el estado según los días transcurridos desde la compra."""
        dias = (timezone.now() - self.fecha).days
        if dias >= 3:
            return "entregado"
        elif dias >= 2:
            return "en_reparto"
        elif dias >= 1:
            return "enviado"
        return "comprado"

    def actualizar_estado(self):
        """Persiste el estado en BD si ha cambiado respecto al calculado."""
        nuevo_estado = self.estado_calculado()
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            self.save(update_fields=["estado"])
        return self.estado

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            self.numero_pedido = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.numero_pedido}"
