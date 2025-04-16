"""
Configurações específicas para o ambiente PythonAnywhere
Este arquivo contém configurações que devem ser adicionadas ou modificadas
no settings.py quando implantado no PythonAnywhere.
"""

# Configurações de Banco de Dados para PythonAnywhere
# Substitua 'seu_usuario' pelo seu nome de usuário do PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'seu_usuario$estoque',
        'USER': 'seu_usuario',
        'PASSWORD': 'sua_senha_do_banco',
        'HOST': 'seu_usuario.mysql.pythonanywhere-services.com',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Configurações de segurança para produção
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'same-origin'

# Configurações de Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configurações de envio de e-mail (opcional)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Ou outro provedor SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua_senha_ou_app_password'
DEFAULT_FROM_EMAIL = 'nome_do_seu_sistema <seu_email@gmail.com>' 