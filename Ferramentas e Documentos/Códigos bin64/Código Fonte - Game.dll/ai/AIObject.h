#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <memory>
#include <vector>
#include "AiCharContext.h"

struct Vec {
    float x, y, z;
    Vec(float _x = 0.0f, float _y = 0.0f, float _z = 0.0f) : x(_x), y(_y), z(_z) {}
};
using Vec3F = Vec;

typedef struct {
    uint32_t targetId;
    int32_t  hatePoints;
    float    lastDamageTime;
} AiHateEntry;

typedef struct {
    float x;
    float y;
    float z;
} AiWaypoint;

// Objeto base de IA e entidades do mundo extraído do RTTI do game.dll (.?AVAIObject@@)
class AIObject {
public:
    AIObject(uint32_t objectId, const std::string& name);
    virtual ~AIObject();

    virtual void Update();

    uint32_t GetObjectId() const { return m_objectId; }
    const std::string& GetName() const { return m_name; }

    void SetPosition(const Vec3F& pos) { m_position = pos; }
    const Vec3F& GetPosition() const { return m_position; }

    void SetSpawnPosition(const Vec3F& pos) { m_spawnPos = pos; }
    const Vec3F& GetSpawnPosition() const { return m_spawnPos; }

    AiCharContext* GetAiContext() { return m_pAiContext.get(); }

    // Gerenciamento de Threat / Hate Table (Tabela de Ameaça do Classic)
    void AddHate(uint32_t targetId, int32_t amount);
    void ReduceHate(uint32_t targetId, int32_t amount);
    void ClearHate();
    uint32_t GetTopHateTarget() const;
    int32_t GetHate(uint32_t targetId) const;
    bool HasHate() const { return !m_hateTable.empty(); }

    // Métricas de distância e Leash (Distância máxima de perseguição)
    float DistanceTo(const Vec3F& other) const;
    float DistanceToSpawn() const;
    bool IsOutOfLeash() const;
    void MoveTowards(const Vec3F& dest, float dt);
    void ResetToSpawn();

    // Combate e Saúde
    void TakeDamage(uint32_t attackerId, int32_t damage, bool isCrit);
    void Heal(uint32_t casterId, int32_t amount);
    bool IsDead() const { return m_isDead; }
    bool IsReturning() const { return m_isReturning; }
    void SetReturning(bool bReturning) { m_isReturning = bReturning; }

    int32_t GetHp() const { return m_hp; }
    int32_t GetMaxHp() const { return m_maxHp; }
    void SetHp(int32_t hp, int32_t maxHp) { m_hp = hp; m_maxHp = maxHp; }

    uint32_t GetTargetId() const { return m_targetId; }
    void SetTargetId(uint32_t targetId) { m_targetId = targetId; }

    float GetAttackRange() const { return m_attackRange; }
    void SetAttackRange(float range) { m_attackRange = range; }
    float GetAttackSpeed() const { return m_attackSpeed; }
    void SetAttackSpeed(float spd) { m_attackSpeed = spd; }

    bool CanAttack(float currentTime) const;
    void RecordAttack(float currentTime) { m_lastAttackTime = currentTime; }

    // Rotas de patrulha
    void AddWaypoint(float x, float y, float z);
    void UpdatePatrol(float dt);

private:
    uint32_t m_objectId;
    std::string m_name;
    Vec3F m_position;
    Vec3F m_spawnPos;
    std::unique_ptr<AiCharContext> m_pAiContext;

    uint32_t m_targetId;
    float    m_leashDistance;
    float    m_aggroRadius;
    bool     m_isAggressive;
    bool     m_isReturning;
    bool     m_isDead;

    int32_t  m_hp;
    int32_t  m_maxHp;
    int32_t  m_mp;
    int32_t  m_maxMp;

    float    m_attackRange;
    float    m_attackSpeed;
    float    m_lastAttackTime;
    float    m_moveSpeed;
    float    m_returnSpeed;

    std::vector<AiHateEntry> m_hateTable;
    std::vector<AiWaypoint>  m_patrolWaypoints;
    size_t   m_currentWaypointIndex;
    float    m_patrolWaitTimer;
};
