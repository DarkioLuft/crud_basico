from django.db import models
from django.urls import reverse


class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    login = models.CharField(max_length=50, unique=True)
    senha = models.CharField(max_length=128)
    email = models.EmailField(max_length=254, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Receita(models.Model):
    TIPO_CHOICES = [
        ('Doce', 'Doce'),
        ('Salgado', 'Salgado'),
    ]

    id_receita = models.AutoField(primary_key=True)
    # Vínculo ao dono da receita. Receitas pré-existentes migram para user_id=1.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='receitas',
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    ingredientes = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_receita = models.CharField(max_length=50, choices=TIPO_CHOICES)

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('receita_list')