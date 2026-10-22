#include "Player.h"
#include "../core/GameLog.h"
#include <cmath>

// Tabela canônica de Experiência do Aion Classic (Nível 1 ao 65)
static const int64_t s_ExpTable[66] = {
    0,
    400,             // Nível 1
    1400,            // Nível 2
    3600,            // Nível 3
    7600,            // Nível 4
    14200,           // Nível 5
    24200,           // Nível 6
    38600,           // Nível 7
    58400,           // Nível 8
    84800,           // Nível 9
    119000,          // Nível 10 (Ascensão Daeva)
    162600,          // Nível 11
    217400,          // Nível 12
    285200,          // Nível 13
    368000,          // Nível 14
    468000,          // Nível 15
    587400,          // Nível 16
    728600,          // Nível 17
    894200,          // Nível 18
    1087000,         // Nível 19
    1309800,         // Nível 20
    1565600,         // Nível 21
    1857600,         // Nível 22
    2189200,         // Nível 23
    2564000,         // Nível 24
    2985800,         // Nível 25
    3458600,         // Nível 26
    3986600,         // Nível 27
    4574200,         // Nível 28
    5226000,         // Nível 29
    5946800,         // Nível 30
    6741800,         // Nível 31
    7616400,         // Nível 32
    8576400,         // Nível 33
    9628000,         // Nível 34
    10777400,        // Nível 35
    12031200,        // Nível 36
    13396400,        // Nível 37
    14880200,        // Nível 38
    16490200,        // Nível 39
    18234600,        // Nível 40
    20121800,        // Nível 41
    22160600,        // Nível 42
    24360200,        // Nível 43
    26730000,        // Nível 44
    29280000,        // Nível 45
    32021000,        // Nível 46
    34964600,        // Nível 47
    38123200,        // Nível 48
    41510400,        // Nível 49
    45140200,        // Nível 50
    55648000,        // Nível 51
    68984000,        // Nível 52
    85652000,        // Nível 53
    106230000,       // Nível 54
    131370000,       // Nível 55
    165780000,       // Nível 56
    212640000,       // Nível 57
    275980000,       // Nível 58
    360780000,       // Nível 59
    473520000,       // Nível 60
    634580000,       // Nível 61
    862400000,       // Nível 62
    1184600000,      // Nível 63
    1638200000,      // Nível 64
    2278900000       // Nível 65 (Cap Máximo Classic)
};

// BasicObject
BasicObject::BasicObject(uint32_t id, const std::string& name) : m_id(id), m_name(name) {}
BasicObject::~BasicObject() {}

// NpcScriptMgr
NpcScriptMgr::NpcScriptMgr() {}
NpcScriptMgr::~NpcScriptMgr() {}
bool NpcScriptMgr::ExecuteScript(uint32_t npcId, const std::string& eventName) {
    if (npcId == 0 || eventName.empty()) {
        GameLog_Error("NpcScriptMgr: Parametros invalidos (npcId=%u)", npcId);
        return false;
    }
    GameLog_Info("NpcScriptMgr: Executando script para NPC=%u Evento='%s'", npcId, eventName.c_str());
    return true;
}

// Player
Player::Player(uint32_t objectId, const std::string& name, uint8_t playerClass, uint8_t race, uint8_t gender)
    : AIObject(objectId, name)
    , m_playerClass(playerClass)
    , m_race(race)
    , m_gender(gender)
    , m_level(1)
    , m_exp(0)
    , m_reposeEnergy(100.0f)
    , m_kinah(0)
    , m_ap(0)
    , m_raceStandingRank(0)
    , m_abyssRank(ABYSS_RANK_SOLDIER_9)
    , m_hp(100)
    , m_maxHp(100)
    , m_mp(100)
    , m_maxMp(100)
    , m_dp(0)
    , m_flightState(FLIGHT_NONE)
    , m_flightTime(60)
    , m_maxFlightTime(60)
    , m_soulSicknessTier(0)
    , m_bRegularStigmaQuest(false)
    , m_bGreaterStigmaQuest(false)
    , m_stigmaShards(0)
    , m_unlockedCubeSlots(27)
    , m_bInCombat(false)
    , m_combatTimer(0.0f)
    , m_targetObjectId(0)
{
    RecalculateStats();
    m_hp = m_maxHp;
    m_mp = m_maxMp;
    GameLog_Info("Player instanciado: Obj=%u Nome='%s' Classe=%u Raca=%u Nivel=%u HP=%d MP=%d",
        objectId, name.c_str(), playerClass, race, m_level, m_hp, m_mp);
}

