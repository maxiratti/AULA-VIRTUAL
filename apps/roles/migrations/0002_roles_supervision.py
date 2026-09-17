from django.db import migrations

ROLES = ["Preceptor", "Observador institucional"]

def crear_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nombre in ROLES:
        Group.objects.get_or_create(name=nombre)

def eliminar_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=ROLES).delete()

class Migration(migrations.Migration):
    dependencies = [("roles", "0001_crear_roles_base")]
    operations = [migrations.RunPython(crear_roles, eliminar_roles)]
