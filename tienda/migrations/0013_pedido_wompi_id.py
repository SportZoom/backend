from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0012_alter_pedido_estado'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE tienda_pedido ADD COLUMN IF NOT EXISTS wompi_id varchar(100) NULL;",
            reverse_sql="ALTER TABLE tienda_pedido DROP COLUMN wompi_id;",
        ),
    ]
