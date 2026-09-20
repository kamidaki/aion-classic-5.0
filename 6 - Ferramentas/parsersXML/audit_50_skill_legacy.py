#!/usr/bin/env python3
"""Auditoria independente das lacunas após migração de skills para Classic 5.0.

Não altera dados do servidor. Os achados distinguem divergência direta de
suspeita sem equivalência demonstrada. Evidência completa em JSON e resumo MD.
"""
from pathlib import Path
import collections
import json
import re
import xml.etree.ElementTree as ET

import common_bxml
from generate_skill_tree_50 import CLASS_EXPANSION, CLASS_PRIORITY, RACE_MAP
from refresh_50_skills import stats_for
from rebuild_50_item_templates import load_strings

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / '1 - Código Fonte [Emulador]/game-server/data/static_data'
CLIENT = Path(common_bxml.BASE_CLIENT)
JAVA = ROOT / '1 - Código Fonte [Emulador]/game-server/src/com/aionemu/gameserver/skillengine'
ALIASES = {'skillatkinstant': {'skillatk'}, 'amrmastery': {'armormastery'},
           'wpnmastery': {'wpnmastery'}, 'dashatk': {'dash'}, 'movebehindatk': {'movebehind'},
           'blinkatk': {'movebehind'}, 'backdashatk': {'backdash'},
           'returnhome': {'return'}, 'delayedspellatkinstant': {'delaydamage'},
           'deboosthealamount': {'deboostheal'}, 'mpatkdraininstant': {'spellatkdraininstant'},
           'healcastoronattacked': {'healcastoronatk'}, 'boosthealeffect': {'boostheal'},
           'onetimeboosthealeffect': {'onetimeboostheal'}, 'extendaurarange': {'extendedaurarange'},
           'switchhpmpinstant': {'switchhpmp'}, 'boostspellattackeffect': {'boostspellattack'},
           'noreducespellatkinstant': {'noreducespellatk'}, 'resurrectpositional': {'resurrectpos'}}


def norm(v):
    return (v or '').lower().replace('_', '')


