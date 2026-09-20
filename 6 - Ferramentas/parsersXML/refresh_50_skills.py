#!/usr/bin/env python3
"""Atualiza templates completos pelos dados oficiais Classic 5.0, sem inferir números.

Ao contrário dos geradores de stubs, também revisa efeitos já existentes.
Tipos não equivalentes são registrados para revisão, nunca recebem números
de outro tipo de efeito. O XML é validado antes de sincronizar fonte e produto.
"""
import argparse
import collections
import copy
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import backup_manager
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR, load_strings
from rebuild_50_skill_effects import stat_por_nome

BLOCK = re.compile(r'\t<skill_template\b[^>]*?(?:/>|>.*?</skill_template>)', re.S)
ALIASES = {
    'skillatkinstant': 'skillatk',
    'amrmastery': 'armormastery', 'dashatk': 'dash',
    'blinkatk': 'movebehind', 'movebehindatk': 'movebehind',
    'backdashatk': 'backdash', 'returnhome': 'return',
    'delayedspellatkinstant': 'delaydamage', 'deboosthealamount': 'deboostheal',
    'noreducespellatkinstant': 'noreducespellatk',
    'healcastoronattacked': 'healcastoronatk', 'boosthealeffect': 'boostheal',
    'onetimeboosthealeffect': 'onetimeboostheal',
    'extendaurarange': 'extendedaurarange', 'switchhpmpinstant': 'switchhpmp',
    'boostspellattackeffect': 'boostspellattack',
    'mpatkdraininstant': 'spellatkdraininstant',
    'resurrectpositional': 'resurrectpos',
}
INSTANT = {'spellatkinstant', 'spellatkdraininstant', 'mpattackinstant',
           'healinstant', 'mphealinstant', 'dphealinstant', 'fphealinstant',
           'sphealinstant', 'noreducespellatk'}
OVERTIME = {'spellatk', 'heal', 'mpheal', 'bleed', 'poison'}
STATS = {'statup', 'statdown', 'statboost', 'weaponstatup', 'weaponstatboost'}
COMMON = {'duration1': 'remain1', 'duration2': 'remain2', 'effectid': 'effectid',
          'basiclvl': 'basiclv', 'randomtime': 'randomtime', 'checktime': 'checktime',
          'accmod1': 'acc_mod1', 'accmod2': 'acc_mod2',
          'critprobmod2': 'critical_prob_mod2', 'critadddmg1': 'critical_add_dmg1',
          'critadddmg2': 'critical_add_dmg2', 'hopa': 'hop_a', 'hopb': 'hop_b',
          'hittypeprob2': 'reserved_cond1_prob2', 'preeffect_prob': 'cond_preeffect_prob2'}
WEAPON_FLAGS = [
    ('GREATSWORD', 'required_2hsword'), ('SPELLBOOK', 'required_book'),
    ('BOW', 'required_bow'), ('CHAINBLADE', 'required_chainblade'),
    ('DAGGER', 'required_dagger'), ('DIMENSIONSWORD', 'required_dimensionsword'),
    ('GAUNTLET', 'required_gauntlet'), ('GUN', 'required_gun'),
    ('MACE', 'required_mace'), ('ORB', 'required_orb'),
    ('POLEARM', 'required_polearm'), ('RUNESWORD', 'required_runesword'),
    ('STAFF', 'required_staff'), ('SWORD', 'required_sword'),
]


def norm(value):
    return (value or '').lower().replace('_', '')


def number(value):
    if value in (None, ''):
        return None
    try:
        f = float(value)
        # Os campos numéricos atualizados usam inteiros no JAXB do servidor.
        return str(int(f))
    except ValueError:
        return None


def set_if(element, attribute, value):
    if value is not None:
        if str(value) == '0' and attribute not in element.attrib:
            return
        element.set(attribute, str(value))


def semantic_xml(element):
    """Serializa ignorando apenas espaços de indentação entre elementos."""
    normalized = copy.deepcopy(element)
    for child in normalized.iter():
        if child.text is not None and not child.text.strip():
            child.text = None
        if child.tail is not None and not child.tail.strip():
            child.tail = None
    return ET.tostring(normalized)