Player::~Player() {
    GameLog_Info("Player destruido: Obj=%u Nome='%s'", GetObjectId(), GetName().c_str());
}

int64_t Player::GetMaxExpForLevel(uint32_t level) const {
    if (level < 1) return s_ExpTable[1];
    if (level >= 65) return s_ExpTable[65];
    return s_ExpTable[level];
}

void Player::SetLevel(uint32_t level) {
    if (level < 1) level = 1;
    if (level > 65) level = 65;
    m_level = level;
    RecalculateStats();
    m_hp = m_maxHp;
    m_mp = m_maxMp;
    GameLog_Info("Player::SetLevel: Jogador Obj=%u atingiu Nivel=%u", GetObjectId(), m_level);
}

void Player::AddExp(int64_t expGain) {
    if (expGain <= 0 || m_level >= 65) return;

    // Bônus de Energia de Repouso Classic (1.4x)
    if (m_reposeEnergy > 0.0f) {
        float bonus = static_cast<float>(expGain) * 0.4f;
        expGain += static_cast<int64_t>(bonus);
        m_reposeEnergy = (std::max)(0.0f, m_reposeEnergy - (bonus / 1000.0f));
    }

    m_exp += expGain;
    GameLog_Info("Player::AddExp: +%lld EXP (Total=%lld)", expGain, m_exp);

    while (m_level < 65) {
        int64_t needed = GetMaxExpForLevel(m_level);
        if (m_exp >= needed) {
            m_exp -= needed;
            m_level++;
            RecalculateStats();
            m_hp = m_maxHp;
            m_mp = m_maxMp;
            GameLog_Info(">>> LEVEL UP! Jogador Obj=%u atingiu Nivel %u! HP Max=%d MP Max=%d <<<",
                GetObjectId(), m_level, m_maxHp, m_maxMp);
        } else {
            break;
        }
    }
}

bool Player::AddKinah(int64_t amount) {
    if (amount <= 0) return false;
    if (m_kinah > INT64_MAX - amount) {
        m_kinah = INT64_MAX;
    } else {
        m_kinah += amount;
    }
    GameLog_Info("Player::AddKinah: +%lld Kinah (Total=%lld)", amount, m_kinah);
    return true;
}

bool Player::ConsumeKinah(int64_t amount) {
    if (amount <= 0) return true;
    if (m_kinah >= amount) {
        m_kinah -= amount;
        GameLog_Info("Player::ConsumeKinah: -%lld Kinah (Restante=%lld)", amount, m_kinah);
        return true;
    }
    return false;
}

void Player::SetAp(uint32_t ap) {
    if (ap > 20000000) ap = 20000000;
    m_ap = ap;
    UpdateAbyssRank();
}

void Player::AddAp(uint32_t amount) {
    SetAp(m_ap + amount);
}

bool Player::ConsumeAp(uint32_t amount) {
    if (amount == 0) return true;
    if (m_ap >= amount) {
        m_ap -= amount;
        UpdateAbyssRank();
        return true;
    }
    return false;
}

