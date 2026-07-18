import django.db.models.deletion
import django.db.models.manager
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0001_initial'),
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('activo', models.BooleanField(default=True)),
                ('eliminado_en', models.DateTimeField(blank=True, null=True)),
                ('nombre', models.CharField(max_length=50)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_creados', to=settings.AUTH_USER_MODEL)),
                ('negocio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorias_producto', to='businesses.negocio')),
            ],
            options={
                'verbose_name': 'Categoría de producto',
                'verbose_name_plural': 'Categorías de producto',
                'ordering': ['nombre'],
                'constraints': [models.UniqueConstraint(condition=models.Q(('activo', True)), fields=('negocio', 'nombre'), name='unique_categoria_por_negocio')],
            },
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('todos', django.db.models.manager.Manager()),
            ],
        ),
    ]