def stats_for(token):
    aliases = {'phyattack': ('PHYSICAL_ATTACK',), 'phydefend': ('PHYSICAL_DEFENSE',),
               'phyhitaccuracy': ('PHYSICAL_ACCURACY',), 'hitaccuracy': ('PHYSICAL_ACCURACY',),
               'phycritical': ('PHYSICAL_CRITICAL',), 'attackdelay': ('ATTACK_SPEED',),
               'elementaldefendall': ('WATER_RESISTANCE', 'WIND_RESISTANCE',
                                      'FIRE_RESISTANCE', 'EARTH_RESISTANCE')}
    return aliases.get(norm(token)) or stat_por_nome(token) or ()


def fields(client, position):
    prefix = f'effect{position}_'
    return {k[len(prefix):]: v for k, v in client.items() if k.startswith(prefix)}


def expected(f):
    t = norm(f.get('type'))
    return ALIASES.get(t, t)


def equivalent(effect, f):
    return norm(effect.tag) == expected(f)


def stack_blending_attributes(f, skill_ids, blending_combinations):
    if not skill_ids or not blending_combinations:
        return None
    references = [f.get(f'reserved{i}') for i in range(2, 16)
                  if f.get(f'reserved{i}') and norm(f.get(f'reserved{i}')) not in {'0', 'none'}]
    if len(references) != 1:
        return None
    combination = blending_combinations.get(references[0].lower())
    if not combination or len(combination['requirements']) != 1:
        return None
    requirement = combination['requirements'][0]
    stack_level = number(requirement.get('stack_level'))
    result = skill_ids.get(combination['result'].lower())
    sources = [skill_ids.get(name.lower()) for name in requirement['skills']]
    if stack_level is None or int(stack_level) <= 1 or result is None or any(source is None for source in sources):
        return None
    return {'stack_level': stack_level, 'skill_id': result, 'source_skills': ' '.join(sources)}


