from rest_framework import serializers
from .models import Producto
from django.contrib.auth import authenticate
from .models import Pedido
from django.contrib.auth.password_validation import validate_password
from .models import Cliente, Usuario
from .storage import upload_product_image

class ProductoSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(write_only=True, required=False, allow_null=True)
    imagen_url = serializers.SerializerMethodField(read_only=True)
    disponibilidad = serializers.SerializerMethodField(read_only=True)
    

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock', 'marca', 'talla', 'imagen', 'imagen_url', 'disponibilidad']  # Agregados marca y talla
        extra_kwargs = {
            'imagen': {'required': False, 'allow_null': True },
        }
        

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['imagen'] = instance.imagen
        return data

    def get_imagen_url(self, obj):
        return obj.imagen or None

    def get_disponibilidad(self, obj):
        return 'Disponible' if obj.stock > 0 else 'Agotado'

    def create(self, validated_data):
        uploaded_image = validated_data.pop('imagen', None)
        if uploaded_image:
            validated_data['imagen'] = upload_product_image(uploaded_image)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_image = validated_data.pop('imagen', None)
        if uploaded_image:
            validated_data['imagen'] = upload_product_image(uploaded_image)
        return super().update(instance, validated_data)

class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Usuario o contraseña incorrectos')
        if not user.es_admin:
            raise serializers.ValidationError('No tienes permisos de administrador')
        data['user'] = user
        return data
  
class PedidoSerializer(serializers.ModelSerializer):
    estado_actual = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ['numero_pedido', 'fecha', 'wompi_id']

    def get_estado_actual(self, obj):
        # Persiste el estado actualizado y lo devuelve
        return obj.actualizar_estado()


class ClienteRegistroSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    correo = serializers.EmailField()
    genero = serializers.ChoiceField(choices=['M', 'F', 'O', 'P'])
    password = serializers.CharField(write_only=True, validators=[validate_password])
    acepta_terminos = serializers.BooleanField()

    def validate_correo(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este correo ya está registrado.')
        return value

    def validate_acepta_terminos(self, value):
        if not value:
            raise serializers.ValidationError('Debes aceptar los términos y condiciones.')
        return value

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            username=validated_data['correo'],   
            email=validated_data['correo'],
            first_name=validated_data['nombre'],
            password=validated_data['password'],
            es_admin=False
        )
        Cliente.objects.create(
            usuario=user,
            genero=validated_data['genero'],
            acepta_terminos=validated_data['acepta_terminos']
        )
        return user


class ClienteLoginSerializer(serializers.Serializer):
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['correo'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Correo o contraseña incorrectos.')
        if user.es_admin:
            raise serializers.ValidationError('Usa el panel de administrador.')
        data['user'] = user
        return data

class PedidoClienteSerializer(serializers.ModelSerializer):
    cantidad_productos = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()
    estado_actual = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'numero_pedido', 'fecha', 'total',
            'estado', 'estado_actual', 'estado_display',
            'cantidad_productos', 'carrito'
        ]

    def get_cantidad_productos(self, obj):
        return sum(item.get('cantidad', 1) for item in obj.carrito)

    def get_estado_display(self, obj):
        return dict(Pedido.ESTADOS).get(obj.estado, obj.estado)

    def get_estado_actual(self, obj):
        return obj.actualizar_estado()
