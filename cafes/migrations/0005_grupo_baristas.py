from django.db import migrations


def crear_grupo_baristas(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    grupo, _ = Group.objects.get_or_create(name='Baristas')
    codenames = [
        'add_receta',
        'change_receta',
        'delete_receta',
        'view_receta',
        'publicar_receta',
    ]
    permisos = Permission.objects.filter(
        content_type__app_label='cafes',
        codename__in=codenames,
    )
    grupo.permissions.add(*permisos)


def borrar_grupo_baristas(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Baristas').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cafes', '0004_alter_receta_options_receta_actualizado_en_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(crear_grupo_baristas, borrar_grupo_baristas),
    ]
