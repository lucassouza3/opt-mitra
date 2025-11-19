from datetime import datetime

def calcular_diferenca_tempo(timestamp1, timestamp2):
    """
    Calcula a diferença detalhada entre dois timestamps.
    
    Args:
        timestamp1 (str ou datetime): Primeiro timestamp 
        timestamp2 (str ou datetime): Segundo timestamp
    
    Returns:
        dict: Dicionário com dias, horas, minutos e segundos de diferença
    """
    # Converte para datetime se for string
    if isinstance(timestamp1, str):
        timestamp1 = datetime.strptime(timestamp1, '%Y-%m-%d %H:%M:%S')
    
    if isinstance(timestamp2, str):
        timestamp2 = datetime.strptime(timestamp2, '%Y-%m-%d %H:%M:%S')
    
    # Verifica se são objetos datetime válidos
    if not (isinstance(timestamp1, datetime) and isinstance(timestamp2, datetime)):
        raise TypeError("Os timestamps devem ser strings no formato 'YYYY-MM-DD HH:MM:SS' ou objetos datetime")
    
    # Calcula a diferença absoluta entre os timestamps
    diferenca = abs(timestamp2 - timestamp1)
    
    # Extrai dias, horas, minutos e segundos
    dias = diferenca.days
    segundos_restantes = diferenca.seconds
    
    # Converte segundos restantes em horas, minutos e segundos
    horas = segundos_restantes // 3600
    segundos_restantes %= 3600
    
    minutos = segundos_restantes // 60
    segundos = segundos_restantes % 60
    
    return {
        'dias': dias,
        'horas': horas,
        'minutos': minutos,
        'segundos': segundos
    }

# Exemplo de uso
if __name__ == "__main__":
    # Exemplo 1: Usando strings
    print("Usando strings:")
    diferenca_str = calcular_diferenca_tempo(
        '2024-03-01 10:15:30', 
        '2024-03-04 11:20:45'
    )
    print(diferenca_str)
    
    # Exemplo 2: Usando objetos datetime
    print("\nUsando objetos datetime:")
    import datetime
    
    dt1 = datetime.datetime(2024, 3, 1, 10, 15, 30)
    dt2 = datetime.datetime(2024, 3, 4, 11, 20, 45)
    
    diferenca_dt = calcular_diferenca_tempo(dt1, dt2)
    print(diferenca_dt)