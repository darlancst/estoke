from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F, Sum
import uuid
from decimal import Decimal

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

class Produto(models.Model):
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    data_criacao = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    imagem = models.ImageField('Imagem', upload_to='produtos/', blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    @property
    def quantidade(self):
        """Retorna a quantidade total em estoque somando todos os lotes."""
        return self.lotes.aggregate(total=Sum('quantidade'))['total'] or 0

    @property
    def lote_ativo(self):
        """Retorna o lote mais antigo com estoque disponível."""
        return self.lotes.filter(quantidade__gt=0).order_by('data_entrada').first()

    @property
    def preco_compra(self):
        lote = self.lote_ativo
        return lote.preco_compra if lote else None

    @property
    def preco_venda(self):
        lote = self.lote_ativo
        return lote.preco_venda if lote else None
    
    @property
    def fornecedor(self):
         lote = self.lote_ativo
         return lote.fornecedor if lote else None

class Lote(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='lotes')
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    quantidade = models.PositiveIntegerField('Quantidade')
    preco_compra = models.DecimalField('Preço de Compra', max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField('Preço de Venda', max_digits=10, decimal_places=2)
    data_entrada = models.DateTimeField('Data de Entrada', default=timezone.now)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['data_entrada']

    def __str__(self):
        return f"Lote de {self.produto.nome} ({self.quantidade} un.)"

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
        ('loja', 'Loja'),
    )
    STATUS_CHOICES = (
        ('concluida', 'Concluída'),
        ('devolvida', 'Devolvida'),
    )
    
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas')
    produto_nome_historico = models.CharField('Nome do Produto no ato da venda', max_length=100, null=True, blank=True)
    cliente_nome = models.CharField('Nome do Cliente', max_length=100)
    quantidade = models.PositiveIntegerField('Quantidade Vendida')
    preco_venda = models.DecimalField('Preço de Venda Registrado (sem promoção)', max_digits=10, decimal_places=2)
    preco_compra_registrado = models.DecimalField('Preço de Compra Registrado', max_digits=10, decimal_places=2, null=True, blank=True)
    data = models.DateTimeField('Data da Venda', default=timezone.now)
    tipo_venda = models.CharField('Tipo de Venda', max_length=10, choices=TIPO_CHOICES, default='retirada')
    promocao = models.ForeignKey(Promocao, on_delete=models.PROTECT, null=True, blank=True, related_name='vendas')
    status = models.CharField('Status da Venda', max_length=30, choices=STATUS_CHOICES, default='concluida')
    
    def __str__(self):
        nome_produto = self.produto.nome if self.produto else self.produto_nome_historico
        return f"{self.cliente_nome} - {nome_produto} ({self.data.strftime('%d/%m/%Y')}) - {self.get_status_display()}"
    
    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-data']
    
    def promocao_aplicada_na_venda(self):
        """Verifica se a promoção associada estava ativa na data da venda."""
        if not self.promocao:
            return False
        
        venda_data = self.data.date()
        promocao_data_inicio = self.promocao.data_inicio.date()
        promocao_data_fim = self.promocao.data_fim.date()

        return (self.promocao.ativa and
                promocao_data_inicio <= venda_data <= promocao_data_fim)

    def preco_efetivo_pago(self):
        """Retorna o preço unitário efetivamente pago, considerando a promoção na data da venda."""
        if self.promocao_aplicada_na_venda() and self.produto:
            return self.promocao.preco_final(self.produto)
        return self.preco_venda

    def valor_total_efetivo(self):
        """Calcula o valor total efetivamente pago na venda."""
        return self.quantidade * self.preco_efetivo_pago()

    def valor_desconto_aplicado(self):
        """Calcula o valor do desconto obtido pela promoção na data da venda."""
        if self.promocao_aplicada_na_venda():
            desconto_unitario = self.preco_venda - self.preco_efetivo_pago()
            return self.quantidade * desconto_unitario
        return Decimal('0')
    
    def lucro(self):
        """Calcula o lucro da venda, considerando o tipo de venda 'Loja'."""
        if self.status == 'devolvida' or not self.preco_compra_registrado:
            return Decimal('0')

        custo_total = self.quantidade * self.preco_compra_registrado
        lucro_bruto = self.valor_total_efetivo() - custo_total
        
        if self.tipo_venda == 'loja':
            return lucro_bruto / 2
        return lucro_bruto
    
    def margem_lucro(self):
        """Calcula a margem de lucro percentual da venda."""
        if self.status == 'devolvida' or not self.preco_compra_registrado:
            return Decimal('0')
            
        custo_total = self.quantidade * self.preco_compra_registrado
        if custo_total > 0:
            # O método self.lucro() já retorna o valor ajustado (dividido por 2 se for 'loja')
            margem = (self.lucro() / custo_total) * 100
            return margem
        return 0
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        # Validação e captura de dados históricos para novas vendas
        if is_new and self.produto:
            if self.quantidade > self.produto.quantidade:
                raise ValueError(f"Estoque insuficiente para {self.produto.nome}. "
                                 f"Disponível: {self.produto.quantidade}, Pedido: {self.quantidade}")

            # Armazena dados históricos no momento da venda
            self.produto_nome_historico = self.produto.nome
            if not self.preco_venda:
                self.preco_venda = self.produto.preco_venda
            
            # O custo é baseado no lote que será consumido
            self.preco_compra_registrado = self.produto.preco_compra

        super().save(*args, **kwargs)

        # Lógica de dedução do estoque para novas vendas
        if is_new and self.produto:
            quantidade_a_deduzir = self.quantidade
            lotes_disponiveis = self.produto.lotes.filter(quantidade__gt=0).order_by('data_entrada')

            for lote in lotes_disponiveis:
                if quantidade_a_deduzir <= 0:
                    break
                
                retirar = min(lote.quantidade, quantidade_a_deduzir)
                lote.quantidade -= retirar
                lote.save()
                quantidade_a_deduzir -= retirar

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
        old_obj = None
        if self.pk:
            try:
                old_obj = Devolucao.objects.get(pk=self.pk)
            except Devolucao.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        status_changed_to_approved_or_concluded = False
        if old_obj and old_obj.status not in ['aprovada', 'concluida'] and self.status in ['aprovada', 'concluida']:
            status_changed_to_approved_or_concluded = True
        elif not old_obj and self.status in ['aprovada', 'concluida']:
            status_changed_to_approved_or_concluded = True

        if status_changed_to_approved_or_concluded:
            # Atualiza o estoque
            if self.tipo == 'devolucao':
                # Devoluções devem retornar para um lote. Qual? O mais novo? Ou um lote de "devolvidos"?
                # Por simplicidade, vamos criar um novo lote para o item devolvido.
                Lote.objects.create(
                    produto=self.venda.produto,
                    fornecedor=self.venda.produto.fornecedor, # Fornecedor do lote ativo no momento
                    quantidade=self.quantidade,
                    preco_compra=self.venda.preco_compra_registrado, # Custo da venda original
                    preco_venda=self.venda.preco_venda, # Preço de venda original
                    data_entrada=timezone.now()
                )
            elif self.tipo == 'troca' and self.produto_troca:
                # Adiciona o produto original de volta ao estoque (novo lote)
                Lote.objects.create(
                    produto=self.venda.produto,
                    fornecedor=self.venda.produto.fornecedor,
                    quantidade=self.quantidade,
                    preco_compra=self.venda.preco_compra_registrado,
                    preco_venda=self.venda.preco_venda,
                    data_entrada=timezone.now()
                )
                
                # Remove o produto de troca do estoque (usando a mesma lógica FIFO da Venda)
                quantidade_a_deduzir = self.quantidade
                lotes_para_troca = self.produto_troca.lotes.filter(quantidade__gt=0).order_by('data_entrada')
                for lote in lotes_para_troca:
                    if quantidade_a_deduzir <= 0:
                        break
                    retirar = min(lote.quantidade, quantidade_a_deduzir)
                    lote.quantidade -= retirar
                    lote.save()
                    quantidade_a_deduzir -= retirar

            # Atualiza o status da Venda relacionada
            if self.venda.status != 'devolvida':
                self.venda.status = 'devolvida'
                self.venda.save(update_fields=['status'])

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
