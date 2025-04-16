"""
Arquivo WSGI para implantação no PythonAnywhere
"""

import os
import sys

# Adicione o diretório do projeto ao path
path = '/home/SEU_USUARIO/SEU_PROJETO'
if path not in sys.path:
    sys.path.append(path)

# Configurar variáveis de ambiente
os.environ['DJANGO_SETTINGS_MODULE'] = 'estoque_control.settings'
os.environ['DJANGO_SECRET_KEY'] = 'sua-chave-secreta-muito-segura-aqui'
os.environ['DJANGO_DEBUG'] = 'False'

# Importe a aplicação WSGI do Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 