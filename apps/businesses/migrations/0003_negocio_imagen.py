from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0002_alter_negocio_zona'),
    ]

    operations = [
        migrations.AddField(
            model_name='negocio',
            name='imagen',
            field=models.ImageField(blank=True, null=True, upload_to='negocios/'),
        ),
    ]
