import re
from datetime import datetime


import re


def validar_celular_brasileiro(numero):
    codigos_ddd = [
        11, 12, 13, 14, 15, 16, 17, 18, 19,  # São Paulo
        21, 22, 24,                         # Rio de Janeiro
        27, 28,                             # Espírito Santo
        31, 32, 33, 34, 35, 37, 38,         # Minas Gerais
        41, 42, 43, 44, 45, 46,             # Paraná
        47, 48, 49,                         # Santa Catarina
        51, 53, 54, 55,                     # Rio Grande do Sul
        61,                                 # Distrito Federal
        62, 64,                             # Goiás
        63,                                 # Tocantins
        65, 66,                             # Mato Grosso
        67,                                 # Mato Grosso do Sul
        68,                                 # Acre
        69,                                 # Rondônia
        71, 73, 74, 75, 77,                 # Bahia
        79,                                 # Sergipe
        81, 87,                             # Pernambuco
        82,                                 # Alagoas
        83,                                 # Paraíba
        84,                                 # Rio Grande do Norte
        85, 88,                             # Ceará
        86, 89,                             # Piauí
        91, 93, 94,                         # Pará
        92, 97,                             # Amazonas
        95,                                 # Roraima
        96,                                 # Amapá
        98, 99                              # Maranhão
    ]

    # Remove todos os caracteres não numéricos
    numero_limpo = re.sub(r'\D', '', numero)
    
    # Verifica se o número possui exatamente 11 dígitos, se o terceiro dígito é '9' e se o DDD é válido
    if (len(numero_limpo) == 11 and
        numero_limpo[2] == '9' and
        int(numero_limpo[:2]) in codigos_ddd):
        return numero_limpo
    else:
        return False


def validate_cpf(numbers: str | int) -> str:
    """
    Validates a Brazilian CPF number for correct formatting and checks the digits according to the CPF rules.
    
    The CPF (Cadastro de Pessoas Físicas) is a Brazilian individual taxpayer registry identification. This function
    checks if the provided CPF is valid by ensuring it contains 11 digits, is not a sequence of identical numbers,
    and both of its verifying digits are correct according to the standard CPF formula.
    
    Parameters:
    - numbers (str | int): The CPF number to validate. It can be provided as a string or integer. Strings
      can contain non-digit characters, which will be ignored.
    
    Returns:
    - str: The validated CPF number as a string of digits if it is valid.
    - bool: False if the CPF number is invalid.
    - None: If the input is not a string or an integer, or if it's an empty or whitespace-only string.
    
    Examples:
    - validate_cpf("123.456.789-09") -> False (assuming it's an invalid CPF number)
    - validate_cpf(12345678909) -> "12345678909" (assuming it's a valid CPF number)
    - validate_cpf("111.111.111-11") -> False (invalid because it's a sequence of identical numbers)
    """
    if isinstance(numbers, int):
        numbers = str(numbers)


    if isinstance(numbers, str) and numbers is not None and len(numbers.strip()) > 0:
        cpf = [int(char) for char in numbers if char.isdigit()]
        if len(cpf) != 11:
            return False
        if all(cpf[i] == cpf[i + 1] for i in range(0, len(cpf) - 1)):
            return False
        for i in range(9, 11):
            value = sum((cpf[num] * ((i + 1) - num) for num in range(0, i)))
            digit = ((value * 10) % 11) % 10
            if digit != cpf[i]:
                return False    
        return ''.join(str(x) for x in cpf)


def remove_non_alphanumeric(text):
    """
    Remove todos os caracteres não alfanuméricos de uma string.
    
    :param text: A string a ser processada.
    :return: A string contendo apenas caracteres alfanuméricos.
    """
    if not isinstance(text, str):
        raise ValueError("O parâmetro deve ser uma string.")

    # Expressão regular para manter apenas caracteres alfanuméricos
    result = re.sub(r'[^a-zA-Z0-9]', '', text)
    return result

if __name__ == '__main__':

    cpf = '623.969.272-73'
    celular = '95-98102-1111'

    # print(validate_cpf(cpf))

    print(validar_celular_brasileiro(celular))