from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from .models import Pedido, Producto, Usuario, Cliente


# ============================================================
#  HELPERS
# ============================================================

def crear_pedido_con_fecha(dias_atras=0, estado="comprado"):
    """Crea un pedido y ajusta su fecha de creación manualmente."""
    pedido = Pedido.objects.create(
        total=100.00,
        carrito=[{"id": 1, "nombre": "Tenis", "cantidad": 1, "precio": 100}],
        estado=estado,
    )
    # auto_now_add no se puede sobreescribir en create, se usa update
    Pedido.objects.filter(pk=pedido.pk).update(
        fecha=timezone.now() - timedelta(days=dias_atras)
    )
    return Pedido.objects.get(pk=pedido.pk)


# ============================================================
#  TESTS: lógica de estado_calculado() en el modelo
# ============================================================

class EstadoCalculadoModelTest(TestCase):

    def test_estado_comprado_mismo_dia(self):
        pedido = crear_pedido_con_fecha(dias_atras=0)
        self.assertEqual(pedido.estado_calculado(), "comprado")

    def test_estado_enviado_al_dia_siguiente(self):
        pedido = crear_pedido_con_fecha(dias_atras=1)
        self.assertEqual(pedido.estado_calculado(), "enviado")

    def test_estado_en_reparto_dos_dias(self):
        pedido = crear_pedido_con_fecha(dias_atras=2)
        self.assertEqual(pedido.estado_calculado(), "en_reparto")

    def test_estado_entregado_tres_dias(self):
        pedido = crear_pedido_con_fecha(dias_atras=3)
        self.assertEqual(pedido.estado_calculado(), "entregado")

    def test_estado_entregado_mas_de_tres_dias(self):
        pedido = crear_pedido_con_fecha(dias_atras=10)
        self.assertEqual(pedido.estado_calculado(), "entregado")


# ============================================================
#  TESTS: actualizar_estado() persiste en BD
# ============================================================

class ActualizarEstadoModelTest(TestCase):

    def test_actualizar_estado_persiste_en_bd(self):
        """Si el estado calculado difiere del guardado, debe actualizarse en BD."""
        pedido = crear_pedido_con_fecha(dias_atras=2, estado="comprado")

        estado_retornado = pedido.actualizar_estado()

        pedido_en_bd = Pedido.objects.get(pk=pedido.pk)
        self.assertEqual(estado_retornado, "en_reparto")
        self.assertEqual(pedido_en_bd.estado, "en_reparto")

    def test_actualizar_estado_no_hace_save_innecesario(self):
        """Si el estado ya es correcto, no debe hacer ningún cambio."""
        pedido = crear_pedido_con_fecha(dias_atras=1, estado="enviado")

        with self.assertNumQueries(0):
            # estado_calculado() no toca la BD
            resultado = pedido.estado_calculado()

        self.assertEqual(resultado, "enviado")

    def test_actualizar_estado_retorna_estado_correcto(self):
        pedido = crear_pedido_con_fecha(dias_atras=3, estado="comprado")
        self.assertEqual(pedido.actualizar_estado(), "entregado")


# ============================================================
#  TESTS: endpoint consultar_pedido actualiza el estado
# ============================================================

class ConsultarPedidoAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_consultar_pedido_retorna_estado_actual(self):
        pedido = crear_pedido_con_fecha(dias_atras=2, estado="comprado")
        url = f"/api/pedidos/consultar/{pedido.numero_pedido}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado_actual"], "en_reparto")

    def test_consultar_pedido_sincroniza_estado_en_bd(self):
        """Al consultar, el campo estado en BD debe quedar actualizado."""
        pedido = crear_pedido_con_fecha(dias_atras=3, estado="comprado")
        url = f"/api/pedidos/consultar/{pedido.numero_pedido}/"

        self.client.get(url)

        pedido_actualizado = Pedido.objects.get(pk=pedido.pk)
        self.assertEqual(pedido_actualizado.estado, "entregado")

    def test_consultar_pedido_inexistente_retorna_404(self):
        response = self.client.get("/api/pedidos/consultar/NOEXISTE/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
#  TESTS: endpoint verificar_pago también actualiza el estado
# ============================================================

class VerificarPagoAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_verificar_pago_retorna_estado_calculado(self):
        pedido = crear_pedido_con_fecha(dias_atras=1, estado="comprado")
        url = f"/api/checkout/verificar/{pedido.numero_pedido}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "enviado")


# ============================================================
#  TESTS: transición completa de estados día a día
# ============================================================

class TransicionCompletaTest(TestCase):

    def test_ciclo_completo_de_estados(self):
        """Verifica que cada día corresponde al estado correcto."""
        casos = [
            (0, "comprado"),
            (1, "enviado"),
            (2, "en_reparto"),
            (3, "entregado"),
            (5, "entregado"),
        ]
        for dias, estado_esperado in casos:
            with self.subTest(dias=dias):
                pedido = crear_pedido_con_fecha(dias_atras=dias)
                self.assertEqual(
                    pedido.estado_calculado(),
                    estado_esperado,
                    msg=f"Con {dias} días debería ser '{estado_esperado}'"
                )