def main():
    client = {e.findtext('id'): {x.tag: (x.text or '').strip() for x in e}
              for e in ET.parse(CLIENT / 'data/skills/client_skills.xml').getroot()}
    templates = {e.get('skill_id'): e for e in ET.parse(DATA / 'skills/skill_templates.xml').getroot()}
    tree = list(ET.parse(DATA / 'skill_tree/skill_tree.xml').getroot())
    blending_learning_sources = {
        skill_id
        for entry in tree if entry.get('blendingSources')
        for skill_id in re.findall(r'\d+', entry.get('blendingSources'))
    }
    player = {e.get('skillId') for e in tree}
    classes = collections.defaultdict(set)
    for e in tree:
        classes[e.get('skillId')].add(e.get('classId'))
    names = {c['name'].lower(): sid for sid, c in client.items() if c.get('name')}
    registry_text = (JAVA / 'effect/Effects.java').read_text(encoding='utf-8')
    registry = dict(re.findall(r'@XmlElement\(name\s*=\s*"([^"]+)"\s*,\s*type\s*=\s*(\w+)\.class', registry_text))
    motions = {norm(e.get('name')) for e in ET.parse(DATA/'skills/motion_times.xml').getroot()}
    string_ids, _ = load_strings(str(CLIENT))
    findings = collections.defaultdict(list)
    def add(category, sid, field, server, official, confidence='divergência direta'):
        findings[category].append({'skill_id': sid, 'name': client.get(sid, {}).get('name', templates.get(sid).get('name') if sid in templates else ''),
                                   'classes': sorted(classes[sid]), 'field': field, 'server': server,
                                   'client': official, 'confidence': confidence})
    for sid in sorted(set(client) - set(templates), key=int):
        add('definicao_cliente_sem_template', sid, 'template', None, client[sid]['name'])
    for sid in sorted(set(templates) - set(client), key=int):
        add('template_sem_definicao_cliente', sid, 'template', templates[sid].get('stack'), None, 'ausência confirmada; origem histórica a confirmar')
    common = set(client) & set(templates)
    for sid in sorted(common, key=int):
        c, s = client[sid], templates[sid]
        official_name_id = string_ids.get(c.get('desc','').upper())
        if official_name_id is not None and s.get('nameId') != str(official_name_id):
            add('identificador_nome_divergente',sid,'nameId',s.get('nameId'),str(official_name_id),'ID oficial do texto; nome traduzido pode ser preservado')
        for attr, field in [('tslot', 'target_slot'), ('dispel_category', 'dispel_category'),
                            ('req_dispel_level', 'dispel_level'), ('tslot_level', 'target_slot_level'),
                            ('cooldown_delta_lv', 'delay_time_lv'), ('toggle_timer', 'toggle_timer')]:
            if c.get(field) is not None:
                a, b = norm(s.get(attr, '0' if attr not in {'tslot', 'dispel_category'} else 'none')), norm(c[field])
                if attr == 'dispel_category':
                    b = {'debuffphy':'debuffphysical','debuffmen':'debuffmental','npcdebuffphy':'npcdebuffphysical'}.get(b,b)
                if attr == 'tslot':
                    b = {'special':'spec','special2':'spec2'}.get(b,b)
                if a != b:
                    add('metadados_nao_migrados', sid, attr, s.get(attr), c[field])
        effects = s.find('effects')
        official_slots = {int(m[1]) for key in c if (m := re.fullmatch(r'effect(\d+)_type', key)) and c[key]}
        existing_effects = list(effects) if effects is not None else []
        server_slots = collections.Counter(int(e.get('e', '0')) for e in existing_effects)
        for n in official_slots - set(server_slots):
            if norm(c[f'effect{n}_type']) == 'blending' and sid in blending_learning_sources:
                continue
            add('efeito_oficial_ausente', sid, f'effect{n}', None, c[f'effect{n}_type'])
        for n in set(server_slots) - official_slots:
            add('efeito_sem_slot_oficial', sid, f'effect{n}', [e.tag for e in effects if e.get('e') == str(n)], None, 'estrutura residual; equivalência funcional a confirmar')
        for n, count in server_slots.items():
            if count > 1:
                add('posicao_efeito_duplicada', sid, f'effect{n}', count, 1)
        for effect in existing_effects:
            n = effect.get('e', '0')
            prefix = f'effect{n}_'
            official_type = c.get(prefix + 'type')
            allowed = {norm(official_type)} | ALIASES.get(norm(official_type), set())
            matched = norm(effect.tag) in allowed
            if official_type and not matched:
                add('tipo_efeito_sem_equivalencia', sid, prefix+'type', effect.tag, official_type, 'conversão exige revisão semântica')
            if official_type and not any(norm(tag) in allowed for tag in registry):
                add('tipo_oficial_sem_registro_jaxb', sid, prefix+'type', sorted(allowed), official_type, 'lacuna de representação; conferir aliases específicos')
            if effect.tag == 'statup' and len(effect.findall('change')) == 1:
                change = effect.find('change')
                signature = {k:change.get(k) for k in ['stat','func','value']}
                if signature == {'stat': 'PHYSICAL_ATTACK', 'func': 'ADD', 'value': '10'} and norm(official_type) != 'statup':
                    add('assinatura_fallback_atk10', sid, prefix+'type', ET.tostring(effect, encoding='unicode').strip(), official_type, 'assinatura exata do fallback do gerador')
            if effect.tag == 'deform' and effect.get('model') == '200000':
                add('assinatura_modelo_fixo', sid, prefix+'reserved9', '200000', c.get(prefix+'reserved9'), 'assinatura do fallback de transformação')
            if not matched:
                continue
            official_stats = {stat for slot in [13,14,15] for stat in stats_for(c.get(prefix+'reserved'+str(slot)))
                              if norm(c.get(prefix+'reserved'+str(slot))) not in {'','0','none'}}
            if norm(official_type) in {'statup','statdown','weaponstatup','weaponstatboost'} and c.get(prefix+'reserved6') in {'0','1'}:
                for change in effect.findall('change'):
                    # R6 qualifica o primeiro token; R7 o segundo. Não aplicar
                    # a função do primeiro grupo indiscriminadamente aos demais.
                    slot = next((slot for slot in [13,14] if change.get('stat') in stats_for(c.get(prefix+'reserved'+str(slot)))),None)
                    flag = c.get(prefix+'reserved'+str(6 if slot==13 else 7)) if slot else None
                    if flag not in {'0','1'}:
                        continue
                    function='PERCENT' if flag=='1' else 'ADD'
                    if change.get('stat') in official_stats and change.get('func') != function:
                        add('funcao_stat_divergente',sid,prefix+change.get('stat')+'.func',change.get('func'),function)
            if norm(official_type) == 'statboost':
                for function,field in [('ADD','reserved2'),('PERCENT','reserved4')]:
                    value = c.get(prefix+field)
                    if value and re.fullmatch(r'-?\d+(\.\d+)?',value) and float(value)!=0:
                        for stat in official_stats:
                            if not any(e.get('stat')==stat and e.get('func')==function for e in effect.findall('change')):
                                add('componente_statboost_ausente',sid,prefix+stat+'.'+function,None,value,'dupla explícita do cliente; verificar aplicação conjunta')
            for attr, field, default in [('duration1', 'remain1', '0'), ('duration2', 'remain2', '0'),
                                         ('basiclvl', 'basiclv', '0'), ('effectid', 'effectid', '0'),
                                         ('preeffect_prob', 'cond_preeffect_prob2', '100')]:
                # Campo ausente no cliente não confirma zero: registrar, sem corrigir.
                if attr in effect.attrib and field not in {k[len(prefix):] for k in c if k.startswith(prefix)}:
                    if effect.get(attr) != default:
                        add('atributo_preservado_sem_fonte', sid, prefix+attr, effect.get(attr), None, 'resíduo possível; ausência não prova erro')
            linked = effect.get('skill_id')
            if linked:
                if linked not in templates:
                    add('referencia_skill_inexistente', sid, prefix+'skill_id', linked, None)
                if linked == sid and effect.tag in {'provoker', 'skilllauncher', 'delayedskill'}:
                    add('gatilho_aponta_para_si', sid, prefix+'skill_id', linked, c.get(prefix+'reserved17') or c.get(prefix+'reserved1'), 'potencial recursão; conferir se intencional')
            props = c.get(prefix+'cond_preeffect')
            if not props and effect.get('preeffect'):
                add('preefeito_sem_condicao_cliente', sid, prefix+'preeffect', effect.get('preeffect'), None, 'resíduo possível')
        start = s.find('startconditions')
        weapon = start.find('weapon') if start is not None else None
        weapon_map = {'2hsword':'GREATSWORD','book':'SPELLBOOK','bow':'BOW','dagger':'DAGGER','mace':'MACE','orb':'ORB',
                      'polearm':'POLEARM','staff':'STAFF','sword':'SWORD','chainblade':'CHAINBLADE','gauntlet':'GAUNTLET',
                      'gun':'GUN','harp':'HARP','cannon':'CANNON','keyblade':'KEYBLADE'}
        required = {v for k,v in weapon_map.items() if c.get('required_'+k) == '1'}
        actual = set(weapon.get('weapon','').split()) if weapon is not None else set()
        if required != actual and required:
            add('restricao_arma_divergente', sid, 'weapon', sorted(actual), sorted(required))
        if actual and not required:
            add('restricao_arma_sem_fonte', sid, 'weapon', sorted(actual), None, 'restrição residual; conferir campos novos')
        chain = start.find('chain') if start is not None else None
        if c.get('chain_category_name') and (c.get('prechain_category_name') or c.get('skill_category') == 'SKILLCTG_CHAIN_SKILL'):
            expected_chain = {'category':c['chain_category_name'].upper()}
            if c.get('chain_time') is not None:
                expected_chain['time']=c['chain_time']
            if c.get('prechain_category_name'):
                expected_chain['precategory']=c['prechain_category_name'].upper()
            for k,v in expected_chain.items():
                if chain is None or chain.get(k) != v:
                    add('corrente_divergente', sid, 'chain.'+k, chain.get(k) if chain is not None else None, v)
        move = s.find('useconditions/playermove')
        if c.get('move_casting') == '1' and move is not None and move.get('allow') == 'false':
            add('movimento_bloqueado_cliente_permite', sid, 'playermove', 'false', 'move_casting=1')
        motion = s.find('motion')
        if c.get('motion_name') and (motion is None or norm(motion.get('name')) != norm(c['motion_name'])):
            available = norm(c['motion_name']) in motions
            add('motion_divergente', sid, 'motion', motion.get('name') if motion is not None else None, c['motion_name'],
                'motion oficial disponível no servidor' if available else 'motion oficial também ausente de motion_times.xml')
    orphan_ids = set(templates)-set(client)
    for path in DATA.rglob('*.xml'):
        if path.name == 'skill_templates.xml':
            continue
        for match in re.finditer(r'\b(skill_id|skillId|skillid)="(\d+)"',path.read_text(encoding='utf-8',errors='replace')):
            sid=match[2]
            if sid in orphan_ids:
                add('referencia_a_template_sem_cliente',sid,str(path.relative_to(ROOT)),sid,None)
    for sid,c in client.items():
        if ('SOUL_REAPER' in classes[sid] and sid not in blending_learning_sources
                and any(norm(v)=='blending' for k,v in c.items() if re.fullmatch(r'effect\d+_type',k))
                and (sid not in templates or templates[sid].find('effects/blending') is None)):
            add('blending_combate_soul_reaper_pendente',sid,'Blending.stack','ausente','combinação por stack_level',
                'as combinações de aprendizado já foram separadas; este grupo usa acúmulo em combate')
    learns = list(ET.parse(CLIENT/'data/skills/client_skill_learns.xml').getroot())
    expected_tree = {}
    for learn in learns:
        c = {e.tag:(e.text or '').strip() for e in learn}
        sid = names.get(c.get('skill','').lower())
        if not sid:
            continue
        raw = c.get('class','').upper()
        race = RACE_MAP.get(c.get('race','All'),'PC_ALL')
        prio = CLASS_PRIORITY.get(raw,15)
        for cls in CLASS_EXPANSION.get(raw,[raw]):
            key = (cls,sid,c.get('skill_level','1'),race)
            blended = c.get('stigma_display') == '5'
            stigma = c.get('stigma_display') in {'1','2'} or c.get('learntype') == '1'
            automatic = c.get('autolearn','').upper() == 'TRUE'
            row = {'minLevel':c.get('pc_level','1'),'autoLearn':str(automatic).lower(), 'stigma':str(stigma).lower(),
                   'skillBook':str(not automatic and not stigma and not blended).lower()}
            if key not in expected_tree or prio > expected_tree[key][0]:
                expected_tree[key]=(prio,row)
    actual_tree={(e.get('classId'),e.get('skillId'),e.get('skillLevel','1'),e.get('race','PC_ALL')):e for e in tree}
    for key,(_,row) in expected_tree.items():
        actual = actual_tree.get(key)
        for k,v in row.items():
            if actual is None or actual.get(k,'false' if k!='minLevel' else '1')!=v:
                add('arvore_divergente',key[1],str(key)+'.'+k,actual.get(k) if actual is not None else None,v,'segundo tradução de classes do gerador atual')
    for key in actual_tree.keys()-expected_tree.keys():
        add('arvore_sem_regra_cliente',key[1],str(key),actual_tree[key].attrib,None)
    empty_classes=[]
    for tag,cls in registry.items():
        path=JAVA/'effect'/f'{cls}.java'
        if path.exists() and 'TODO Auto-generated method stub' in path.read_text(encoding='utf-8'):
            empty_classes.append({'xml_type':tag,'class':cls,'skills':[sid for sid,s in templates.items() if s.find('effects/'+tag) is not None]})
    summary={k:{'findings':len(v),'skills':len({x['skill_id'] for x in v}),
                'player_skills':len({x['skill_id'] for x in v if x['skill_id'] in player})} for k,v in findings.items()}
    out={'counts':{'client':len(client),'server':len(templates),'player_skills':len(player),'tree_rows':len(tree)},
         'summary':summary,'findings':dict(findings),'java_stubs':empty_classes}
    folder=Path(__file__).parent
    (folder/'auditoria_legado_skills_50.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Auditoria detalhada das skills Classic 5.0','',
           'Esta auditoria não altera os dados. Divergência em relação ao cliente não prova, sozinha, origem na 4.8. Aliases e regras do servidor exigem confirmação semântica.', '',
           '## Escopo e conclusão','',
           f'Foram comparadas {len(client)} definições oficiais com {len(templates)} templates do servidor, {len(player)} IDs presentes na árvore de jogadores e {len(tree)} registros de aprendizado. Também foram examinados o registro JAXB, implementações de efeitos Java e os geradores XML.', '',
           'A migração anterior não encerrou a compatibilidade 5.0. Ainda há efeitos oficiais ausentes, conversões sem equivalência e implementações incompletas. Os 62 casos estruturais do relatório anterior não eram o total de pendências. As categorias abaixo se sobrepõem: seus totais não devem ser somados.', '',
           '## Estado das correções','',
           '- As funções ADD/PERCENT, incluindo a passiva 2750 do Brawler, estão sincronizadas com os pares explícitos R2/R4 e flags R6/R7 do cliente.',
           '- As restrições de armas e a permissão de movimento das skills presentes na árvore de jogadores estão sincronizadas. Divergências de arma remanescentes pertencem a NPCs; WeaponCondition não as valida para NPCs.',
           '- As skills 724, 2088, 2189 e 2206 receberam o DispelDebuffPhysical oficial que estava ausente.',
           '- **4448 e outras seis passivas do Soul Reaper:** o segundo efeito agora usa StatSynergy com fonte, destino e razão oficiais; o motor recalcula o bônus a partir do atributo atual.',
           '- **Blending do Soul Reaper:** seis passivas combinadas são concedidas e removidas pelas combinações oficiais de aprendizado. As cinco graduações de Blade Assault agora compartilham o contador oficial e disparam a skill combinada no segundo acúmulo.',
           '- **2521–2523 — Utility:** os templates usam uma classe cujo applyEffect está vazio. Registro JAXB e XML válido não garantem execução do efeito.', '',
           '## Riscos nos geradores e na atualização anterior','',
           '- build_50_player_skill_effects.py não gera mais PHYSICAL_ATTACK/ADD/10, NPC 200000, duração ou valor genérico para efeitos desconhecidos. Tipos não traduzidos permanecem como pendência.',
           '- rebuild_50_skill_effects.py aprende correspondências a partir dos templates 4.8 por frequência estatística. Uma correspondência frequente não prova equivalência para todos os tipos e parâmetros 5.0.',
           '- refresh_50_skills.py preserva atributos sem fonte explícita para não apagar comportamento ainda não compreendido. ADD/PERCENT e as flags R6/R7 já são tratadas separadamente.',
           '- ShapeChange e Polymorph têm classes Java distintas; Polymorph altera também a tribo do NPC. O alias usado na atualização anterior não demonstra equivalência de comportamento.', '',
           '## Como interpretar os números','',
           'Ausência de efeito e diferença de campo explícito são evidências diretas. Conversão de tipo, atributo sem fonte, motion e política de aprendizado exigem revisão semântica. A divergência de nameId inclui IDs ausentes e IDs diferentes; não mede a qualidade da tradução textual.', '',
           '| Achado | Ocorrências | Skills | Skills de jogadores |','|---|---:|---:|---:|']
    lines += [f'| {k} | {v["findings"]} | {v["skills"]} | {v["player_skills"]} |' for k,v in summary.items()]
    lines += ['',f'Classes Java com implementação vazia: {len(empty_classes)}.','',
              'A árvore foi comparada usando a tradução de classes do gerador atual; esta comparação não valida a própria tradução.',
              'A comparação de motions mede nomes e disponibilidade em motion_times.xml; não comprova, sozinha, animação incorreta no cliente. Os 26 templates sem definição oficial não aparecem na árvore de jogadores, e a busca por atributos skill_id/skillId/skillid não encontrou referências a eles nos demais XMLs; isso não basta para autorizar sua remoção.',
              '', '## Ordem recomendada para correção','',
              '1. Remover dos geradores as substituições e valores inventados; tipos desconhecidos devem produzir pendência identificada.',
              '2. Corrigir funções de atributos, contribuições de StatBoost, restrições e efeitos ausentes com tradução confirmada; preservar efeitos ainda não compreendidos.',
              '3. Implementar os efeitos 5.0 especiais no motor, começando por StatSynergy e Blending de Soul Reaper; corrigir Utility e resolver Control/FlyBoost/RadarAngle.',
              '4. Revisar motion_times, identificadores de texto e política de aprendizado. Validar por classe e tipo de efeito em combate, comparando com capturas oficiais quando disponíveis.',
              '', '## Limites da validação','',
              'Esta etapa é uma análise estática. Não houve teste de combate nem demonstração de equivalência com Game.dll. A classificação de skills de jogadores segue a árvore atual do servidor. Nenhum template, Java ou binário foi alterado pela execução deste auditor.',
              '', '## Exemplos por categoria','']
    for category, entries in findings.items():
        lines += [f'### {category}','']
        selected=sorted(entries,key=lambda x:(not bool(x['classes']),int(x['skill_id'])))[:5]
        for x in selected:
            a=str(x['server']).replace('\n',' ')[:180];b=str(x['client'])[:180]
            lines.append(f'- `{x["skill_id"]}` / `{x["name"]}`: `{x["field"]}` servidor `{a}`; cliente `{b}`. {x["confidence"]}.')
        lines.append('')
    lines += ['## Evidência completa','', 'IDs, classes, campos e valores estão em `auditoria_legado_skills_50.json`.']
    (folder/'auditoria_legado_skills_50.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'counts':out['counts'],'summary':summary,'java_stubs':len(empty_classes)},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
