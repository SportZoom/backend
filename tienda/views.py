from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend  # NUEVO
from rest_framework import filters  # NUEVO
from .models import Producto, Pedido, Cliente, PagoMercadoPago
from .serializers import ProductoSerializer, AdminLoginSerializer, PedidoSerializer
from .permissions import IsAdminUserCustom
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import PedidoSerializer
from rest_framework.decorators import api_view
from django.conf import settings
from django.utils import timezone
import hashlib
import requests
import uuid
import mercadopago
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import ClienteRegistroSerializer, ClienteLoginSerializer, PedidoClienteSerializer



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
    

class ClienteRegistroView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClienteRegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'mensaje': 'Registro exitoso',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'nombre': user.first_name,
            'correo': user.email,
        }, status=status.HTTP_201_CREATED)


class ClienteLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClienteLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'nombre': user.first_name,
            'correo': user.email,
        }, status=status.HTTP_200_OK)
    
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

    # ← NUEVO: asociar cliente si está autenticado
    if request.user.is_authenticated:
        try:
            pedido.cliente = request.user.cliente
            pedido.save()
        except Exception:
            pass  # Si no tiene perfil cliente, el pedido igual se crea
    
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
    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)
    
    nuevo_estado = request.data.get('estado')
    estados_validos = [choice[0] for choice in Pedido.ESTADOS]
    
    if nuevo_estado not in estados_validos:
        return Response({
            "error": f"Estado inválido. Estados válidos: {estados_validos}"
        }, status=400)
    
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
    pedido.estado = "comprado"
    
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
        "estado": pedido.actualizar_estado()
    })


# Vista: listar pedidos del cliente autenticado
class MisPedidosView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'No tienes un perfil de cliente.'}, status=403)

        pedidos = cliente.pedidos.all().order_by('-fecha')
        serializer = PedidoClienteSerializer(pedidos, many=True)
        return Response(serializer.data)

def get_mp_sdk():
    return mercadopago.SDK(settings.MP_ACCESS_TOKEN)


def descontar_stock_pedido(pedido):
    for item in pedido.carrito:
        try:
            producto = Producto.objects.get(id=item['id'])
            cantidad = int(item.get('cantidad', 1))
            if producto.stock >= cantidad:
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])
        except Producto.DoesNotExist:
            pass


def aprobar_pago_pedido_debug(numero_pedido):
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(numero_pedido=numero_pedido)
        referencia = f"DEMO-{pedido.numero_pedido}-{uuid.uuid4().hex[:10].upper()}"

        pago, creado = PagoMercadoPago.objects.select_for_update().get_or_create(
            pedido=pedido,
            defaults={
                'monto': pedido.total,
                'preference_id': referencia,
                'payment_id': referencia,
                'estado': 'approved',
            }
        )

        ya_estaba_aprobado = not creado and pago.estado == 'approved'
        pago.preference_id = pago.preference_id or referencia
        pago.payment_id = pago.payment_id or referencia
        pago.estado = 'approved'
        pago.monto = pedido.total
        pago.save()

        if not ya_estaba_aprobado:
            descontar_stock_pedido(pedido)

        pedido.estado = 'comprado'
        pedido.wompi_id = pago.payment_id
        pedido.referencia_pago = pago.preference_id
        pedido.save(update_fields=['estado', 'wompi_id', 'referencia_pago'])

    return pedido, pago


@api_view(['POST'])
def aprobar_pago_demo(request, numero_pedido):
    # if not settings.DEBUG:
    #     return Response({'error': 'Endpoint no disponible'}, status=404)

    try:
        pedido, pago = aprobar_pago_pedido_debug(numero_pedido)
        return Response({
            'mensaje': 'Pago aprobado',
            'numero_pedido': pedido.numero_pedido,
            'estado_pedido': pedido.estado,
            'estado_pago': pago.estado,
            'referencia_pago': pedido.referencia_pago,
            'payment_id': pago.payment_id,
        })
    except Pedido.DoesNotExist:
        return Response({'error': 'Pedido no encontrado'}, status=404)

