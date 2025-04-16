from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtrai o argumento do valor"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Adiciona o argumento ao valor"""
    try:
        return Decimal(str(value)) + Decimal(str(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Multiplica o valor pelo argumento"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Divide o valor pelo argumento"""
    try:
        if Decimal(str(arg)) == 0:
            return 0
        return Decimal(str(value)) / Decimal(str(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value):
    """Formata o valor como porcentagem"""
    try:
        return f"{Decimal(str(value)):.2f}%"
    except (ValueError, TypeError):
        return value 