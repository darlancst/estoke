from django.contrib import admin
from .models import (
    Fornecedor, Produto, HistoricoPreco, Promocao, 
    Venda, NotaFiscal, Devolucao, Configuracao
)

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email')
    search_fields = ('nome', 'contato', 'email')

class HistoricoPrecoInline(admin.TabularInline):
    model = HistoricoPreco
    extra = 0
    readonly_fields = ('data',)
    can_delete = False

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade', 'preco_compra', 'preco_venda', 'margem_lucro', 'fornecedor')
    list_filter = ('fornecedor',)
    search_fields = ('nome', 'descricao')
    inlines = [HistoricoPrecoInline]
    readonly_fields = ('data_criacao', 'data_atualizacao')

@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_inicio', 'data_fim', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome',)
    filter_horizontal = ('produtos',)

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('cliente_nome', 'produto', 'quantidade', 'preco_venda', 'valor_total', 'data')
    list_filter = ('tipo_venda', 'data')
    search_fields = ('cliente_nome', 'produto__nome')
    date_hierarchy = 'data'

@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente_nome', 'valor_total', 'data_emissao', 'metodo_pagamento')
    list_filter = ('metodo_pagamento', 'data_emissao')
    search_fields = ('cliente_nome', 'numero')
    readonly_fields = ('numero', 'data_emissao')

@admin.register(Devolucao)
class DevolucaoAdmin(admin.ModelAdmin):
    list_display = ('venda', 'tipo', 'quantidade', 'status', 'data')
    list_filter = ('tipo', 'status', 'data')
    search_fields = ('venda__cliente_nome', 'motivo')
    readonly_fields = ('data',)

@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('nome_empresa', 'cnpj', 'limite_estoque_baixo')
    
    def has_add_permission(self, request):
        # Limita a criação de apenas uma instância
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
