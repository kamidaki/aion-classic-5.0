"""Regressões dos campos oficiais e das unidades usadas pelo skill engine."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'parsersXML'))
from refresh_50_skills import build_confirmed_effect, refresh, semantic_xml, update_effect
from build_50_player_skill_effects import build_effect_block, clone_from_earlier_grade


class RefreshSkillsTest(unittest.TestCase):
    def test_cooldown_and_cast_have_different_units(self):
        skill = ET.fromstring('<skill_template cooldown="60" duration="0"/>')
        refresh(skill, {'delay_time': '60000', 'casting_delay': '2500'}, [])
        self.assertEqual('600', skill.get('cooldown'))
        self.assertEqual('2500', skill.get('duration'))

    def test_damage_uses_delta_from_same_pair_including_zero(self):
        effect = ET.fromstring('<skillatk value="11" delta="8"/>')
        update_effect(effect, {'reserved1': '17', 'reserved2': '0', 'reserved3': '0', 'reserved4': '22'})
        self.assertEqual('22', effect.get('value'))
        self.assertEqual('0', effect.get('delta'))

    def test_overtime_uses_periodic_pair_and_milliseconds(self):
        effect = ET.fromstring('<spellatk value="100" delta="0" checktime="2"/>')
        update_effect(effect, {'reserved1': '0', 'reserved2': '80', 'reserved8': '2', 'reserved9': '106', 'checktime': '3000'})
        self.assertEqual(('106', '2', '3000'), tuple(effect.get(k) for k in ['value', 'delta', 'checktime']))

    def test_effect_slots_are_not_list_indices(self):
        skill = ET.fromstring('<skill_template><effects><statdown e="1" effectid="22"/><skillatk e="2"/></effects></skill_template>')
        c = {'effect1_type': 'SkillATK_Instant', 'effect1_reserved4': '40',
             'effect2_type': 'StatDown', 'effect2_effectid': '22'}
        refresh(skill, c, [])
        self.assertEqual(['skillatk', 'statdown'], [e.tag for e in skill.find('effects')])
        self.assertEqual('40', skill.find('effects/skillatk').get('value'))

    def test_unresolved_type_cannot_receive_damage_numbers(self):
        skill = ET.fromstring('<skill_template><effects><reflector e="1" value="7"/></effects></skill_template>')
        issues = []
        refresh(skill, {'effect1_type': 'Unsupported', 'effect1_reserved2': '100'}, issues)
        self.assertEqual('7', skill.find('effects/reflector').get('value'))
        self.assertTrue(issues)

    def test_zero_cost_removes_both_validation_and_consumption(self):
        skill = ET.fromstring('<skill_template><startconditions><mp value="40"/></startconditions><actions><mpuse value="40"/></actions></skill_template>')
        refresh(skill, {'cost_parameter': 'MP', 'cost_end': '0'}, [])
        self.assertIsNone(skill.find('startconditions/mp'))
        self.assertIsNone(skill.find('actions/mpuse'))

    def test_previous_grade_clone_updates_periodic_damage(self):
        previous = ET.fromstring('<skill_template skill_id="1"><effects><spellatk e="1" value="10" checktime="3000"/></effects></skill_template>')
        c = {'delay_time': '60000', 'effect1_type': 'SpellATK', 'effect1_reserved2': '900',
             'effect1_reserved9': '106', 'effect1_checktime': '3000'}
        clone = ET.fromstring(clone_from_earlier_grade(previous, '2', c))
        self.assertEqual('600', clone.get('cooldown'))
        self.assertEqual('106', clone.find('effects/spellatk').get('value'))

    def test_refresh_is_idempotent(self):
        skill = ET.fromstring('<skill_template><effects><skillatk e="1" value="1"/></effects></skill_template>')
        c = {'delay_time': '12000', 'effect1_type': 'SkillATK_Instant', 'effect1_reserved4': '22'}
        refresh(skill, c, [])
        once = ET.tostring(skill)
        refresh(skill, c, [])
        self.assertEqual(once, ET.tostring(skill))

    def test_stat_type_unchanged_but_contributions_changed(self):
        effect = ET.fromstring('<statup><change stat="PHYSICAL_ATTACK" func="ADD" value="10"/></statup>')
        update_effect(effect, {'type': 'StatUp', 'reserved13': 'maxhp', 'reserved2': '400', 'reserved1': '2'})
        change = effect.find('change')
        self.assertEqual(('MAXHP', '400', '2'), tuple(change.get(k) for k in ['stat', 'value', 'delta']))

    def test_statboost_fixed_value_replaces_legacy_percent(self):
        effect = ET.fromstring('<statboost><change stat="MAXHP" func="PERCENT" value="100"/></statboost>')
        update_effect(effect, {'type': 'StatBoost', 'reserved13': 'maxhp', 'reserved2': '100'})
        change = effect.find('change')
        self.assertEqual(('MAXHP', 'ADD', '100'), tuple(change.get(k) for k in ['stat', 'func', 'value']))

    def test_each_stat_uses_its_own_function_flag(self):
        effect = ET.fromstring('<statup><change stat="PHYSICAL_ATTACK" func="ADD" value="1"/><change stat="PHYSICAL_ACCURACY" func="ADD" value="1"/></statup>')
        update_effect(effect, {'type': 'StatUp', 'reserved13': 'phyattack', 'reserved2': '26', 'reserved6': '1',
                               'reserved14': 'hitaccuracy', 'reserved4': '50', 'reserved7': '0'})
        changes = {c.get('stat'): (c.get('func'), c.get('value')) for c in effect.findall('change')}
        self.assertEqual(('PERCENT', '26'), changes['PHYSICAL_ATTACK'])
        self.assertEqual(('ADD', '50'), changes['PHYSICAL_ACCURACY'])

    def test_confirmed_physical_dispel_uses_explicit_fields(self):
        effect = build_confirmed_effect({'type': 'DispelDebuffPhysical', 'reserved2': '1',
                                         'reserved16': '1', 'reserved18': '30',
                                         'hop_type': 'SkillLV', 'hop_b': '733', 'noresist': '1'})
        self.assertEqual(('dispeldebuffphysical', '1', '1', '30', '733'),
                         (effect.tag, effect.get('value'), effect.get('dispel_level'), effect.get('power'), effect.get('hopb')))

    def test_stub_generator_never_invents_unknown_effect(self):
        c = {'effect1_type': 'UnsupportedEffect', 'effect1_reserved2': '999'}
        self.assertIsNone(build_effect_block(c, 1, '999', {}, {}))

    def test_shapechange_is_not_treated_as_polymorph(self):
        skill = ET.fromstring('<skill_template><effects><polymorph e="1" model="1"/></effects></skill_template>')
        issues = []
        refresh(skill, {'effect1_type': 'ShapeChange', 'effect1_reserved9': 'unknown'}, issues)
        self.assertTrue(issues)
        self.assertEqual('1', skill.find('effects/polymorph').get('model'))

    def test_shapechange_converts_only_matching_official_model(self):
        skill = ET.fromstring('<skill_template><effects>'
                              '<polymorph e="1" model="202500" type="PC" cantJump="true"/>'
                              '</effects></skill_template>')
        issues = []
        refresh(skill, {'effect1_type': 'ShapeChange', 'effect1_reserved8': 'PC',
                        'effect1_reserved9': 'LycanL', 'effect1_remain2': '120000'},
                issues, npc_ids={'lycanl': '202500'})
        effect = skill.find('effects/shapechange')
        self.assertIsNotNone(effect)
        self.assertEqual(('202500', 'PC', 'true', '120000'),
                         tuple(effect.get(k) for k in ['model', 'type', 'cantJump', 'duration2']))
        self.assertFalse(issues)

    def test_partial_alignment_does_not_reorder_other_effects(self):
        skill = ET.fromstring('<skill_template><effects><skillatk e="2" value="7"/><reflector e="1"/></effects></skill_template>')
        refresh(skill, {'effect1_type': 'SkillATK_Instant', 'effect1_reserved4': '100',
                        'effect2_type': 'Unsupported'}, [])
        self.assertEqual('2', skill.find('effects/skillatk').get('e'))
        self.assertEqual('7', skill.find('effects/skillatk').get('value'))

    def test_explicit_movement_permission_removes_legacy_block(self):
        skill = ET.fromstring('<skill_template><useconditions><playermove allow="false"/></useconditions></skill_template>')
        refresh(skill, {'move_casting': '1'}, [])
        self.assertIsNone(skill.find('useconditions'))

    def test_official_weapon_and_shield_conditions_replace_legacy_list(self):
        skill = ET.fromstring('<skill_template><startconditions><weapon weapon="GREATSWORD POLEARM"/></startconditions></skill_template>')
        refresh(skill, {'required_sword': '1', 'required_mace': '1', 'required_dagger': '1',
                        'required_leftweapon': 'Shield'}, [])
        self.assertEqual('DAGGER MACE SWORD', skill.find('startconditions/weapon').get('weapon'))
        self.assertEqual('SHIELD', skill.find('startconditions/lefthandweapon').get('type'))

    def test_new_class_weapon_flags_are_supported(self):
        skill = ET.fromstring('<skill_template/>')
        refresh(skill, {'required_gauntlet': '1', 'required_dimensionsword': '1', 'required_runesword': '1'}, [])
        self.assertEqual('DIMENSIONSWORD GAUNTLET RUNESWORD', skill.find('startconditions/weapon').get('weapon'))

    def test_always_resist_uses_explicit_duration_and_value(self):
        effect = build_confirmed_effect({'type': 'AlwaysResist', 'remain2': '10000',
                                         'reserved9': '2', 'effectid': '204'})
        self.assertEqual(('alwaysresist', '2', '10000', '204'),
                         (effect.tag, effect.get('value'), effect.get('duration2'), effect.get('effectid')))

    def test_effect_id_dispel_builds_ids_and_limits(self):
        effect = build_confirmed_effect({'type': 'Dispel', 'reserved1': 'Effect_ID',
                                         'reserved2': '154', 'reserved3': '151',
                                         'reserved14': '2', 'reserved16': '1', 'reserved18': '45'})
        self.assertEqual(('EFFECTID', '2', '1', '45'),
                         tuple(effect.get(k) for k in ['dispeltype', 'count', 'dispel_level', 'power']))
        self.assertEqual(['154', '151'], [e.text for e in effect.findall('effectids')])

    def test_elemental_defense_all_expands_to_four_resistances(self):
        effect = build_confirmed_effect({'type': 'StatUp', 'reserved13': 'ElementalDefendAll',
                                         'reserved2': '200', 'reserved6': '0'})
        self.assertEqual({'WATER_RESISTANCE', 'WIND_RESISTANCE', 'FIRE_RESISTANCE', 'EARTH_RESISTANCE'},
                         {change.get('stat') for change in effect.findall('change')})

    def test_reflector_uses_confirmed_counterchain_layout(self):
        effect = build_confirmed_effect({'type': 'Reflector', 'remain2': '20000',
                                         'reserved2': '700', 'reserved5': '30'})
        self.assertEqual(('700', '30', '0', '20000'),
                         tuple(effect.get(k) for k in ['hitvalue', 'radius', 'value', 'duration2']))

    def test_passive_deboost_heal_preserves_negative_percent(self):
        effect = build_confirmed_effect({'type': 'DeboostHealAmount', 'reserved2': '-20'})
        change = effect.find('change')
        self.assertEqual(('HEAL_SKILL_DEBOOST', 'PERCENT', '-20'),
                         tuple(change.get(k) for k in ['stat', 'func', 'value']))

    def test_stat_synergy_preserves_both_official_ratios(self):
        effect = build_confirmed_effect({'type': 'StatSynergy', 'reserved1': 'maxhp',
                                         'reserved2': 'HitAccuracy', 'reserved3': '0',
                                         'reserved4': '5', 'reserved5': '200', 'reserved6': '0',
                                         'reserved7': 'MagicalHitAccuracy', 'reserved8': '0',
                                         'reserved9': '3', 'reserved10': '200', 'reserved11': '0'})
        self.assertEqual('statsynergy', effect.tag)
        self.assertEqual(('MAXHP', 'PHYSICAL_ACCURACY', '200', '5',
                          'MAGICAL_ACCURACY', '200', '3'),
                         tuple(effect.get(k) for k in ['source', 'target', 'source_value', 'target_value',
                                                       'target2', 'source_value2', 'target_value2']))

    def test_stack_blending_resolves_official_combination(self):
        skill_ids = {'sys_rb_bladeassault': '9639',
                     **{f'rb_bladeassault_g{i}': str(4403 + i) for i in range(1, 6)}}
        combinations = {
            'blending_rb_bladeassault_g1': {
                'result': 'sys_RB_BladeAssault',
                'requirements': [{
                    'skills': [f'RB_BladeAssault_G{i}' for i in range(1, 6)],
                    'stack_level': '2',
                }],
            }
        }
        effect = build_confirmed_effect(
            {'type': 'Blending', 'reserved2': 'Blending_RB_BladeAssault_G1',
             'cond_preeffect': 'e1', 'noresist': '1'},
            skill_ids, combinations)
        self.assertEqual(('blending', '2', '9639', '4404 4405 4406 4407 4408', '1', 'true'),
                         (effect.tag, effect.get('stack_level'), effect.get('skill_id'),
                          effect.get('source_skills'), effect.get('preeffect'), effect.get('noresist')))

        legacy = ET.fromstring('<blending note="A"/>')
        update_effect(legacy,
                      {'type': 'Blending', 'reserved2': 'Blending_RB_BladeAssault_G1'},
                      skill_ids, combinations)
        self.assertIsNone(legacy.get('note'))
        self.assertEqual('2', legacy.get('stack_level'))

    def test_client_only_passives_keep_their_real_effect_types(self):
        flyboost = build_confirmed_effect({'type': 'FlyBoost', 'noresist': '1'})
        radar = build_confirmed_effect({'type': 'RadarAngle', 'reserved1': '300',
                                        'effectid': '139381', 'basiclv': '30', 'noresist': '1'})
        self.assertEqual(('flyboost', 'true'), (flyboost.tag, flyboost.get('noresist')))
        self.assertEqual(('radarangle', '300', '139381', '30', 'true'),
                         (radar.tag, radar.get('value'), radar.get('effectid'),
                          radar.get('basiclvl'), radar.get('noresist')))

    def test_control_is_distinct_from_its_visual_deform(self):
        skill = ET.fromstring('<skill_template><effects>'
                              '<deform e="1" effectid="20105" model="200000"/>'
                              '<deform e="2" effectid="175" model="220279"/>'
                              '</effects></skill_template>')
        client = {'effect1_type': 'Control', 'effect1_remain2': '7000',
                  'effect1_effectid': '20105', 'effect1_acc_mod2': '3000',
                  'effect1_reserved10': 'Earth',
                  'effect2_type': 'Deform', 'effect2_remain2': '7000',
                  'effect2_effectid': '175', 'effect2_reserved9': 'arcdrakanmaster_lupyllini'}
        refresh(skill, client, [])
        effects = list(skill.find('effects'))
        self.assertEqual(['control', 'deform'], [effect.tag for effect in effects])
        self.assertEqual(('20105', '7000', '3000', 'EARTH'),
                         tuple(effects[0].get(k) for k in ['effectid', 'duration2', 'accmod2', 'element']))
        self.assertIsNone(effects[0].get('model'))

    def test_provoker_preserves_dodge_and_parry_triggers(self):
        skill_ids = {'as_repeatevade_proc_g1': '91001', 'ch_steelstance_proc_g1': '91002'}
        dodge = build_confirmed_effect(
            {'type': 'Provoker', 'reserved17': 'AS_RepeatEvade_Proc_G1',
             'reserved14': 'Me', 'reserved_cond1': 'DodgeHit',
             'reserved_cond1_prob2': '1000'}, skill_ids)
        parry = build_confirmed_effect(
            {'type': 'Provoker', 'reserved17': 'CH_SteelStance_Proc_G1',
             'reserved14': 'Me', 'reserved_cond1': 'ParryHit',
             'reserved_cond1_prob2': '1000'}, skill_ids)
        self.assertEqual(('91001', 'ME', 'DODGEHIT', '1000'),
                         tuple(dodge.get(k) for k in ['skill_id', 'provoke_target', 'hittype', 'hittypeprob2']))
        self.assertEqual(('91002', 'ME', 'PARRYHIT', '1000'),
                         tuple(parry.get(k) for k in ['skill_id', 'provoke_target', 'hittype', 'hittypeprob2']))

    def test_deform_without_official_model_keeps_only_abnormal_state(self):
        effect = build_confirmed_effect(
            {'type': 'Deform', 'reserved8': 'None', 'reserved9': 'None',
             'remain2': '20000', 'effectid': '175', 'cond_preeffect': 'e1'})
        self.assertEqual(('deform', None, '20000', '175', '1'),
                         (effect.tag, effect.get('model'), effect.get('duration2'),
                          effect.get('effectid'), effect.get('preeffect')))

    def test_target_lock_uses_all_official_damage_fields(self):
        effect = build_confirmed_effect(
            {'type': 'TargetLock', 'reserved1': '1', 'reserved2': '80',
             'reserved3': '1', 'reserved4': '80', 'reserved5': '1',
             'reserved6': '10', 'reserved7': '30',
             'reserved8': 'RB_Isolation_G1_Caster', 'checktime': '1000',
             'remain2': '10000', 'effectid': '144681'},
            {'rb_isolation_g1_caster': '9638'})
        self.assertEqual(('9638', '1', '80', '1', '80', '1', '10', '30', '1000'),
                         tuple(effect.get(k) for k in ['skill_id', 'focus_delta', 'focus_value',
                                                       'cover_delta', 'cover_value', 'focus_drop_delta',
                                                       'focus_drop_value', 'range', 'checktime']))

    def test_semantic_comparison_ignores_only_indentation(self):
        compact = ET.fromstring('<effects><dispel e="1"><effectids>154</effectids></dispel></effects>')
        indented = ET.fromstring('<effects>\n\t<dispel e="1">\n\t\t<effectids>154</effectids>\n\t</dispel>\n</effects>')
        self.assertEqual(semantic_xml(compact), semantic_xml(indented))

    def test_official_template_metadata_are_synchronized(self):
        skill = ET.fromstring('<skill_template nameId="1" tslot="NONE" dispel_category="NONE"/>')
        refresh(skill, {'_official_name_id': '2281165', 'target_slot': 'Special',
                        'target_slot_level': '2', 'dispel_category': 'DebuffPhy'}, [])
        self.assertEqual(('2281165', 'SPEC', '2', 'DEBUFF_PHYSICAL'),
                         tuple(skill.get(k) for k in ['nameId', 'tslot', 'tslot_level', 'dispel_category']))


if __name__ == '__main__':
    unittest.main()
