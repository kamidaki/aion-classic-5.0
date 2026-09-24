"""
Orquestrador Mestre de Parsers XML 5.0 (tools/parsersXML/run_all_parsers.py)
Executa sequencialmente todos os 17 parsers especializados em tools/parsersXML/
para sincronizar 100% dos dados do servidor (data/server/data) com o cliente oficial 5.0 (data/client/data).
"""

import os
import sys
import time

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
if PARSERS_DIR not in sys.path:
    sys.path.insert(0, PARSERS_DIR)

import parse_items
import parse_npcs
import parse_skills
import parse_quests
import parse_spawns
import parse_zones
import parse_trade
import parse_teleport
import parse_recipes
import parse_player
import parse_gatherables
import parse_pets
import parse_tribes
import parse_windstreams
import parse_instances
import parse_events
import parse_drops


PARSERS = [
    ("Itens e Cosméticos", parse_items.parse_items),
    ("NPCs e Entidades", parse_npcs.parse_npcs),
    ("Skills e Habilidades", parse_skills.parse_skills),
    ("Missões e Quests", parse_quests.parse_quests),
    ("Spawns e Objetos 3D", parse_spawns.parse_spawns),
    ("Zonas e Mapas de Mundo", parse_zones.parse_zones),
    ("Comércio e Lojas", parse_trade.parse_trade),
    ("Teleportes e Rotas de Voo", parse_teleport.parse_teleport),
    ("Receitas de Crafting", parse_recipes.parse_recipes),
    ("Dados de Jogador e EXP", parse_player.parse_player),
    ("Fontes de Coleta", parse_gatherables.parse_gatherables),
    ("Pets e Mascotes", parse_pets.parse_pets),
    ("Tribos e Hostilidades", parse_tribes.parse_tribes),
    ("Windstreams e Portas", parse_windstreams.parse_windstreams),
    ("Instâncias, Cerco e Rifts", parse_instances.parse_instances),
    ("Eventos e Passe de Batalha", parse_events.parse_events),
    ("Drops de Monstros", parse_drops.parse_drops),
]


import backup_manager

def main():
    print("=" * 80)
    print(" INICIANDO SINCRONIZAÇÃO COMPLETA DE DADOS 5.0 (SERVER DATA <- CLIENT DATA)")
    print("=" * 80)
    
    # Cria sessão de backup unificada com data e hora para todo o ciclo de execução
    session_dir = backup_manager.init_backup_session("run_all_parsers")
    
    start_total = time.time()
    success_count = 0
    errors = []
    
    for idx, (name, fn) in enumerate(PARSERS, 1):
        t0 = time.time()
        print(f"\n[{idx:02d}/{len(PARSERS):02d}] Executando Parser: {name}...")
        try:
            fn()
            dt = time.time() - t0
            print(f"  -> Concluído com sucesso em {dt:.2f}s")
            success_count += 1
        except Exception as e:
            dt = time.time() - t0
            print(f"  -> ERRO no parser {name} ({dt:.2f}s): {e}")
            import traceback
            traceback.print_exc()
            errors.append((name, str(e)))

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f" RESULTADO FINAL: {success_count}/{len(PARSERS)} PARSERS CONCLUÍDOS ({total_time:.2f}s)")
    if errors:
        print(f" AVISO: {len(errors)} parsers apresentaram falhas:")
        for name, err in errors:
            print(f"   - {name}: {err}")
    else:
        print(" SUCESSO ABSOLUTO: 100% DOS DADOS DO SERVIDOR SINCRONIZADOS COM A VERSÃO 5.0!")
    print("=" * 80)


if __name__ == "__main__":
    main()