def build_confirmed_effect(f, skill_ids=None, blending_combinations=None, npc_ids=None):
    """Gera apenas tipos cujos campos têm tradução explícita no servidor."""
    tag = expected(f)
    if tag == 'statsynergy':
        source = stats_for(f.get('reserved1'))
        target = stats_for(f.get('reserved2'))
        fixed = number(f.get('reserved3'))
        target_value = number(f.get('reserved4'))
        source_value = number(f.get('reserved5'))
        # R6/R11 são limites reservados e estão zerados nas definições 5.0.
        if len(source) != 1 or len(target) != 1 or None in {fixed, target_value, source_value}:
            return None
        if number(f.get('reserved6')) not in {None, '0'} or int(source_value) <= 0:
            return None
        effect = ET.Element(tag, source=source[0], target=target[0],
                            source_value=source_value, target_value=target_value,
                            fixed_value=fixed)
        target2_token = f.get('reserved7')
        if target2_token and norm(target2_token) not in {'0', 'none'}:
            target2 = stats_for(target2_token)
            fixed2 = number(f.get('reserved8'))
            target_value2 = number(f.get('reserved9'))
            source_value2 = number(f.get('reserved10'))
            if len(target2) != 1 or None in {fixed2, target_value2, source_value2}:
                return None
            if number(f.get('reserved11')) not in {None, '0'} or int(source_value2) <= 0:
                return None
            effect.attrib.update(target2=target2[0], source_value2=source_value2,
                                 target_value2=target_value2, fixed_value2=fixed2)
    elif tag == 'blending':
        attributes = stack_blending_attributes(f, skill_ids, blending_combinations)
        if attributes is None:
            return None
        effect = ET.Element(tag, **attributes)
    elif tag in {'flyboost', 'control'}:
        effect = ET.Element(tag)
    elif tag == 'radarangle' and number(f.get('reserved1')) is not None:
        effect = ET.Element(tag, value=number(f['reserved1']))
    elif tag == 'targetlock' and skill_ids:
        linked = skill_ids.get(f.get('reserved8', '').lower())
        values = {name: number(f.get(field)) for name, field in {
            'focus_delta': 'reserved1', 'focus_value': 'reserved2',
            'cover_delta': 'reserved3', 'cover_value': 'reserved4',
            'focus_drop_delta': 'reserved5', 'focus_drop_value': 'reserved6',
            'range': 'reserved7', 'checktime': 'checktime'}.items()}
        if linked is None or any(value is None for value in values.values()):
            return None
        effect = ET.Element(tag, skill_id=linked, **values)
    elif tag == 'shapechange' and npc_ids:
        model = npc_ids.get(f.get('reserved9', '').lower())
        transform_type = (f.get('reserved8') or 'NONE').upper()
        if model is None or transform_type not in {'AVATAR', 'FORM1', 'NONE', 'PC'}:
            return None
        effect = ET.Element(tag, model=model, type=transform_type)
    elif tag == 'deform' and norm(f.get('reserved9')) in {'', 'none'}:
        # Classic also uses Deform as an abnormal state without changing the
        # creature model (WI_Sleep_G1). An absent model is meaningful here.
        effect = ET.Element(tag)
    elif tag in STATS:
        effect = ET.Element(tag)
        # StatBoost usa um único stat (R13): R2 é contribuição fixa e R4
        # percentual. StatUp/Down usa R6 para R13 e R7 para R14.
        sources = [(13, 4, 3, 'PERCENT')] if tag in {'statboost', 'weaponstatboost'} and number(f.get('reserved4')) not in {None, '0'} else (
                  [(13, 2, 1, 'ADD')] if tag in {'statboost', 'weaponstatboost'} else
                  [(13, 2, 1, 'PERCENT' if f.get('reserved6') == '1' else 'ADD'),
                   (14, 4, 3, 'PERCENT' if f.get('reserved7') == '1' else 'ADD')])
        for slot, value_field, delta_field, func in sources:
            token = f.get(f'reserved{slot}')
            if not token or norm(token) in {'0', 'none'}:
                continue
            stats = stats_for(token)
            if not stats:
                return None
            value = number(f.get(f'reserved{value_field}'))
            if value is None:
                return None
            for stat in stats:
                ET.SubElement(effect, 'change', stat=stat, func=func, value=value)
        if not len(effect):
            return None
    elif tag in INSTANT or tag == 'skillatk':
        effect = ET.Element(tag)
    elif tag == 'boosthate' and number(f.get('reserved2')) is not None:
        effect = ET.Element(tag)
        ET.SubElement(effect, 'change', stat='BOOST_HATE', func='PERCENT', value=number(f['reserved2']))
    elif tag == 'boostskillcost' and number(f.get('reserved2')) is not None:
        effect = ET.Element(tag, value=number(f['reserved2']))
    elif tag == 'boostskillcastingtime' and number(f.get('reserved2')) is not None:
        category = norm(f.get('reserved3'))
        stats = {'heal': 'BOOST_CASTING_TIME_HEAL', 'attack': 'BOOST_CASTING_TIME_ATTACK',
                 'summontrap': 'BOOST_CASTING_TIME_TRAP', 'none': 'BOOST_CASTING_TIME', '': 'BOOST_CASTING_TIME'}
        if category not in stats:
            return None
        effect = ET.Element(tag)
        ET.SubElement(effect, 'change', stat=stats[category], func='PERCENT', value=number(f['reserved2']))
    elif tag == 'snare' and number(f.get('reserved2')) is not None:
        effect = ET.Element(tag)
        for stat in ['SPEED', 'FLY_SPEED']:
            ET.SubElement(effect, 'change', stat=stat, func='PERCENT', value=str(-int(number(f['reserved2']))))
    elif tag == 'provoker' and skill_ids:
        linked = skill_ids.get(f.get('reserved17', '').lower())
        target = f.get('reserved14', '').upper()
        hit = f.get('reserved_cond1', '').upper()
        if linked is None or target not in {'ME', 'OPPONENT'} or hit not in {'EVERYHIT', 'NMLATK', 'MAHIT', 'PHHIT', 'BACKATK', 'DODGEHIT', 'PARRYHIT'}:
            return None
        effect = ET.Element(tag, skill_id=linked, provoke_target=target)
    elif tag in {'dispeldebuffphysical', 'dispeldebuffmental'}:
        value = number(f.get('reserved2'))
        power = number(f.get('reserved18'))
        dispel_level = number(f.get('reserved16'))
        if None in {value, power, dispel_level}:
            return None
        effect = ET.Element(tag, value=value, power=power, dispel_level=dispel_level)
    elif tag == 'dispel' and norm(f.get('reserved1')) == 'effectid':
        ids = [number(f.get(f'reserved{i}')) for i in range(2, 10)]
        ids = [value for value in ids if value not in {None, '0'}]
        count = number(f.get('reserved14'))
        dispel_level = number(f.get('reserved16'))
        power = number(f.get('reserved18'))
        if not ids or None in {count, dispel_level, power}:
            return None
        effect = ET.Element(tag, dispeltype='EFFECTID', count=count,
                            dispel_level=dispel_level, power=power)
        for effect_id in ids:
            ET.SubElement(effect, 'effectids').text = effect_id
    elif tag == 'alwaysresist':
        value = number(f.get('reserved9'))
        if value is None or not f.get('remain2'):
            return None
        effect = ET.Element(tag, value=value)
    elif tag == 'reflector':
        hitvalue = number(f.get('reserved2'))
        radius = number(f.get('reserved5'))
        if hitvalue is None or radius is None or not f.get('remain2'):
            return None
        effect = ET.Element(tag, hitvalue=hitvalue, radius=radius, value='0')
    elif tag in OVERTIME and float(f.get('checktime') or 0) > 0:
        effect = ET.Element(tag, checktime=number(f['checktime']))
    elif tag in {'stun', 'silence', 'blind', 'root', 'sleep', 'paralyze', 'confuse', 'shield'}:
        if not f.get('remain2'):
            return None
        effect = ET.Element(tag)
    elif tag == 'deboostheal':
        value = number(f.get('reserved2'))
        if value is None:
            return None
        effect = ET.Element(tag)
        ET.SubElement(effect, 'change', stat='HEAL_SKILL_DEBOOST', func='PERCENT', value=str(-abs(int(value))))
    else:
        return None
    update_effect(effect, f, skill_ids, blending_combinations, npc_ids)
    return effect


