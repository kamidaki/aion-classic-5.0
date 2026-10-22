#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <algorithm>
#include "../ai/AIObject.h"
#include "GameplayExt.h"
#include "CombatMath.h"

// Objeto base genérico (.?AVBasicObject@@)
class BasicObject {
public:
    BasicObject(uint32_t id, const std::string& name);
    virtual ~BasicObject();

    uint32_t GetId() const { return m_id; }
    const std::string& GetName() const { return m_name; }

private:
    uint32_t m_id;
    std::string m_name;
};

// Gerenciador de scripts de NPCs (.?AVNpcScriptMgr@@)
class NpcScriptMgr {
public:
    NpcScriptMgr();
    ~NpcScriptMgr();

    bool ExecuteScript(uint32_t npcId, const std::string& eventName);
};

// Enums Canônicos do Jogador no Aion Classic (Fiel ao Classic: SEM Bard, SEM Gunner, SEM Rider)
enum PlayerClass : uint8_t {
    CLASS_WARRIOR        = 0,
    CLASS_GLADIATOR      = 1,
    CLASS_TEMPLAR        = 2,
    CLASS_SCOUT          = 3,
    CLASS_ASSASSIN       = 4,
    CLASS_RANGER         = 5,
    CLASS_MAGE           = 6,
    CLASS_SORCERER       = 7,
    CLASS_SPIRITMASTER   = 8,
    CLASS_PRIEST         = 9,
    CLASS_CLERIC         = 10,
    CLASS_CHANTER        = 11,
    CLASS_THUNDERER      = 12 // Revenant / Executor (Adição exclusiva do Classic)
};

enum PlayerRace : uint8_t {
    RACE_ELYOS    = 0,
    RACE_ASMODIAN = 1
};

enum PlayerGender : uint8_t {
    GENDER_MALE   = 0,
    GENDER_FEMALE = 1
};

enum PlayerFlightState : uint8_t {
    FLIGHT_NONE        = 0,
    FLIGHT_FLYING      = 1,
    FLIGHT_GLIDING     = 2,
    FLIGHT_WINDSTREAM  = 3
};

// Postos do Abyss do Aion Classic (100% Abyss Points / AP e Quotas de Posição de Corrida da Raça)
enum AbyssRankType : uint8_t {
    ABYSS_RANK_SOLDIER_9 = 1,
    ABYSS_RANK_SOLDIER_8 = 2,
    ABYSS_RANK_SOLDIER_7 = 3,
    ABYSS_RANK_SOLDIER_6 = 4,
    ABYSS_RANK_SOLDIER_5 = 5,
    ABYSS_RANK_SOLDIER_4 = 6,
    ABYSS_RANK_SOLDIER_3 = 7,
    ABYSS_RANK_SOLDIER_2 = 8,
    ABYSS_RANK_SOLDIER_1 = 9,
    ABYSS_RANK_OFFICER_1 = 10,
    ABYSS_RANK_OFFICER_2 = 11,
    ABYSS_RANK_OFFICER_3 = 12,
    ABYSS_RANK_OFFICER_4 = 13,
    ABYSS_RANK_OFFICER_5 = 14,
    ABYSS_RANK_GENERAL   = 15,
    ABYSS_RANK_GREAT_GENERAL = 16,
    ABYSS_RANK_COMMANDER     = 17,
    ABYSS_RANK_SUPREME_COMMANDER = 18
};

enum EquipSlotType : uint8_t {
    EQUIP_SLOT_MAIN_HAND   = 0,
    EQUIP_SLOT_OFF_HAND    = 1,
    EQUIP_SLOT_HELMET      = 2,
    EQUIP_SLOT_TORSO       = 3,
    EQUIP_SLOT_LEGS        = 4,
    EQUIP_SLOT_SHOULDERS   = 5,
    EQUIP_SLOT_GLOVES      = 6,
    EQUIP_SLOT_BOOTS       = 7,
    EQUIP_SLOT_EARRING_1   = 8,
    EQUIP_SLOT_EARRING_2   = 9,
    EQUIP_SLOT_RING_1      = 10,
    EQUIP_SLOT_RING_2      = 11,
    EQUIP_SLOT_NECKLACE    = 12,
    EQUIP_SLOT_BELT        = 13,
    EQUIP_SLOT_WINGS       = 14,
    EQUIP_SLOT_PLUME       = 15,
    EQUIP_SLOT_BRACELET    = 16,
    EQUIP_SLOT_WAIST       = 17,
    EQUIP_SLOT_TITLE       = 18,
    EQUIP_SLOT_COUNT       = 20
};

