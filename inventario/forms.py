from django import forms
from .models import (
    Fornecedor, Produto, Promocao, Venda, 
    NotaFiscal, Devolucao, Configuracao
)
from django.utils import timezone

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'telefone', 'email', 'contato', 'endereco', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'endereco': forms.Textarea(attrs={'rows': 2}),
        }

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'quantidade', 'preco_compra', 'preco_venda', 'fornecedor', 'imagem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class BuscaProdutoForm(forms.Form):
    termo = forms.CharField(label='', max_length=100, required=False, 
                           widget=forms.TextInput(attrs={
                               'placeholder': 'Buscar por nome de produto...',
                               'class': 'form-control' # Adiciona a classe form-control
                           }))
    # O campo fornecedor foi removido da interface, mas pode ser mantido no form se necessário para outras lógicas
    fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.all(),
        required=False,
        empty_label="Todos os fornecedores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class BuscaVendaForm(forms.Form):
    termo = forms.CharField(
        label='', 
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nome de cliente, nome de produto ou código da venda...',
            'class': 'form-control'
        })
    )

class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = ['nome', 'produtos', 'percentual_desconto', 'preco_promocional', 
                 'data_inicio', 'data_fim', 'ativa']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'produtos': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        percentual_desconto = cleaned_data.get('percentual_desconto')
        preco_promocional = cleaned_data.get('preco_promocional')
        
        if not percentual_desconto and not preco_promocional:
            raise forms.ValidationError(
                "Você deve fornecer um percentual de desconto ou um preço promocional."
            )
        
        if percentual_desconto and preco_promocional:
            raise forms.ValidationError(
                "Forneça apenas um: percentual de desconto OU preço promocional, não ambos."
            )
        
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim and data_inicio >= data_fim:
            raise forms.ValidationError(
                "A data de início deve ser anterior à data de término."
            )
        
        return cleaned_data

class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ['produto', 'cliente_nome', 'quantidade', 'preco_venda', 'data', 'tipo_venda'] # 'promocao' removido
        widgets = {
            'data': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            # 'promocao' widget removido
        }
    
    def __init__(self, *args, **kwargs):
        super(VendaForm, self).__init__(*args, **kwargs)
        
        # Código relacionado a 'promocao' removido
        
        # Se já existe um produto selecionado, defina o preço de venda
        if 'instance' in kwargs and kwargs['instance']:
            produto = kwargs['instance'].produto
            self.fields['preco_venda'].initial = produto.preco_venda
    
    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade')
        
        if produto and quantidade:
            if quantidade > produto.quantidade:
                raise forms.ValidationError(
                    f"Quantidade insuficiente em estoque. Disponível: {produto.quantidade}"
                )
        
        return cleaned_data

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = ['cliente_nome', 'cliente_documento', 'valor_imposto', 'metodo_pagamento', 'notas_adicionais']
        widgets = {
            'notas_adicionais': forms.Textarea(attrs={'rows': 3}),
        }

class DevolucaoForm(forms.ModelForm):
    class Meta:
        model = Devolucao
        fields = ['venda', 'tipo', 'quantidade', 'motivo', 'status', 'produto_troca']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super(DevolucaoForm, self).__init__(*args, **kwargs)
        
        # Se já existe uma venda selecionada, limite a quantidade máxima
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].venda:
            self.fields['quantidade'].widget.attrs['max'] = kwargs['instance'].venda.quantidade
    
    def clean(self):
        cleaned_data = super().clean()
        venda = cleaned_data.get('venda')
        quantidade = cleaned_data.get('quantidade')
        tipo = cleaned_data.get('tipo')
        produto_troca = cleaned_data.get('produto_troca')
        
        if venda and quantidade and quantidade > venda.quantidade:
            raise forms.ValidationError(
                f"A quantidade de devolução não pode exceder a quantidade vendida ({venda.quantidade})."
            )
        
        if tipo == 'troca' and not produto_troca:
            raise forms.ValidationError(
                "Para uma troca, você deve selecionar um produto para troca."
            )
        
        if tipo == 'troca' and produto_troca and quantidade > produto_troca.quantidade:
            raise forms.ValidationError(
                f"Quantidade insuficiente do produto de troca em estoque. Disponível: {produto_troca.quantidade}"
            )
            
        return cleaned_data

class ConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = Configuracao
        fields = ['nome_empresa', 'cnpj', 'endereco', 'telefone', 'email', 'limite_estoque_baixo', 'logo']
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3}),
        }

class PeriodoForm(forms.Form):
    PERIODO_CHOICES = [
        ('7', 'Última Semana'),
        ('30', 'Último Mês'),
        ('90', 'Último Trimestre'),
        ('365', 'Último Ano'),
        ('custom', 'Período Personalizado'),
    ]
    
    periodo = forms.ChoiceField(choices=PERIODO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    data_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    data_fim = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if periodo == 'custom':
            if not data_inicio or not data_fim:
                raise forms.ValidationError("Para período personalizado, você deve fornecer datas de início e fim.")
            
            if data_inicio and data_fim and data_inicio > data_fim:
                raise forms.ValidationError("A data de início deve ser anterior à data de término.")
        
        return cleaned_data

class AdicionarEstoqueForm(forms.Form):
    quantidade = forms.IntegerField(
        label='Quantidade a adicionar',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantidade'
        })
    )
    
    observacao = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observação (opcional)'
        })
    ) 