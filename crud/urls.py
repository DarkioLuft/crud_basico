# crud/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Rotas de Autenticação
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Rotas de Receitas
    path('', views.ReceitaListView.as_view(), name='receita_list'),
    path('receita/<int:pk>/', views.ReceitaDetailView.as_view(), name='receita_detail'),
    path('receita/nova/', views.ReceitaCreateView.as_view(), name='receita_create'),
    path('receita/<int:pk>/editar/', views.ReceitaUpdateView.as_view(), name='receita_update'),
    path('receita/<int:pk>/deletar/', views.ReceitaDeleteView.as_view(), name='receita_delete'),
]