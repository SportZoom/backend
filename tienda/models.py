from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


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
        ("pendiente", "Pendiente de pago"),
        ("pagado", "Pagado"),
        ("fallido", "Pago fallido"),
        ("enviado", "Enviado"),        
        ("entregado", "Entregado"),        
        ("cancelado", "Cancelado"),

    )

    numero_pedido = models.CharField(max_length=20, unique=True, editable=False)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    carrito = models.JSONField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    wompi_id = models.CharField(max_length=100, blank=True, null=True)
    referencia_pago = models.CharField(max_length=150, null=True, blank=True)


    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            self.numero_pedido = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.numero_pedido}"