from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F, Sum
import uuid

class Fornecedor(models.Model):
    nome = models.CharField('Nome', max_length=100)
    cnpj = models.CharField('CNPJ', max_length=20, blank=True)
    contato = models.CharField('Nome de Contato', max_length=100, blank=True)
    telefone = models.CharField('Telefone', max_length=20)
    email = models.EmailField('E-mail')
    endereco = models.TextField('Endereço', blank=True)
    observacoes = models.TextField('Observações', blank=True)
    data_criacao = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']

class HistoricoPreco(models.Model):
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE, related_name='historico_precos')
    preco_compra = models.DecimalField('Preço de Compra', max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField('Preço de Venda', max_digits=10, decimal_places=2)
    data = models.DateTimeField('Data de Alteração', auto_now_add=True)
    
    def __str__(self):
        return f"{self.produto.nome} - {self.data.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Históricos de Preços'
        ordering = ['-data']

class Produto(models.Model):
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    quantidade = models.PositiveIntegerField('Quantidade em Estoque', default=0)
    preco_compra = models.DecimalField('Preço de Compra', max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField('Preço de Venda Sugerido', max_digits=10, decimal_places=2)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, related_name='produtos')
    data_criacao = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    imagem = models.ImageField('Imagem', upload_to='produtos/', blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']
    
    def margem_lucro(self):
        """Calcula a margem de lucro do produto"""
        if self.preco_compra > 0:
            return ((self.preco_venda - self.preco_compra) / self.preco_compra) * 100
        return 0
    
    def save(self, *args, **kwargs):
        # Verifica se é um produto novo ou se o preço foi alterado
        if self.pk:
            old_produto = Produto.objects.get(pk=self.pk)
            if old_produto.preco_compra != self.preco_compra or old_produto.preco_venda != self.preco_venda:
                # Cria um registro de histórico de preço
                HistoricoPreco.objects.create(
                    produto=self,
                    preco_compra=self.preco_compra,
                    preco_venda=self.preco_venda
                )
        else:
            # Produto novo, salva primeiro para poder criar o histórico de preço
            super().save(*args, **kwargs)
            HistoricoPreco.objects.create(
                produto=self,
                preco_compra=self.preco_compra,
                preco_venda=self.preco_venda
            )
            return
        
        super().save(*args, **kwargs)

class Promocao(models.Model):
    nome = models.CharField('Nome da Promoção', max_length=100)
    produtos = models.ManyToManyField(Produto, related_name='promocoes')
    percentual_desconto = models.DecimalField('Percentual de Desconto (%)', max_digits=5, decimal_places=2, 
                                             validators=[MinValueValidator(0), MaxValueValidator(100)],
                                             blank=True, null=True)
    preco_promocional = models.DecimalField('Preço Promocional', max_digits=10, decimal_places=2, 
                                           blank=True, null=True)
    data_inicio = models.DateTimeField('Data de Início')
    data_fim = models.DateTimeField('Data de Término')
    ativa = models.BooleanField('Ativa', default=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['-data_inicio']
    
    def esta_ativa(self):
        """Verifica se a promoção está ativa baseado na data atual e no campo ativa"""
        agora = timezone.now()
        return self.ativa and self.data_inicio <= agora <= self.data_fim

    def preco_final(self, produto):
        """Calcula o preço final do produto com desconto"""
        if self.preco_promocional:
            return self.preco_promocional
        elif self.percentual_desconto:
            desconto = (produto.preco_venda * self.percentual_desconto) / 100
            return produto.preco_venda - desconto
        return produto.preco_venda

class Venda(models.Model):
    TIPO_CHOICES = (
        ('entrega', 'Entrega'),
        ('retirada', 'Retirada'),
    )
    
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='vendas')
    cliente_nome = models.CharField('Nome do Cliente', max_length=100)
    quantidade = models.PositiveIntegerField('Quantidade Vendida')
    preco_venda = models.DecimalField('Preço de Venda', max_digits=10, decimal_places=2)
    data = models.DateTimeField('Data da Venda', default=timezone.now)
    tipo_venda = models.CharField('Tipo de Venda', max_length=10, choices=TIPO_CHOICES, default='retirada')
    promocao = models.ForeignKey(Promocao, on_delete=models.PROTECT, null=True, blank=True, related_name='vendas') # Alterado de SET_NULL para PROTECT
    
    def __str__(self):
        return f"{self.cliente_nome} - {self.produto.nome} ({self.data.strftime('%d/%m/%Y')})"
    
    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-data']
    
    def preco_com_promocao(self):
        """Retorna o preço unitário considerando a promoção, se houver"""
        if self.promocao:
            return self.promocao.preco_final(self.produto)
        return self.preco_venda
    
    def valor_total(self):
        """Calcula o valor total da venda considerando possíveis promoções"""
        return self.quantidade * self.preco_com_promocao()
    
    def valor_desconto(self):
        """Calcula o valor do desconto obtido pela promoção"""
        if self.promocao:
            desconto = self.preco_venda - self.preco_com_promocao()
            return self.quantidade * desconto
        return 0
    
    def lucro(self):
        """Calcula o lucro da venda"""
        custo_total = self.quantidade * self.produto.preco_compra
        return self.valor_total() - custo_total
    
    def margem_lucro(self):
        """Calcula a margem de lucro da venda"""
        custo_total = self.quantidade * self.produto.preco_compra
        if custo_total > 0:
            return (self.lucro() / custo_total) * 100
        return 0
    
    def save(self, *args, **kwargs):
        # Se for uma venda nova, atualiza o estoque
        if not self.pk:
            self.produto.quantidade -= self.quantidade
            self.produto.save()
        
        super().save(*args, **kwargs)

class NotaFiscal(models.Model):
    METODO_PAGAMENTO_CHOICES = (
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('transferencia', 'Transferência Bancária'),
    )
    
    numero = models.UUIDField('Número da Nota', default=uuid.uuid4, editable=False, unique=True)
    venda = models.OneToOneField(Venda, on_delete=models.CASCADE, related_name='nota_fiscal')
    cliente_nome = models.CharField('Nome do Cliente', max_length=100)
    cliente_documento = models.CharField('Documento do Cliente', max_length=20, blank=True)
    valor_total = models.DecimalField('Valor Total', max_digits=10, decimal_places=2)
    valor_imposto = models.DecimalField('Valor de Impostos', max_digits=10, decimal_places=2)
    data_emissao = models.DateTimeField('Data de Emissão', auto_now_add=True)
    metodo_pagamento = models.CharField('Método de Pagamento', max_length=20, choices=METODO_PAGAMENTO_CHOICES)
    notas_adicionais = models.TextField('Notas Adicionais', blank=True)
    
    def __str__(self):
        return f"NF-{self.numero} - {self.cliente_nome}"
    
    class Meta:
        verbose_name = 'Nota Fiscal'
        verbose_name_plural = 'Notas Fiscais'
        ordering = ['-data_emissao']

class Devolucao(models.Model):
    TIPO_CHOICES = (
        ('devolucao', 'Devolução'),
        ('troca', 'Troca'),
    )
    
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('recusada', 'Recusada'),
        ('concluida', 'Concluída'),
    )
    
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='devolucoes')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    data = models.DateTimeField('Data da Solicitação', auto_now_add=True)
    quantidade = models.PositiveIntegerField('Quantidade')
    motivo = models.TextField('Motivo')
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='pendente')
    produto_troca = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='trocas', verbose_name='Produto para Troca')
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.venda.cliente_nome} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = 'Devolução/Troca'
        verbose_name_plural = 'Devoluções/Trocas'
        ordering = ['-data']
    
    def valor_reembolso(self):
        """Calcula o valor de reembolso com base na quantidade e preço da venda original"""
        return self.quantidade * self.venda.preco_venda
    
    def save(self, *args, **kwargs):
        # Se o status mudou para aprovado ou concluído, atualiza o estoque
        if self.pk:
            old_obj = Devolucao.objects.get(pk=self.pk)
            if old_obj.status not in ['aprovada', 'concluida'] and self.status in ['aprovada', 'concluida']:
                # Se for devolução, retorna itens ao estoque
                if self.tipo == 'devolucao':
                    self.venda.produto.quantidade += self.quantidade
                    self.venda.produto.save()
                # Se for troca, diminui o estoque do produto de troca
                elif self.tipo == 'troca' and self.produto_troca:
                    # Adiciona o produto original de volta ao estoque
                    self.venda.produto.quantidade += self.quantidade
                    self.venda.produto.save()
                    
                    # Remove o produto de troca do estoque
                    self.produto_troca.quantidade -= self.quantidade
                    self.produto_troca.save()
        
        super().save(*args, **kwargs)

class Configuracao(models.Model):
    nome_empresa = models.CharField('Nome da Empresa', max_length=100)
    cnpj = models.CharField('CNPJ', max_length=20)
    endereco = models.TextField('Endereço')
    telefone = models.CharField('Telefone', max_length=20)
    email = models.EmailField('E-mail')
    limite_estoque_baixo = models.PositiveIntegerField('Limite de Estoque Baixo', default=5)
    logo = models.ImageField('Logo', upload_to='logo/', blank=True, null=True)
    
    def __str__(self):
        return self.nome_empresa
    
    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'
