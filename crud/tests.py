# crud/tests.py
import time
import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase, Client, RequestFactory
from django.urls import reverse

from crud.models import User, Receita
from crud.views import _get_current_user, _apply_receita_filters, RequerLoginMixin


# =====================================================================
# HELPERS (Funções Auxiliares de Teste)
# =====================================================================
def criar_usuario(**kwargs):
    """Cria e retorna um usuário no banco de dados de teste."""
    defaults = dict(name='Teste', login='testuser', email='test@test.com', senha='123', status=True)
    defaults.update(kwargs)
    return User.objects.create(**defaults)

def criar_receita(user, **kwargs):
    """Cria e retorna uma receita vinculada a um usuário no banco de dados de teste."""
    defaults = dict(nome='Bolo Mock', descricao='Desc', ingredientes='Ing', custo=Decimal('20.00'), tipo_receita='Doce')
    defaults.update(kwargs)
    return Receita.objects.create(user=user, **defaults)

def logar(client, user):
    """Força o login de um usuário no Client de testes manipulando a sessão."""
    session = client.session
    session['user_id'] = user.id_user
    session['user_name'] = user.name
    session.save()


# =====================================================================
# 1. TESTES UNITÁRIOS E MOCKS (17 Testes)
# =====================================================================

class ModelsUnitTests(TestCase):
    """Testes unitários isolados para os Modelos (4 testes)"""
    
    def test_01_user_str_retorna_nome(self):
        user = User(name="Darkio", login="darkio", senha="123")
        self.assertEqual(str(user), "Darkio")

    def test_02_receita_str_retorna_nome(self):
        receita = Receita(nome="Torta de Maçã")
        self.assertEqual(str(receita), "Torta de Maçã")

    @patch('crud.models.reverse')
    def test_03_receita_get_absolute_url_mock(self, mock_reverse):
        mock_reverse.return_value = '/receitas/mock/'
        receita = Receita(nome="Mock")
        self.assertEqual(receita.get_absolute_url(), '/receitas/mock/')
        mock_reverse.assert_called_once_with('receita_list')

    def test_04_user_status_padrao_true(self):
        user = User(name="Test", login="test", email="test@test.com", senha="123")
        self.assertTrue(user.status)


class HelpersAndMixinsMockTests(TestCase):
    """Testes unitários utilizando Mocks para funções internas e Mixins (4 testes)"""
    
    def setUp(self):
        self.factory = RequestFactory()

    def test_05_get_current_user_sem_sessao(self):
        request = self.factory.get('/')
        request.session = {}
        self.assertIsNone(_get_current_user(request))

    @patch('crud.views.User.objects.get')
    def test_06_get_current_user_com_sessao(self, mock_get):
        mock_get.return_value = MagicMock(name="UsuarioAtivo")
        request = self.factory.get('/')
        request.session = {'user_id': 99}
        _get_current_user(request)
        mock_get.assert_called_once_with(pk=99, status=True)

    @patch('crud.views.redirect')
    def test_07_requer_login_mixin_bloqueia_acesso(self, mock_redirect):
        request = self.factory.get('/')
        request.session = {}
        RequerLoginMixin().dispatch(request)
        mock_redirect.assert_called_once_with('login')

    def test_08_apply_receita_filters_mock(self):
        request = self.factory.get('/?tipo=Doce&min_custo=15.00')
        qs_mock = MagicMock()
        
        # Diz ao Mock para retornar ele mesmo (simulando o encadeamento do Django)
        qs_mock.filter.return_value = qs_mock
        
        _apply_receita_filters(qs_mock, request)
        
        # Verifica se as chamadas de filtro foram enfileiradas corretamente no mock
        qs_mock.filter.assert_any_call(tipo_receita='Doce')
        self.assertEqual(qs_mock.filter.call_count, 2)