typedef struct {
    // Atributos Primários Classic
    int32_t power;       // Força
    int32_t health;      // Vitalidade
    int32_t agility;     // Agilidade
    int32_t accuracy;    // Precisão
    int32_t knowledge;   // Conhecimento
    int32_t will;        // Vontade

    // Atributos Secundários de Combate
    int32_t physicalAttack;
    int32_t physicalDefense;
    int32_t physicalAccuracy;
    int32_t physicalCritical;
    int32_t evasion;
    int32_t parry;
    int32_t block;

    int32_t magicBoost;
    int32_t magicDefense;
    int32_t magicAccuracy;
    int32_t magicResist;
    int32_t magicSuppression;
    int32_t spellCritical;

    int32_t strikeResist;
    int32_t strikeFortify;

    float   moveSpeed;        // m/s (padrão 6.0)
    float   flySpeed;         // m/s (padrão 9.0)
    float   glideSpeed;       // m/s (padrão 12.0)
    float   attackSpeed;      // multiplicador de velocidade (1.0 = base)
    float   castSpeed;        // multiplicador de velocidade (1.0 = base)

    float   pvpAttackRatio;   // % de bônus PVP
    float   pvpDefenseRatio;  // % de mitigação PVP

    // Resistências Elementais
    int32_t fireResist;
    int32_t waterResist;
    int32_t windResist;
    int32_t earthResist;
    int32_t lightResist;
    int32_t darkResist;
} PlayerAttributes;

typedef struct {
    uint32_t itemId;
    uint32_t enchantLevel;
    uint32_t itemLevel;
    int32_t  bonusHp;
    int32_t  bonusMp;
    int32_t  bonusPhysicalAttack;
    int32_t  bonusPhysicalDefense;
    int32_t  bonusMagicBoost;
    int32_t  bonusMagicResist;
    int32_t  bonusAccuracy;
    int32_t  bonusCritical;
    int32_t  bonusBlock;
    int32_t  bonusParry;
    float    bonusPvpAttack;
    float    bonusPvpDefense;
    uint32_t godstoneItemId;
    uint32_t godstoneProcRate;
    std::vector<uint32_t> manastoneIds;
} EquippedItemData;

// Classe canônica do jogador (Player) extraída do RTTI (.?AVPlayer@@)
class Player : public AIObject, public CharacterObject {
public:
    Player(uint32_t objectId, const std::string& name, uint8_t playerClass, uint8_t race, uint8_t gender);
    virtual ~Player();

    virtual void Update() override;

    // Identificação Básica
    uint8_t GetPlayerClass() const { return m_playerClass; }
    void SetPlayerClass(uint8_t pClass) { m_playerClass = pClass; RecalculateStats(); }

    uint8_t GetRace() const { return m_race; }
    uint8_t GetGender() const { return m_gender; }

    // Nível e Experiência
    uint32_t GetLevel() const { return m_level; }
    void SetLevel(uint32_t level);
    int64_t GetExp() const { return m_exp; }
    int64_t GetMaxExpForLevel(uint32_t level) const;
    void AddExp(int64_t expGain);
    float GetReposeEnergy() const { return m_reposeEnergy; }
    void AddReposeEnergy(float amount) { m_reposeEnergy = (std::min)(100.0f, m_reposeEnergy + amount); }

    // Economia e Pontos do Abyss (Classic: 100% AP, Zero GP)
    int64_t GetKinah() const { return m_kinah; }
    void SetKinah(int64_t kinah) { m_kinah = (std::max)((int64_t)0, kinah); }
    bool AddKinah(int64_t amount);
    bool ConsumeKinah(int64_t amount);

    uint32_t GetAp() const { return m_ap; }
    void SetAp(uint32_t ap);
    void AddAp(uint32_t amount);
    bool ConsumeAp(uint32_t amount);

    uint32_t GetRaceStandingRank() const { return m_raceStandingRank; }
    void SetRaceStandingRank(uint32_t rank) { m_raceStandingRank = rank; UpdateAbyssRank(); }

    AbyssRankType GetAbyssRank() const { return m_abyssRank; }
    void UpdateAbyssRank();

    // Vida, Mana e Pontos Divinos
    int32_t GetHp() const { return m_hp; }
    int32_t GetMaxHp() const { return m_maxHp; }
    void SetHp(int32_t hp, int32_t maxHp);
    void ModifyHp(int32_t delta);