def update_effect(effect, f, skill_ids=None, blending_combinations=None, npc_ids=None):
    for attr, field in COMMON.items():
        if attr == 'checktime' and norm(effect.tag) not in OVERTIME and attr not in effect.attrib:
            continue
        if attr in {'critprobmod2', 'preeffect_prob', 'hittypeprob2'} and f.get(field) == '100' and attr not in effect.attrib:
            continue
        set_if(effect, attr, number(f.get(field)))
    for attr, field in [('element', 'reserved10'), ('hoptype', 'hop_type'),
                        ('hittype', 'reserved_cond1')]:
        v = f.get(field)
        if attr == 'hittype' and (v or '').upper() not in {'EVERYHIT', 'NMLATK', 'MAHIT', 'PHHIT', 'FEAR', 'SKILL', 'BACKATK', 'DODGEHIT', 'PARRYHIT'}:
            continue
        if attr == 'hoptype' and (v or '').upper() not in {'DAMAGE', 'SKILLLV'}:
            continue
        if v and (attr != 'element' or v.upper() in {'NONE', 'FIRE', 'EARTH', 'WIND', 'WATER', 'LIGHT', 'DARK'}):
            effect.set(attr, v.upper())
    if 'noresist' in f:
        if f['noresist'] == '1' or 'noresist' in effect.attrib:
            effect.set('noresist', 'true' if f['noresist'] == '1' else 'false')
    if 'cond_preeffect' in f:
        indices = re.findall(r'e(\d+)', f['cond_preeffect'], re.I)
        if indices:
            effect.set('preeffect', ' '.join(indices))
    tag = norm(effect.tag)
    if tag == 'skillatk':
        # Duas duplas: dano fixo R1/R2, dano de arma R3/R4.
        pair = (1, 2) if float(f.get('reserved2') or 0) != 0 else (3, 4)
        set_if(effect, 'delta', number(f.get(f'reserved{pair[0]}')) or '0')
        set_if(effect, 'value', number(f.get(f'reserved{pair[1]}')) or '0')
    elif tag in INSTANT:
        set_if(effect, 'delta', number(f.get('reserved1')) or '0')
        set_if(effect, 'value', number(f.get('reserved2')) or '0')
        if tag in {'healinstant', 'mphealinstant', 'dphealinstant', 'fphealinstant', 'sphealinstant'} and 'reserved6' in f:
            effect.set('percent', 'true' if f['reserved6'] == '1' else 'false')
    elif tag in OVERTIME:
        set_if(effect, 'delta', number(f.get('reserved8')) or '0')
        set_if(effect, 'value', number(f.get('reserved9')) or '0')
    elif tag == 'shield':
        for attr, field in [('delta', 'reserved1'), ('value', 'reserved2'),
                            ('hitdelta', 'reserved7'), ('hitvalue', 'reserved8')]:
            set_if(effect, attr, number(f.get(field)))
    elif tag == 'shadowmove':
        set_if(effect, 'distance', number(f.get('reserved2')))
    elif tag == 'boostskillcost':
        set_if(effect, 'value', number(f.get('reserved2')))
    elif tag == 'boostskillcastingtime':
        for change in effect.findall('change'):
            set_if(change, 'value', number(f.get('reserved2')))
    elif tag == 'alwaysresist':
        set_if(effect, 'value', number(f.get('reserved9')))
    elif tag == 'reflector':
        set_if(effect, 'hitvalue', number(f.get('reserved2')))
        set_if(effect, 'radius', number(f.get('reserved5')))
        if 'value' in effect.attrib:
            effect.set('value', '0')
    elif tag == 'statsynergy':
        source = stats_for(f.get('reserved1'))
        target = stats_for(f.get('reserved2'))
        if len(source) == 1 and len(target) == 1:
            values = {'source': source[0], 'target': target[0],
                      'fixed_value': number(f.get('reserved3')),
                      'target_value': number(f.get('reserved4')),
                      'source_value': number(f.get('reserved5'))}
            target2 = stats_for(f.get('reserved7'))
            if len(target2) == 1:
                values.update(target2=target2[0], fixed_value2=number(f.get('reserved8')),
                              target_value2=number(f.get('reserved9')),
                              source_value2=number(f.get('reserved10')))
            synergy_names = {'source', 'target', 'source_value', 'target_value', 'fixed_value',
                             'target2', 'source_value2', 'target_value2', 'fixed_value2'}
            for name in synergy_names:
                effect.attrib.pop(name, None)
            effect.attrib.update({name: value for name, value in values.items() if value is not None})
    elif tag == 'blending':
        attributes = stack_blending_attributes(f, skill_ids, blending_combinations)
        if attributes is not None:
            # O atributo note pertence ao protocolo de notas do Luminess e não
            # pode sobreviver quando o mesmo tipo representa acúmulo por skill.
            for name in {'note', 'stack_level', 'skill_id', 'source_skills'}:
                effect.attrib.pop(name, None)
            effect.attrib.update(attributes)
    elif tag == 'shapechange' and npc_ids:
        model = npc_ids.get(f.get('reserved9', '').lower())
        transform_type = (f.get('reserved8') or 'NONE').upper()
        if model is not None:
            effect.set('model', model)
        if transform_type in {'AVATAR', 'FORM1', 'NONE', 'PC'}:
            effect.set('type', transform_type)
    elif tag == 'deform' and norm(f.get('reserved9')) in {'', 'none'}:
        effect.attrib.pop('model', None)
    elif tag == 'dispel' and norm(f.get('reserved1')) == 'effectid':
        effect.set('dispeltype', 'EFFECTID')
        set_if(effect, 'count', number(f.get('reserved14')))
        set_if(effect, 'dispel_level', number(f.get('reserved16')))
        set_if(effect, 'power', number(f.get('reserved18')))
        ids = [number(f.get(f'reserved{i}')) for i in range(2, 10)]
        ids = [value for value in ids if value not in {None, '0'}]
        for child in list(effect.findall('effectids')):
            effect.remove(child)
        for effect_id in ids:
            ET.SubElement(effect, 'effectids').text = effect_id
    if tag in STATS:
        tokens = [f.get(f'reserved{k}') for k in [13, 14]
                  if norm(f.get(f'reserved{k}')) not in {'', '0', 'none'}]
        official_stats = {stat for token in tokens for stat in stats_for(token)}
        actual_stats = {change.get('stat') for change in effect.findall('change')}
        if tokens and all(stats_for(token) for token in tokens) and official_stats != actual_stats:
            # O tipo pode continuar StatUp enquanto seus stats mudam na 5.0.
            # Só substitui a lista quando todos os tokens têm tradução conhecida.
            generated = build_confirmed_effect(f)
            if generated is not None:
                previous = {change.get('stat'): change for change in effect.findall('change')}
                for change in list(effect.findall('change')):
                    effect.remove(change)
                for change in generated.findall('change'):
                    old = previous.get(change.get('stat'))
                    if old is not None:
                        for condition in old:
                            change.append(copy.deepcopy(condition))
                    effect.append(change)
        # Só atualiza um change quando o stat identifica sua fonte oficial.
        for change in effect.findall('change'):
            if tag in {'statboost', 'weaponstatboost'}:
                sources = [(13, 4, 3, 'PERCENT')] if number(f.get('reserved4')) not in {None, '0'} else [(13, 2, 1, 'ADD')]
            else:
                sources = [(13, 2, 1, 'PERCENT' if f.get('reserved6') == '1' else 'ADD'),
                           (14, 4, 3, 'PERCENT' if f.get('reserved7') == '1' else 'ADD')]
            for slot, value_field, delta_field, func in sources:
                stats = stats_for(f.get(f'reserved{slot}'))
                if change.get('stat') not in stats:
                    continue
                value = number(f.get(f'reserved{value_field}'))
                if value is None:
                    break
                # StatDown inverte a contribuição; velocidade de ataque inverte
                # o sinal porque o servidor armazena o intervalo entre ataques.
                sign = -1 if tag == 'statdown' else 1
                if change.get('stat') in {'ATTACK_SPEED', 'BOOST_CASTING_TIME'}:
                    sign *= -1
                change.set('func', func)
                change.set('value', number(str(sign * float(value))))
                set_if(change, 'delta', number(str(sign * float(f.get(f'reserved{delta_field}') or 0))))
                break
    elif tag == 'boosthate':
        for change in effect.findall('change'):
            if change.get('stat') == 'BOOST_HATE':
                set_if(change, 'value', number(f.get('reserved2')))


