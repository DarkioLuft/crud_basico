# crud/views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from .models import Receita, User

# --- 1. MIXIN DE PROTEÇÃO MANUAL ---
class RequerLoginMixin:
    """Impede o acesso se o id do usuário não estiver na sessão"""
    def dispatch(self, request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

# --- 2. VIEWS DE AUTENTICAÇÃO MANUAIS ---
class LoginView(View):
    def get(self, request):
        # Se já estiver logado, manda pra lista
        if 'user_id' in request.session:
            return redirect('receita_list')
        return render(request, 'crud/login.html')

    def post(self, request):
        login_form = request.POST.get('login')
        senha_form = request.POST.get('senha')

        try:
            # Busca o usuário no banco
            user = User.objects.get(login=login_form, senha=senha_form, status=True)
            
            # Salva os dados na sessão (Isso é o que "loga" o usuário)
            request.session['user_id'] = user.id_user
            request.session['user_name'] = user.name
            return redirect('receita_list')
        except User.DoesNotExist:
            # Se errar a senha ou login não existir
            return render(request, 'crud/login.html', {'erro': 'Login ou senha inválidos.'})

def logout_view(request):
    request.session.flush() # Apaga a sessão inteira (Desloga)
    return redirect('login')


# --- 3. VIEWS DO CRUD DE RECEITAS ---
# Note que agora usamos o nosso RequerLoginMixin em vez do padrão do Django

class ReceitaListView(RequerLoginMixin, ListView):
    model = Receita
    template_name = 'crud/receita_list.html'
    context_object_name = 'receitas'
    success_url = reverse_lazy('receita_list')

class ReceitaDetailView(RequerLoginMixin, DetailView):
    model = Receita
    template_name = 'crud/receita_detail.html'

class ReceitaCreateView(RequerLoginMixin, CreateView):
    model = Receita
    template_name = 'crud/receita_form.html'
    fields = ['nome', 'descricao', 'ingredientes', 'custo', 'tipo_receita']
    success_url = reverse_lazy('receita_list')

class ReceitaUpdateView(RequerLoginMixin, UpdateView):
    model = Receita
    template_name = 'crud/receita_form.html'
    fields = ['nome', 'descricao', 'ingredientes', 'custo', 'tipo_receita']
    success_url = reverse_lazy('receita_list')

class ReceitaDeleteView(RequerLoginMixin, DeleteView):
    model = Receita
    template_name = 'crud/receita_confirm_delete.html'
    success_url = reverse_lazy('receita_list')
    