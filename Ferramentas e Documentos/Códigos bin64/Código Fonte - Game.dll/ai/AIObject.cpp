#include "AIObject.h"
#include "AiCharContext.h"
#include "AiCharState.h"
#include "../core/GameLog.h"
#include <cmath>
#include <algorithm>

// Implementação de AiCharContext
AiCharContext::AiCharContext(AIObject* pOwner) 
    : m_pOwner(pOwner)
    , m_pCurrentState(std::make_unique<AiCharStateRest>())
{
}

AiCharContext::~AiCharContext() {}

void AiCharContext::ChangeState(std::unique_ptr<AiCharState> newState) {
    if (!newState) return;
    if (m_pCurrentState) {
        m_pCurrentState->OnExit(this);
    }
    m_pCurrentState = std::move(newState);
    m_pCurrentState->OnEnter(this);
}

void AiCharContext::Update() {
    if (m_pCurrentState) {
        m_pCurrentState->OnUpdate(this);
    }
}

// --- Estados Básicos de Ação ---
void AiCharStateAttack::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u Alvo=%u", GetStateName(), pContext->GetOwner()->GetObjectId(), pContext->GetOwner()->GetTargetId()); 
}

void AiCharStateAttack::OnUpdate(AiCharContext* pContext) {
    AIObject* pOwner = pContext->GetOwner();
    if (!pOwner || pOwner->IsDead() || pOwner->IsReturning()) return;

    uint32_t targetId = pOwner->GetTopHateTarget();
    if (targetId == 0) {
        pContext->ChangeState(std::make_unique<AiCharStateRest>());
        return;
    }

    if (pOwner->IsOutOfLeash()) {
        GameLog_Info("AiCharStateAttack: Obj=%u ultrapassou a Leash Distance (%0.1fm)! Retornando ao Spawn.",
                     pOwner->GetObjectId(), pOwner->DistanceToSpawn());
        pOwner->SetReturning(true);
        pOwner->ClearHate();
        pContext->ChangeState(std::make_unique<AiCharStateRest>());
        return;
    }

    // Executa golpe a cada intervalo de ataque canônico
    if (pOwner->CanAttack(1.0f)) {
        pOwner->RecordAttack(1.0f);
        GameLog_Info("AiCharStateAttack: Obj=%u desfere ataque basico contra Alvo=%u.",
                     pOwner->GetObjectId(), targetId);
    }
}

void AiCharStateAttack::OnExit(AiCharContext* pContext) {
    GameLog_Info("AiCharState [%s] EXIT Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId());
}

void AiCharStateFollow::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}

void AiCharStateFollow::OnUpdate(AiCharContext* pContext) {
    AIObject* pOwner = pContext->GetOwner();
    if (!pOwner || pOwner->IsDead()) return;

    if (pOwner->IsReturning()) {
        pOwner->MoveTowards(pOwner->GetSpawnPosition(), 0.05f);
        if (pOwner->DistanceToSpawn() < 1.0f) {
            pOwner->SetReturning(false);
            pOwner->SetHp(pOwner->GetMaxHp(), pOwner->GetMaxHp());
            pContext->ChangeState(std::make_unique<AiCharStateRest>());
        }
    }
}

void AiCharStateFollow::OnExit(AiCharContext* pContext) {
    GameLog_Info("AiCharState [%s] EXIT Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId());
}

void AiCharStateRest::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}

void AiCharStateRest::OnUpdate(AiCharContext* pContext) {
    AIObject* pOwner = pContext->GetOwner();
    if (!pOwner || pOwner->IsDead()) return;

    // Em repouso, recupera vida gradualmente se estiver fora de combate
    if (!pOwner->HasHate() && pOwner->GetHp() < pOwner->GetMaxHp()) {
        int32_t regen = pOwner->GetMaxHp() / 20; // 5% por tick
        if (regen < 1) regen = 1;
        pOwner->Heal(0, regen);
    }

    // Se receber ameaça de algum jogador, transita para ataque
    if (pOwner->HasHate()) {
        pContext->ChangeState(std::make_unique<AiCharStateAttack>());
    }
}

