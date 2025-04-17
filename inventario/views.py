from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, FloatField, Q, Count, DecimalField
from django.db.models.functions import TruncDay, TruncMonth
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Fornecedor, Produto, HistoricoPreco, Promocao, 
    Venda, NotaFiscal, Devolucao, Configuracao
)
from .forms import (
    FornecedorForm, ProdutoForm, BuscaProdutoForm, PromocaoForm,
    VendaForm, NotaFiscalForm, DevolucaoForm, ConfiguracaoForm,
    PeriodoForm, BuscaVendaForm, AdicionarEstoqueForm
)

# Funções utilitárias
def get_periodo_datas(periodo_form):
    """Retorna as datas de início e fim baseado no formulário de período"""
    hoje = timezone.now().date()
    
    if periodo_form.is_valid():
        periodo = periodo_form.cleaned_data['periodo']
        
        if periodo == 'custom':
            data_inicio = periodo_form.cleaned_data['data_inicio']
            data_fim = periodo_form.cleaned_data['data_fim']
        else:
            dias = int(periodo)
            data_inicio = hoje - timedelta(days=dias)
            data_fim = hoje
    else:
        # Padrão: último mês
        data_inicio = hoje - timedelta(days=30)
        data_fim = hoje
        
    return data_inicio, data_fim

def get_configuracao():
    """Retorna a configuração do sistema ou cria uma padrão se não existir"""
    config, created = Configuracao.objects.get_or_create(
        pk=1,
        defaults={
            'nome_empresa': 'Minha Empresa',
            'cnpj': '00.000.000/0001-00',
            'endereco': 'Endereço da Empresa',
            'telefone': '(00) 00000-0000',
            'email': 'contato@empresa.com',
            'limite_estoque_baixo': 5
        }
    )
    return config