def insert_group(skill, tag):
    group = skill.find(tag)
    if group is None:
        group = ET.Element(tag)
        order = ['properties', 'startconditions', 'useconditions', 'endconditions', 'effects', 'actions', 'motion']
        index = next((i for i, child in enumerate(skill) if child.tag in order and order.index(child.tag) > order.index(tag)), len(skill))
        skill.insert(index, group)
    return group


def update_costs(skill, client):
    parameter = client.get('cost_parameter', '').upper()
    if parameter not in {'MP', 'HP', 'HP_RATIO', 'SP'}:
        return
    # Campos ausentes não significam custo zero; só altera com evidência.
    for condition, action, value, delta, ratio in [
        ('mp', 'mpuse', client.get('cost_end') if parameter == 'MP' else None, client.get('cost_end_lv'), False),
        ('hp', 'hpuse', client.get('cost_end') if parameter in {'HP', 'HP_RATIO'} else None, client.get('cost_end_lv'), parameter == 'HP_RATIO'),
        ('sp', 'spuse', client.get('cost_sp'), None, False),
        ('dp', 'dpuse', client.get('cost_dp'), None, False),
    ]:
        v = number(value)
        if v is None:
            continue
        for group_tag, child_tag in [('startconditions', condition), ('actions', action)]:
            group = skill.find(group_tag)
            child = group.find(child_tag) if group is not None else None
            if float(v) == 0:
                if child is not None:
                    group.remove(child)
                continue
            if child is None:
                child = ET.SubElement(insert_group(skill, group_tag), child_tag)
            child.set('value', v)
            if condition in {'mp', 'hp'}:
                child.set('delta', number(delta) or '0')
            if condition == 'hp':
                child.set('ratio', str(ratio).lower())