void AiCharStateRest::OnExit(AiCharContext* pContext) {
    GameLog_Info("AiCharState [%s] EXIT Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId());
}

void AiCharStateLooting::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Iniciando coleta de loot)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateLooting::OnUpdate(AiCharContext* pContext) {
    // Coleta o loot após delay de animação
    pContext->ChangeState(std::make_unique<AiCharStateFollow>());
}
void AiCharStateLooting::OnExit(AiCharContext* pContext) {}

void AiCharStateAlarm::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Detectou inimigo camuflado!)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateAlarm::OnUpdate(AiCharContext* pContext) {
    pContext->ChangeState(std::make_unique<AiCharStateAttack>());
}
void AiCharStateAlarm::OnExit(AiCharContext* pContext) {}

void AiCharStateDoping::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Aplicando item de doping/buff)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateDoping::OnUpdate(AiCharContext* pContext) {
    pContext->ChangeState(std::make_unique<AiCharStateFollow>());
}
void AiCharStateDoping::OnExit(AiCharContext* pContext) {}

void AiCharStateEatFeed::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Consumindo alimento do mascote)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateEatFeed::OnUpdate(AiCharContext* pContext) {
    pContext->ChangeState(std::make_unique<AiCharStateFollow_ToyPet>());
}
void AiCharStateEatFeed::OnExit(AiCharContext* pContext) {}

void AiCharStateEmotion::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Executando emote)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateEmotion::OnUpdate(AiCharContext* pContext) {
    pContext->ChangeState(std::make_unique<AiCharStateFollow>());
}
void AiCharStateEmotion::OnExit(AiCharContext* pContext) {}

// --- Estados Especializados de Combate (Healer / Tank) ---
void AiCharStateAttack_Healer::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Iniciando suporte de cura)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateAttack_Healer::OnUpdate(AiCharContext* pContext) {
    AIObject* pOwner = pContext->GetOwner();
    if (!pOwner || pOwner->IsDead()) return;
    // Healer prioriza suporte aos aliados
    if (pOwner->GetHp() < pOwner->GetMaxHp() / 2) {
        pOwner->Heal(pOwner->GetObjectId(), pOwner->GetMaxHp() / 4);
    }
}
void AiCharStateAttack_Healer::OnExit(AiCharContext* pContext) {}

void AiCharStateAttack_Tank::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Obj=%u (Iniciando provocação e absorção de dano)", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateAttack_Tank::OnUpdate(AiCharContext* pContext) {
    AIObject* pOwner = pContext->GetOwner();
    if (!pOwner || pOwner->IsDead()) return;
    // Tank aplica bônus de aggro (Taunt canônico de Templar/Gladiator)
    uint32_t target = pOwner->GetTopHateTarget();
    if (target != 0) {
        pOwner->AddHate(target, 500); // bônus de taunt
    }
}
void AiCharStateAttack_Tank::OnExit(AiCharContext* pContext) {}

void AiCharStateFollow_Healer::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateFollow_Healer::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateFollow_Healer::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateFollow_Tank::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateFollow_Tank::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateFollow_Tank::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateFollow_ToyPet::OnEnter(AiCharContext* pContext) { 
    GameLog_Info("AiCharState [%s] ENTER Mascote Obj=%u seguindo mestre", GetStateName(), pContext->GetOwner()->GetObjectId()); 
}
void AiCharStateFollow_ToyPet::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateFollow_ToyPet::OnExit(AiCharContext* pContext) { (void)pContext; }

// --- Estados Físicos e Movimentação ---
void AiCharStateJump::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateJump::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateJump::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateLand::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateLand::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateLand::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateEndJump::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateEndJump::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateEndJump::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateRoam::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateRoam::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateRoam::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateSearch::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateSearch::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateSearch::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateTakeOff::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateTakeOff::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateTakeOff::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateThreaten::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateThreaten::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateThreaten::OnExit(AiCharContext* pContext) { (void)pContext; }

