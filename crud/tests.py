"""
Testes unitários para o sistema de Gestão de Receitas.
Cobertura: modelos, autenticação, cadastro de usuário, CRUD de receitas e filtros.

Execute com:
    python manage.py test crud
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Receita


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def criar_usuario(**kwargs):
    defaults = dict(
        name='Teste User', login='testuser',
        email='test@example.com', senha='senha123', status=True,
    )
    defaults.update(kwargs)
    return User.objects.create(**defaults)


def criar_receita(**kwargs):
    defaults = dict(
        nome='Bolo de Chocolate', descricao='Delicioso bolo',
        ingredientes='Farinha, ovos, chocolate',
        custo=Decimal('25.50'), tipo_receita='Doce',
    )
    defaults.update(kwargs)
    return Receita.objects.create(**defaults)


def sessao_logada(client, user):
    """Simula login via sessão sem passar pela view de login."""
    session = client.session
    session['user_id'] = user.id_user
    session['user_name'] = user.name
    session.save()


# ─────────────────────────────────────────────
# 1. Testes de Modelo – User
# ─────────────────────────────────────────────

class UserModelTest(TestCase):

    def test_criacao_usuario_basico(self):
        """Deve criar um usuário com todos os campos obrigatórios."""
        user = criar_usuario()
        self.assertEqual(user.name, 'Teste User')
        self.assertEqual(user.login, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.status)

    def test_str_retorna_nome(self):
        """__str__ deve retornar o nome do usuário."""
        user = criar_usuario()
        self.assertEqual(str(user), 'Teste User')

    def test_login_unico(self):
        """Dois usuários não podem ter o mesmo login."""
        criar_usuario()
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create(
                name='Outro', login='testuser',
                email='outro@example.com', senha='abc123',
            )

    def test_email_unico(self):
        """Dois usuários não podem ter o mesmo e-mail."""
        criar_usuario()
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create(
                name='Outro', login='outro_login',
                email='test@example.com', senha='abc123',
            )

    def test_status_padrao_true(self):
        """Status padrão de um novo usuário deve ser True."""
        user = User.objects.create(
            name='X', login='xlogin',
            email='x@x.com', senha='abc123',
        )
        self.assertTrue(user.status)


# ─────────────────────────────────────────────
# 2. Testes de Modelo – Receita
# ─────────────────────────────────────────────

class ReceitaModelTest(TestCase):

    def test_criacao_receita(self):
        """Deve criar uma receita com todos os campos."""
        receita = criar_receita()
        self.assertEqual(receita.nome, 'Bolo de Chocolate')
        self.assertEqual(receita.tipo_receita, 'Doce')
        self.assertEqual(receita.custo, Decimal('25.50'))

    def test_str_retorna_nome(self):
        """__str__ da receita deve retornar o nome."""
        receita = criar_receita(nome='Coxinha')
        self.assertEqual(str(receita), 'Coxinha')

    def test_data_criacao_automatica(self):
        """data_criacao deve ser preenchida automaticamente."""
        receita = criar_receita()
        self.assertIsNotNone(receita.data_criacao)

    def test_get_absolute_url(self):
        """get_absolute_url deve apontar para receita_list."""
        receita = criar_receita()
        self.assertEqual(receita.get_absolute_url(), reverse('receita_list'))


# ─────────────────────────────────────────────
# 3. Testes de Autenticação – Login
# ─────────────────────────────────────────────

class LoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()
        self.url = reverse('login')

    def test_get_exibe_formulario(self):
        """GET /login/ deve retornar 200."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Acesso ao Sistema')

    def test_login_valido_redireciona(self):
        """Login com credenciais corretas deve redirecionar para receita_list."""
        resp = self.client.post(self.url, {'login': 'testuser', 'senha': 'senha123'})
        self.assertRedirects(resp, reverse('receita_list'))

    def test_login_salva_sessao(self):
        """Após login válido, user_id deve estar na sessão."""
        self.client.post(self.url, {'login': 'testuser', 'senha': 'senha123'})
        self.assertIn('user_id', self.client.session)
        self.assertEqual(self.client.session['user_id'], self.user.id_user)

    def test_login_senha_errada(self):
        """Senha incorreta deve retornar 200 com mensagem de erro."""
        resp = self.client.post(self.url, {'login': 'testuser', 'senha': 'errada'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'inválidos')

    def test_login_usuario_inexistente(self):
        """Login inexistente deve retornar mensagem de erro."""
        resp = self.client.post(self.url, {'login': 'naoexiste', 'senha': 'qualquer'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'inválidos')

    def test_usuario_ja_logado_redireciona(self):
        """Usuário já logado ao acessar /login/ deve ir para receita_list."""
        sessao_logada(self.client, self.user)
        resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse('receita_list'))

    def test_login_usuario_inativo(self):
        """Usuário com status=False não deve conseguir logar."""
        self.user.status = False
        self.user.save()
        resp = self.client.post(self.url, {'login': 'testuser', 'senha': 'senha123'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'inválidos')


# ─────────────────────────────────────────────
# 4. Testes de Autenticação – Logout
# ─────────────────────────────────────────────

class LogoutViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()

    def test_logout_limpa_sessao(self):
        """Após logout, user_id não deve existir na sessão."""
        sessao_logada(self.client, self.user)
        self.client.post(reverse('logout'))
        self.assertNotIn('user_id', self.client.session)

    def test_logout_redireciona_para_login(self):
        """Logout deve redirecionar para /login/."""
        sessao_logada(self.client, self.user)
        resp = self.client.post(reverse('logout'))
        self.assertRedirects(resp, reverse('login'))


# ─────────────────────────────────────────────
# 5. Testes de Cadastro – Register
# ─────────────────────────────────────────────

class RegisterViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')
        self.dados_validos = {
            'name': 'Novo Usuário',
            'login': 'novologin',
            'email': 'novo@email.com',
            'senha': 'senha123',
            'senha_confirm': 'senha123',
        }

    def test_get_exibe_formulario(self):
        """GET /register/ deve retornar 200."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_cadastro_valido_cria_usuario(self):
        """Cadastro válido deve criar um User no banco."""
        self.client.post(self.url, self.dados_validos)
        self.assertTrue(User.objects.filter(login='novologin').exists())

    def test_cadastro_valido_redireciona_login(self):
        """Cadastro válido deve exibir tela de login com mensagem de sucesso."""
        resp = self.client.post(self.url, self.dados_validos)
        self.assertContains(resp, 'sucesso')

    def test_cadastro_login_duplicado(self):
        """Login já existente deve retornar erro."""
        criar_usuario(login='novologin', email='x@x.com')
        resp = self.client.post(self.url, self.dados_validos)
        self.assertContains(resp, 'login já está em uso')

    def test_cadastro_email_duplicado(self):
        """E-mail já existente deve retornar erro."""
        criar_usuario(login='outrologin', email='novo@email.com')
        resp = self.client.post(self.url, self.dados_validos)
        self.assertContains(resp, 'e-mail já está cadastrado')

    def test_cadastro_senhas_diferentes(self):
        """Senhas que não coincidem devem retornar erro."""
        dados = {**self.dados_validos, 'senha_confirm': 'diferente'}
        resp = self.client.post(self.url, dados)
        self.assertContains(resp, 'senhas não coincidem')

    def test_cadastro_email_invalido(self):
        """E-mail sem @ deve retornar erro de validação."""
        dados = {**self.dados_validos, 'email': 'emailsemarroba'}
        resp = self.client.post(self.url, dados)
        self.assertContains(resp, 'e-mail válido')

    def test_cadastro_senha_curta(self):
        """Senha com menos de 6 caracteres deve retornar erro."""
        dados = {**self.dados_validos, 'senha': '123', 'senha_confirm': '123'}
        resp = self.client.post(self.url, dados)
        self.assertContains(resp, '6 caracteres')

    def test_cadastro_campos_obrigatorios(self):
        """Envio de formulário vazio deve retornar erros obrigatórios."""
        resp = self.client.post(self.url, {})
        self.assertContains(resp, 'obrigatório')


# ─────────────────────────────────────────────
# 6. Testes de Proteção de Rotas
# ─────────────────────────────────────────────

class ProtecaoRotasTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_lista_redireciona_sem_login(self):
        """Acessar lista sem estar logado redireciona para /login/."""
        resp = self.client.get(reverse('receita_list'))
        self.assertRedirects(resp, reverse('login'))

    def test_detalhe_redireciona_sem_login(self):
        """Acessar detalhe sem login redireciona."""
        receita = criar_receita()
        resp = self.client.get(reverse('receita_detail', args=[receita.pk]))
        self.assertRedirects(resp, reverse('login'))

    def test_criar_redireciona_sem_login(self):
        """Acessar criação sem login redireciona."""
        resp = self.client.get(reverse('receita_create'))
        self.assertRedirects(resp, reverse('login'))


# ─────────────────────────────────────────────
# 7. Testes de CRUD – Receitas
# ─────────────────────────────────────────────

class ReceitaCRUDTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()
        sessao_logada(self.client, self.user)

    def test_lista_acessivel_logado(self):
        """Lista de receitas deve retornar 200 quando logado."""
        resp = self.client.get(reverse('receita_list'))
        self.assertEqual(resp.status_code, 200)

    def test_lista_exibe_receitas(self):
        """Receitas cadastradas devem aparecer na listagem."""
        criar_receita(nome='Quiche Lorraine')
        resp = self.client.get(reverse('receita_list'))
        self.assertContains(resp, 'Quiche Lorraine')

    def test_detalhe_exibe_campos(self):
        """Página de detalhe deve exibir nome e ingredientes."""
        receita = criar_receita(nome='Torta Salgada', ingredientes='Frango, requeijão')
        resp = self.client.get(reverse('receita_detail', args=[receita.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Torta Salgada')
        self.assertContains(resp, 'Frango, requeijão')

    def test_criar_receita_post(self):
        """POST válido em receita/nova/ deve criar receita e redirecionar."""
        resp = self.client.post(reverse('receita_create'), {
            'nome': 'Brigadeiro', 'descricao': 'Doce tradicional',
            'ingredientes': 'Leite condensado, chocolate', 'custo': '5.00',
            'tipo_receita': 'Doce',
        })
        self.assertRedirects(resp, reverse('receita_list'))
        self.assertTrue(Receita.objects.filter(nome='Brigadeiro').exists())

    def test_editar_receita(self):
        """PUT em receita/<pk>/editar/ deve atualizar o nome."""
        receita = criar_receita(nome='Original')
        resp = self.client.post(reverse('receita_update', args=[receita.pk]), {
            'nome': 'Atualizado', 'descricao': 'Desc',
            'ingredientes': 'Ing', 'custo': '10.00',
            'tipo_receita': 'Salgado',
        })
        self.assertRedirects(resp, reverse('receita_list'))
        receita.refresh_from_db()
        self.assertEqual(receita.nome, 'Atualizado')

    def test_deletar_receita(self):
        """POST em receita/<pk>/deletar/ deve remover a receita do banco."""
        receita = criar_receita()
        pk = receita.pk
        self.client.post(reverse('receita_delete', args=[pk]))
        self.assertFalse(Receita.objects.filter(pk=pk).exists())


# ─────────────────────────────────────────────
# 8. Testes de Filtros
# ─────────────────────────────────────────────

class FiltroReceitaTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()
        sessao_logada(self.client, self.user)

        self.doce1 = criar_receita(nome='Bolo', tipo_receita='Doce',  custo=Decimal('30.00'))
        self.doce2 = criar_receita(nome='Pudim', tipo_receita='Doce', custo=Decimal('15.00'))
        self.salg1 = criar_receita(nome='Coxinha', tipo_receita='Salgado', custo=Decimal('8.00'))
        self.salg2 = criar_receita(nome='Quiche',  tipo_receita='Salgado', custo=Decimal('50.00'))
        self.url   = reverse('receita_list')

    def test_filtro_tipo_doce(self):
        """Filtrar por Doce deve retornar apenas receitas doces."""
        resp = self.client.get(self.url, {'tipo': 'Doce'})
        self.assertContains(resp, 'Bolo')
        self.assertContains(resp, 'Pudim')
        self.assertNotContains(resp, 'Coxinha')
        self.assertNotContains(resp, 'Quiche')

    def test_filtro_tipo_salgado(self):
        """Filtrar por Salgado deve retornar apenas receitas salgadas."""
        resp = self.client.get(self.url, {'tipo': 'Salgado'})
        self.assertContains(resp, 'Coxinha')
        self.assertContains(resp, 'Quiche')
        self.assertNotContains(resp, 'Bolo')
        self.assertNotContains(resp, 'Pudim')

    def test_filtro_custo_minimo(self):
        """Filtrar por custo mínimo deve excluir receitas mais baratas."""
        resp = self.client.get(self.url, {'min_custo': '20'})
        self.assertContains(resp, 'Bolo')
        self.assertContains(resp, 'Quiche')
        self.assertNotContains(resp, 'Pudim')
        self.assertNotContains(resp, 'Coxinha')

    def test_filtro_custo_maximo(self):
        """Filtrar por custo máximo deve excluir receitas mais caras."""
        resp = self.client.get(self.url, {'max_custo': '20'})
        self.assertContains(resp, 'Pudim')
        self.assertContains(resp, 'Coxinha')
        self.assertNotContains(resp, 'Bolo')
        self.assertNotContains(resp, 'Quiche')

    def test_filtro_faixa_de_preco(self):
        """Filtrar por min e max deve retornar apenas receitas na faixa."""
        resp = self.client.get(self.url, {'min_custo': '10', 'max_custo': '35'})
        self.assertContains(resp, 'Bolo')
        self.assertContains(resp, 'Pudim')
        self.assertNotContains(resp, 'Coxinha')
        self.assertNotContains(resp, 'Quiche')

    def test_filtro_combinado_tipo_e_preco(self):
        """Combinar tipo e custo mínimo deve refinar corretamente."""
        resp = self.client.get(self.url, {'tipo': 'Doce', 'min_custo': '20'})
        self.assertContains(resp, 'Bolo')
        self.assertNotContains(resp, 'Pudim')
        self.assertNotContains(resp, 'Coxinha')

    def test_sem_filtro_retorna_tudo(self):
        """Sem filtros, todas as receitas devem aparecer."""
        resp = self.client.get(self.url)
        self.assertContains(resp, 'Bolo')
        self.assertContains(resp, 'Pudim')
        self.assertContains(resp, 'Coxinha')
        self.assertContains(resp, 'Quiche')

    def test_filtro_tipo_invalido_retorna_tudo(self):
        """Tipo inválido (não Doce/Salgado) não deve filtrar nada."""
        resp = self.client.get(self.url, {'tipo': 'Invalido'})
        self.assertContains(resp, 'Bolo')
        self.assertContains(resp, 'Coxinha')

    def test_filtro_custo_invalido_ignorado(self):
        """Valor não numérico em custo deve ser ignorado, retornando tudo."""
        resp = self.client.get(self.url, {'min_custo': 'abc'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Bolo')
        self.assertContains(resp, 'Coxinha')
