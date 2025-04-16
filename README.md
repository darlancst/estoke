# Sistema de Controle de Estoque

Um sistema completo de gerenciamento de estoque desenvolvido com Django, permitindo controle de produtos, fornecedores, vendas, promoções, notas fiscais e devoluções.

## Funcionalidades

- **Dashboard** com estatísticas gerais, gráficos de receita/lucro e produtos mais lucrativos
- **Gerenciamento de Produtos** com histórico de preços e cálculo de margem de lucro
- **Controle de Fornecedores**
- **Gestão de Vendas** com atualização automática de estoque
- **Sistema de Promoções** com datas de início/fim e descontos
- **Emissão de Notas Fiscais**
- **Gestão de Devoluções e Trocas**
- **Monitoramento de produtos com estoque baixo**
- **Configurações do sistema**

## Requisitos

- Python 3.6+
- Django 5.0+
- Outras dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
   ```
   git clone <url-do-repositorio>
   cd estoque_control
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Execute as migrações:
   ```
   python manage.py migrate
   ```

5. Crie um superusuário:
   ```
   python manage.py createsuperuser
   ```

6. Inicie o servidor:
   ```
   python manage.py runserver
   ```

7. Acesse em seu navegador: http://127.0.0.1:8000

## Estrutura do Projeto

- `estoque_control/` - Configurações do projeto Django
- `inventario/` - Aplicativo principal de controle de estoque
  - `models.py` - Modelos de dados
  - `views.py` - Lógica da aplicação
  - `forms.py` - Formulários
  - `urls.py` - Mapeamento de URLs
  - `templates/` - Templates HTML
  - `templatetags/` - Filtros personalizados para templates

## Uso

1. Acesse o painel administrativo em `/admin/` para gerenciar dados diretamente
2. Configure os dados da sua empresa em "Configurações"
3. Cadastre fornecedores e produtos
4. Registre vendas, gerando notas fiscais quando necessário
5. Crie promoções para produtos
6. Gerencie devoluções e trocas
7. Acompanhe o desempenho pelo dashboard

## Tecnologias Utilizadas

- **Backend**: Django
- **Frontend**: Bootstrap 5, Chart.js
- **Banco de Dados**: SQLite (pode ser adaptado para PostgreSQL, MySQL, etc.)
- **Interatividade**: JavaScript

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

## Instruções de Implantação no PythonAnywhere

### 1. Preparação Inicial

Faça login na sua conta do PythonAnywhere. Se você já tem um projeto existente que deseja substituir, primeiro faça backup dos dados importantes.

### 2. Faça Upload do Projeto

#### Opção 1: Usando Git
```bash
# No console do PythonAnywhere
cd ~
# Se já existe um diretório com o projeto antigo, renomeie-o como backup
mv seu_projeto_antigo seu_projeto_antigo_backup

# Clone o repositório ou faça upload dos arquivos manualmente
git clone https://github.com/seu-usuario/seu-repositorio.git seu_projeto
```

#### Opção 2: Usando Upload Manual
- No painel do PythonAnywhere, vá para a seção "Files"
- Navegue até o diretório onde deseja colocar o projeto
- Use a opção de upload para enviar os arquivos (pode ser como ZIP e depois extrair)

### 3. Configure o Ambiente Virtual

```bash
# Crie um novo ambiente virtual (ou use o existente)
mkvirtualenv --python=python3.10 venv
workon venv

# Instale as dependências
cd ~/seu_projeto
pip install -r requirements.txt
```

### 4. Configure o Banco de Dados

```bash
# Configure o banco de dados
python manage.py migrate
python manage.py createsuperuser
```

### 5. Configure os Arquivos Estáticos

```bash
# Coleta de arquivos estáticos
python manage.py collectstatic
```

### 6. Configure o WSGI

- No PythonAnywhere, vá para a seção "Web"
- Clique em "Add a new web app" ou configure seu app existente
- Escolha "Manual Configuration" e selecione Python 3.10
- Em "Code" configure o caminho para o arquivo WSGI:
  - `/var/www/seu_usuario_pythonanywhere_com_wsgi.py`
- Edite o arquivo WSGI para apontar para seu projeto:
  - Substitua o código pelo conteúdo do arquivo `wsgi.py` que criamos
  - Ajuste o caminho do projeto e o nome de usuário corretamente

### 7. Configure o Caminho dos Arquivos Estáticos

Na seção "Web" do PythonAnywhere:
- Static Files:
  - URL: `/static/` | Directory: `/home/seu_usuario/seu_projeto/staticfiles`
  - URL: `/media/` | Directory: `/home/seu_usuario/seu_projeto/media`

### 8. Atualize o arquivo `settings.py`

Se necessário, atualize o arquivo `settings.py` para adicionar seu domínio do PythonAnywhere em `ALLOWED_HOSTS`.

### 9. Reinicie o Aplicativo Web

- No PythonAnywhere, na seção "Web", clique em "Reload seu_usuario.pythonanywhere.com"

### 10. Verificação

- Acesse seu site usando o URL fornecido pelo PythonAnywhere
- Faça login com o superusuário criado para verificar se tudo está funcionando

## Solução de Problemas

- Verifique os logs de erro na seção "Web" do PythonAnywhere
- Certifique-se de que os caminhos estejam corretos no arquivo WSGI
- Verifique se todas as dependências estão instaladas corretamente
- Se tiver problemas com o banco de dados, verifique as configurações de conexão 