from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("cursos", "0005_mensajecurso_leido_por_alumno_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name="curso",
            name="preceptores",
            field=models.ManyToManyField(
                blank=True,
                related_name="cursos_como_preceptor",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