void Player::UpdateAbyssRank() {
    // Tabela Canônica e Oficial de Abyss Ranks do Aion Classic (100% AP e Quotas de Posição da Raça)
    if (m_ap < 1200)       m_abyssRank = ABYSS_RANK_SOLDIER_9;
    else if (m_ap < 4220)  m_abyssRank = ABYSS_RANK_SOLDIER_8;
    else if (m_ap < 10990) m_abyssRank = ABYSS_RANK_SOLDIER_7;
    else if (m_ap < 23500) m_abyssRank = ABYSS_RANK_SOLDIER_6;
    else if (m_ap < 42780) m_abyssRank = ABYSS_RANK_SOLDIER_5;
    else if (m_ap < 69700) m_abyssRank = ABYSS_RANK_SOLDIER_4;
    else if (m_ap < 105600) m_abyssRank = ABYSS_RANK_SOLDIER_3;
    else if (m_ap < 150800) m_abyssRank = ABYSS_RANK_SOLDIER_2;
    else if (m_ap < 214100) m_abyssRank = ABYSS_RANK_SOLDIER_1;
    else {
        // Postos de Oficiais e Generais: Requer AP mínimo E posição de ranking da raça (Quota)
        if (m_raceStandingRank == 1 && m_ap >= 1112400) {
            m_abyssRank = ABYSS_RANK_SUPREME_COMMANDER; // Governador (Top 1)
        } else if (m_raceStandingRank <= 3 && m_raceStandingRank > 0 && m_ap >= 946200) {
            m_abyssRank = ABYSS_RANK_COMMANDER;         // Comandante (Top 2-3)
        } else if (m_raceStandingRank <= 10 && m_raceStandingRank > 0 && m_ap >= 797000) {
            m_abyssRank = ABYSS_RANK_GREAT_GENERAL;     // Grande General (Top 4-10)
        } else if (m_raceStandingRank <= 30 && m_raceStandingRank > 0 && m_ap >= 664000) {
            m_abyssRank = ABYSS_RANK_GENERAL;           // General (Top 11-30)
        } else if (m_raceStandingRank <= 100 && m_raceStandingRank > 0 && m_ap >= 546400) {
            m_abyssRank = ABYSS_RANK_OFFICER_5;         // Oficial 5 Estrelas (Top 31-100)
        } else if (m_raceStandingRank <= 250 && m_raceStandingRank > 0 && m_ap >= 443400) {
            m_abyssRank = ABYSS_RANK_OFFICER_4;         // Oficial 4 Estrelas (Top 101-250)
        } else if (m_raceStandingRank <= 500 && m_raceStandingRank > 0 && m_ap >= 354200) {
            m_abyssRank = ABYSS_RANK_OFFICER_3;         // Oficial 3 Estrelas (Top 251-500)
        } else if (m_raceStandingRank <= 1000 && m_raceStandingRank > 0 && m_ap >= 278000) {
            m_abyssRank = ABYSS_RANK_OFFICER_2;         // Oficial 2 Estrelas (Top 501-1000)
        } else if (m_raceStandingRank <= 1500 && m_raceStandingRank > 0 && m_ap >= 214100) {
            m_abyssRank = ABYSS_RANK_OFFICER_1;         // Oficial 1 Estrela (Top 1001-1500)
        } else {
            m_abyssRank = ABYSS_RANK_SOLDIER_1;         // Soldado 1 caso fora da quota
        }
    }
}

void Player::SetHp(int32_t hp, int32_t maxHp) {
    if (maxHp > 0) m_maxHp = maxHp;
    m_hp = (std::max)(0, (std::min)(hp, m_maxHp));
}

void Player::ModifyHp(int32_t delta) {
    SetHp(m_hp + delta, m_maxHp);
}

void Player::SetMp(int32_t mp, int32_t maxMp) {
    if (maxMp > 0) m_maxMp = maxMp;
    m_mp = (std::max)(0, (std::min)(mp, m_maxMp));
}

void Player::ModifyMp(int32_t delta) {
    SetMp(m_mp + delta, m_maxMp);
}

void Player::SetDp(int32_t dp) {
    m_dp = (std::max)(0, (std::min)(dp, 4000));
}

void Player::AddDp(int32_t amount) {
    SetDp(m_dp + amount);
}

bool Player::ConsumeDp(int32_t amount) {
    if (amount <= 0) return true;
    if (m_dp >= amount) {
        m_dp -= amount;
        return true;
    }
    return false;
}

