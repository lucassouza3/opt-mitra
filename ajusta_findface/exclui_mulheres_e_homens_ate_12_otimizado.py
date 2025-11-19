#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Otimizado de Exclusão de Cards - Findface Multi
=====================================
Exclui em UMA SÓ PASSAGEM:
- Mulheres (todas idades) 
- Homens (até 12 anos)
da watch list MA/CIVIL

Otimização: Processa ambos critérios por página (não duas passadas completas)
"""

import os
import sys
import time
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Optional, List, Dict, Tuple

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

# Importa a classe FindfaceMulti
from findface_multi.findface_multi import FindfaceMulti

class OptimizedCardDeletionManager:
    """Gerenciador otimizado de exclusão de cards com processamento conjunto por página"""
    
    def __init__(self, ff: FindfaceMulti, max_workers: int = 10):
        self.ff = ff
        self.max_workers = max_workers
        self.deleted_count = 0
        self.error_count = 0
        self.total_processed = 0
        self.log_file = "cards_excluídos_otimizado.txt"
        self.log_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Cache para nomes de watch lists
        self.watch_list_cache = {}
        self._load_watch_lists()
        
        # Inicializa arquivo de log
        self._init_log_file()
    
    def _load_watch_lists(self):
        """Carrega todas as watch lists no cache"""
        try:
            response = self.ff.get_watch_lists()
            watch_lists = response.get('results', [])
            for wl in watch_lists:
                self.watch_list_cache[wl['id']] = wl['name']
            print(f"📋 Carregadas {len(self.watch_list_cache)} watch lists no cache")
        except Exception as e:
            print(f"⚠️  Erro carregando watch lists: {e}")
            self.watch_list_cache = {}
    
    def _init_log_file(self):
        """Inicializa o arquivo de log com cabeçalho"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header = f"""# LOG DE EXCLUSÃO OTIMIZADA - FINDFACE MULTI
# Iniciado em: {timestamp}
# Critérios: Mulheres (todas idades) + Homens (até 12 anos)
# Watch List: MA/CIVIL (ID 24)
# Formato: TIMESTAMP | ID_CARD | NOME | SEXO | IDADE | WATCH_LISTS | STATUS
# ==================================================================================

