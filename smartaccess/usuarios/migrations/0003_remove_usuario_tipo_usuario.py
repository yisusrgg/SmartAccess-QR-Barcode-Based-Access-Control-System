# Generated migration to remove tipo_usuario field that exists in database but not in model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_remove_usuario_correo'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE usuarios_usuario DROP COLUMN tipo_usuario;",
            reverse_sql="ALTER TABLE usuarios_usuario ADD COLUMN tipo_usuario VARCHAR(50) NULL;",
        ),
    ]