void AiCharStateTremble::OnEnter(AiCharContext* pContext) { (void)pContext; }
void AiCharStateTremble::OnUpdate(AiCharContext* pContext) { (void)pContext; }
void AiCharStateTremble::OnExit(AiCharContext* pContext) { (void)pContext; }

// =========================================================================
// Implementação de AIObject (Mob, NPC, ToyPet no Aion Classic 5.0)
// =========================================================================
AIObject::AIObject(uint32_t objectId, const std::string& name)
    : m_objectId(objectId)
    , m_name(name)
    , m_position(0.0f, 0.0f, 0.0f)
    , m_spawnPos(0.0f, 0.0f, 0.0f)
    , m_targetId(0)
    , m_leashDistance(55.0f)
    , m_aggroRadius(16.0f)
    , m_isAggressive(false)
    , m_isReturning(false)
    , m_isDead(false)
    , m_hp(1000)
    , m_maxHp(1000)
    , m_mp(500)
    , m_maxMp(500)
    , m_attackRange(2.5f)
    , m_attackSpeed(1.8f)
    , m_lastAttackTime(0.0f)
    , m_moveSpeed(6.0f)
    , m_returnSpeed(12.0f)
    , m_currentWaypointIndex(0)
    , m_patrolWaitTimer(0.0f)
{
    m_pAiContext = std::make_unique<AiCharContext>(this);
}

AIObject::~AIObject() {}

void AIObject::Update() {
    if (m_isDead) return;

    if (m_isReturning) {
        MoveTowards(m_spawnPos, 0.05f);
        if (DistanceToSpawn() < 1.0f) {
            m_isReturning = false;
            m_hp = m_maxHp;
            ClearHate();
            if (m_pAiContext) {
                m_pAiContext->ChangeState(std::make_unique<AiCharStateRest>());
            }
        }
        return;
    }

    if (HasHate()) {
        if (IsOutOfLeash()) {
            GameLog_Info("AIObject: Obj=%u (%s) excedeu o limite do Leash (%0.1fm)! Abandonando alvo.",
                         m_objectId, m_name.c_str(), DistanceToSpawn());
            m_isReturning = true;
            ClearHate();
            if (m_pAiContext) {
                m_pAiContext->ChangeState(std::make_unique<AiCharStateRest>());
            }
            return;
        }
        m_targetId = GetTopHateTarget();
    } else {
        UpdatePatrol(0.05f);
    }

    if (m_pAiContext) {
        m_pAiContext->Update();
    }
}

void AIObject::AddHate(uint32_t targetId, int32_t amount) {
    if (m_isReturning || m_isDead || targetId == 0 || amount <= 0) return;

    for (auto& entry : m_hateTable) {
        if (entry.targetId == targetId) {
            entry.hatePoints += amount;
            return;
        }
    }

    AiHateEntry newEntry = { targetId, amount, 0.0f };
    m_hateTable.push_back(newEntry);

    if (m_targetId == 0) {
        m_targetId = targetId;
        if (m_pAiContext) {
            m_pAiContext->ChangeState(std::make_unique<AiCharStateAttack>());
        }
    }
}

void AIObject::ReduceHate(uint32_t targetId, int32_t amount) {
    for (auto it = m_hateTable.begin(); it != m_hateTable.end(); ++it) {
        if (it->targetId == targetId) {
            it->hatePoints -= amount;
            if (it->hatePoints <= 0) {
                m_hateTable.erase(it);
            }
            break;
        }
    }

    if (m_hateTable.empty()) {
        m_targetId = 0;
        if (!m_isReturning) {
            m_isReturning = true;
        }
    }
}

void AIObject::ClearHate() {
    m_hateTable.clear();
    m_targetId = 0;
}

