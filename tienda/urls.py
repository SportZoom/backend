from django.urls import path, include
from .views import ProductoList
from .views import AdminLoginView
#from .views import ProductoDetail
from .views import ProductoCreate
from .views import ProductoUpdate
from .views import ProductoDelete
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet
from .views import crear_pedido
from .views import iniciar_pago
from .views import verificar_pago
from .views import consultar_pedido
from .views import listar_pedidos, actualizar_estado_pedido

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = [
    path('', include(router.urls)),
    path('productos/', ProductoList.as_view(), name='productos-list'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('admin/productos/crear/', ProductoCreate.as_view(), name='producto-create'),
    path('admin/productos/<int:pk>/actualizar/', ProductoUpdate.as_view(), name='producto-update'),
    path('admin/productos/<int:pk>/eliminar/', ProductoDelete.as_view(), name='producto-delete'),
    path('checkout/crear-pedido/', crear_pedido, name='crear-pedido'),
    path('checkout/pago/', iniciar_pago, name='iniciar-pago'),
    path('checkout/verificar/<str:numero_pedido>/', verificar_pago, name='verificar-pago'),
    path('pedidos/consultar/<str:numero_pedido>/', consultar_pedido, name='consultar-pedido'),
    path('admin/pedidos/', listar_pedidos, name='listar-pedidos'),  # ← AGREGAR
    path('admin/pedidos/<str:numero_pedido>/estado/', actualizar_estado_pedido, name='actualizar-estado'),  # ← AGREGAR
]