"""
Migration 0003 – Vincula receitas ao usuário dono.

Estratégia de dados:
  1. Adiciona a coluna `user_id` como nullable.
  2. Preenche todas as linhas existentes com user_id = 1
     (conforme requisito: "a lista atual deve ser vinculada ao usuário 1").
  3. Torna a coluna NOT NULL e adiciona a FK constraint.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crud', '0002_user_email'),
    ]

    operations = [
        # Passo 1: coluna nullable
        migrations.AddField(
            model_name='receita',
            name='user',
            field=models.ForeignKey(
                to='crud.User',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='receitas',
                null=True,
            ),
        ),

        # Passo 2: popula dados existentes → user_id = 1
        migrations.RunSQL(
            sql="UPDATE crud_receita SET user_id = 1;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Passo 3: torna NOT NULL
        migrations.AlterField(
            model_name='receita',
            name='user',
            field=models.ForeignKey(
                to='crud.User',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='receitas',
            ),
        ),
    ]