uint32_t AIObject::GetTopHateTarget() const {
    if (m_hateTable.empty()) return 0;
    int32_t maxHate = -1;
    uint32_t topTarget = 0;
    for (const auto& entry : m_hateTable) {
        if (entry.hatePoints > maxHate) {
            maxHate = entry.hatePoints;
            topTarget = entry.targetId;
        }
    }
    return topTarget;
}

int32_t AIObject::GetHate(uint32_t targetId) const {
    for (const auto& entry : m_hateTable) {
        if (entry.targetId == targetId) return entry.hatePoints;
    }
    return 0;
}

float AIObject::DistanceTo(const Vec3F& other) const {
    float dx = m_position.x - other.x;
    float dy = m_position.y - other.y;
    float dz = m_position.z - other.z;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

float AIObject::DistanceToSpawn() const {
    return DistanceTo(m_spawnPos);
}

bool AIObject::IsOutOfLeash() const {
    return DistanceToSpawn() > m_leashDistance;
}

void AIObject::MoveTowards(const Vec3F& dest, float dt) {
    float dist = DistanceTo(dest);
    if (dist < 0.1f) return;

    float spd = m_isReturning ? m_returnSpeed : m_moveSpeed;
    float step = spd * dt;
    if (step > dist) step = dist;

    float dx = (dest.x - m_position.x) / dist;
    float dy = (dest.y - m_position.y) / dist;
    float dz = (dest.z - m_position.z) / dist;

    m_position.x += dx * step;
    m_position.y += dy * step;
    m_position.z += dz * step;
}

void AIObject::ResetToSpawn() {
    m_position = m_spawnPos;
    m_isReturning = false;
    m_hp = m_maxHp;
    ClearHate();
    if (m_pAiContext) {
        m_pAiContext->ChangeState(std::make_unique<AiCharStateRest>());
    }
}

void AIObject::TakeDamage(uint32_t attackerId, int32_t damage, bool isCrit) {
    if (m_isReturning || m_isDead) return;

    m_hp -= damage;
    GameLog_Info("AIObject: Obj=%u (%s) recebeu %d dano%s de Atacante=%u (HP: %d/%d).",
                 m_objectId, m_name.c_str(), damage, isCrit ? " [CRITICO]" : "", attackerId, m_hp, m_maxHp);

    if (m_hp <= 0) {
        m_hp = 0;
        m_isDead = true;
        ClearHate();
        GameLog_Info("AIObject: Obj=%u (%s) foi DERROTADO por Atacante=%u!",
                     m_objectId, m_name.c_str(), attackerId);
        if (m_pAiContext) {
            m_pAiContext->ChangeState(std::make_unique<AiCharStateRest>());
        }
        return;
    }

    int32_t hateDelta = damage;
    if (isCrit) hateDelta = (int32_t)(hateDelta * 1.2f);
    AddHate(attackerId, hateDelta);
}

void AIObject::Heal(uint32_t casterId, int32_t amount) {
    (void)casterId;
    if (m_isDead || amount <= 0) return;
    m_hp = (std::min)(m_maxHp, m_hp + amount);
}

bool AIObject::CanAttack(float currentTime) const {
    return (currentTime - m_lastAttackTime) >= m_attackSpeed;
}

void AIObject::AddWaypoint(float x, float y, float z) {
    AiWaypoint wp = { x, y, z };
    m_patrolWaypoints.push_back(wp);
}

void AIObject::UpdatePatrol(float dt) {
    if (m_patrolWaypoints.empty()) return;

    if (m_patrolWaitTimer > 0.0f) {
        m_patrolWaitTimer -= dt;
        return;
    }

    const auto& wp = m_patrolWaypoints[m_currentWaypointIndex];
    Vec3F targetPos(wp.x, wp.y, wp.z);
    MoveTowards(targetPos, dt);

    if (DistanceTo(targetPos) < 1.0f) {
        m_patrolWaitTimer = 3.0f; // Pausa 3 segundos no waypoint antes do próximo
        m_currentWaypointIndex = (m_currentWaypointIndex + 1) % m_patrolWaypoints.size();
    }
}