void Player::ResetDp() {
    m_dp = 0;
}

bool Player::StartFlight() {
    if (m_flightTime <= 0 || m_flightState == FLIGHT_WINDSTREAM) return false;
    m_flightState = FLIGHT_FLYING;
    GameLog_Info("Player::StartFlight: Jogador Obj=%u iniciou voo (Tempo restante: %ds)", GetObjectId(), m_flightTime);
    return true;
}

bool Player::StopFlight() {
    if (m_flightState == FLIGHT_FLYING) {
        m_flightState = FLIGHT_NONE;
        GameLog_Info("Player::StopFlight: Jogador Obj=%u pousou", GetObjectId());
        return true;
    }
    return false;
}

bool Player::StartGlide() {
    if (m_flightState == FLIGHT_NONE) {
        m_flightState = FLIGHT_GLIDING;
        return true;
    }
    return false;
}

bool Player::StopGlide() {
    if (m_flightState == FLIGHT_GLIDING) {
        m_flightState = FLIGHT_NONE;
        return true;
    }
    return false;
}

void Player::EnterWindstream() {
    m_flightState = FLIGHT_WINDSTREAM;
}

void Player::ExitWindstream() {
    if (m_flightState == FLIGHT_WINDSTREAM) {
        m_flightState = FLIGHT_GLIDING;
    }
}

void Player::UpdateFlight(float deltaSec) {
    if (m_flightState == FLIGHT_FLYING) {
        float consumed = deltaSec * 1.0f;
        if (m_flightTime > 0) {
            m_flightTime = (std::max)(0, static_cast<int32_t>(m_flightTime - consumed));
            if (m_flightTime == 0) {
                // Esgotou tempo de voo: entra em queda livre
                m_flightState = FLIGHT_NONE;
                GameLog_Warn("Player::UpdateFlight: Tempo de voo esgotado! Entidade Obj=%u caindo!", GetObjectId());
            }
        }
    } else if (m_flightState == FLIGHT_GLIDING) {
        // Planar consome metade da taxa de voo
        float consumed = deltaSec * 0.5f;
        if (m_flightTime > 0) {
            m_flightTime = (std::max)(0, static_cast<int32_t>(m_flightTime - consumed));
        }
    } else if (m_flightState == FLIGHT_NONE) {
        // Regeneração de voo no solo (+1s a cada 2 segundos)
        if (m_flightTime < m_maxFlightTime) {
            m_flightTime = (std::min)(m_maxFlightTime, static_cast<int32_t>(m_flightTime + (deltaSec * 0.5f)));
        }
    }
}

void Player::ApplyDeathPenalty() {
    if (m_soulSicknessTier < 3) {
        m_soulSicknessTier++;
    }
    RecalculateStats();
    GameLog_Warn("Player::ApplyDeathPenalty: Doenca de alma Nivel %u aplicada", m_soulSicknessTier);
}

bool Player::CureSoulSickness() {
    if (m_soulSicknessTier == 0) return false;
    int64_t cost = GetSoulHealerKinahCost();
    if (ConsumeKinah(cost)) {
        m_soulSicknessTier = 0;
        RecalculateStats();
        GameLog_Info("Player::CureSoulSickness: Doenca de alma curada por %lld Kinah", cost);
        return true;
    }
    return false;
}

int64_t Player::GetSoulHealerKinahCost() const {
    if (m_soulSicknessTier == 0) return 0;
    // Custo = Nivel * 120 * (Tier ^ 2)
    return static_cast<int64_t>(m_level) * 120 * (m_soulSicknessTier * m_soulSicknessTier);
}

bool Player::ActivateMantra(uint32_t skillId) {
    for (uint32_t m : m_activeMantras) {
        if (m == skillId) return true;
    }
    if (m_activeMantras.size() >= 3) {
        m_activeMantras.erase(m_activeMantras.begin());
    }
    m_activeMantras.push_back(skillId);
    RecalculateStats();
    return true;
}

