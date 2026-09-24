import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(TOOLS_DIR)))
import os

output_dir = os.path.join(PROJECT_ROOT, "Produto Final\data\server\data\stats\player")

# 1. REAPER (Levels 1 to 10)
# Base: power=105, health=100, agility=115, accuracy=110, knowledge=110, will=95
# Lvl 1: HP 334, MP 375
def gen_reaper():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<player_stats_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../stats.xsd">']
    for lvl in range(1, 10):
        hp = int(334 + (lvl - 1) * 44 + (lvl - 1) * (lvl - 1) * 1.5)
        mp = int(375 + (lvl - 1) * 58 + (lvl - 1) * (lvl - 1) * 1.8)
        eva = 125 + (lvl - 1) * 12
        parry = 115 + (lvl - 1) * 12
        acc = 220 + (lvl - 1) * 8
        macc = 14 + (lvl - 1) * 14
        lines.append(f'\t<player_stats class="REAPER" level="{lvl}">')
        lines.append(f'\t\t<stats_template maxHp="{hp}" maxMp="{mp}" power="105" health="100" agility="115" accuracy="110" knowledge="110" will="95" walk_speed="1.5" run_speed="6" fly_speed="9" attack_speed="1.5" evasion="{eva}" block="0" parry="{parry}" main_hand_attack="18" main_hand_accuracy="{acc}" main_hand_crit_rate="10" magic_accuracy="{macc}" crit_spell="50"/>')
        lines.append('\t</player_stats>')
    lines.append('</player_stats_templates>')
    with open(os.path.join(output_dir, "reaper-templates.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# 2. SOUL_REAPER (Levels 10 to 65)
def gen_soul_reaper():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<player_stats_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../stats.xsd">']
    for lvl in range(10, 66):
        hp = int(780 + (lvl - 10) * 88 + (lvl - 10) * (lvl - 10) * 1.2)
        mp = int(920 + (lvl - 10) * 72 + (lvl - 10) * (lvl - 10) * 0.9)
        eva = 235 + (lvl - 10) * 12
        parry = 225 + (lvl - 10) * 12
        acc = 295 + (lvl - 10) * 8
        macc = 140 + (lvl - 10) * 14
        lines.append(f'\t<player_stats class="SOUL_REAPER" level="{lvl}">')
        lines.append(f'\t\t<stats_template maxHp="{hp}" maxMp="{mp}" power="105" health="100" agility="115" accuracy="110" knowledge="110" will="95" walk_speed="1.5" run_speed="6" fly_speed="9" attack_speed="1.5" evasion="{eva}" block="0" parry="{parry}" main_hand_attack="19" main_hand_accuracy="{acc}" main_hand_crit_rate="10" magic_accuracy="{macc}" crit_spell="50"/>')
        lines.append('\t</player_stats>')
    lines.append('</player_stats_templates>')
    with open(os.path.join(output_dir, "soul_reaper-templates.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# 3. LUMINESS (Levels 1 to 65)
# Base: power=95, health=95, agility=100, accuracy=105, knowledge=115, will=110
def gen_luminess():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<player_stats_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../stats.xsd">']
    for lvl in range(1, 66):
        hp = int(235 + (lvl - 1) * 62 + (lvl - 1) * (lvl - 1) * 0.8)
        mp = int(245 + (lvl - 1) * 85 + (lvl - 1) * (lvl - 1) * 1.1)
        eva = 110 + (lvl - 1) * 11
        parry = 95 + (lvl - 1) * 10
        acc = 210 + (lvl - 1) * 7
        macc = 20 + (lvl - 1) * 15
        lines.append(f'\t<player_stats class="LUMINESS" level="{lvl}">')
        lines.append(f'\t\t<stats_template maxHp="{hp}" maxMp="{mp}" power="95" health="95" agility="100" accuracy="105" knowledge="115" will="110" walk_speed="1.5" run_speed="6" fly_speed="9" attack_speed="1.5" evasion="{eva}" block="0" parry="{parry}" main_hand_attack="16" main_hand_accuracy="{acc}" main_hand_crit_rate="2" magic_accuracy="{macc}" crit_spell="50"/>')
        lines.append('\t</player_stats>')
    lines.append('</player_stats_templates>')
    with open(os.path.join(output_dir, "luminess-templates.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# 4. PHOENIX (Levels 1 to 65)
# Base: power=110, health=105, agility=95, accuracy=105, knowledge=105, will=100
def gen_phoenix():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<player_stats_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../stats.xsd">']
    for lvl in range(1, 66):
        hp = int(310 + (lvl - 1) * 78 + (lvl - 1) * (lvl - 1) * 1.1)
        mp = int(220 + (lvl - 1) * 65 + (lvl - 1) * (lvl - 1) * 0.9)
        eva = 105 + (lvl - 1) * 10
        parry = 120 + (lvl - 1) * 12
        acc = 215 + (lvl - 1) * 8
        macc = 16 + (lvl - 1) * 13
        lines.append(f'\t<player_stats class="PHOENIX" level="{lvl}">')
        lines.append(f'\t\t<stats_template maxHp="{hp}" maxMp="{mp}" power="110" health="105" agility="95" accuracy="105" knowledge="105" will="100" walk_speed="1.5" run_speed="6" fly_speed="9" attack_speed="1.5" evasion="{eva}" block="0" parry="{parry}" main_hand_attack="19" main_hand_accuracy="{acc}" main_hand_crit_rate="2" magic_accuracy="{macc}" crit_spell="50"/>')
        lines.append('\t</player_stats>')
    lines.append('</player_stats_templates>')
    with open(os.path.join(output_dir, "phoenix-templates.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

gen_reaper()
gen_soul_reaper()
gen_luminess()
gen_phoenix()

print("Generated templates: reaper, soul_reaper, luminess, phoenix in", output_dir)
