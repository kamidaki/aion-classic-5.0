#include "AIToyPet.h"
#include "AiCharContext.h"
#include "AiCharState.h"
#include "../core/GameLog.h"

AIToyPet::AIToyPet(uint32_t objectId, uint32_t petTemplateId, uint32_t masterId, const std::string& name)
    : AIObject(objectId, name)
    , m_petTemplateId(petTemplateId)
    , m_masterId(masterId)
    , m_moodPoints(1000)
    , m_bagId(0)
    , m_isHungry(false)
    , m_hasBuff(false)
    , m_hasLoot(false)
    , m_hasAlarm(false)
{
    // Mascotes iniciam por padrão seguindo o dono
    if (GetAiContext()) {
        GetAiContext()->ChangeState(std::make_unique<AiCharStateFollow_ToyPet>());
    }
    GameLog_Info("AIToyPet criado: Obj=%u Tpl=%u Master=%u Nome=%s", objectId, petTemplateId, masterId, name.c_str());
}

AIToyPet::~AIToyPet() {
    GameLog_Info("AIToyPet destruído: Obj=%u", GetObjectId());
}

void AIToyPet::Update() {
    AIObject::Update();

    // Verificação de humor e alarme
    if (m_moodPoints > 0) {
        m_moodPoints--;
    } else {
        m_isHungry = true;
    }
}

void AIToyPet::AddMoodPoints(int32_t delta) {
    m_moodPoints += delta;
    if (m_moodPoints > 10000) m_moodPoints = 10000;
    if (m_moodPoints < 0) m_moodPoints = 0;
    m_isHungry = (m_moodPoints < 500);
}

void AIToyPet::FeedItem(uint32_t itemId) {
    GameLog_Info("AIToyPet alimentado com Item=%u", itemId);
    AddMoodPoints(500);
    m_isHungry = false;
    if (GetAiContext()) {
        GetAiContext()->ChangeState(std::make_unique<AiCharStateEatFeed>());
    }
}