# Views do Dashboard
def dashboard(request):
    configuracao = get_configuracao()
    
    # Formulário de período para estatísticas
    periodo_form = PeriodoForm(request.GET or None)
    data_inicio, data_fim = get_periodo_datas(periodo_form)
    
    # Estatísticas gerais
    total_produtos = Produto.objects.count()
    valor_total_estoque = Produto.objects.aggregate(
        total=Sum(F('quantidade') * F('preco_compra'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    # Estatísticas do período
    vendas_periodo = Venda.objects.filter(data__date__range=[data_inicio, data_fim])
    num_vendas = vendas_periodo.count()
    receita_total = vendas_periodo.aggregate(
        total=Sum(F('quantidade') * F('preco_venda'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    # Cálculo de lucro
    lucro_total = Decimal('0')
    for venda in vendas_periodo:
        lucro_total += venda.lucro()
    
    # Dados para o gráfico de receita e lucro
    # Determina a agregação (diária ou mensal) com base na duração do período
    delta = data_fim - data_inicio
    if delta.days <= 60:  # Se o período for <= 60 dias, usamos agregação diária
        vendas_por_dia = vendas_periodo.annotate(
            dia=TruncDay('data')
        ).values('dia').annotate(
            receita=Sum(F('quantidade') * F('preco_venda'), output_field=DecimalField()),
            custo=Sum(F('quantidade') * F('produto__preco_compra'), output_field=DecimalField())
        ).order_by('dia')
        
        labels = [venda['dia'].strftime('%d/%m/%Y') for venda in vendas_por_dia]
        receitas = [str(venda['receita'] or Decimal('0')) for venda in vendas_por_dia]
        lucros = [str((venda['receita'] or Decimal('0')) - (venda['custo'] or Decimal('0'))) for venda in vendas_por_dia]
    else:  # Para períodos maiores, usamos agregação mensal
        vendas_por_mes = vendas_periodo.annotate(
            mes=TruncMonth('data')
        ).values('mes').annotate(
            receita=Sum(F('quantidade') * F('preco_venda'), output_field=DecimalField()),
            custo=Sum(F('quantidade') * F('produto__preco_compra'), output_field=DecimalField())
        ).order_by('mes')
        
        labels = [venda['mes'].strftime('%m/%Y') for venda in vendas_por_mes]
        receitas = [str(venda['receita'] or Decimal('0')) for venda in vendas_por_mes]
        lucros = [str((venda['receita'] or Decimal('0')) - (venda['custo'] or Decimal('0'))) for venda in vendas_por_mes]
    
    # Top 10 produtos mais lucrativos
    produtos_lucrativos = []
    
    # Agrupamos as vendas por produto e calculamos o lucro total
    vendas_por_produto = vendas_periodo.values('produto').annotate(
        quantidade_total=Sum('quantidade'),
        receita_total=Sum(F('quantidade') * F('preco_venda'), output_field=DecimalField())
    ).order_by('-receita_total')[:10]
    
    for item in vendas_por_produto:
        produto = Produto.objects.get(pk=item['produto'])
        custo_total = item['quantidade_total'] * produto.preco_compra
        lucro = item['receita_total'] - custo_total
        
        produtos_lucrativos.append({
            'nome': produto.nome,
            'lucro': lucro,
            'quantidade': item['quantidade_total']
        })
    
    # Ordenar por lucro
    produtos_lucrativos.sort(key=lambda x: x['lucro'], reverse=True)
    
    # Produtos com estoque baixo
    limite_estoque = configuracao.limite_estoque_baixo
    produtos_estoque_baixo = Produto.objects.filter(quantidade__lte=limite_estoque).order_by('quantidade')
    
    context = {
        'configuracao': configuracao,
        'periodo_form': periodo_form,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_produtos': total_produtos,
        'valor_total_estoque': valor_total_estoque,
        'num_vendas': num_vendas,
        'receita_total': receita_total,
        'lucro_total': lucro_total,
        'chart_labels': json.dumps(labels),
        'chart_receitas': json.dumps(receitas),
        'chart_lucros': json.dumps(lucros),
        'produtos_lucrativos': produtos_lucrativos,
        'produtos_estoque_baixo': produtos_estoque_baixo,
    }
    
    return render(request, 'inventario/dashboard.html', context)

# Views de Fornecedores
def lista_fornecedores(request):
    fornecedores = Fornecedor.objects.all()
    return render(request, 'inventario/fornecedores/lista.html', {'fornecedores': fornecedores})

def criar_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor criado com sucesso!')
            return redirect('inventario:lista_fornecedores')
    else:
        form = FornecedorForm()
    
    return render(request, 'inventario/fornecedores/form.html', {'form': form, 'titulo': 'Novo Fornecedor'})

def detalhe_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    produtos = fornecedor.produtos.all()
    
    return render(request, 'inventario/fornecedores/detalhe.html', {
        'fornecedor': fornecedor,
        'produtos': produtos
    })

def editar_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado com sucesso!')
            return redirect('inventario:detalhe_fornecedor', pk=fornecedor.pk)
    else:
        form = FornecedorForm(instance=fornecedor)
    
    return render(request, 'inventario/fornecedores/form.html', {
        'form': form, 
        'titulo': 'Editar Fornecedor',
        'fornecedor': fornecedor
    })

def excluir_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    # Verificar se há produtos associados a este fornecedor
    produtos_associados = fornecedor.produtos.all()
    
    if request.method == 'POST':
        if produtos_associados.exists():
            messages.error(request, f'Não é possível excluir o fornecedor {fornecedor.nome} porque existem produtos associados a ele. Remova ou reatribua os produtos primeiro.')
            return redirect('inventario:detalhe_fornecedor', pk=fornecedor.pk)
        
        fornecedor.delete()
        messages.success(request, 'Fornecedor excluído com sucesso!')
        return redirect('inventario:lista_fornecedores')
    
    context = {
        'fornecedor': fornecedor,
        'produtos_associados': produtos_associados
    }
    return render(request, 'inventario/fornecedores/confirmar_exclusao.html', context)

# Views de Produtos
def lista_produtos(request):
    produtos = Produto.objects.all()
    form = BuscaProdutoForm()
    configuracao = get_configuracao()
    
    # Adicionar promoções ativas para cada produto
    agora = timezone.now()
    for produto in produtos:
        produto.promocoes_ativas = produto.promocoes.filter(
            ativa=True,
            data_inicio__lte=agora,
            data_fim__gte=agora
        )
    
    return render(request, 'inventario/produtos/lista.html', {
        'produtos': produtos,
        'form': form,
        'configuracao': configuracao
    })

def busca_produtos(request):
    form = BuscaProdutoForm(request.GET)
    termo = request.GET.get('termo', '')
    fornecedor_id = request.GET.get('fornecedor', '')
    configuracao = get_configuracao()
    
    produtos = Produto.objects.all()
    
    if termo:
        produtos = produtos.filter(Q(nome__icontains=termo) | Q(descricao__icontains=termo))
    
    if fornecedor_id:
        produtos = produtos.filter(fornecedor_id=fornecedor_id)
    
    # Adicionar promoções ativas para cada produto
    agora = timezone.now()
    for produto in produtos:
        produto.promocoes_ativas = produto.promocoes.filter(
            ativa=True,
            data_inicio__lte=agora,
            data_fim__gte=agora
        )
    
    return render(request, 'inventario/produtos/lista.html', {
        'produtos': produtos,
        'form': form,
        'configuracao': configuracao
    })

def criar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('inventario:lista_produtos')
    else:
        form = ProdutoForm()
    
    return render(request, 'inventario/produtos/form.html', {'form': form, 'titulo': 'Novo Produto'})

def detalhe_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    historico = produto.historico_precos.all()[:10]  # Últimos 10 registros
    promocoes = produto.promocoes.filter(data_fim__gte=timezone.now())  # Promoções ativas ou futuras
    
    # Calcular preços promocionais para cada promoção
    promocoes_com_precos = []
    for promocao in promocoes:
        promocoes_com_precos.append({
            'promocao': promocao,
            'preco_final': promocao.preco_final(produto)
        })
    
    return render(request, 'inventario/produtos/detalhe.html', {
        'produto': produto,
        'historico': historico,
        'promocoes': promocoes,
        'promocoes_com_precos': promocoes_com_precos
    })

def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('inventario:detalhe_produto', pk=produto.pk)
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'inventario/produtos/form.html', {
        'form': form, 
        'titulo': 'Editar Produto',
        'produto': produto
    })

def excluir_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('inventario:lista_produtos')
    
    return render(request, 'inventario/produtos/confirmar_exclusao.html', {'produto': produto})

def historico_precos(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    historico = produto.historico_precos.all()
    
    return render(request, 'inventario/produtos/historico_precos.html', {
        'produto': produto,
        'historico': historico
    })

def adicionar_estoque(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        form = AdicionarEstoqueForm(request.POST)
        if form.is_valid():
            quantidade = form.cleaned_data['quantidade']
            observacao = form.cleaned_data['observacao']
            
            # Adicionar ao estoque
            produto.quantidade += quantidade
            produto.save()
            
            messages.success(
                request, 
                f'Adicionado {quantidade} item(s) ao estoque de {produto.nome}. Estoque atual: {produto.quantidade}'
            )
            return redirect('inventario:lista_produtos')
    else:
        form = AdicionarEstoqueForm()
    
    return render(request, 'inventario/produtos/adicionar_estoque.html', {
        'form': form,
        'produto': produto
    })

# Views de Promoções
def lista_promocoes(request):
    promocoes = Promocao.objects.all()
    return render(request, 'inventario/promocoes/lista.html', {'promocoes': promocoes})

def criar_promocao(request):
    if request.method == 'POST':
        form = PromocaoForm(request.POST)
        if form.is_valid():
            promocao = form.save()
            messages.success(request, 'Promoção criada com sucesso!')
            return redirect('inventario:detalhe_promocao', pk=promocao.pk)
    else:
        form = PromocaoForm()
    
    return render(request, 'inventario/promocoes/form.html', {'form': form, 'titulo': 'Nova Promoção'})

def detalhe_promocao(request, pk):
    promocao = get_object_or_404(Promocao, pk=pk)
    produtos = promocao.produtos.all()
    
    # Calcular preços promocionais para cada produto
    produtos_com_precos = []
    for produto in produtos:
        produtos_com_precos.append({
            'produto': produto,
            'preco_promocional': promocao.preco_final(produto)
        })
    
    return render(request, 'inventario/promocoes/detalhe.html', {
        'promocao': promocao,
        'produtos': produtos,
        'produtos_com_precos': produtos_com_precos
    })

def editar_promocao(request, pk):
    promocao = get_object_or_404(Promocao, pk=pk)
    
    if request.method == 'POST':
        form = PromocaoForm(request.POST, instance=promocao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Promoção atualizada com sucesso!')
            return redirect('inventario:detalhe_promocao', pk=promocao.pk)
    else:
        form = PromocaoForm(instance=promocao)
    
    return render(request, 'inventario/promocoes/form.html', {
        'form': form, 
        'titulo': 'Editar Promoção',
        'promocao': promocao
    })

def excluir_promocao(request, pk):
    promocao = get_object_or_404(Promocao, pk=pk)
    
    if request.method == 'POST':
        promocao.ativa = False
        promocao.save()
        messages.success(request, 'Promoção desativada com sucesso!')
        return redirect('inventario:lista_promocoes')
    
    return render(request, 'inventario/promocoes/confirmar_exclusao.html', {'promocao': promocao})

# Views de Vendas
def lista_vendas(request):
    vendas = Venda.objects.all()
    periodo_form = PeriodoForm(request.GET or None)
    busca_form = BuscaVendaForm()
    
    if periodo_form.is_valid():
        data_inicio, data_fim = get_periodo_datas(periodo_form)
        vendas = vendas.filter(data__date__range=[data_inicio, data_fim])
    
    return render(request, 'inventario/vendas/lista.html', {
        'vendas': vendas,
        'periodo_form': periodo_form,
        'form': busca_form
    })

def busca_vendas(request):
    form = BuscaVendaForm(request.GET)
    periodo_form = PeriodoForm(request.GET or None)
    termo = request.GET.get('termo', '')
    
    vendas = Venda.objects.all()
    
    # Aplicar filtro de período
    if periodo_form.is_valid():
        data_inicio, data_fim = get_periodo_datas(periodo_form)
        vendas = vendas.filter(data__date__range=[data_inicio, data_fim])
    
    # Aplicar filtro de termo de busca (unificado para cliente, produto e ID)
    if termo:
        # Verificar se o termo é um número inteiro (possível ID)
        try:
            id_venda = int(termo)
            vendas_por_id = Venda.objects.filter(id=id_venda)
            if vendas_por_id.exists():
                return render(request, 'inventario/vendas/lista.html', {
                    'vendas': vendas_por_id,
                    'periodo_form': periodo_form,
                    'form': form
                })
        except ValueError:
            pass
        
        # Busca por nome de cliente ou produto
        vendas = vendas.filter(
            Q(cliente_nome__icontains=termo) | 
            Q(produto__nome__icontains=termo)
        )
    
    return render(request, 'inventario/vendas/lista.html', {
        'vendas': vendas,
        'periodo_form': periodo_form,
        'form': form
    })

def criar_venda(request):
    if request.method == 'POST':
        form = VendaForm(request.POST)
        if form.is_valid():
            # Salva a venda sem commit para poder adicionar a promoção
            venda = form.save(commit=False)

            # Busca a melhor promoção ativa para o produto na data da venda
            produto = venda.produto
            data_venda = venda.data # Usar a data do formulário ou a data atual se não especificada

            promocao_ativa = Promocao.objects.filter(
                produtos=produto,
                ativa=True,
                data_inicio__lte=data_venda.date(), # Comparar apenas com a data
                data_fim__gte=data_venda.date()    # Comparar apenas com a data
            ).order_by('-percentual_desconto', 'preco_promocional').first() # Prioriza maior desconto percentual, depois menor preço fixo

            venda.promocao = promocao_ativa # Associa a promoção encontrada (ou None)

            # Agora salva a venda com a promoção associada
            venda.save()
            form.save_m2m() # Necessário se o formulário tiver campos ManyToMany (não é o caso aqui, mas boa prática)

            messages.success(request, 'Venda registrada com sucesso!')
            return redirect('inventario:detalhe_venda', pk=venda.pk)
            venda.save()
            
            messages.success(request, 'Venda registrada com sucesso!')
            return redirect('inventario:detalhe_venda', pk=venda.pk)
    else:
        form = VendaForm()
        
        # Se um produto foi especificado, preencha o preço de venda sugerido
        produto_id = request.GET.get('produto')
        if produto_id:
            try:
                produto = Produto.objects.get(pk=produto_id)
                form.fields['produto'].initial = produto.pk
                form.fields['preco_venda'].initial = produto.preco_venda
            except Produto.DoesNotExist:
                pass
    
    return render(request, 'inventario/vendas/form.html', {'form': form, 'titulo': 'Nova Venda'})

def detalhe_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    
    # Verifica se a venda já tem nota fiscal
    try:
        nota_fiscal = venda.nota_fiscal
        has_nota = True
    except NotaFiscal.DoesNotExist:
        has_nota = False
        nota_fiscal = None
    
    # Verifica se a venda tem devoluções
    devolucoes = venda.devolucoes.all()
    
    return render(request, 'inventario/vendas/detalhe.html', {
        'venda': venda,
        'has_nota': has_nota,
        'nota_fiscal': nota_fiscal,
        'devolucoes': devolucoes
    })

def editar_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    
    # Se já existir nota fiscal, não permitir edição
    try:
        venda.nota_fiscal
        messages.error(request, 'Não é possível editar uma venda que já possui nota fiscal.')
        return redirect('inventario:detalhe_venda', pk=venda.pk)
    except NotaFiscal.DoesNotExist:
        pass
    
    # Se já existir devolução, não permitir edição
    if venda.devolucoes.exists():
        messages.error(request, 'Não é possível editar uma venda que já possui devoluções registradas.')
        return redirect('inventario:detalhe_venda', pk=venda.pk)

    if request.method == 'POST':
        form = VendaForm(request.POST, instance=venda)
        if form.is_valid():
            # Salva a venda sem commit para poder atualizar a promoção
            venda_atualizada = form.save(commit=False)

            # Busca a melhor promoção ativa para o produto na data da venda
            produto = venda_atualizada.produto
            data_venda = venda_atualizada.data # Usar a data do formulário

            promocao_ativa = Promocao.objects.filter(
                produtos=produto,
                ativa=True,
                data_inicio__lte=data_venda.date(), # Comparar apenas com a data
                data_fim__gte=data_venda.date()    # Comparar apenas com a data
            ).order_by('-percentual_desconto', 'preco_promocional').first()

            venda_atualizada.promocao = promocao_ativa # Atualiza a promoção associada

            # Agora salva a venda com a promoção atualizada
            venda_atualizada.save()
            form.save_m2m() # Boa prática

            messages.success(request, 'Venda atualizada com sucesso!')
            return redirect('inventario:detalhe_venda', pk=venda_atualizada.pk)
    else:
        form = VendaForm(instance=venda)

    return render(request, 'inventario/vendas/form.html', {
        'form': form,
        'titulo': 'Editar Venda',
        'venda': venda
    })
    if venda.devolucoes.exists():
        messages.error(request, 'Não é possível editar uma venda que possui devoluções registradas.')
        return redirect('inventario:detalhe_venda', pk=venda.pk)
    
    if request.method == 'POST':
        form = VendaForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venda atualizada com sucesso!')
            return redirect('inventario:detalhe_venda', pk=venda.pk)
    else:
        form = VendaForm(instance=venda)
    
    return render(request, 'inventario/vendas/form.html', {
        'form': form, 
        'titulo': 'Editar Venda',
        'venda': venda
    })

def excluir_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    
    # Se já existir nota fiscal, não permitir exclusão
    try:
        venda.nota_fiscal
        messages.error(request, 'Não é possível excluir uma venda que já possui nota fiscal.')
        return redirect('inventario:detalhe_venda', pk=venda.pk)
    except NotaFiscal.DoesNotExist:
        pass
    
    devolucoes_associadas = venda.devolucoes.all()
    
    if request.method == 'POST':
        # Devolver os produtos ao estoque original da venda
        produto = venda.produto
        produto.quantidade += venda.quantidade
        produto.save()
        
        # Informar sobre exclusão de devoluções
        if devolucoes_associadas:
            messages.warning(request, 'As devoluções/trocas associadas a esta venda também foram excluídas.')
            # Excluir devoluções associadas (se necessário, ajustar estoque aqui)
            # Nota: A lógica atual do Devolucao.save() pode precisar de revisão
            # dependendo de como o estoque deve ser tratado ao excluir uma devolução
            # que já foi processada.
            devolucoes_associadas.delete()
            
        venda.delete()
        messages.success(request, 'Venda excluída com sucesso!')
        return redirect('inventario:lista_vendas')
    
    context = {
        'venda': venda,
        'devolucoes_associadas': devolucoes_associadas
    }
    return render(request, 'inventario/vendas/confirmar_exclusao.html', context)

def gerar_nota_fiscal(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    
    # Verifica se já existe nota fiscal para esta venda
    try:
        venda.nota_fiscal
        messages.error(request, 'Esta venda já possui uma nota fiscal.')
        return redirect('inventario:detalhe_venda', pk=venda.pk)
    except NotaFiscal.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            nota_fiscal = form.save(commit=False)
            nota_fiscal.venda = venda
            nota_fiscal.valor_total = venda.valor_total()
            nota_fiscal.save()
            
            messages.success(request, 'Nota fiscal gerada com sucesso!')
            return redirect('inventario:detalhe_nota_fiscal', numero=nota_fiscal.numero)
    else:
        # Pré-preencher o formulário com dados da venda
        initial = {
            'cliente_nome': venda.cliente_nome,
            'valor_imposto': venda.valor_total() * 0.12,  # 12% de imposto como exemplo
        }
        form = NotaFiscalForm(initial=initial)
    
    return render(request, 'inventario/notas_fiscais/form.html', {
        'form': form,
        'venda': venda,
        'titulo': 'Gerar Nota Fiscal'
    })

# Views de Notas Fiscais
def lista_notas_fiscais(request):
    notas_fiscais = NotaFiscal.objects.all()
    periodo_form = PeriodoForm(request.GET or None)
    
    if periodo_form.is_valid():
        data_inicio, data_fim = get_periodo_datas(periodo_form)
        notas_fiscais = notas_fiscais.filter(data_emissao__date__range=[data_inicio, data_fim])
    
    return render(request, 'inventario/notas_fiscais/lista.html', {
        'notas_fiscais': notas_fiscais,
        'periodo_form': periodo_form
    })

def detalhe_nota_fiscal(request, numero):
    nota_fiscal = get_object_or_404(NotaFiscal, numero=numero)
    return render(request, 'inventario/notas_fiscais/detalhe.html', {'nota_fiscal': nota_fiscal})

# Views de Devoluções/Trocas
def lista_devolucoes(request):
    devolucoes = Devolucao.objects.all()
    return render(request, 'inventario/devolucoes/lista.html', {'devolucoes': devolucoes})

def criar_devolucao(request):
    if request.method == 'POST':
        form = DevolucaoForm(request.POST)
        if form.is_valid():
            devolucao = form.save()
            messages.success(request, 'Devolução/Troca registrada com sucesso!')
            return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)
    else:
        form = DevolucaoForm()
        
        # Se uma venda foi especificada, preencha o formulário
        venda_id = request.GET.get('venda')
        if venda_id:
            try:
                venda = Venda.objects.get(pk=venda_id)
                form.fields['venda'].initial = venda.pk
                form.fields['quantidade'].initial = venda.quantidade
            except Venda.DoesNotExist:
                pass
    
    return render(request, 'inventario/devolucoes/form.html', {'form': form, 'titulo': 'Nova Devolução/Troca'})

def detalhe_devolucao(request, pk):
    devolucao = get_object_or_404(Devolucao, pk=pk)
    return render(request, 'inventario/devolucoes/detalhe.html', {'devolucao': devolucao})

def editar_devolucao(request, pk):
    devolucao = get_object_or_404(Devolucao, pk=pk)
    
    # Se a devolução já estiver concluída ou aprovada, não permitir edição
    if devolucao.status in ['aprovada', 'concluida']:
        messages.error(request, 'Não é possível editar uma devolução/troca que já foi aprovada ou concluída.')
        return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)
    
    if request.method == 'POST':
        form = DevolucaoForm(request.POST, instance=devolucao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Devolução/Troca atualizada com sucesso!')
            return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)
    else:
        form = DevolucaoForm(instance=devolucao)
    
    return render(request, 'inventario/devolucoes/form.html', {
        'form': form, 
        'titulo': 'Editar Devolução/Troca',
        'devolucao': devolucao
    })

def excluir_devolucao(request, pk):
    devolucao = get_object_or_404(Devolucao, pk=pk)
    
    if request.method == 'POST':
        # Verificar se a exclusão precisa reverter estoque
        reverter_estoque = False
        if devolucao.status in ['aprovada', 'concluida']:
            reverter_estoque = True
        
        # Reverter as alterações de estoque se necessário
        if reverter_estoque:
            produto_original = devolucao.venda.produto
            if devolucao.tipo == 'devolucao':
                # Se foi devolução, remover os itens que voltaram ao estoque
                produto_original.quantidade -= devolucao.quantidade
                produto_original.save()
                messages.warning(request, f'Estoque do produto {produto_original.nome} revertido.')
            elif devolucao.tipo == 'troca' and devolucao.produto_troca:
                # Se foi troca, remover itens do produto original E devolver itens do produto de troca
                produto_original.quantidade -= devolucao.quantidade # Remove o que voltou
                produto_original.save()
                
                produto_troca = devolucao.produto_troca
                produto_troca.quantidade += devolucao.quantidade # Devolve o que saiu
                produto_troca.save()
                messages.warning(request, f'Estoques dos produtos {produto_original.nome} e {produto_troca.nome} revertidos.')
        
        devolucao.delete()
        messages.success(request, 'Devolução/Troca excluída com sucesso!')
        return redirect('inventario:lista_devolucoes')
    
    return render(request, 'inventario/devolucoes/confirmar_exclusao.html', {'devolucao': devolucao})

@require_POST
def aprovar_devolucao(request, pk):
    devolucao = get_object_or_404(Devolucao, pk=pk)
    
    # Verificar se já está aprovada ou concluída
    if devolucao.status != 'pendente':
        messages.error(request, 'Esta devolução/troca não está mais pendente de aprovação.')
        return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)
    
    # Aprovar a devolução
    devolucao.status = 'aprovada'
    devolucao.save()
    
    messages.success(request, 'Devolução/Troca aprovada com sucesso!')
    return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)

@require_POST
def recusar_devolucao(request, pk):
    devolucao = get_object_or_404(Devolucao, pk=pk)
    
    # Verificar se já está aprovada ou concluída
    if devolucao.status != 'pendente':
        messages.error(request, 'Esta devolução/troca não está mais pendente de aprovação.')
        return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)
    
    # Recusar a devolução
    devolucao.status = 'recusada'
    devolucao.save()
    
    messages.success(request, 'Devolução/Troca recusada.')
    return redirect('inventario:detalhe_devolucao', pk=devolucao.pk)

# Views de Configurações
def configuracoes(request):
    config = get_configuracao()
    
    if request.method == 'POST':
        form = ConfiguracaoForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações atualizadas com sucesso!')
            return redirect('inventario:configuracoes')
    else:
        form = ConfiguracaoForm(instance=config)
    
    return render(request, 'inventario/configuracoes.html', {'form': form, 'config': config})

@require_POST
def api_criar_fornecedor(request):
    """API para criar fornecedor rapidamente"""
    try:
        data = json.loads(request.body)
        nome = data.get('nome', '')
        telefone = data.get('telefone', '')
        
        if not nome:
            return JsonResponse({'success': False, 'error': 'Nome do fornecedor é obrigatório'})
        
        # Criar o fornecedor com campos básicos
        fornecedor = Fornecedor.objects.create(
            nome=nome,
            telefone=telefone if telefone else '',
            email='',  # Campo obrigatório mas não mostrado no modal
        )
        
        return JsonResponse({
            'success': True, 
            'fornecedor': {
                'id': fornecedor.id,
                'nome': fornecedor.nome
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
