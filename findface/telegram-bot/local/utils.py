import re

def verifica_username(username):
    match = re.search('^[A-Za-z0-9_]{5,32}$', username)

    if match:
        # print(f'Usuário "{username}" válido')
        return True

    else:
        # print(f'Usuário "{username}" inválido')
        return False
    
def text_to_int(numero):
    algarismos = [x for x in numero if x.isdigit() or x == '-']
    novo_numero = ''.join(algarismos)

    if len(novo_numero) == 1 and novo_numero[0] == '-':
        novo_numero = None

    if novo_numero:
        return int(novo_numero)

def text_to_float(numero):
    algarismos = [x for x in numero if x.isdigit() or x == '-' or x == ',' or x == '.']

    indice_ponto = None
    indice_virgula = None

    # Obtém as posições da vírgula e do ponto no número
    for digito in algarismos:        
        if digito == '.':
            indice_ponto = algarismos.index('.')
        if digito == ',':
            indice_virgula = algarismos.index(',')

    if indice_ponto and indice_virgula:
        if indice_ponto < indice_virgula:
            algarismos[indice_virgula] = '.'
            # Se o número for no formato brasileiro, com ponto separando de milhar, exclui o ponto
            algarismos.pop(indice_ponto)
        else:
            # Se o número for no formato americando, com vírgula separando de milhar, exclui a vírgula
            algarismos.pop(indice_virgula)

    novo_float = ''.join(algarismos)
    
    if len(novo_float) == 1 and ['.', '-'] in novo_float[0]:
        novo_float = None

    if novo_float:
        return float(novo_float)



if __name__ == '__main__':

    print(text_to_float('15.020,7567890'))