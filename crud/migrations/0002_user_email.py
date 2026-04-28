from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crud', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, default='placeholder@change.me'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='receita',
            name='tipo_receita',
            field=models.CharField(
                max_length=50,
                choices=[('Doce', 'Doce'), ('Salgado', 'Salgado')]
            ),
        ),
    ]