    int32_t GetMp() const { return m_mp; }
    int32_t GetMaxMp() const { return m_maxMp; }
    void SetMp(int32_t mp, int32_t maxMp);
    void ModifyMp(int32_t delta);

    int32_t GetDp() const { return m_dp; }
    int32_t GetMaxDp() const { return 4000; }
    void SetDp(int32_t dp);
    void AddDp(int32_t amount);
    bool ConsumeDp(int32_t amount);
    void ResetDp();

    // Sistema de Voo e Asas
    PlayerFlightState GetFlightState() const { return m_flightState; }
    bool IsFlying() const { return m_flightState == FLIGHT_FLYING; }
    bool IsGliding() const { return m_flightState == FLIGHT_GLIDING; }
    bool StartFlight();
    bool StopFlight();
    bool StartGlide();
    bool StopGlide();
    void EnterWindstream();
    void ExitWindstream();

    int32_t GetFlightTime() const { return m_flightTime; }
    int32_t GetMaxFlightTime() const { return m_maxFlightTime; }
    void SetFlightTime(int32_t ft) { m_flightTime = (std::max)(0, (std::min)(ft, m_maxFlightTime)); }
    void UpdateFlight(float deltaSec);

    // Sistema de Doença de Alma (Soul Sickness)
    uint8_t GetSoulSicknessTier() const { return m_soulSicknessTier; }
    void ApplyDeathPenalty();
    bool CureSoulSickness();
    int64_t GetSoulHealerKinahCost() const;

    // Missões e Slots de Estigma
    bool HasCompletedRegularStigmaQuest() const { return m_bRegularStigmaQuest; }
    void SetCompletedRegularStigmaQuest(bool done) { m_bRegularStigmaQuest = done; }

    bool HasCompletedGreaterStigmaQuest() const { return m_bGreaterStigmaQuest; }
    void SetCompletedGreaterStigmaQuest(bool done) { m_bGreaterStigmaQuest = done; }

    uint32_t GetStigmaShards() const { return m_stigmaShards; }
    void SetStigmaShards(uint32_t shards) { m_stigmaShards = shards; }

    // Mantras Ativos (Chanter)
    const std::vector<uint32_t>& GetActiveMantras() const { return m_activeMantras; }
    std::vector<uint32_t>& GetActiveMantras() { return m_activeMantras; }
    bool ActivateMantra(uint32_t skillId);
    bool DeactivateMantra(uint32_t skillId);

    // Equipamento e Atributos Calculados
    bool EquipItem(EquipSlotType slot, const EquippedItemData& item);
    bool UnequipItem(EquipSlotType slot, EquippedItemData* outItem = nullptr);
    const EquippedItemData* GetEquippedItem(EquipSlotType slot) const;

    const PlayerAttributes& GetAttributes() const { return m_attributes; }
    void RecalculateStats();

    // Inventário (Cubo)
    uint32_t GetUnlockedCubeSlots() const { return m_unlockedCubeSlots; }
    bool ExpandCube();

    // Estado de Combate e Alvo
    bool IsInCombat() const { return m_bInCombat; }
    void SetInCombat(bool inCombat) { m_bInCombat = inCombat; m_combatTimer = 0.0f; }
    uint32_t GetTargetObjectId() const { return m_targetObjectId; }
    void SetTargetObjectId(uint32_t targetId) { m_targetObjectId = targetId; }

private:
    uint8_t           m_playerClass;
    uint8_t           m_race;
    uint8_t           m_gender;
    uint32_t          m_level;
    int64_t           m_exp;
    float             m_reposeEnergy;
    int64_t           m_kinah;
    uint32_t          m_ap;
    uint32_t          m_raceStandingRank;
    AbyssRankType     m_abyssRank;

    int32_t           m_hp;
    int32_t           m_maxHp;
    int32_t           m_mp;
    int32_t           m_maxMp;
    int32_t           m_dp;

    PlayerFlightState m_flightState;
    int32_t           m_flightTime;
    int32_t           m_maxFlightTime;

    uint8_t           m_soulSicknessTier;
    bool              m_bRegularStigmaQuest;
    bool              m_bGreaterStigmaQuest;
    uint32_t          m_stigmaShards;
    std::vector<uint32_t> m_activeMantras;

    uint32_t          m_unlockedCubeSlots;
    bool              m_bInCombat;
    float             m_combatTimer;
    uint32_t          m_targetObjectId;

    PlayerAttributes  m_attributes;
    EquippedItemData  m_equippedItems[EQUIP_SLOT_COUNT];
};