bool Player::DeactivateMantra(uint32_t skillId) {
    for (auto it = m_activeMantras.begin(); it != m_activeMantras.end(); ++it) {
        if (*it == skillId) {
            m_activeMantras.erase(it);
            RecalculateStats();
            return true;
        }
    }
    return false;
}

bool Player::EquipItem(EquipSlotType slot, const EquippedItemData& item) {
    if (slot >= EQUIP_SLOT_COUNT) return false;
    m_equippedItems[slot] = item;
    RecalculateStats();
    return true;
}

bool Player::UnequipItem(EquipSlotType slot, EquippedItemData* outItem) {
    if (slot >= EQUIP_SLOT_COUNT) return false;
    if (m_equippedItems[slot].itemId == 0) return false;

    if (outItem) {
        *outItem = m_equippedItems[slot];
    }
    m_equippedItems[slot] = EquippedItemData();
    RecalculateStats();
    return true;
}

const EquippedItemData* Player::GetEquippedItem(EquipSlotType slot) const {
    if (slot >= EQUIP_SLOT_COUNT) return nullptr;
    return &m_equippedItems[slot];
}

bool Player::ExpandCube() {
    if (m_unlockedCubeSlots >= 108) return false;
    m_unlockedCubeSlots += 9;
    GameLog_Info("Player::ExpandCube: Cubo expandido para %u slots", m_unlockedCubeSlots);
    return true;
}

