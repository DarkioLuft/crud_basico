🍲 CRUD de Receitas - Task 2 (GCS)

Este projeto é uma aplicação web desenvolvida como requisito para a Tarefa Final (Task 2) da disciplina de Gerência de Configuração de Software (4815207) - Prof. Fabrício.

A aplicação consiste em um sistema para registro e listagem de receitas culinárias (doces e salgadas), com controle de acesso (login) e integração com banco de dados relacional.

🚀 Tecnologias Utilizadas

O projeto foi construído utilizando o seguinte ecossistema (Golden Stack para Python web):

Backend: Python 3.12 + Django

Banco de Dados: PostgreSQL

Servidor de Aplicação: Gunicorn

Proxy Reverso: Nginx

Sistema Operacional (Deploy): Linux Ubuntu 24.04

✨ Funcionalidades

Autenticação: Tela de login para acesso ao sistema.

Gestão de Receitas (CRUD): * Listagem de todas as receitas cadastradas.

Detalhamento de receitas (Nome, Descrição, Ingredientes, Data de Criação, Custo, Tipo).

Separação por categorias: Doce ou Salgada.

🛠️ Como rodar o projeto localmente

Para rodar este projeto na sua máquina para desenvolvimento ou testes, siga os passos abaixo.

1. Pré-requisitos

Você precisará ter instalado em sua máquina:

Python 3.x

PostgreSQL

Git

2. Clonando o Repositório

git clone [https://github.com/DarkioLuft/crud_basico.git](https://github.com/DarkioLuft/crud_basico.git)
cd crud_basico


3. Criando o Ambiente Virtual

É recomendado usar um ambiente virtual para isolar as dependências do projeto.

# Cria o ambiente virtual
python -m venv venv

# Ativa o ambiente virtual (Linux/macOS)
source venv/bin/activate

# Ativa o ambiente virtual (Windows)
venv\Scripts\activate


4. Instalando as Dependências

Com o ambiente ativado, instale as bibliotecas necessárias:

pip install -r requirements.txt


5. Configuração do Banco de Dados

Crie um banco de dados no seu PostgreSQL local chamado crud_db.

CREATE DATABASE crud_db;


Nota: Verifique o arquivo settings.py para garantir que o usuário e a senha do banco de dados correspondam à sua configuração local.

6. Executando as Migrations

Aplique a estrutura do banco de dados:

python manage.py makemigrations
python manage.py migrate


7. Criando um Superusuário (Opcional)

Para acessar o painel administrativo do Django:

python manage.py createsuperuser


8. Rodando o Servidor

Inicie o servidor de desenvolvimento:

python manage.py runserver


Acesse a aplicação no seu navegador em: http://127.0.0.1:8000

☁️ Deploy

A aplicação foi implantada em uma Máquina Virtual (VM) utilizando Gunicorn como servidor WSGI acoplado via Unix Socket ao Nginx, atuando como proxy reverso para lidar com as requisições HTTP estáticas e dinâmicas.

Desenvolvido para fins acadêmicos.
