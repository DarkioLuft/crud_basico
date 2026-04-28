# crud/views.py
import re
from decimal import Decimal
from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

# ReportLab — geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from .models import Receita, User


# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════

def _get_current_user(request):
    """Retorna o objeto User da sessão, ou None."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(pk=user_id, status=True)
    except User.DoesNotExist:
        return None


def _apply_receita_filters(qs, request):
    """Aplica filtros de tipo e custo ao queryset de Receita."""
    tipo = request.GET.get('tipo', '')
    min_custo = request.GET.get('min_custo', '')
    max_custo = request.GET.get('max_custo', '')

    if tipo in ('Doce', 'Salgado'):
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


# ══════════════════════════════════════════════════════
# MIXIN DE PROTEÇÃO
# ══════════════════════════════════════════════════════

class RequerLoginMixin:
    """Redireciona para login se não houver sessão ativa."""

    def dispatch(self, request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


# ══════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ══════════════════════════════════════════════════════

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
                'erros': erros, 'name': name, 'login': login, 'email': email,
            })

        User.objects.create(name=name, login=login, email=email, senha=senha)
        return render(request, 'crud/login.html', {
            'sucesso': 'Cadastro realizado com sucesso! Faça login para continuar.',
        })


def logout_view(request):
    request.session.flush()
    return redirect('login')


# ══════════════════════════════════════════════════════
# CRUD DE RECEITAS  (escopo por usuário)
# ══════════════════════════════════════════════════════

class ReceitaListView(RequerLoginMixin, ListView):
    model = Receita
    template_name = 'crud/receita_list.html'
    context_object_name = 'receitas'

    def get_queryset(self):
        qs = Receita.objects.filter(
            user_id=self.request.session['user_id']
        ).order_by('nome')
        return _apply_receita_filters(qs, self.request)

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

    def get_queryset(self):
        return Receita.objects.filter(user_id=self.request.session['user_id'])


class ReceitaCreateView(RequerLoginMixin, CreateView):
    model = Receita
    template_name = 'crud/receita_form.html'
    fields = ['nome', 'descricao', 'ingredientes', 'custo', 'tipo_receita']
    success_url = reverse_lazy('receita_list')

    def form_valid(self, form):
        # Vincula a nova receita ao usuário logado
        form.instance.user_id = self.request.session['user_id']
        return super().form_valid(form)


class ReceitaUpdateView(RequerLoginMixin, UpdateView):
    model = Receita
    template_name = 'crud/receita_form.html'
    fields = ['nome', 'descricao', 'ingredientes', 'custo', 'tipo_receita']
    success_url = reverse_lazy('receita_list')

    def get_queryset(self):
        return Receita.objects.filter(user_id=self.request.session['user_id'])


class ReceitaDeleteView(RequerLoginMixin, DeleteView):
    model = Receita
    template_name = 'crud/receita_confirm_delete.html'
    context_object_name = 'receita'
    success_url = reverse_lazy('receita_list')

    def get_queryset(self):
        return Receita.objects.filter(user_id=self.request.session['user_id'])


# ══════════════════════════════════════════════════════
# EXPORTAÇÃO PARA PDF
# ══════════════════════════════════════════════════════

# Paleta de cores (alinhada ao tema verde do sistema)
COR_VERDE = colors.HexColor('#10b981')
COR_VERDE_ESCURO = colors.HexColor('#059669')
COR_VERDE_CLARO = colors.HexColor('#d1fae5')
COR_CINZA_CLARO = colors.HexColor('#f3f4f6')
COR_TEXTO = colors.HexColor('#1f2937')
COR_TEXTO_SUAVE = colors.HexColor('#6b7280')
COR_PERIGO = colors.HexColor('#ef4444')


def _build_pdf_styles():
    styles = getSampleStyleSheet()
    extra = {
        'Titulo': ParagraphStyle(
            'Titulo', parent=styles['Title'],
            fontSize=22, textColor=COR_VERDE_ESCURO, spaceAfter=4,
        ),
        'Subtitulo': ParagraphStyle(
            'Subtitulo', parent=styles['Normal'],
            fontSize=10, textColor=COR_TEXTO_SUAVE, spaceAfter=2,
        ),
        'Filtros': ParagraphStyle(
            'Filtros', parent=styles['Normal'],
            fontSize=9, textColor=COR_TEXTO_SUAVE, spaceAfter=8,
        ),
        'Rodape': ParagraphStyle(
            'Rodape', parent=styles['Normal'],
            fontSize=8, textColor=COR_TEXTO_SUAVE, alignment=1,
        ),
        'Resumo': ParagraphStyle(
            'Resumo', parent=styles['Normal'],
            fontSize=10, textColor=COR_TEXTO, spaceAfter=4,
        ),
    }
    styles.__dict__['byName'].update(extra)
    return styles, extra


def receita_pdf_export(request):
    """Gera e devolve um PDF com a lista de receitas do usuário logado.
    Respeita os mesmos filtros (tipo, min_custo, max_custo) do GET."""
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user_name = request.session.get('user_name', '')

    qs = Receita.objects.filter(user_id=user_id).order_by('nome')
    qs = _apply_receita_filters(qs, request)
    receitas = list(qs)

    # ── Filtros aplicados (descrição legível) ──────────────────────────
    tipo_filtro = request.GET.get('tipo', '')
    min_custo = request.GET.get('min_custo', '')
    max_custo = request.GET.get('max_custo', '')

    filtros_desc = []
    if tipo_filtro:
        filtros_desc.append(f'Tipo: {tipo_filtro}')
    if min_custo:
        filtros_desc.append(f'Custo mínimo: R$ {min_custo}')
    if max_custo:
        filtros_desc.append(f'Custo máximo: R$ {max_custo}')

    # ── Geração do PDF ─────────────────────────────────────────────────
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title='Minhas Receitas',
        author=user_name,
    )

    styles, ext = _build_pdf_styles()
    story = []

    # Cabeçalho
    story.append(Paragraph('Gestão de Receitas', ext['Titulo']))
    story.append(Paragraph(f'Receitas de: <b>{user_name}</b>', ext['Subtitulo']))

    if filtros_desc:
        story.append(Paragraph('Filtros aplicados: ' + ' | '.join(filtros_desc), ext['Filtros']))

    story.append(HRFlowable(width='100%', thickness=2, color=COR_VERDE, spaceAfter=12))

    if not receitas:
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(
            'Nenhuma receita encontrada com os filtros aplicados.',
            styles['Normal'],
        ))
    else:
        # Tabela
        col_widths = [1.2 * cm, 6.5 * cm, 3 * cm, 2.8 * cm]
        header = [
            Paragraph('<b>#</b>', styles['Normal']),
            Paragraph('<b>Nome</b>', styles['Normal']),
            Paragraph('<b>Tipo</b>', styles['Normal']),
            Paragraph('<b>Custo (R$)</b>', styles['Normal']),
        ]
        data = [header]

        total = Decimal('0')
        for i, r in enumerate(receitas, start=1):
            total += r.custo
            tipo_cor = COR_VERDE_ESCURO if r.tipo_receita == 'Doce' else COR_TEXTO_SUAVE
            data.append([
                Paragraph(str(i), styles['Normal']),
                Paragraph(r.nome, styles['Normal']),
                Paragraph(
                    f'<font color="{tipo_cor.hexval()}">{r.tipo_receita}</font>',
                    styles['Normal'],
                ),
                Paragraph(f'{r.custo:.2f}', styles['Normal']),
            ])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND',  (0, 0), (-1, 0), COR_VERDE),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING',  (0, 0), (-1, 0), 8),
            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COR_CINZA_CLARO]),
            # Bordas
            ('GRID',        (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
            ('LINEBELOW',   (0, 0), (-1, 0), 1.5, COR_VERDE_ESCURO),
            # Alinhamento
            ('ALIGN',       (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN',       (3, 0), (3, -1), 'RIGHT'),
            ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE',    (0, 1), (-1, -1), 9),
            ('TOPPADDING',  (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(table)

        # Totais
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width='100%', thickness=0.5, color=COR_VERDE_CLARO))
        story.append(Spacer(1, 0.3 * cm))

        resumo_data = [
            [
                Paragraph(f'<b>Total de receitas:</b> {len(receitas)}', ext['Resumo']),
                Paragraph(
                    f'<b>Custo total:</b> R$ {total:.2f}',
                    ParagraphStyle(
                        'ResumoDir', parent=styles['Normal'],
                        fontSize=10, textColor=COR_VERDE_ESCURO, alignment=2,
                    ),
                ),
            ]
        ]
        resumo_table = Table(resumo_data, colWidths=[9 * cm, 4.5 * cm])
        resumo_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(resumo_table)

    # Rodapé com data de geração
    from datetime import datetime
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=COR_VERDE_CLARO))
    story.append(Spacer(1, 0.2 * cm))
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    story.append(Paragraph(f'Documento gerado em {agora}', ext['Rodape']))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="minhas-receitas.pdf"'
    return response