from django.contrib import admin
from .models import (
    Fornecedor, Produto, Promocao, 
    Venda, NotaFiscal, Devolucao, Configuracao, Lote
)

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email')
    search_fields = ('nome', 'contato', 'email')

class LoteInline(admin.TabularInline):
    model = Lote
    extra = 1  # Permite adicionar um lote por vez

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade', 'preco_compra', 'preco_venda', 'fornecedor')
    list_filter = ('lotes__fornecedor',)
    search_fields = ('nome', 'descricao')
    inlines = [LoteInline]
    readonly_fields = ('data_criacao', 'data_atualizacao')

    def get_queryset(self, request):
        # Otimiza as consultas para buscar os dados dos lotes
        return super().get_queryset(request).prefetch_related('lotes__fornecedor')

    def quantidade(self, obj):
        return obj.quantidade
    quantidade.short_description = 'Quantidade em Estoque'

    def preco_compra(self, obj):
        return obj.preco_compra
    preco_compra.short_description = 'Preço de Compra (Lote Ativo)'
    
    def preco_venda(self, obj):
        return obj.preco_venda
    preco_venda.short_description = 'Preço de Venda (Lote Ativo)'

    def fornecedor(self, obj):
        return obj.fornecedor
    fornecedor.short_description = 'Fornecedor (Lote Ativo)'

@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_inicio', 'data_fim', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome',)
    filter_horizontal = ('produtos',)

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('cliente_nome', 'produto', 'quantidade', 'preco_venda', 'valor_total_efetivo', 'data', 'status')
    list_filter = ('tipo_venda', 'data', 'status')
    search_fields = ('cliente_nome', 'produto__nome')
    date_hierarchy = 'data'
    readonly_fields = ('promocao',)

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
