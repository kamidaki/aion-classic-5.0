#include "AIOtherToyPet.h"
#include "AiCharContext.h"
#include "AiCharState.h"
#include "../core/GameLog.h"

AIOtherToyPet::AIOtherToyPet(uint32_t objectId, uint32_t petTemplateId, uint32_t masterId, const std::string& name)
    : AIObject(objectId, name)
    , m_petTemplateId(petTemplateId)
    , m_masterId(masterId)
{
    if (GetAiContext()) {
        GetAiContext()->ChangeState(std::make_unique<AiCharStateFollow_ToyPet>());
    }
}

AIOtherToyPet::~AIOtherToyPet() {
}

void AIOtherToyPet::Update() {
    AIObject::Update();
}
