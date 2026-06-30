"""
Comando de gerenciamento para popular o banco de dados com dados iniciais.

Uso:
    python manage.py seed_data          # Interativo (pede confirmação)
    python manage.py seed_data --noinput  # Silencioso (para CI/CD)

O comando é IDEMPOTENTE: se o usuário 'teste' já existir, não duplica nada.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from crud.models import User, Receita


# ── Dados iniciais ─────────────────────────────────────────────
USUARIO_PADRAO = {
    'name': 'Usuário Teste',
    'login': 'teste',
    'email': 'teste@teste.com',
    'senha': 'teste123',
    'status': True,
}

RECEITAS_INICIAIS = [
    {
        'nome': 'Bolo de Chocolate',
        'descricao': 'Bolo fofinho de chocolate com cobertura cremosa.',
        'ingredientes': '3 ovos\n2 xícaras de farinha de trigo\n1 xícara de chocolate em pó\n1 xícara de leite\n1/2 xícara de óleo\n2 xícaras de açúcar\n1 colher de fermento',
        'custo': Decimal('25.00'),
        'tipo_receita': 'Doce',
    },
    {
        'nome': 'Coxinha de Frango',
        'descricao': 'Coxinha crocante recheada com frango desfiado e catupiry.',
        'ingredientes': '500g de frango desfiado\n2 xícaras de farinha de trigo\n1 caldo de galinha\n200g de catupiry\nÓleo para fritar',
        'custo': Decimal('35.00'),
        'tipo_receita': 'Salgado',
    },
    {
        'nome': 'Brigadeiro Gourmet',
        'descricao': 'Brigadeiro cremoso feito com chocolate belga.',
        'ingredientes': '1 lata de leite condensado\n200g de chocolate belga\n1 colher de manteiga\nGranulado para decorar',
        'custo': Decimal('18.50'),
        'tipo_receita': 'Doce',
    },
    {
        'nome': 'Pão de Queijo Mineiro',
        'descricao': 'Receita tradicional mineira, crocante por fora e macio por dentro.',
        'ingredientes': '500g de polvilho azedo\n200ml de leite\n100ml de óleo\n3 ovos\n200g de queijo minas curado ralado\nSal a gosto',
        'custo': Decimal('22.00'),
        'tipo_receita': 'Salgado',
    },
    {
        'nome': 'Pudim de Leite Condensado',
        'descricao': 'Pudim clássico com calda de caramelo.',
        'ingredientes': '1 lata de leite condensado\n1 lata de leite (mesma medida)\n3 ovos\n1 xícara de açúcar (para a calda)',
        'custo': Decimal('15.00'),
        'tipo_receita': 'Doce',
    },
    {
        'nome': 'Empadão de Palmito',
        'descricao': 'Torta salgada recheada com palmito e temperos.',
        'ingredientes': '3 xícaras de farinha de trigo\n200g de manteiga\n1 ovo\n1 vidro de palmito\n1 lata de milho\nAzeitonas a gosto\nSal e pimenta',
        'custo': Decimal('40.00'),
        'tipo_receita': 'Salgado',
    },
    {
        'nome': 'Mousse de Maracujá',
        'descricao': 'Mousse leve e refrescante de maracujá.',
        'ingredientes': '1 lata de leite condensado\n1 lata de creme de leite\n1/2 xícara de suco de maracujá concentrado',
        'custo': Decimal('12.00'),
        'tipo_receita': 'Doce',
    },
    {
        'nome': 'Bolinho de Bacalhau',
        'descricao': 'Bolinhos fritos de bacalhau desfiado, receita portuguesa.',
        'ingredientes': '400g de bacalhau dessalgado\n500g de batata\n2 ovos\nSalsinha picada\nSal e pimenta\nÓleo para fritar',
        'custo': Decimal('55.00'),
        'tipo_receita': 'Salgado',
    },
    {
        'nome': 'Torta de Limão',
        'descricao': 'Torta com base crocante e recheio cremoso de limão com merengue.',
        'ingredientes': '200g de biscoito maisena\n100g de manteiga\n1 lata de leite condensado\nSuco de 4 limões\n3 claras de ovo\n6 colheres de açúcar',
        'custo': Decimal('20.00'),
        'tipo_receita': 'Doce',
    },
    {
        'nome': 'Esfiha Aberta de Carne',
        'descricao': 'Esfiha aberta com recheio temperado de carne moída.',
        'ingredientes': '500g de farinha de trigo\n1 sachê de fermento biológico\n300g de carne moída\n2 tomates\n1 cebola\nHortelã e limão\nSal e pimenta',
        'custo': Decimal('30.00'),
        'tipo_receita': 'Salgado',
    },
]


class Command(BaseCommand):
    help = 'Popula o banco com o usuário padrão (teste/teste123) e 10 receitas iniciais.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', action='store_true',
            help='Executa sem pedir confirmação (uso em CI/CD).',
        )

    def handle(self, *args, **options):
        # ── Verifica se já existe ──────────────────────────────
        if User.objects.filter(login=USUARIO_PADRAO['login']).exists():
            self.stdout.write(self.style.WARNING(
                '⚠️  Usuário "teste" já existe. Seed ignorado (idempotente).'
            ))
            return

        if not options['noinput']:
            confirm = input('Deseja popular o banco com dados iniciais? [s/N] ')
            if confirm.lower() not in ('s', 'sim', 'y', 'yes'):
                self.stdout.write('Operação cancelada.')
                return

        # ── Cria o usuário ─────────────────────────────────────
        user = User.objects.create(**USUARIO_PADRAO)
        self.stdout.write(self.style.SUCCESS(
            f'✅ Usuário criado: login={user.login}'
        ))

        # ── Cria as receitas ───────────────────────────────────
        receitas = [Receita(user=user, **dados) for dados in RECEITAS_INICIAIS]
        Receita.objects.bulk_create(receitas)
        self.stdout.write(self.style.SUCCESS(
            f'✅ {len(receitas)} receitas inseridas com sucesso!'
        ))