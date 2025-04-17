from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # API
    path('api/fornecedores/criar/', views.api_criar_fornecedor, name='api_criar_fornecedor'),
    
    # Fornecedores
    # Produtos
    path('produtos/', views.lista_produtos, name='lista_produtos'),
    path('produtos/novo/', views.criar_produto, name='criar_produto'),
    path('produtos/<int:pk>/', views.detalhe_produto, name='detalhe_produto'),
    path('produtos/<int:pk>/editar/', views.editar_produto, name='editar_produto'),
    path('produtos/<int:pk>/excluir/', views.excluir_produto, name='excluir_produto'),
    path('produtos/<int:pk>/historico-precos/', views.historico_precos, name='historico_precos'),
    path('produtos/<int:pk>/adicionar-estoque/', views.adicionar_estoque, name='adicionar_estoque'),
    path('produtos/busca/', views.busca_produtos, name='busca_produtos'),
    
    # Promoções
    path('promocoes/', views.lista_promocoes, name='lista_promocoes'),
    path('promocoes/nova/', views.criar_promocao, name='criar_promocao'),
    path('promocoes/<int:pk>/', views.detalhe_promocao, name='detalhe_promocao'),
    path('promocoes/<int:pk>/editar/', views.editar_promocao, name='editar_promocao'),
    path('promocoes/<int:pk>/excluir/', views.excluir_promocao, name='excluir_promocao'),
    
    # Vendas
    path('vendas/', views.lista_vendas, name='lista_vendas'),
    path('vendas/nova/', views.criar_venda, name='criar_venda'),
    path('vendas/<int:pk>/', views.detalhe_venda, name='detalhe_venda'),
    path('vendas/<int:pk>/editar/', views.editar_venda, name='editar_venda'),
    path('vendas/<int:pk>/excluir/', views.excluir_venda, name='excluir_venda'),
    path('vendas/<int:pk>/gerar-nota-fiscal/', views.gerar_nota_fiscal, name='gerar_nota_fiscal'),
    path('vendas/busca/', views.busca_vendas, name='busca_vendas'),
    
    # Notas Fiscais
    path('notas-fiscais/', views.lista_notas_fiscais, name='lista_notas_fiscais'),
    path('notas-fiscais/<uuid:numero>/', views.detalhe_nota_fiscal, name='detalhe_nota_fiscal'),
    
    # Devoluções/Trocas
    path('devolucoes/', views.lista_devolucoes, name='lista_devolucoes'),
    path('devolucoes/nova/', views.criar_devolucao, name='criar_devolucao'),
    path('devolucoes/<int:pk>/', views.detalhe_devolucao, name='detalhe_devolucao'),
    path('devolucoes/<int:pk>/editar/', views.editar_devolucao, name='editar_devolucao'),
    path('devolucoes/<int:pk>/excluir/', views.excluir_devolucao, name='excluir_devolucao'),
    path('devolucoes/<int:pk>/aprovar/', views.aprovar_devolucao, name='aprovar_devolucao'),
    path('devolucoes/<int:pk>/recusar/', views.recusar_devolucao, name='recusar_devolucao'),
    
    # Configurações
    path('configuracoes/', views.configuracoes, name='configuracoes'),
] 