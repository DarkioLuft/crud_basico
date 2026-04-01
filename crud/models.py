from django.db import models

class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    login = models.CharField(max_length=50, unique=True)
    senha = models.CharField(max_length=128)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Receita(models.Model):
    id_receita = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    ingredientes = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_receita = models.CharField(max_length=50)

    def __str__(self):
        return self.name

def get_absolute_url(self):
        return reverse('receita_list')