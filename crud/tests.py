"""
Testes unitários – Gestão de Receitas.

Execute com:
    python manage.py test crud
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Receita


# ─────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────

def criar_usuario(**kw):
    defaults = dict(name='Teste', login='testuser',
                    email='test@test.com', senha='senha123', status=True)
    defaults.update(kw)
    return User.objects.create(**defaults)


def criar_receita(user, **kw):
    defaults = dict(nome='Bolo', descricao='Desc', ingredientes='Ing',
                    custo=Decimal('20.00'), tipo_receita='Doce')
    defaults.update(kw)
    return Receita.objects.create(user=user, **defaults)


def logar(client, user):
    s = client.session
    s['user_id'] = user.id_user
    s['user_name'] = user.name
    s.save()


# ══════════════════════════════════════════════════════
# 1. Modelo User
# ══════════════════════════════════════════════════════

class UserModelTest(TestCase):

    def test_criacao_campos(self):
        u = criar_usuario()
        self.assertEqual(u.login, 'testuser')
        self.assertEqual(u.email, 'test@test.com')
        self.assertTrue(u.status)

    def test_str_retorna_nome(self):
        self.assertEqual(str(criar_usuario()), 'Teste')

    def test_login_unico(self):
        criar_usuario()
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create(name='X', login='testuser',
                                email='x@x.com', senha='abc')

    def test_email_unico(self):
        criar_usuario()
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create(name='Y', login='outro',
                                email='test@test.com', senha='abc')

    def test_status_padrao_true(self):
        u = User.objects.create(name='Z', login='z', email='z@z.com', senha='x')
        self.assertTrue(u.status)


# ══════════════════════════════════════════════════════
# 2. Modelo Receita
# ══════════════════════════════════════════════════════

class ReceitaModelTest(TestCase):

    def setUp(self):
        self.user = criar_usuario()

    def test_criacao(self):
        r = criar_receita(self.user, nome='Torta')
        self.assertEqual(r.nome, 'Torta')
        self.assertEqual(r.user, self.user)

    def test_str(self):
        self.assertEqual(str(criar_receita(self.user, nome='Coxinha')), 'Coxinha')

    def test_data_criacao_automatica(self):
        self.assertIsNotNone(criar_receita(self.user).data_criacao)

    def test_get_absolute_url(self):
        r = criar_receita(self.user)
        self.assertEqual(r.get_absolute_url(), reverse('receita_list'))

    def test_receita_vinculada_ao_usuario(self):
        r = criar_receita(self.user)
        self.assertEqual(r.user.id_user, self.user.id_user)


# ══════════════════════════════════════════════════════
# 3. Login / Logout
# ══════════════════════════════════════════════════════

class AuthTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()

    def test_get_login(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def test_login_valido_redireciona(self):
        r = self.client.post(reverse('login'),
                             {'login': 'testuser', 'senha': 'senha123'})
        self.assertRedirects(r, reverse('receita_list'))

    def test_login_salva_sessao(self):
        self.client.post(reverse('login'),
                         {'login': 'testuser', 'senha': 'senha123'})
        self.assertEqual(self.client.session['user_id'], self.user.id_user)

    def test_login_senha_errada(self):
        r = self.client.post(reverse('login'),
                             {'login': 'testuser', 'senha': 'errada'})
        self.assertContains(r, 'inválidos')

    def test_login_usuario_inativo(self):
        self.user.status = False
        self.user.save()
        r = self.client.post(reverse('login'),
                             {'login': 'testuser', 'senha': 'senha123'})
        self.assertContains(r, 'inválidos')

    def test_usuario_logado_nao_ve_login(self):
        logar(self.client, self.user)
        self.assertRedirects(self.client.get(reverse('login')),
                             reverse('receita_list'))

    def test_logout_limpa_sessao(self):
        logar(self.client, self.user)
        self.client.post(reverse('logout'))
        self.assertNotIn('user_id', self.client.session)

    def test_logout_redireciona(self):
        logar(self.client, self.user)
        self.assertRedirects(self.client.post(reverse('logout')),
                             reverse('login'))


# ══════════════════════════════════════════════════════
# 4. Cadastro de Usuário
# ══════════════════════════════════════════════════════

class RegisterTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')
        self.ok = dict(name='Novo', login='novo', email='novo@x.com',
                       senha='senha123', senha_confirm='senha123')

    def test_cadastro_valido_cria_user(self):
        self.client.post(self.url, self.ok)
        self.assertTrue(User.objects.filter(login='novo').exists())

    def test_cadastro_exibe_sucesso(self):
        r = self.client.post(self.url, self.ok)
        self.assertContains(r, 'sucesso')

    def test_login_duplicado(self):
        criar_usuario(login='novo', email='outro@x.com')
        self.assertContains(self.client.post(self.url, self.ok),
                            'login já está em uso')

    def test_email_duplicado(self):
        criar_usuario(login='outro', email='novo@x.com')
        self.assertContains(self.client.post(self.url, self.ok),
                            'e-mail já está cadastrado')

    def test_senhas_diferentes(self):
        self.assertContains(
            self.client.post(self.url, {**self.ok, 'senha_confirm': 'outra'}),
            'senhas não coincidem',
        )

    def test_email_invalido(self):
        self.assertContains(
            self.client.post(self.url, {**self.ok, 'email': 'invalido'}),
            'e-mail válido',
        )

    def test_senha_curta(self):
        self.assertContains(
            self.client.post(self.url, {**self.ok, 'senha': '123', 'senha_confirm': '123'}),
            '6 caracteres',
        )


# ══════════════════════════════════════════════════════
# 5. Isolamento de Receitas por Usuário
# ══════════════════════════════════════════════════════

class IsolamentoUsuarioTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.u1 = criar_usuario(login='u1', email='u1@x.com')
        self.u2 = criar_usuario(login='u2', email='u2@x.com')
        self.r1 = criar_receita(self.u1, nome='Receita do U1')
        self.r2 = criar_receita(self.u2, nome='Receita do U2')

    def test_lista_mostra_apenas_proprias(self):
        logar(self.client, self.u1)
        r = self.client.get(reverse('receita_list'))
        self.assertContains(r, 'Receita do U1')
        self.assertNotContains(r, 'Receita do U2')

    def test_u2_nao_ve_lista_de_u1(self):
        logar(self.client, self.u2)
        r = self.client.get(reverse('receita_list'))
        self.assertNotContains(r, 'Receita do U1')

    def test_u1_nao_acessa_detalhe_de_u2(self):
        logar(self.client, self.u1)
        r = self.client.get(reverse('receita_detail', args=[self.r2.pk]))
        self.assertEqual(r.status_code, 404)

    def test_u1_nao_edita_receita_de_u2(self):
        logar(self.client, self.u1)
        r = self.client.get(reverse('receita_update', args=[self.r2.pk]))
        self.assertEqual(r.status_code, 404)

    def test_u1_nao_deleta_receita_de_u2(self):
        logar(self.client, self.u1)
        self.client.post(reverse('receita_delete', args=[self.r2.pk]))
        self.assertTrue(Receita.objects.filter(pk=self.r2.pk).exists())

    def test_criar_associa_usuario_logado(self):
        logar(self.client, self.u1)
        self.client.post(reverse('receita_create'), {
            'nome': 'Nova', 'descricao': 'D', 'ingredientes': 'I',
            'custo': '10.00', 'tipo_receita': 'Doce',
        })
        nova = Receita.objects.get(nome='Nova')
        self.assertEqual(nova.user, self.u1)


# ══════════════════════════════════════════════════════
# 6. Filtros da Lista
# ══════════════════════════════════════════════════════

class FiltroTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()
        logar(self.client, self.user)
        criar_receita(self.user, nome='Bolo',   tipo_receita='Doce',    custo=Decimal('30'))
        criar_receita(self.user, nome='Pudim',  tipo_receita='Doce',    custo=Decimal('15'))
        criar_receita(self.user, nome='Coxinha',tipo_receita='Salgado', custo=Decimal('8'))
        criar_receita(self.user, nome='Quiche', tipo_receita='Salgado', custo=Decimal('50'))

    def _get(self, params):
        return self.client.get(reverse('receita_list'), params)

    def test_filtro_doce(self):
        r = self._get({'tipo': 'Doce'})
        self.assertContains(r, 'Bolo')
        self.assertNotContains(r, 'Coxinha')

    def test_filtro_salgado(self):
        r = self._get({'tipo': 'Salgado'})
        self.assertContains(r, 'Coxinha')
        self.assertNotContains(r, 'Bolo')

    def test_filtro_min_custo(self):
        r = self._get({'min_custo': '20'})
        self.assertContains(r, 'Bolo')
        self.assertNotContains(r, 'Pudim')

    def test_filtro_max_custo(self):
        r = self._get({'max_custo': '20'})
        self.assertContains(r, 'Pudim')
        self.assertNotContains(r, 'Bolo')

    def test_filtro_faixa(self):
        r = self._get({'min_custo': '10', 'max_custo': '35'})
        self.assertContains(r, 'Bolo')
        self.assertContains(r, 'Pudim')
        self.assertNotContains(r, 'Quiche')
        self.assertNotContains(r, 'Coxinha')

    def test_filtro_tipo_e_preco(self):
        r = self._get({'tipo': 'Doce', 'min_custo': '20'})
        self.assertContains(r, 'Bolo')
        self.assertNotContains(r, 'Pudim')

    def test_tipo_invalido_retorna_tudo(self):
        r = self._get({'tipo': 'Invalido'})
        self.assertContains(r, 'Bolo')
        self.assertContains(r, 'Coxinha')

    def test_custo_invalido_ignorado(self):
        r = self._get({'min_custo': 'abc'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Bolo')


# ══════════════════════════════════════════════════════
# 7. Exportação PDF
# ══════════════════════════════════════════════════════

class PDFExportTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = criar_usuario()
        logar(self.client, self.user)
        criar_receita(self.user, nome='Torta Doce',   tipo_receita='Doce',    custo=Decimal('25'))
        criar_receita(self.user, nome='Pastel Salgado',tipo_receita='Salgado', custo=Decimal('10'))

    def test_pdf_retorna_200(self):
        r = self.client.get(reverse('receita_pdf'))
        self.assertEqual(r.status_code, 200)

    def test_pdf_content_type(self):
        r = self.client.get(reverse('receita_pdf'))
        self.assertEqual(r['Content-Type'], 'application/pdf')

    def test_pdf_header_attachment(self):
        r = self.client.get(reverse('receita_pdf'))
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('.pdf', r['Content-Disposition'])

    def test_pdf_sem_login_redireciona(self):
        client = Client()   # cliente sem sessão
        r = client.get(reverse('receita_pdf'))
        self.assertRedirects(r, reverse('login'))

    def test_pdf_com_filtro_tipo(self):
        # Deve retornar 200 mesmo com filtros aplicados
        r = self.client.get(reverse('receita_pdf'), {'tipo': 'Doce'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')

    def test_pdf_lista_vazia_retorna_200(self):
        # Filtro que não bate em nada — PDF ainda deve ser gerado
        r = self.client.get(reverse('receita_pdf'),
                            {'min_custo': '9999'})
        self.assertEqual(r.status_code, 200)

    def test_pdf_nao_contem_dados_de_outro_usuario(self):
        """Usuário 2 não deve receber receitas do usuário 1 no PDF."""
        u2 = criar_usuario(login='u2', email='u2@x.com')
        criar_receita(u2, nome='Receita Secreta U2')
        # PDF gerado como u1 (sessão atual) — não deve conter receita de u2
        r = self.client.get(reverse('receita_pdf'))
        # PDF é binário; checamos que "Receita Secreta U2" não está no stream
        self.assertNotIn(b'Receita Secreta U2', r.content)