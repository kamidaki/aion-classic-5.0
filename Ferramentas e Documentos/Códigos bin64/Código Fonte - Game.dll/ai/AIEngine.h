#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <cmath>
#include <algorithm>

// Posição 3D Vector
struct AIVector3 {
    float x, y, z;

    float DistanceTo(const AIVector3& other) const {
        float dx = x - other.x;
        float dy = y - other.y;
        float dz = z - other.z;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }
};

// Item dropado no chão
struct GroundDropItem {
    uint32_t objectId;
    uint32_t itemId;
    uint32_t count;
    AIVector3 position;
    uint32_t droppedByMonsterId;
};

// -------------------------------------------------------------
// 4.2 Tabela de Ameaça e Ódio (Hate / Threat System)
// -------------------------------------------------------------
struct HateEntry {
    uint32_t targetId;
    int32_t  hatePoints;
    int32_t  totalDamageDealt;
    int32_t  totalHealDealt;
};

class HateTable {
public:
    HateTable();
    ~HateTable();

    // 4.2.1 Cálculo de Hate por dano direto (1 Dano = 1 Ponto de Hate)
    void AddDamageHate(uint32_t attackerId, int32_t damage);

    // 4.2.2 Cálculo de Hate por cura (1 Cura = 0.5 Ponto de Hate distribuído)
    void AddHealHate(uint32_t healerId, int32_t healAmount);

    // 4.2.3 Provocação / Taunt (+5000 Hate imediato)
    void AddTauntHate(uint32_t tankId, int32_t tauntBonus = 5000);

    // 4.2.4 Redução de Hate (Feigned Death / Calming Whispers)
    void ReduceHate(uint32_t targetId, float percentageReduction);
    void ClearHate(uint32_t targetId);
    void Reset();

    uint32_t GetMostHatedTarget() const;
    uint32_t GetTopHealerTarget() const;
    int32_t  GetHate(uint32_t targetId) const;
    bool     IsEmpty() const { return m_hateMap.empty(); }
    const std::unordered_map<uint32_t, HateEntry>& GetEntries() const { return m_hateMap; }

private:
    std::unordered_map<uint32_t, HateEntry> m_hateMap;
};

// -------------------------------------------------------------
// 4.3 Mecânicas de Chefe (Boss Phases & Enrage)
// -------------------------------------------------------------
enum class BossPhase : uint8_t {
    PHASE_1_100 = 1, // 100% a 75% HP
    PHASE_2_75  = 2, // 75% a 50% HP (Invoca Adds)
    PHASE_3_50  = 3, // 50% a 25% HP (Habilidade Suprema AoE)
    PHASE_4_25  = 4  // < 25% HP (Fase Final de Fúria)
};

struct BossState {
    uint32_t  bossId;
    int32_t   currentHp;
    int32_t   maxHp;
    BossPhase currentPhase;
    bool      addsSpawned;
    bool      isEnraged;
    uint64_t  combatStartTimeMs;
    uint32_t  enrageTimeoutMs; // ex: 600000 ms = 10 minutos
    float     damageMultiplier; // 1.0x normal, 5.0x no Enrage (500% de aumento)
};

// -------------------------------------------------------------
// 4.1 FSM do Monstro / NPC (Roam, Search, Threaten, Attack, Leash)
// -------------------------------------------------------------
enum class NpcAiState : uint8_t {
    REST,
    ROAM,
    SEARCH,
    THREATEN,
    ATTACK,
    FOLLOW,
    RETURN_LEASH
};

struct NpcAiEntity {
    uint32_t       objectId;
    std::string    name;
    AIVector3      spawnPosition;
    AIVector3      currentPosition;
    AIVector3      targetPosition;
    NpcAiState     state;
    HateTable      hateTable;
    uint32_t       currentTargetId;
    int32_t        currentHp;
    int32_t        maxHp;
    bool           isInvulnerable;
    float          aggroRadius;    // Raio de busca (ex: 15 metros)
    float          leashMaxRadius; // Raio máximo de coleira (50 metros)
    float          attackRange;    // Alcance do golpe (ex: 3 metros)
    uint64_t       stateEnterTimeMs;
    uint64_t       threatenDurationMs;
    std::vector<AIVector3> waypoints;
    size_t         currentWaypointIdx;
    bool           isBoss;
    BossState      bossInfo;
};

// -------------------------------------------------------------
// 4.4 Mascotes Funcionais (ToyPets)
// -------------------------------------------------------------
struct PetBagSlot {
    uint8_t  slotIndex;
    uint32_t itemId;
    uint32_t count;
};

struct ToyPetEntity {
    uint32_t petId;
    uint32_t masterId;
    uint8_t  masterRace; // 0: Elyos, 1: Asmodian
    AIVector3 position;
    bool     hasAutoLoot;
    bool     hasAutoDoping;
    bool     hasEnemyAlarm;
    uint8_t  petBagCapacity; // 6 a 32 slots
    std::vector<PetBagSlot> petBag;
    std::vector<uint32_t> dopingItemIds; // Scrolls e poções configurados
    bool     enemyAlarmTriggered;
    uint32_t detectedEnemyId;
};

// Motor Central de IA do Game.dll
class AIEngine {
public:
    static AIEngine& GetInstance();

    AIEngine();
    ~AIEngine();

    // Registro e Consulta de Entidades
    void RegisterNpc(const NpcAiEntity& npc);
    NpcAiEntity* GetNpc(uint32_t objectId);
    void UnregisterNpc(uint32_t objectId);

    // Ciclo de Atualização da Máquina de Estados (FSM)
    void UpdateFSM(uint32_t npcId, const std::vector<std::pair<uint32_t, AIVector3>>& nearbyPlayers, uint64_t currentTimeMs);

    // Sistema de Hate
    void NotifyDamageDealt(uint32_t npcId, uint32_t attackerId, int32_t damage);
    void NotifyHealApplied(uint32_t npcId, uint32_t healerId, int32_t healAmount);
    void NotifyTauntUsed(uint32_t npcId, uint32_t tankId, int32_t tauntHate = 5000);
    void NotifyHateDrop(uint32_t npcId, uint32_t targetId, float percentage);

    // Boss Mechanics
    void ProcessBossPhases(NpcAiEntity& npc, uint64_t currentTimeMs);

    // ToyPet Functions
    void RegisterToyPet(const ToyPetEntity& pet);
    ToyPetEntity* GetToyPet(uint32_t petId);
    bool ProcessPetAutoLoot(uint32_t petId, std::vector<GroundDropItem>& groundItems);
    bool ProcessPetAutoDoping(uint32_t petId, const std::vector<uint32_t>& activeMasterBuffs, std::vector<uint32_t>& consumedItems);
    bool ProcessPetEnemyAlarm(uint32_t petId, const std::vector<std::pair<uint32_t, std::pair<AIVector3, uint8_t>>>& playersInArea);

private:
    std::unordered_map<uint32_t, NpcAiEntity> m_npcs;
    std::unordered_map<uint32_t, ToyPetEntity> m_toyPets;
};
