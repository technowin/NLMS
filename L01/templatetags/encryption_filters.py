from django import template
from NLMS.encryption import * # adjust import

register = template.Library()

@register.filter(name ='encrypt')
def encrypt(value):
    return enc(str(value))
