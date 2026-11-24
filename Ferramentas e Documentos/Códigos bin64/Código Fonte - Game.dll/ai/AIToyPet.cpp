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
    , m_autoLootCooldown(0.0f)
    , m_alarmCooldown(0.0f)
{
    m_autoBuffSlots[0] = 0;
    m_autoBuffSlots[1] = 0;
    m_autoBuffSlots[2] = 0;

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

    if (m_autoLootCooldown > 0.0f) {
        m_autoLootCooldown -= 0.05f;
    }
    if (m_alarmCooldown > 0.0f) {
        m_alarmCooldown -= 0.05f;
    }

    // Auto Buff se equipado
    if (m_hasBuff) {
        CheckAndTriggerAutoBuff();
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

void AIToyPet::SetAutoBuffSlot(int slot, uint32_t itemId) {
    if (slot >= 0 && slot < 3) {
        m_autoBuffSlots[slot] = itemId;
        GameLog_Info("AIToyPet: Slot de auto-buff %d configurado com Item=%u", slot, itemId);
    }
}

uint32_t AIToyPet::GetAutoBuffSlot(int slot) const {
    if (slot >= 0 && slot < 3) {
        return m_autoBuffSlots[slot];
    }
    return 0;
}

bool AIToyPet::CheckAndTriggerAutoBuff() {
    if (!m_hasBuff || m_isHungry) return false;

    for (int i = 0; i < 3; ++i) {
        if (m_autoBuffSlots[i] != 0) {
            // Se o buff estiver pronto ou expirado, ativa doping
            if (GetAiContext()) {
                GetAiContext()->ChangeState(std::make_unique<AiCharStateDoping>());
            }
            GameLog_Info("AIToyPet: Auto-buff disparado para Master=%u (Item=%u, Slot=%d).",
                         m_masterId, m_autoBuffSlots[i], i);
            return true;
        }
    }
    return false;
}

bool AIToyPet::CheckAndTriggerAutoLoot(const Vec3F& corpsePos, uint32_t corpseId) {
    if (!m_hasLoot || m_isHungry || m_autoLootCooldown > 0.0f) return false;

    float dist = DistanceTo(corpsePos);
    if (dist <= 12.0f) { // Raio canônico de 12 metros de loot do pet
        GameLog_Info("AIToyPet: Obj=%u detectou loot do corpo %u a %0.1fm. Coletando!",
                     GetObjectId(), corpseId, dist);
        m_autoLootCooldown = 1.5f; // Delay canônico entre coletas de itens
        if (GetAiContext()) {
            GetAiContext()->ChangeState(std::make_unique<AiCharStateLooting>());
        }
        return true;
    }
    return false;
}

bool AIToyPet::CheckAndTriggerAlarm(const Vec3F& enemyPos, bool isStealthed) {
    if (!m_hasAlarm || m_alarmCooldown > 0.0f) return false;

    float dist = DistanceTo(enemyPos);
    if (dist <= 25.0f) { // Raio canônico de percepção de 25 metros
        m_alarmCooldown = 5.0f; // Alerta com cooldown de 5s
        GameLog_Info("AIToyPet [ALARME]: ALERTA! Inimigo detectado a %0.1fm! (Camuflado: %s)",
                     dist, isStealthed ? "SIM" : "NAO");
        if (GetAiContext()) {
            GetAiContext()->ChangeState(std::make_unique<AiCharStateAlarm>());
        }
        return true;
    }
    return false;
}

void AIToyPet::CheerMaster() {
    GameLog_Info("AIToyPet: Mascote comemorando vitoria do mestre!");
    AddMoodPoints(200);
    if (GetAiContext()) {
        GetAiContext()->ChangeState(std::make_unique<AiCharStateEmotion>());
    }
}