def update_conditions(skill, client):
    """Sincroniza somente condições declaradas explicitamente pelo cliente."""
    if client.get('move_casting') == '1':
        group = skill.find('useconditions')
        if group is not None:
            for condition in list(group):
                if condition.tag in {'playermove', 'move_casting'} and condition.get('allow', 'false') == 'false':
                    group.remove(condition)
            if len(group) == 0:
                skill.remove(group)

    weapons = [name for name, field in WEAPON_FLAGS if client.get(field) == '1']
    left = client.get('required_leftweapon', '').upper()
    if weapons or left in {'SHIELD', 'DUAL'}:
        group = insert_group(skill, 'startconditions')
        weapon = group.find('weapon')
        if weapons:
            if weapon is None:
                weapon = ET.SubElement(group, 'weapon')
            weapon.set('weapon', ' '.join(weapons))
        left_condition = group.find('lefthandweapon')
        if left in {'SHIELD', 'DUAL'}:
            if left_condition is None:
                left_condition = ET.SubElement(group, 'lefthandweapon')
            left_condition.set('type', left)


def refresh(skill, client, issues, skill_ids=None, blending_combinations=None, npc_ids=None):
    if client.get('_official_name_id'):
        skill.set('nameId', str(client['_official_name_id']))
    for attr, field in [('activation', 'activation_attribute'), ('skilltype', 'type'), ('skillsubtype', 'sub_type')]:
        if client.get(field):
            skill.set(attr, client[field].upper())
    skill.set('duration', number(client.get('casting_delay')) or '0')
    skill.set('cooldown', str(int(float(client.get('delay_time') or 0)) // 100))
    set_if(skill, 'delayId', client.get('delay_id'))
    tslot = {'SPECIAL': 'SPEC', 'SPECIAL2': 'SPEC2'}.get(client.get('target_slot', '').upper(),
                                                       client.get('target_slot', '').upper())
    if tslot in {'BUFF', 'DEBUFF', 'CHANT', 'SPEC', 'SPEC2', 'BOOST', 'NOSHOW', 'NONE'}:
        skill.set('tslot', tslot)
    dispel = {'DEBUFFPHY': 'DEBUFF_PHYSICAL', 'DEBUFFMEN': 'DEBUFF_MENTAL',
              'NPC_DEBUFFPHY': 'NPC_DEBUFF_PHYSICAL'}.get(client.get('dispel_category', '').upper(),
                                                         client.get('dispel_category', '').upper())
    if dispel in {'NONE', 'ALL', 'BUFF', 'DEBUFF', 'DEBUFF_MENTAL', 'DEBUFF_PHYSICAL',
                  'EXTRA', 'NEVER', 'NPC_BUFF', 'NPC_DEBUFF_PHYSICAL', 'STUN'}:
        skill.set('dispel_category', dispel)
    set_if(skill, 'tslot_level', number(client.get('target_slot_level')))
    for attr, field in [('pvp_damage', 'pvp_damage_ratio'), ('pvp_duration', 'pvp_remain_time_ratio'),
                        ('req_dispel_level', 'dispel_level'), ('chain_skill_prob', 'chain_skill_prob2'),
                        ('cancel_rate', 'cancel_rate')]:
        set_if(skill, attr, number(client.get(field)))
    properties = skill.find('properties')
    if properties is not None:
        for attr, field in [('first_target', 'first_target'), ('target_relation', 'target_relation_restriction'),
                            ('target_type', 'target_range')]:
            if client.get(field):
                allowed = {
                    'first_target': {'TARGETORME', 'ME', 'MYPET', 'MYMASTER', 'TARGET', 'PASSIVE', 'TARGET_MYPARTY_NONVISIBLE', 'POINT'},
                    'target_relation': {'NONE', 'ENEMY', 'MYPARTY', 'ALL', 'FRIEND'},
                    'target_type': {'ONLYONE', 'PARTY', 'AREA', 'PARTY_WITHPET', 'POINT'},
                }
                if client[field].upper() not in allowed[attr]:
                    issues.append((skill.get('skill_id'), client.get('name'), attr, client[field], 'enum sem suporte'))
                    continue
                properties.set(attr, client[field].upper())
        for attr, field in [('first_target_range', 'first_target_valid_distance'), ('target_maxcount', 'target_maxcount'),
                            ('target_distance', 'target_range_opt1')]:
            set_if(properties, attr, number(client.get(field)))
        if 'add_wpn_range' in client:
            properties.set('awr', 'true' if client['add_wpn_range'] == '1' else 'false')
    update_costs(skill, client)
    update_conditions(skill, client)
    effects = skill.find('effects')
    if effects is None:
        return
    positions = sorted(int(m[1]) for key in client if (m := re.fullmatch(r'effect(\d+)_type', key)) and client[key])
    official = [(n, fields(client, n)) for n in positions]
    remaining = list(effects)
    aligned = []
    for n, f in official:
        candidates = [e for e in remaining if equivalent(e, f)]
        if not candidates and expected(f) == 'shapechange' and npc_ids:
            model = npc_ids.get(f.get('reserved9', '').lower())
            candidates = [e for e in remaining
                          if norm(e.tag) in {'polymorph', 'deform'} and model is not None and e.get('model') == model]
        exact_id = [e for e in candidates if f.get('effectid') and e.get('effectid') == f['effectid']]
        exact_position = [e for e in candidates if e.get('e') == str(n)]
        selected = exact_id if len(exact_id) == 1 else exact_position if len(exact_position) == 1 else candidates
        if len(selected) != 1:
            generated = build_confirmed_effect(f, skill_ids, blending_combinations, npc_ids) if not candidates else None
            if generated is not None:
                aligned.append((generated, n, f))
                continue
            issues.append((skill.get('skill_id'), client.get('name'), n, f['type'], 'sem correspondência única'))
            continue
        effect = selected[0]
        if expected(f) == 'shapechange':
            effect.tag = 'shapechange'
        remaining.remove(effect)
        aligned.append((effect, n, f))
    # Reordenar só quando TODOS os efeitos canônicos têm correspondência.
    # Isto também remove efeitos antigos que desapareceram do cliente 5.0.
    complete = bool(official) and len(aligned) == len(official)
    if complete:
        effects[:] = [e for e, _, _ in aligned]
    for effect, n, f in aligned:
        if not complete and effect not in effects:
            continue
        if not complete and effect.get('e') != str(n):
            continue
        effect.set('e', str(n))
        update_effect(effect, f, skill_ids, blending_combinations, npc_ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cliente', default=DEFAULT_CLIENT_DIR)
    parser.add_argument('--aplicar', action='store_true')
    parser.add_argument('--saida-preview', help='grava o XML validado fora dos dados do servidor para revisão')
    args = parser.parse_args()
    client_path = Path(args.cliente) / 'data/skills/client_skills.xml'
    clients = {e.findtext('id'): {c.tag: (c.text or '').strip() for c in e}
               for e in ET.parse(client_path).getroot()}
    string_ids, _ = load_strings(args.cliente)
    for client in clients.values():
        official_name_id = string_ids.get(client.get('desc', '').upper())
        if official_name_id is not None:
            client['_official_name_id'] = official_name_id
    skill_ids = {c['name'].lower(): sid for sid, c in clients.items() if c.get('name')}
    npc_path = Path(args.cliente) / 'data/npcs/client_npcs.xml'
    npc_ids = {npc.findtext('name').lower(): npc.findtext('id')
               for npc in ET.parse(npc_path).getroot()
               if npc.findtext('name') and npc.findtext('id')}
    blending_path = Path(args.cliente) / 'data/PC/client_bledingskill_combination.xml'
    blending_combinations = {}
    for combination in ET.parse(blending_path).getroot():
        name = combination.findtext('name')
        result = combination.findtext('blended_skill')
        requirements = []
        group = combination.find('blending_combination')
        if group is not None:
            for requirement in group.findall('data'):
                skills = [value.strip() for value in (requirement.findtext('condition_skill') or '').split(',')
                          if value.strip()]
                requirements.append({'skills': skills,
                                     'stack_level': requirement.findtext('stack_level')})
        if name and result:
            blending_combinations[name.lower()] = {'result': result, 'requirements': requirements}
    relative = Path('skills/skill_templates.xml')
    source = Path(backup_manager.SERVER_DATA_DIR) / relative
    text = source.read_bytes().decode('utf-8')
    issues, changes = [], []
    counts = collections.Counter()
    def replace(match):
        skill = ET.fromstring(match.group(0).strip())
        client = clients.get(skill.get('skill_id'))
        if client is None:
            return match.group(0)
        before = semantic_xml(skill)
        old = copy.deepcopy(skill)
        refresh(skill, client, issues, skill_ids, blending_combinations, npc_ids)
        if semantic_xml(skill) == before:
            return match.group(0)
        for key in set(old.attrib) | set(skill.attrib):
            if old.get(key) != skill.get(key):
                counts[key] += 1
        changes.append((skill.get('skill_id'), client.get('name')))
        ET.indent(skill, space='\t', level=1)
        return '\t' + ET.tostring(skill, encoding='unicode')
    result = BLOCK.sub(replace, text)
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(str(source.parent / 'skills.xsd')))
    schema.assertValid(etree.fromstring(result.encode('utf-8')))
    report = Path(__file__).with_name('relatorio_refresh_skills_50.txt')
    report_text = ('Templates completos atualizados com client_skills.xml Classic 5.0.\n'
                      f'Templates alterados: {len(changes)}\nAtributos: {dict(counts)}\n'
                      f'Efeitos que exigem revisão estrutural: {len(issues)}\n\n'
                      + '\n'.join(f'{sid}\t{name}' for sid, name in changes)
                      + '\n\nRevisão estrutural (não inferida):\n'
                      + '\n'.join('\t'.join(map(str, issue)) for issue in issues) + '\n')
    if changes or not report.exists():
        report.write_text(report_text, encoding='utf-8')
    if args.saida_preview:
        Path(args.saida_preview).write_bytes(result.encode('utf-8'))
    print(f'Templates alterados: {len(changes)}; atributos: {dict(counts)}; revisão estrutural: {len(issues)}; XSD válido.')
    if args.aplicar:
        backup_manager.backup_file_before_modification(str(relative))
        for base in [backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR]:
            (Path(base) / relative).write_bytes(result.encode('utf-8'))


if __name__ == '__main__':
    main()
