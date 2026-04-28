# crud/views.py
import re
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
        if 'user_id' in request.session:
            return redirect('receita_list')
        return render(request, 'crud/login.html')

    def post(self, request):
        login_form = request.POST.get('login')
        senha_form = request.POST.get('senha')

        try:
            user = User.objects.get(login=login_form, senha=senha_form, status=True)
            request.session['user_id'] = user.id_user
            request.session['user_name'] = user.name
            return redirect('receita_list')
        except User.DoesNotExist:
            return render(request, 'crud/login.html', {'erro': 'Login ou senha inválidos.'})


class RegisterView(View):
    def get(self, request):
        if 'user_id' in request.session:
            return redirect('receita_list')
        return render(request, 'crud/register.html')

    def post(self, request):
        name = request.POST.get('name', '').strip()
        login = request.POST.get('login', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '').strip()
        senha_confirm = request.POST.get('senha_confirm', '').strip()

        erros = []

        # Validações
        if not name:
            erros.append('O nome é obrigatório.')
        if not login:
            erros.append('O login é obrigatório.')
        if not email:
            erros.append('O e-mail é obrigatório.')
        elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            erros.append('Informe um e-mail válido.')
        if not senha:
            erros.append('A senha é obrigatória.')
        elif len(senha) < 6:
            erros.append('A senha deve ter pelo menos 6 caracteres.')
        if senha != senha_confirm:
            erros.append('As senhas não coincidem.')

        if not erros:
            if User.objects.filter(login=login).exists():
                erros.append('Este login já está em uso.')
            if email and User.objects.filter(email=email).exists():
                erros.append('Este e-mail já está cadastrado.')

        if erros:
            return render(request, 'crud/register.html', {
                'erros': erros,
                'name': name,
                'login': login,
                'email': email,
            })

        User.objects.create(name=name, login=login, email=email, senha=senha)
        return render(request, 'crud/login.html', {
            'sucesso': 'Cadastro realizado com sucesso! Faça login para continuar.'
        })


def logout_view(request):
    request.session.flush()
    return redirect('login')


# --- 3. VIEWS DO CRUD DE RECEITAS ---
class ReceitaListView(RequerLoginMixin, ListView):
    model = Receita
    template_name = 'crud/receita_list.html'
    context_object_name = 'receitas'

    def get_queryset(self):
        qs = Receita.objects.all().order_by('nome')
        tipo = self.request.GET.get('tipo', '')
        min_custo = self.request.GET.get('min_custo', '')
        max_custo = self.request.GET.get('max_custo', '')

        if tipo in ['Doce', 'Salgado']:
            qs = qs.filter(tipo_receita=tipo)
        if min_custo:
            try:
                qs = qs.filter(custo__gte=float(min_custo))
            except ValueError:
                pass
        if max_custo:
            try:
                qs = qs.filter(custo__lte=float(max_custo))
            except ValueError:
                pass
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_filtro'] = self.request.GET.get('tipo', '')
        context['min_custo'] = self.request.GET.get('min_custo', '')
        context['max_custo'] = self.request.GET.get('max_custo', '')
        return context


class ReceitaDetailView(RequerLoginMixin, DetailView):
    model = Receita
    template_name = 'crud/receita_detail.html'
    context_object_name = 'receita'


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
    context_object_name = 'receita'
    success_url = reverse_lazy('receita_list')