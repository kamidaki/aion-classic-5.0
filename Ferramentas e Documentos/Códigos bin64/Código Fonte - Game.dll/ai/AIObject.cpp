#include "AIObject.h"
#include "AiCharContext.h"
#include "AiCharState.h"
#include "../core/GameLog.h"

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

// Implementação dos métodos dos estados básicos
void AiCharStateAttack::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateAttack::OnUpdate(AiCharContext* pContext) {}
void AiCharStateAttack::OnExit(AiCharContext* pContext) {}

void AiCharStateFollow::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateFollow::OnUpdate(AiCharContext* pContext) {}
void AiCharStateFollow::OnExit(AiCharContext* pContext) {}

void AiCharStateRest::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateRest::OnUpdate(AiCharContext* pContext) {}
void AiCharStateRest::OnExit(AiCharContext* pContext) {}

void AiCharStateLooting::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateLooting::OnUpdate(AiCharContext* pContext) {}
void AiCharStateLooting::OnExit(AiCharContext* pContext) {}

void AiCharStateAlarm::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateAlarm::OnUpdate(AiCharContext* pContext) {}
void AiCharStateAlarm::OnExit(AiCharContext* pContext) {}

void AiCharStateDoping::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateDoping::OnUpdate(AiCharContext* pContext) {}
void AiCharStateDoping::OnExit(AiCharContext* pContext) {}

void AiCharStateEatFeed::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateEatFeed::OnUpdate(AiCharContext* pContext) {}
void AiCharStateEatFeed::OnExit(AiCharContext* pContext) {}

void AiCharStateEmotion::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateEmotion::OnUpdate(AiCharContext* pContext) {}
void AiCharStateEmotion::OnExit(AiCharContext* pContext) {}

// Implementação dos métodos dos estados especializados de combate
void AiCharStateAttack_Dealer::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateAttack_Dealer::OnUpdate(AiCharContext* pContext) {}
void AiCharStateAttack_Dealer::OnExit(AiCharContext* pContext) {}

void AiCharStateAttack_Healer::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateAttack_Healer::OnUpdate(AiCharContext* pContext) {}
void AiCharStateAttack_Healer::OnExit(AiCharContext* pContext) {}

void AiCharStateAttack_Tank::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateAttack_Tank::OnUpdate(AiCharContext* pContext) {}
void AiCharStateAttack_Tank::OnExit(AiCharContext* pContext) {}

void AiCharStateFollow_Dealer::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateFollow_Dealer::OnUpdate(AiCharContext* pContext) {}
void AiCharStateFollow_Dealer::OnExit(AiCharContext* pContext) {}

void AiCharStateFollow_Healer::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateFollow_Healer::OnUpdate(AiCharContext* pContext) {}
void AiCharStateFollow_Healer::OnExit(AiCharContext* pContext) {}

void AiCharStateFollow_Tank::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateFollow_Tank::OnUpdate(AiCharContext* pContext) {}
void AiCharStateFollow_Tank::OnExit(AiCharContext* pContext) {}

void AiCharStateFollow_ToyPet::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateFollow_ToyPet::OnUpdate(AiCharContext* pContext) {}
void AiCharStateFollow_ToyPet::OnExit(AiCharContext* pContext) {}

// Implementação dos métodos dos estados físicos
void AiCharStateJump::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateJump::OnUpdate(AiCharContext* pContext) {}
void AiCharStateJump::OnExit(AiCharContext* pContext) {}

void AiCharStateLand::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateLand::OnUpdate(AiCharContext* pContext) {}
void AiCharStateLand::OnExit(AiCharContext* pContext) {}

void AiCharStateEndJump::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateEndJump::OnUpdate(AiCharContext* pContext) {}
void AiCharStateEndJump::OnExit(AiCharContext* pContext) {}

void AiCharStateRoam::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateRoam::OnUpdate(AiCharContext* pContext) {}
void AiCharStateRoam::OnExit(AiCharContext* pContext) {}

void AiCharStateSearch::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateSearch::OnUpdate(AiCharContext* pContext) {}
void AiCharStateSearch::OnExit(AiCharContext* pContext) {}

void AiCharStateTakeOff::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateTakeOff::OnUpdate(AiCharContext* pContext) {}
void AiCharStateTakeOff::OnExit(AiCharContext* pContext) {}

void AiCharStateThreaten::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateThreaten::OnUpdate(AiCharContext* pContext) {}
void AiCharStateThreaten::OnExit(AiCharContext* pContext) {}

void AiCharStateTremble::OnEnter(AiCharContext* pContext) { GameLog_Info("AiCharState [%s] ENTER Obj=%u", GetStateName(), pContext->GetOwner()->GetObjectId()); }
void AiCharStateTremble::OnUpdate(AiCharContext* pContext) {}
void AiCharStateTremble::OnExit(AiCharContext* pContext) {}

// Implementação de AIObject
AIObject::AIObject(uint32_t objectId, const std::string& name)
    : m_objectId(objectId)
    , m_name(name)
    , m_position(0.0f, 0.0f, 0.0f)
{
    m_pAiContext = std::make_unique<AiCharContext>(this);
}

AIObject::~AIObject() {}

void AIObject::Update() {
    if (m_pAiContext) {
        m_pAiContext->Update();
    }
}
