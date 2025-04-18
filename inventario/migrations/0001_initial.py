# Generated by Django 5.1.7 on 2025-04-09 15:33

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Configuracao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_empresa', models.CharField(max_length=100, verbose_name='Nome da Empresa')),
                ('cnpj', models.CharField(max_length=20, verbose_name='CNPJ')),
                ('endereco', models.TextField(verbose_name='Endereço')),
                ('telefone', models.CharField(max_length=20, verbose_name='Telefone')),
                ('email', models.EmailField(max_length=254, verbose_name='E-mail')),
                ('limite_estoque_baixo', models.PositiveIntegerField(default=5, verbose_name='Limite de Estoque Baixo')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='logo/', verbose_name='Logo')),
            ],
            options={
                'verbose_name': 'Configuração',
                'verbose_name_plural': 'Configurações',
            },
        ),
        migrations.CreateModel(
            name='Fornecedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('contato', models.CharField(blank=True, max_length=100, verbose_name='Nome de Contato')),
                ('telefone', models.CharField(max_length=20, verbose_name='Telefone')),
                ('email', models.EmailField(max_length=254, verbose_name='E-mail')),
                ('endereco', models.TextField(blank=True, verbose_name='Endereço')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Última Atualização')),
            ],
            options={
                'verbose_name': 'Fornecedor',
                'verbose_name_plural': 'Fornecedores',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('quantidade', models.PositiveIntegerField(default=0, verbose_name='Quantidade em Estoque')),
                ('preco_compra', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço de Compra')),
                ('preco_venda', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço de Venda Sugerido')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Última Atualização')),
                ('imagem', models.ImageField(blank=True, null=True, upload_to='produtos/', verbose_name='Imagem')),
                ('fornecedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='inventario.fornecedor')),
            ],
            options={
                'verbose_name': 'Produto',
                'verbose_name_plural': 'Produtos',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='HistoricoPreco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preco_compra', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço de Compra')),
                ('preco_venda', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço de Venda')),
                ('data', models.DateTimeField(auto_now_add=True, verbose_name='Data de Alteração')),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico_precos', to='inventario.produto')),
            ],
            options={
                'verbose_name': 'Histórico de Preço',
                'verbose_name_plural': 'Históricos de Preços',
                'ordering': ['-data'],
            },
        ),
        migrations.CreateModel(
            name='Promocao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da Promoção')),
                ('percentual_desconto', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Percentual de Desconto (%)')),
                ('preco_promocional', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço Promocional')),
                ('data_inicio', models.DateTimeField(verbose_name='Data de Início')),
                ('data_fim', models.DateTimeField(verbose_name='Data de Término')),
                ('ativa', models.BooleanField(default=True, verbose_name='Ativa')),
                ('produtos', models.ManyToManyField(related_name='promocoes', to='inventario.produto')),
            ],
            options={
                'verbose_name': 'Promoção',
                'verbose_name_plural': 'Promoções',
                'ordering': ['-data_inicio'],
            },
        ),
        migrations.CreateModel(
            name='Venda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente_nome', models.CharField(max_length=100, verbose_name='Nome do Cliente')),
                ('quantidade', models.PositiveIntegerField(verbose_name='Quantidade Vendida')),
                ('preco_venda', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço de Venda')),
                ('data', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Data da Venda')),
                ('tipo_venda', models.CharField(choices=[('entrega', 'Entrega'), ('retirada', 'Retirada')], default='retirada', max_length=10, verbose_name='Tipo de Venda')),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vendas', to='inventario.produto')),
                ('promocao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vendas', to='inventario.promocao')),
            ],
            options={
                'verbose_name': 'Venda',
                'verbose_name_plural': 'Vendas',
                'ordering': ['-data'],
            },
        ),
        migrations.CreateModel(
            name='NotaFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Número da Nota')),
                ('cliente_nome', models.CharField(max_length=100, verbose_name='Nome do Cliente')),
                ('cliente_documento', models.CharField(blank=True, max_length=20, verbose_name='Documento do Cliente')),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor Total')),
                ('valor_imposto', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor de Impostos')),
                ('data_emissao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Emissão')),
                ('metodo_pagamento', models.CharField(choices=[('dinheiro', 'Dinheiro'), ('cartao_credito', 'Cartão de Crédito'), ('cartao_debito', 'Cartão de Débito'), ('pix', 'PIX'), ('boleto', 'Boleto'), ('transferencia', 'Transferência Bancária')], max_length=20, verbose_name='Método de Pagamento')),
                ('notas_adicionais', models.TextField(blank=True, verbose_name='Notas Adicionais')),
                ('venda', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='nota_fiscal', to='inventario.venda')),
            ],
            options={
                'verbose_name': 'Nota Fiscal',
                'verbose_name_plural': 'Notas Fiscais',
                'ordering': ['-data_emissao'],
            },
        ),
        migrations.CreateModel(
            name='Devolucao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('devolucao', 'Devolução'), ('troca', 'Troca')], max_length=10, verbose_name='Tipo')),
                ('data', models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')),
                ('quantidade', models.PositiveIntegerField(verbose_name='Quantidade')),
                ('motivo', models.TextField(verbose_name='Motivo')),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('aprovada', 'Aprovada'), ('recusada', 'Recusada'), ('concluida', 'Concluída')], default='pendente', max_length=10, verbose_name='Status')),
                ('produto_troca', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trocas', to='inventario.produto', verbose_name='Produto para Troca')),
                ('venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devolucoes', to='inventario.venda')),
            ],
            options={
                'verbose_name': 'Devolução/Troca',
                'verbose_name_plural': 'Devoluções/Trocas',
                'ordering': ['-data'],
            },
        ),
    ]
