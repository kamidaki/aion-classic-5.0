#pragma once
#include "AIObject.h"
#include <string>
#include <vector>

// Representação canônica de Mascote/Pet do jogador local extraída do RTTI (.?AVAIToyPet@@)
class AIToyPet : public AIObject {
public:
    AIToyPet(uint32_t objectId, uint32_t petTemplateId, uint32_t masterId, const std::string& name);
    virtual ~AIToyPet();

    virtual void Update() override;

    uint32_t GetPetTemplateId() const { return m_petTemplateId; }
    uint32_t GetMasterId() const { return m_masterId; }
    
    // Funções canônicas de Pet (Alimentação, Alarme, Buff/Doping, Inventário/Loot)
    int32_t GetMoodPoints() const { return m_moodPoints; }
    void SetMoodPoints(int32_t mood) { m_moodPoints = mood; }
    void AddMoodPoints(int32_t delta);

    bool IsHungry() const { return m_isHungry; }
    void FeedItem(uint32_t itemId);

    uint32_t GetBagId() const { return m_bagId; }
    void SetBagId(uint32_t bagId) { m_bagId = bagId; }

    bool HasBuffFunction() const { return m_hasBuff; }
    bool HasLootFunction() const { return m_hasLoot; }
    bool HasAlarmFunction() const { return m_hasAlarm; }

    void SetFunctions(bool hasBuff, bool hasLoot, bool hasAlarm) {
        m_hasBuff = hasBuff;
        m_hasLoot = hasLoot;
        m_hasAlarm = hasAlarm;
    }

private:
    uint32_t m_petTemplateId;
    uint32_t m_masterId;
    int32_t  m_moodPoints;
    uint32_t m_bagId;
    bool     m_isHungry;
    bool     m_hasBuff;
    bool     m_hasLoot;
    bool     m_hasAlarm;
};
