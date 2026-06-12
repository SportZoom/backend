from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0013_pedido_wompi_id'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE tienda_pedido ADD COLUMN IF NOT EXISTS referencia_pago varchar(150) NULL;",
            reverse_sql="ALTER TABLE tienda_pedido DROP COLUMN referencia_pago;",
        ),
    ]