void Player::RecalculateStats() {
    PlayerAttributes attr = {};
    attr.moveSpeed = 6.0f;
    attr.flySpeed = 9.0f;
    attr.glideSpeed = 12.0f;
    attr.attackSpeed = 1.0f;
    attr.castSpeed = 1.0f;

    // 1. Atributos Base por Classe Canônica do Aion Classic
    switch (m_playerClass) {
    case CLASS_WARRIOR:
    case CLASS_GLADIATOR:
        attr.power = 110; attr.health = 110; attr.agility = 100; attr.accuracy = 100; attr.knowledge = 90; attr.will = 90;
        break;
    case CLASS_TEMPLAR:
        attr.power = 115; attr.health = 115; attr.agility = 90; attr.accuracy = 100; attr.knowledge = 85; attr.will = 95;
        break;
    case CLASS_SCOUT:
    case CLASS_ASSASSIN:
        attr.power = 100; attr.health = 95; attr.agility = 115; attr.accuracy = 115; attr.knowledge = 90; attr.will = 85;
        break;
    case CLASS_RANGER:
        attr.power = 100; attr.health = 90; attr.agility = 110; attr.accuracy = 120; attr.knowledge = 90; attr.will = 90;
        break;
    case CLASS_MAGE:
    case CLASS_SORCERER:
        attr.power = 90; attr.health = 85; attr.agility = 90; attr.accuracy = 95; attr.knowledge = 120; attr.will = 120;
        break;
    case CLASS_SPIRITMASTER:
        attr.power = 90; attr.health = 90; attr.agility = 90; attr.accuracy = 95; attr.knowledge = 115; attr.will = 120;
        break;
    case CLASS_PRIEST:
    case CLASS_CLERIC:
        attr.power = 105; attr.health = 105; attr.agility = 90; attr.accuracy = 90; attr.knowledge = 105; attr.will = 115;
        break;
    case CLASS_CHANTER:
        attr.power = 110; attr.health = 105; attr.agility = 95; attr.accuracy = 100; attr.knowledge = 95; attr.will = 105;
        break;
    case CLASS_THUNDERER: // Revenant / Executor
        attr.power = 110; attr.health = 100; attr.agility = 110; attr.accuracy = 105; attr.knowledge = 95; attr.will = 90;
        break;
    default:
        attr.power = 100; attr.health = 100; attr.agility = 100; attr.accuracy = 100; attr.knowledge = 100; attr.will = 100;
        break;
    }

    // 2. Crescimento Base por Nível Classic
    int32_t lvl = static_cast<int32_t>(m_level);
    attr.physicalAttack   = (attr.power * 2) + (lvl * 3);
    attr.physicalDefense  = (attr.health * 2) + (lvl * 5);
    attr.physicalAccuracy = (attr.accuracy * 2) + (lvl * 4);
    attr.physicalCritical = (attr.accuracy / 2) + 10;
    attr.evasion          = (attr.agility * 2) + (lvl * 3);
    attr.parry            = (attr.agility + attr.power) + (lvl * 2);
    attr.block            = (attr.health * 2) + (lvl * 2);

    attr.magicBoost       = (attr.knowledge * 3) + (lvl * 6);
    attr.magicDefense     = (attr.will * 2) + (lvl * 4);
    attr.magicAccuracy    = (attr.knowledge * 2) + (lvl * 4);
    attr.magicResist      = (attr.will * 2) + (lvl * 3);
    attr.magicSuppression = (attr.will + attr.knowledge) + (lvl * 3);
    attr.spellCritical    = (attr.knowledge / 3) + 5;

    int32_t computedHp = (attr.health * 25) + (lvl * 85);
    int32_t computedMp = (attr.will * 20) + (lvl * 65);

    // 3. Aplicação dos Bônus dos Itens Equipados e Pedras de Encantamento
    for (int i = 0; i < EQUIP_SLOT_COUNT; ++i) {
        const auto& eq = m_equippedItems[i];
        if (eq.itemId == 0) continue;

        computedHp            += eq.bonusHp;
        computedMp            += eq.bonusMp;
        attr.physicalAttack   += eq.bonusPhysicalAttack;
        attr.physicalDefense  += eq.bonusPhysicalDefense;
        attr.magicBoost       += eq.bonusMagicBoost;
        attr.magicResist      += eq.bonusMagicResist;
        attr.physicalAccuracy += eq.bonusAccuracy;
        attr.physicalCritical += eq.bonusCritical;
        attr.block            += eq.bonusBlock;
        attr.parry            += eq.bonusParry;
        attr.pvpAttackRatio   += eq.bonusPvpAttack;
        attr.pvpDefenseRatio  += eq.bonusPvpDefense;

        // Bônus adicional por nível de encantamento (+1 a +15)
        if (eq.enchantLevel > 0) {
            if (i == EQUIP_SLOT_MAIN_HAND || i == EQUIP_SLOT_OFF_HAND) {
                attr.physicalAttack += (eq.enchantLevel * 4);
                attr.magicBoost     += (eq.enchantLevel * 20);
            } else if (i >= EQUIP_SLOT_HELMET && i <= EQUIP_SLOT_BOOTS) {
                attr.physicalDefense += (eq.enchantLevel * 6);
                computedHp           += (eq.enchantLevel * 30);
            }
        }
    }

    // 4. Penalidade de Doença de Alma (Soul Sickness)
    if (m_soulSicknessTier > 0) {
        float penalty = 1.0f - (m_soulSicknessTier * 0.10f); // 10%, 20%, 30%
        computedHp = static_cast<int32_t>(computedHp * penalty);
        computedMp = static_cast<int32_t>(computedMp * penalty);
        attr.moveSpeed *= penalty;
        attr.flySpeed  *= penalty;
    }

    m_maxHp = (std::max)(50, computedHp);
    m_maxMp = (std::max)(50, computedMp);
    if (m_hp > m_maxHp) m_hp = m_maxHp;
    if (m_mp > m_maxMp) m_mp = m_maxMp;

    m_attributes = attr;
}

void Player::Update() {
    AIObject::Update();

    // Atualização de voo
    UpdateFlight(0.016f); // 60hz frame delta

    // Temporizador de combate (desengajamento após 5 segundos)
    if (m_bInCombat) {
        m_combatTimer += 0.016f;
        if (m_combatTimer >= 5.0f) {
            m_bInCombat = false;
            m_combatTimer = 0.0f;
            GameLog_Info("Player::Update: Jogador Obj=%u saiu do modo de combate", GetObjectId());
        }
    }
}
