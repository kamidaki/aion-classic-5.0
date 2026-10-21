#pragma once
#include "AIObject.h"
#include <string>

// Representação de Mascote de outro jogador no campo de visão extraído do RTTI (.?AVAIOtherToyPet@@)
class AIOtherToyPet : public AIObject {
public:
    AIOtherToyPet(uint32_t objectId, uint32_t petTemplateId, uint32_t masterId, const std::string& name);
    virtual ~AIOtherToyPet();

    virtual void Update() override;

    uint32_t GetPetTemplateId() const { return m_petTemplateId; }
    uint32_t GetMasterId() const { return m_masterId; }

private:
    uint32_t m_petTemplateId;
    uint32_t m_masterId;
};