class AuthViewsTests(TestCase):
    """Testes das rotas de Autenticação utilizando o Client (5 testes)"""

    def setUp(self):
        self.client = Client()

    def test_09_login_get_renderiza_template(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/login.html')

    def test_10_login_post_sucesso_redireciona(self):
        user = criar_usuario(login="admin", senha="123")
        response = self.client.post(reverse('login'), {'login': 'admin', 'senha': '123'})
        self.assertRedirects(response, reverse('receita_list'))
        self.assertEqual(self.client.session['user_id'], user.id_user)

    def test_11_login_post_falha_exibe_erro(self):
        response = self.client.post(reverse('login'), {'login': 'errado', 'senha': '000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inválidos')

    def test_12_register_post_senhas_incompativeis(self):
        dados = {'name': 'A', 'login': 'B', 'email': 'c@c.com', 'senha': '123', 'senha_confirm': '456'}
        response = self.client.post(reverse('register'), dados)
        self.assertContains(response, 'As senhas não coincidem')

    def test_13_logout_limpa_sessao(self):
        user = criar_usuario()
        logar(self.client, user)
        response = self.client.post(reverse('logout'))
        self.assertNotIn('user_id', self.client.session)
        self.assertRedirects(response, reverse('login'))


class ReceitasViewsTests(TestCase):
    """Testes das rotas de Receitas com isolamento de usuário (4 testes)"""

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()
        logar(self.client, self.user)

    def test_14_receita_list_exige_login_e_lista_dados(self):
        criar_receita(self.user, nome="Coxinha Teste")
        response = self.client.get(reverse('receita_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coxinha Teste")

    def test_15_receita_create_salva_com_usuario_logado(self):
        dados = {'nome': 'Nova', 'descricao': 'D', 'ingredientes': 'I', 'custo': '10.00', 'tipo_receita': 'Doce'}
        response = self.client.post(reverse('receita_create'), dados)
        self.assertRedirects(response, reverse('receita_list'))
        self.assertTrue(Receita.objects.filter(nome='Nova', user=self.user).exists())

    def test_16_receita_delete_remove_registro(self):
        receita = criar_receita(self.user, nome="Deletar Isso")
        response = self.client.post(reverse('receita_delete', args=[receita.pk]))
        self.assertRedirects(response, reverse('receita_list'))
        self.assertFalse(Receita.objects.filter(pk=receita.pk).exists())

    def test_17_receita_update_altera_dados(self):
        receita = criar_receita(self.user, nome="Antigo")
        dados = {'nome': 'Atualizado', 'descricao': 'D', 'ingredientes': 'I', 'custo': '15.00', 'tipo_receita': 'Doce'}
        response = self.client.post(reverse('receita_update', args=[receita.pk]), dados)
        self.assertRedirects(response, reverse('receita_list'))
        receita.refresh_from_db()
        self.assertEqual(receita.nome, 'Atualizado')


# =====================================================================
# 2. TESTES DE CARGA E STRESS (3 Testes)
# =====================================================================

class DatabaseLoadTests(TransactionTestCase):
    """
    Testes de performance utilizando TransactionTestCase para garantir 
    que as transações em massa reflitam a realidade do banco de dados.
    """
    
    def setUp(self):
        self.user = criar_usuario(login="loadtest", email="load@test.com")

    def test_18_bulk_insert_100k_registros(self):
        """Teste de Carga 1: Escrita massiva no banco de dados com bulk_create."""
        receitas_para_inserir = [
            Receita(
                user=self.user,
                nome=f"Receita Massiva {i}",
                descricao="Gerado automaticamente",
                ingredientes="Água, Sal",
                custo=Decimal('15.50'),
                tipo_receita="Doce" if i % 2 == 0 else "Salgado"
            ) for i in range(100000)
        ]
        
        start_time = time.time()
        # O batch_size = 5000 evita o estouro de memória no PostgreSQL/SQLite
        Receita.objects.bulk_create(receitas_para_inserir, batch_size=5000)
        duration = time.time() - start_time
        
        self.assertEqual(Receita.objects.count(), 100000)
        self.assertLess(duration, 15.0, f"O insert demorou muito: {duration:.2f}s")

    def test_19_stress_filtros_complexos_50k(self):
        """Teste de Carga 2: Leitura e scan de tabela completa sem índices (Seq Scan)."""
        receitas = [
            Receita(
                user=self.user, nome=f"R {i}", descricao="D",
                ingredientes="I", custo=Decimal(i % 100), 
                tipo_receita="Salgado" if i % 3 == 0 else "Doce"
            ) for i in range(50000)
        ]
        Receita.objects.bulk_create(receitas, batch_size=5000)

        start_time = time.time()
        # Força o banco a varrer todas as 50k linhas procurando por custos e ordenando
        queryset = Receita.objects.filter(
            user=self.user,
            tipo_receita="Doce",
            custo__gte=Decimal('20.00'),
            custo__lte=Decimal('80.00')
        ).order_by('-custo')
        
        resultados = list(queryset) # Força a execução SQL imediata
        duration = time.time() - start_time
        
        self.assertTrue(len(resultados) > 0)
        self.assertLess(duration, 2.0, f"A leitura da tabela demorou muito: {duration:.2f}s.")

    def test_20_simulacao_concorrencia_e_io(self):
        """Teste de Carga 3: I/O de múltiplas queries sequenciais via Foreign Key."""
        users = [User(name=f"U{i}", login=f"u{i}", email=f"u{i}@x.com", senha="1") for i in range(500)]
        User.objects.bulk_create(users)
        
        db_users = User.objects.exclude(id_user=self.user.id_user)
        receitas = []
        for u in db_users:
            for r in range(10):
                receitas.append(
                    Receita(user=u, nome="R", descricao="D", ingredientes="I", custo=Decimal('1'), tipo_receita="Doce")
                )
        Receita.objects.bulk_create(receitas, batch_size=2000)

        start_time = time.time()
        # Simula 1.000 requisições buscando relações de diferentes usuários de forma sequencial rápida
        for i in range(1000):
            user_aleatorio = User.objects.order_by('?').first()
            _ = list(Receita.objects.filter(user=user_aleatorio))
            
        duration = time.time() - start_time
        
        # Este teste avalia o tempo de round-trip do banco de dados (Gargalo de I/O)
        self.assertLess(duration, 5.0, f"Tempo de I/O do banco excedeu o limite: {duration:.2f}s.")