"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def _calculate_age(self, data_nascimento: str) -> Optional[int]:
        """Calcula idade a partir da data de nascimento em vários formatos"""
        if not data_nascimento:
            return None
        
        try:
            # Remove espaços e caracteres especiais
            clean_date = data_nascimento.strip().replace('-', '').replace('/', '')
            
            # Formato YYYYMMDD
            if len(clean_date) == 8 and clean_date.isdigit():
                year = int(clean_date[:4])
                month = int(clean_date[4:6])
                day = int(clean_date[6:8])
                birth_date = date(year, month, day)
                
                today = date.today()
                age = today.year - birth_date.year
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    age -= 1
                return age
                
            # Formato YYYY-MM-DD
            elif '-' in data_nascimento:
                birth_date = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - birth_date.year
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    age -= 1
                return age
                
        except (ValueError, TypeError):
            return None
        
        return None
    
    def _get_watch_list_names(self, watch_lists: List[int]) -> str:
        """Converte IDs de watch lists para nomes"""
        names = []
        for wl_id in watch_lists:
            name = self.watch_list_cache.get(wl_id, f"ID_{wl_id}")
            names.append(name)
        return ", ".join(names)
    
    def _should_delete_card(self, card: Dict) -> Tuple[bool, str]:
        """
        Verifica se o card deve ser excluído baseado nos critérios otimizados
        Retorna (deve_excluir, motivo)
        """
        meta = card.get('meta', {})
        sexo = meta.get('sexo', '').upper()
        
        # Critério 1: Mulheres (todas idades)
        if sexo == 'F':
            return True, "Mulher (todas idades)"
        
        # Critério 2: Homens até 12 anos
        elif sexo == 'M':
            data_nascimento = meta.get('data_nascimento', '')
            age = self._calculate_age(data_nascimento)
            
            if age is not None and age <= 12:
                return True, f"Homem ({age} anos ≤ 12)"
            else:
                return False, f"Homem ({age if age else 'idade desconhecida'} anos > 12)"
        
        # Não atende critérios
        return False, f"Sexo não informado ou critérios não atendidos"
    
    def _delete_single_card(self, card: Dict) -> Tuple[bool, str]:
        """Exclui um único card e retorna resultado"""
        try:
            card_id = card.get('id')
            if not card_id:
                return False, f"❌ Card sem ID válido"
            
            # Nome está fora do meta
            nome = card.get('name', 'Nome não informado')
            
            meta = card.get('meta', {})
            sexo = meta.get('sexo', 'N/A').upper()
            data_nascimento = meta.get('data_nascimento', '')
            age = self._calculate_age(data_nascimento)
            watch_lists = card.get('watch_lists', [])
            
            # Exclui o card
            result = self.ff.delete_human_card(int(card_id))
            
            # API pode retornar None em caso de sucesso
            # Verificamos se NÃO há erro (diferente de False)
            if result is not False:
                # Prepara dados para log
                age_str = f"{age} anos" if age is not None else "idade desconhecida"
                sexo_desc = {"F": "Feminino", "M": "Masculino"}.get(sexo, sexo)
                watch_list_names = self._get_watch_list_names(watch_lists)
                
                # Log thread-safe
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                thread_name = threading.current_thread().name
                
                log_entry = f"{timestamp} | {card_id} | {nome} | {sexo_desc} | {age_str} | {watch_list_names} | EXCLUÍDO\n"
                
                with self.log_lock:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry)
                
                return True, f"✅ [{thread_name}] Card {card_id} excluído: {nome} ({sexo_desc}, {age_str}) - {watch_list_names}"
            else:
                return False, f"❌ Falha na exclusão do card {card_id}"
                
        except Exception as e:
            return False, f"❌ Erro ao excluir card {card.get('id', 'ID_DESCONHECIDO')}: {e}"
    
    def process_page_optimized(self, cards: List[Dict]) -> Tuple[int, int, Dict]:
        """
        Processa uma página aplicando AMBOS os filtros simultaneamente
        Retorna (excluídos, erros, estatísticas)
        """
        # Filtra cards que devem ser excluídos
        cards_to_delete = []
        stats = {"women": 0, "young_men": 0, "ignored": 0}
        
        for card in cards:
            should_delete, reason = self._should_delete_card(card)
            if should_delete:
                cards_to_delete.append(card)
                if "Mulher" in reason:
                    stats["women"] += 1
                elif "Homem" in reason:
                    stats["young_men"] += 1
            else:
                stats["ignored"] += 1
        
        if not cards_to_delete:
            return 0, 0, stats
        
        print(f"   🔄 Processando {len(cards_to_delete)} cards em {self.max_workers} threads...")
        print(f"      🚺 Mulheres: {stats['women']} | 🚹 Homens ≤12: {stats['young_men']} | ⚪ Ignorados: {stats['ignored']}")
        
        deleted_count = 0
        error_count = 0
        
        # Processa em paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete todas as tarefas
            future_to_card = {
                executor.submit(self._delete_single_card, card): card 
                for card in cards_to_delete
            }
            
            # Coleta resultados
            for future in as_completed(future_to_card):
                try:
                    success, message = future.result()
                    if success:
                        deleted_count += 1
                        print(f"   {message}")
                    else:
                        error_count += 1
                        print(f"   {message}")
                        
                except Exception as e:
                    error_count += 1
                    print(f"   ❌ Erro inesperado na thread: {e}")
        
        # Atualiza estatísticas globais thread-safe
        with self.stats_lock:
            self.deleted_count += deleted_count
            self.error_count += error_count
            self.total_processed += len(cards_to_delete)
        
        return deleted_count, error_count, stats
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas atuais"""
        with self.stats_lock:
            return {
                'deleted_count': self.deleted_count,
                'error_count': self.error_count,
                'total_processed': self.total_processed
            }

def delete_optimized_criteria(ff: FindfaceMulti, deletion_manager: OptimizedCardDeletionManager):
    """
    Exclui cards aplicando AMBOS critérios por página:
    - Mulheres (todas idades)
    - Homens (até 12 anos)
    """
    print("\n🎯 INICIANDO EXCLUSÃO OTIMIZADA: Mulheres + Homens ≤12 anos - MODO PARALELO")
    print("   📋 Processamento: AMBOS critérios por página (uma única passagem)")
    
    page = 1
    total_deleted = 0
    total_women = 0
    total_young_men = 0
    next_page_url = None
    
    while True:
        print(f"\n📄 Processando página {page}...")
        
        try:
            # Busca cards com paginação por cursor e filtro MA/CIVIL
            if page == 1:
                # Primeira página - sem cursor, com filtro MA/CIVIL (ID 24)
                response = ff.get_human_cards(limit=100, watch_lists=[24])
            else:
                # Páginas seguintes - usar cursor da página anterior
                if not next_page_url:
                    print("   ✅ Não há mais páginas para processar")
                    break
                
                # Extrair cursor da URL next_page
                if 'page=' in next_page_url:
                    cursor = next_page_url.split('page=')[1].split('&')[0]
                    response = ff.get_human_cards(limit=100, page=cursor, watch_lists=[24])
                else:
                    print("   ❌ Formato de cursor inválido")
                    break
            
            cards = response.get('results', [])
            next_page_url = response.get('next_page')
            
            if not cards:
                print("   ✅ Não há mais cards para processar")
                break
            
            print(f"   📊 Página {page}: {len(cards)} cards recebidos")
            print(f"   📍 Next page: {'Disponível' if next_page_url else 'Última página'}")
            
            # Processa exclusões otimizadas (ambos critérios)
            page_deleted, page_errors, page_stats = deletion_manager.process_page_optimized(cards)
            
            total_deleted += page_deleted
            total_women += page_stats["women"]
            total_young_men += page_stats["young_men"]
            
            print(f"   📈 Página {page}: {page_deleted} cards excluídos ({page_errors} erros)")
            print(f"      🚺 Mulheres: {page_stats['women']} | 🚹 Homens ≤12: {page_stats['young_men']}")
            
            # Pausa entre páginas para não sobrecarregar
            time.sleep(1)
            page += 1
            
        except Exception as e:
            print(f"   ❌ Erro na página {page}: {e}")
            break
    
    print(f"\n🎯 CONCLUSÃO OTIMIZADA:")
    print(f"   📊 Total de cards excluídos: {total_deleted}")
    print(f"   🚺 Mulheres: {total_women}")
    print(f"   🚹 Homens ≤ 12 anos: {total_young_men}")
    
    return total_deleted, total_women, total_young_men

def main():
    """Função principal"""
    print("🗑️  SCRIPT OTIMIZADO DE EXCLUSÃO DE CARDS - FINDFACE")
    print("   Watch List: MA/CIVIL (ID 24)")
    print("   Critérios: Mulheres (todas idades) + Homens (até 12 anos)")
    print("   Otimização: AMBOS critérios por página (uma única passagem)")
    print("   Paralelismo: 10 threads simultâneas por página")
    print("="*60)
    
    try:
        print("\n🔗 Conectando ao Findface...")
        
        # Verifica variáveis de ambiente
        url_base = os.getenv('FINDFACE_URL_BASE')
        user = os.getenv('FINDFACE_USER')
        password = os.getenv('FINDFACE_PASSWORD')
        uuid = os.getenv('FINDFACE_UUID')
        
        if not all([url_base, user, password, uuid]):
            print("❌ Erro: Variáveis de ambiente não configuradas no arquivo .env")
            return
        
        # Conecta ao Findface (garantindo que não são None)
        assert url_base and user and password and uuid, "Variáveis de ambiente inválidas"
        ff = FindfaceMulti(
            url_base=url_base,
            user=user,
            password=password,
            uuid=uuid
        )
        
        print("✅ Conexão estabelecida!")
        
        # Verifica se há cards na watch list MA/CIVIL
        print("\n📊 Verificando se há cards na watch list MA/CIVIL...")
        test_response = ff.get_human_cards(limit=10, watch_lists=[24])
        test_cards = test_response.get('results', [])
        
        if not test_cards:
            print("❌ Nenhum card encontrado na watch list MA/CIVIL (ID 24)")
            ff.logout()
            return
        
        print("✅ Encontrados cards na watch list MA/CIVIL!")
        print("📋 Exemplo dos primeiros cards:")
        for i, card in enumerate(test_cards[:3], 1):
            meta = card.get('meta', {})
            sexo = meta.get('sexo', 'N/A')
            print(f"   {i}. Card {card.get('id')} - Sexo: {sexo}")
        
        if test_response.get('next_page'):
            print("📄 Paginação disponível - processamento continuará além da primeira página")
        else:
            print("📄 Apenas uma página de dados disponível")
        
        # Inicializa gerenciador de exclusão otimizado
        max_workers = 10  # Número de threads paralelas
        deletion_manager = OptimizedCardDeletionManager(ff, max_workers=max_workers)
        
        start_time = datetime.now()
        print(f"⏰ Início da operação: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Executa exclusão otimizada (uma única passagem)
        total_deleted, total_women, total_young_men = delete_optimized_criteria(ff, deletion_manager)
        
        # Estatísticas finais
        end_time = datetime.now()
        duration = end_time - start_time
        stats = deletion_manager.get_statistics()
        
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DE EXCLUSÃO OTIMIZADA")
        print("="*60)
        print(f"📄 Watch List: MA/CIVIL (ID 24)")
        print(f"⏰ Duração total: {duration}")
        print(f"📄 Total de cards processados: {stats['total_processed']}")
        print(f"✅ Cards excluídos com sucesso: {stats['deleted_count']}")
        print(f"   🚺 Mulheres (todas idades): {total_women}")
        print(f"   🚹 Homens (≤ 12 anos): {total_young_men}")
        print(f"❌ Erros durante exclusão: {stats['error_count']}")
        print(f"📝 Log salvo em: {deletion_manager.log_file}")
        print(f"🎯 Otimização: Uma única passagem (vs duas passagens no script anterior)")
        
        # Finaliza log
        with open(deletion_manager.log_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "-" * 80 + "\n")
            f.write(f"# RESUMO FINAL - {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Duração: {duration}\n")
            f.write(f"# Watch List: MA/CIVIL (ID 24)\n")
            f.write(f"# Total processados: {stats['total_processed']}\n")
            f.write(f"# Excluídos: {stats['deleted_count']} | Erros: {stats['error_count']}\n")
            f.write(f"# Mulheres: {total_women} | Homens ≤12: {total_young_men}\n")
            f.write(f"# Otimização: Uma única passagem pela base de dados\n")
        
        # Logout
        ff.logout()
        print("\n✅ Operação otimizada concluída!")
        
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operação interrompida pelo usuário")

if __name__ == "__main__":
    main()