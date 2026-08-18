from django.db import migrations


ROLES_BASE = [
    "Administrador institucional",
    "Coordinador",
    "Docente",
    "Alumno",
]


def crear_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")

    for nombre in ROLES_BASE:
        Group.objects.get_or_create(name=nombre)


def eliminar_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")

    Group.objects.filter(
        name__in=ROLES_BASE
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            crear_roles,
            eliminar_roles,
        ),
    ]