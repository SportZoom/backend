import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tienda.models import Producto

# Limpiar productos existentes (opcional)
# Producto.objects.all().delete()
# print("✓ Productos anteriores eliminados")

productos = [
    {
        'nombre': 'Nike Air Max 270',
        'marca': 'Nike',
        'talla': '42',
        'precio': 450000,
        'stock': 15,
        'descripcion': 'Zapatillas con tecnología Air visible. Comodidad máxima para el día a día.',
        'imagen': ''
    },
    {
        'nombre': 'Adidas Ultraboost 22',
        'marca': 'Adidas',
        'talla': '41',
        'precio': 520000,
        'stock': 10,
        'descripcion': 'Running de alto rendimiento con amortiguación Boost responsive.',
        'imagen': ''
    },
    {
        'nombre': 'Puma RS-X Reinvention',
        'marca': 'Puma',
        'talla': '40',
        'precio': 380000,
        'stock': 20,
        'descripcion': 'Estilo retro con diseño moderno. Ideal para uso casual.',
        'imagen': ''
    },
    {
        'nombre': 'Nike Air Force 1 07',
        'marca': 'Nike',
        'talla': '43',
        'precio': 420000,
        'stock': 25,
        'descripcion': 'Clásico atemporal. Diseño icónico en blanco.',
        'imagen': ''
    },
    {
        'nombre': 'Adidas Superstar',
        'marca': 'Adidas',
        'talla': '39',
        'precio': 350000,
        'stock': 18,
        'descripcion': 'Icono del streetwear. Punta de goma característica.',
        'imagen': ''
    },
    {
        'nombre': 'Converse Chuck Taylor All Star',
        'marca': 'Converse',
        'talla': '41',
        'precio': 180000,
        'stock': 30,
        'descripcion': 'El clásico canvas. Disponible en negro.',
        'imagen': ''
    },
    {
        'nombre': 'Vans Old Skool',
        'marca': 'Vans',
        'talla': '42',
        'precio': 220000,
        'stock': 22,
        'descripcion': 'Skate clásico con la franja lateral característica.',
        'imagen': ''
    },
    {
        'nombre': 'New Balance 574',
        'marca': 'New Balance',
        'talla': '40',
        'precio': 320000,
        'stock': 12,
        'descripcion': 'Lifestyle runner con suela ENCAP. Comodidad todo el día.',
        'imagen': ''
    },
    {
        'nombre': 'Asics Gel-Kayano 29',
        'marca': 'Asics',
        'talla': '44',
        'precio': 580000,
        'stock': 8,
        'descripcion': 'Running de estabilidad premium. Tecnología GEL en talón y antepié.',
        'imagen': ''
    },
    {
        'nombre': 'Nike React Infinity Run',
        'marca': 'Nike',
        'talla': '43',
        'precio': 480000,
        'stock': 14,
        'descripcion': 'Diseñadas para reducir lesiones. Amortiguación React suave.',
        'imagen': ''
    },
    {
        'nombre': 'Under Armour HOVR Phantom 3',
        'marca': 'Under Armour',
        'talla': '42',
        'precio': 420000,
        'stock': 10,
        'descripcion': 'Entrenamiento versátil con tecnología HOVR.',
        'imagen': ''
    },
    {
        'nombre': 'Reebok Classic Leather',
        'marca': 'Reebok',
        'talla': '41',
        'precio': 280000,
        'stock': 16,
        'descripcion': 'Retro simplicity. Cuero suave y diseño minimalista.',
        'imagen': ''
    },
    {
        'nombre': 'Puma Suede Classic',
        'marca': 'Puma',
        'talla': '40',
        'precio': 290000,
        'stock': 20,
        'descripcion': 'Icono de los 80s. Gamuza premium y suela de goma.',
        'imagen': ''
    }
]

# Crear productos
contador = 0
for p in productos:
    producto, created = Producto.objects.get_or_create(
        nombre=p['nombre'],
        defaults={
            'marca': p['marca'],
            'talla': p['talla'],
            'precio': p['precio'],
            'stock': p['stock'],
            'descripcion': p['descripcion'],
            'imagen': p['imagen']
        }
    )
    
    if created:
        contador += 1
        print(f"✓ Creado: {producto.nombre} - ${producto.precio:,.0f} - Stock: {producto.stock}")
    else:
        print(f"⊗ Ya existe: {producto.nombre}")

print(f"\n{'='*50}")
print(f"✅ Proceso completado: {contador} productos nuevos creados")
print(f"📦 Total de productos en BD: {Producto.objects.count()}")