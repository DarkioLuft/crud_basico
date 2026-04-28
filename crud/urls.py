# crud/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Autenticação
    path('login/',    views.LoginView.as_view(),   name='login'),
    path('logout/',   views.logout_view,            name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Receitas
    path('',                              views.ReceitaListView.as_view(),   name='receita_list'),
    path('receita/nova/',                 views.ReceitaCreateView.as_view(), name='receita_create'),
    path('receita/<int:pk>/',             views.ReceitaDetailView.as_view(), name='receita_detail'),
    path('receita/<int:pk>/editar/',      views.ReceitaUpdateView.as_view(), name='receita_update'),
    path('receita/<int:pk>/deletar/',     views.ReceitaDeleteView.as_view(), name='receita_delete'),

    # Exportação
    path('receitas/exportar-pdf/',        views.receita_pdf_export,          name='receita_pdf'),
]