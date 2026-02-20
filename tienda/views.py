from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend  # NUEVO
from rest_framework import filters  # NUEVO
from .models import Producto, Pedido
from .serializers import ProductoSerializer, AdminLoginSerializer, PedidoSerializer
from .permissions import IsAdminUserCustom
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import PedidoSerializer
from rest_framework.decorators import api_view
from django.conf import settings
import requests
import uuid



class ProductoList(generics.ListAPIView):
    queryset = Producto.objects.all().order_by('nombre')
    serializer_class = ProductoSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # NUEVO
    filterset_fields = ['marca', 'talla']  # NUEVO
    search_fields = ['nombre']  # NUEVO

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por rango de precio
        precio_min = self.request.query_params.get('precio_min')
        precio_max = self.request.query_params.get('precio_max')
        
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
            
        return queryset



# VISTAS ADMINISTRATIVAS

class ProductoCreate(generics.CreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_context(self):
        return {'request': self.request}


class ProductoUpdate(generics.UpdateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_context(self):
        return {'request': self.request}


class ProductoDelete(generics.DestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminUserCustom]


class AdminLoginView(APIView):
    """
    Vista para iniciar sesión como administrador.
    Devuelve un token JWT si las credenciales son válidas y el usuario es administrador.
    """
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'es_admin': getattr(user, 'es_admin', False)
        }, status=status.HTTP_200_OK)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('nombre')
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # NUEVO
    filterset_fields = ['marca', 'talla']  # NUEVO
    search_fields = ['nombre']  # NUEVO
    
    def get_serializer_context(self):
        return {'request': self.request}

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUserCustom()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por rango de precio
        precio_min = self.request.query_params.get('precio_min')
        precio_max = self.request.query_params.get('precio_max')
        
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        print("FILES:", request.FILES)
        print("POST:", request.data)
        return super().create(request, *args, **kwargs)
    
# Nuevo endpoint para crear pedidos
# ======================================
#  PEDIDOS
# ======================================

@api_view(['POST'])
def crear_pedido(request):
    # Validar stock ANTES de crear el pedido
    carrito = request.data.get('carrito', [])
    
    for item in carrito:
        try:
            producto = Producto.objects.get(id=item['id'])
            cantidad_solicitada = item.get('cantidad', 1)
            
            if producto.stock < cantidad_solicitada:
                return Response({
                    "error": f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}, Solicitado: {cantidad_solicitada}"
                }, status=400)
        except Producto.DoesNotExist:
            return Response({
                "error": f"Producto {item['id']} no encontrado"
            }, status=404)
    
    # Calcular subtotal e IVA
    subtotal = float(request.data.get('total', 0))
    iva = subtotal * 0.19  # 19% IVA Colombia
    total_con_iva = subtotal + iva
    
    # Crear pedido con total incluyendo IVA
    data = request.data.copy()
    data['total'] = total_con_iva
    
    serializer = PedidoSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    pedido = serializer.save()
    
    return Response({
        "mensaje": "Pedido creado",
        "numero_pedido": pedido.numero_pedido,
        "subtotal": subtotal,
        "iva": iva,
        "total": total_con_iva
    })

#Endpoint de consulta de pedido

@api_view(['GET'])
def consultar_pedido(request, numero_pedido):
    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
        serializer = PedidoSerializer(pedido)
        return Response(serializer.data)
    except Pedido.DoesNotExist:
        return Response({
            "error": "No se encontró ningún pedido con ese código"
        }, status=404)

@api_view(['GET'])
def listar_pedidos(request):
    """
    Lista todos los pedidos ordenados por fecha (más recientes primero)
    Solo accesible para administradores
    """
    pedidos = Pedido.objects.all().order_by('-fecha')
    serializer = PedidoSerializer(pedidos, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
def actualizar_estado_pedido(request, numero_pedido):
    """
    Actualiza el estado de un pedido
    Solo accesible para administradores
    """
    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)
    
    nuevo_estado = request.data.get('estado')
    if nuevo_estado not in ['pendiente', 'pagado', 'enviado', 'entregado', 'fallido']:
        return Response({"error": "Estado inválido"}, status=400)
    
    pedido.estado = nuevo_estado
    pedido.save()
    
    serializer = PedidoSerializer(pedido)
    return Response(serializer.data)

# ======================================
#  PAGO SIMULADO
# ======================================

@api_view(['POST'])
def iniciar_pago(request):
    print("📦 Datos recibidos:", request.data)
    
    numero_pedido = request.data.get("numero_pedido")
    nombre = request.data.get("nombre")
    email = request.data.get("email")
    direccion = request.data.get("direccion")
    total = request.data.get("total")

    print(f"✅ Nombre: {nombre}, Email: {email}, Dirección: {direccion}")

    if not numero_pedido or not total:
        return Response({"error": "Datos incompletos"}, status=400)

    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)

    # Actualizar información del pedido
    pedido.nombre = nombre if nombre else pedido.nombre
    pedido.email = email if email else pedido.email
    pedido.direccion = direccion if direccion else pedido.direccion
    pedido.estado = "pagado"
    
    # ← NUEVO: Descontar inventario automáticamente
    for item in pedido.carrito:
        try:
            producto = Producto.objects.get(id=item['id'])
            cantidad_comprada = item.get('cantidad', 1)
            
            # Verificar que hay suficiente stock
            if producto.stock >= cantidad_comprada:
                producto.stock -= cantidad_comprada
                producto.save()
                print(f"✅ Inventario actualizado: {producto.nombre} - Stock restante: {producto.stock}")
            else:
                print(f"⚠️ Stock insuficiente para {producto.nombre}: solicitado {cantidad_comprada}, disponible {producto.stock}")
        except Producto.DoesNotExist:
            print(f"❌ Producto {item['id']} no encontrado")
            continue
    
    pedido.save()

    print(f"💾 Pedido guardado - Email: {pedido.email}, Dirección: {pedido.direccion}")

    return Response({
        "mensaje": "Pago aprobado",
        "numero_pedido": pedido.numero_pedido,
        "nombre": pedido.nombre,
        "email": pedido.email,
        "direccion": pedido.direccion,
        "total": pedido.total,
        "carrito": pedido.carrito
    })

# ======================================
#  VERIFICAR PAGO
# ======================================

@api_view(['GET'])
def verificar_pago(request, numero_pedido):
    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no existe"}, status=404)

    return Response({
        "estado": pedido.estado
    })