@api_view(['POST'])
def crear_preferencia_mp(request):
    try:
        numero_pedido = request.data.get('numero_pedido')
        print(f"🔍 Buscando pedido: {numero_pedido}")

        try:
            pedido = Pedido.objects.get(numero_pedido=numero_pedido)
        except Pedido.DoesNotExist:
            return Response({'error': 'Pedido no encontrado'}, status=404)

        print(f"✅ Pedido encontrado: {pedido}")
        print(f"🛒 Carrito: {pedido.carrito}")

        sdk = get_mp_sdk()

        items = []
        for item in pedido.carrito:
            print(f"📦 Procesando item: {item}")
            items.append({
                "id": str(item.get('id')),
                "title": str(item.get('nombre', 'Producto')),
                "quantity": int(item.get('cantidad', 1)),
                "unit_price": float(item.get('precio', 0)),
                "currency_id": "COP",
            })

        print(f"📋 Items construidos: {items}")

        preference_data = {
            "items": items,
            "payer": {
                "email": pedido.email or "test@test.com",
                "name": pedido.nombre or "Cliente",
            },
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/confirmacion",
                "failure": f"{settings.FRONTEND_URL}/confirmacion",
                "pending": f"{settings.FRONTEND_URL}/confirmacion",
            },
            "external_reference": pedido.numero_pedido,
            "statement_descriptor": "SPORTZOOM",
        }

        print(f"📤 Enviando a MP: {preference_data}")

        result = sdk.preference().create(preference_data)
        print(f"📥 Respuesta MP status: {result['status']}")
        print(f"📥 Respuesta MP response: {result['response']}")

        preference = result["response"]

        if result["status"] != 201:
            return Response({'error': 'Error creando preferencia', 'detalle': preference}, status=500)

        from .models import PagoMercadoPago
        PagoMercadoPago.objects.update_or_create(
            pedido=pedido,
            defaults={
                'preference_id': preference['id'],
                'monto': pedido.total,
            }
        )
        pedido.referencia_pago = preference['id']
        pedido.save()

        return Response({
            'preference_id': preference['id'],
            'sandbox_init_point': preference['sandbox_init_point'],
            'init_point': preference['init_point'],
        })

    except Exception as e:
        import traceback
        print(f"❌ ERROR COMPLETO: {str(e)}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@csrf_exempt
def webhook_mp(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    topic = data.get('type') or request.GET.get('topic')

    if topic == 'payment':
        payment_id = (data.get('data') or {}).get('id') or request.GET.get('id')

        sdk = get_mp_sdk()
        payment_info = sdk.payment().get(payment_id)
        payment = payment_info["response"]

        numero_pedido = payment.get('external_reference')
        estado_mp = payment.get('status')  # approved, rejected, pending

        try:
            pedido = Pedido.objects.get(numero_pedido=numero_pedido)
            from .models import PagoMercadoPago
            pago, _ = PagoMercadoPago.objects.get_or_create(
                pedido=pedido,
                defaults={'monto': pedido.total}
            )
            pago.payment_id = str(payment_id)
            pago.estado = estado_mp
            pago.save()

            # Si el pago fue aprobado, descontar inventario
            if estado_mp == 'approved' and pedido.estado == 'comprado':
                for item in pedido.carrito:
                    try:
                        producto = Producto.objects.get(id=item['id'])
                        cantidad = int(item.get('cantidad', 1))
                        if producto.stock >= cantidad:
                            producto.stock -= cantidad
                            producto.save()
                    except Producto.DoesNotExist:
                        pass

                pedido.wompi_id = str(payment_id)
                pedido.save()

        except Pedido.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok'})


@api_view(['GET'])
def estado_pago_mp(request, numero_pedido):
    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
        from .models import PagoMercadoPago
        pago = PagoMercadoPago.objects.get(pedido=pedido)
        return Response({
            'estado': pago.estado,
            'payment_id': pago.payment_id,
            'monto': str(pago.monto),
        })
    except (Pedido.DoesNotExist, PagoMercadoPago.DoesNotExist):
        return Response({'estado': 'pending', 'payment_id': '', 'monto': '0'})


# ======================================
#  WOMPI INTEGRATION
# ======================================

def generar_firma_integridad(reference, amount_in_cents, currency):
    """Genera firma SHA256 para Wompi según documentación.
    Concatena: reference + amount_in_cents + currency + integrity_secret"""
    integrity_secret = settings.WOMPI_INTEGRITY_SECRET
    cadena = f"{reference}{amount_in_cents}{currency}{integrity_secret}"
    return hashlib.sha256(cadena.encode('utf-8')).hexdigest()


@api_view(['POST'])
def wompi_init_payment(request):
    """Genera los parámetros necesarios para abrir el Widget de Wompi.
    La firma de integridad se genera exclusivamente en el backend."""
    numero_pedido = request.data.get('numero_pedido')
    if not numero_pedido:
        return Response({"error": "numero_pedido es requerido"}, status=400)

    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)

    # Generar referencia única para Wompi
    reference = f"PEDIDO-{pedido.numero_pedido}-{int(timezone.now().timestamp())}"

    # Calcular monto en centavos (COP, sin decimales)
    amount_in_cents = int(float(pedido.total) * 100)

    currency = "COP"

    # Generar firma de integridad en el servidor
    signature_integrity = generar_firma_integridad(reference, amount_in_cents, currency)

    # Guardar la referencia en el pedido para trazabilidad
    pedido.referencia_pago = reference
    pedido.save(update_fields=['referencia_pago'])

    return Response({
        "currency": currency,
        "amount_in_cents": amount_in_cents,
        "reference": reference,
        "public_key": settings.WOMPI_PUBLIC_KEY,
        "signature_integrity": signature_integrity,
        "redirect_url": f"{settings.FRONTEND_URL}/confirmacion",
    })


@csrf_exempt
def wompi_webhook(request):
    """Recibe eventos de Wompi (transaction.updated).
    Verifica la firma del evento antes de procesarlo."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    event = data.get('event')
    environment = data.get('environment', 'test')

    # Solo procesar eventos de transacciones
    if event != 'transaction.updated':
        return JsonResponse({'status': 'ignored'})

    # --- Verificación de firma del evento (seguridad) ---
    signature = data.get('signature', {})
    properties = signature.get('properties', [])
    checksum_recibido = signature.get('checksum', '')
    timestamp = data.get('timestamp', '')

    if properties and checksum_recibido:
        # Construir cadena para verificar: valores de properties + timestamp + events_secret
        transaction = data.get('data', {}).get('transaction', {})
        valores = []
        for prop in properties:
            partes = prop.split('.')
            valor = transaction
            try:
                for parte in partes:
                    valor = valor[parte]
            except (KeyError, TypeError):
                valor = ''
            valores.append(str(valor) if valor is not None else '')

        cadena_verificacion = ''.join(valores) + str(timestamp) + settings.WOMPI_EVENTS_SECRET
        checksum_calculado = hashlib.sha256(cadena_verificacion.encode('utf-8')).hexdigest().upper()

        if checksum_calculado != checksum_recibido.upper():
            return JsonResponse({'error': 'Firma inválida'}, status=403)

    # --- Procesar la transacción ---
    transaction = data.get('data', {}).get('transaction', {})
    transaccion_id = transaction.get('id', '')
    reference = transaction.get('reference', '')
    status = transaction.get('status', '').lower()
    amount_in_cents = transaction.get('amount_in_cents')
    customer_email = transaction.get('customer_email', '')
    payment_method_type = transaction.get('payment_method_type', '')

    if not reference:
        return JsonResponse({'error': 'Referencia no encontrada en el evento'}, status=400)

    # Buscar pedido por referencia de pago
    try:
        pedido = Pedido.objects.get(referencia_pago=reference)
    except Pedido.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado para esta referencia'}, status=404)

    with transaction.atomic():
        pago, creado = PagoMercadoPago.objects.select_for_update().get_or_create(
            pedido=pedido,
            defaults={
                'monto': pedido.total,
                'payment_id': transaccion_id,
                'estado': status,
            }
        )

        if not creado:
            pago.payment_id = transaccion_id or pago.payment_id
            pago.estado = status
            pago.monto = pedido.total
            pago.save()

        pedido.wompi_id = transaccion_id or pedido.wompi_id

        if status == 'approved':
            # Solo descontar stock y cambiar estado si no se ha hecho antes
            if not creado and pago.estado == 'approved':
                pass  # Ya estaba aprobado, no repetir
            else:
                descontar_stock_pedido(pedido)
                pedido.estado = 'comprado'

        pedido.save(update_fields=['estado', 'wompi_id'])

    return JsonResponse({'status': 'ok'})


@api_view(['GET'])
def wompi_estado_pago(request, numero_pedido):
    """Retorna el estado del pago Wompi para un pedido.
    Útil para que el frontend verifique el estado después del webhook."""
    try:
        pedido = Pedido.objects.get(numero_pedido=numero_pedido)
    except Pedido.DoesNotExist:
        return Response({'error': 'Pedido no encontrado'}, status=404)

    try:
        pago = PagoMercadoPago.objects.get(pedido=pedido)
        return Response({
            'estado': pago.estado,
            'payment_id': pago.payment_id,
            'monto': str(pago.monto),
            'pedido_estado': pedido.estado,
        })
    except PagoMercadoPago.DoesNotExist:
        return Response({
            'estado': 'pending',
            'payment_id': '',
            'monto': str(pedido.total),
            'pedido_estado': pedido.estado,
        })
