import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(TOOLS_DIR)))
import os

BASE_DIR = os.path.join(PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0")

classes = [
    "01_Soul_Reaper",
    "02_Phoenix",
    "03_Gladiator",
    "04_Templar",
    "05_Assassin",
    "06_Ranger",
    "07_Sorcerer",
    "08_SpiritMaster",
    "09_Cleric",
    "10_Chanter",
    "11_Revenant",
    "12_Brawler",
    "13_Luminess",
    "Deslogue_Intermediario"
]

folders = [
    "01_Login_World/Elyos",
    "01_Login_World/Asmodians",
    "02_Character_Creation/Elyos",
    "02_Character_Creation/Asmodians",
]

# Tutorial folders for Elyos and Asmodians
for race in ["Elyos", "Asmodians"]:
    for cls in classes:
        folders.append(f"03_Tutorial/{race}/{cls}")

# Quests folders
folders.extend([
    "04_Realizando_Missoes/Elyos/Campanha_Poeta",
    "04_Realizando_Missoes/Elyos/Campanha_Verteron",
    "04_Realizando_Missoes/Elyos/Campanha_Sanctum",
    "04_Realizando_Missoes/Elyos/Quests_Normais",
    "04_Realizando_Missoes/Elyos/Teleport_Locate_NPCs",
    "04_Realizando_Missoes/Asmodians/Campanha_Ishalgen",
    "04_Realizando_Missoes/Asmodians/Campanha_Altgard",
    "04_Realizando_Missoes/Asmodians/Campanha_Pandaemonium",
    "04_Realizando_Missoes/Asmodians/Quests_Normais",
    "04_Realizando_Missoes/Asmodians/Teleport_Locate_NPCs",
    "05_Combate_Skills/Elyos",
    "05_Combate_Skills/Asmodians",
    "06_Sistemas_Novos_5.0",
    "07_Deletar_Personagem_Voltar_Servidores/Elyos",
    "07_Deletar_Personagem_Voltar_Servidores/Asmodians"
])

for f in folders:
    target_path = os.path.join(BASE_DIR, f.replace('/', os.sep))
    os.makedirs(target_path, exist_ok=True)
    gitkeep = os.path.join(target_path, ".gitkeep")
    if not os.path.exists(gitkeep):
        with open(gitkeep, "w") as gk:
            gk.write("")

print(f"Created/verified {len(folders)} organized directory structures.")
