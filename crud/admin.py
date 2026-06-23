from django.contrib import admin
from .models import User, Receita


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'name', 'login', 'email', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'login', 'email')
    list_editable = ('status',)


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('id_receita', 'nome', 'tipo_receita', 'custo', 'user', 'data_criacao')
    list_filter = ('tipo_receita', 'user')
    search_fields = ('nome', 'descricao', 'ingredientes')
    list_per_page = 20