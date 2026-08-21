from django.db import migrations


def migrar_membresias(apps, schema_editor):
    Usuario = apps.get_model(
        "usuarios",
        "Usuario",
    )

    MembresiaInstitucional = apps.get_model(
        "usuarios",
        "MembresiaInstitucional",
    )

    usuarios = (
        Usuario.objects
        .exclude(institucion_id=None)
        .prefetch_related("groups")
    )

    for usuario in usuarios:
        membresia, _ = (
            MembresiaInstitucional.objects.get_or_create(
                usuario_id=usuario.pk,
                institucion_id=usuario.institucion_id,
                defaults={
                    "activa": usuario.is_active,
                },
            )
        )

        roles = usuario.groups.all()

        if roles.exists():
            membresia.roles.set(roles)


def revertir_membresias(apps, schema_editor):
    MembresiaInstitucional = apps.get_model(
        "usuarios",
        "MembresiaInstitucional",
    )

    MembresiaInstitucional.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "usuarios",
            "0003_membresiainstitucional",
        ),
    ]

    operations = [
        migrations.RunPython(
            migrar_membresias,
            revertir_membresias,
        ),
    ]