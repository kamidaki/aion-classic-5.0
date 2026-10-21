#include "HUDManager.h"
#include "../core/GameLog.h"
#include <cmath>

// =======================================================================
// HUDQuickBar
// =======================================================================
HUDQuickBar::HUDQuickBar(int barIndex)
    : m_barIndex(barIndex)
{
    for (int i = 0; i < NUM_SLOTS; ++i) {
        m_slots[i].slotIndex = i;
        m_slots[i].type = QuickBarSlotType::Empty;
        m_slots[i].actionId = 0;
        m_slots[i].cooldownRemainingMs = 0;
        m_slots[i].cooldownTotalMs = 0;

        // Binds padrão por barra
        char bindBuf[32];
        const char* keyNames[] = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=" };
        if (barIndex == 0) {
            snprintf(bindBuf, sizeof(bindBuf), "%s", keyNames[i]);
        } else if (barIndex == 1) {
            snprintf(bindBuf, sizeof(bindBuf), "Alt+%s", keyNames[i]);
        } else if (barIndex == 2) {
            snprintf(bindBuf, sizeof(bindBuf), "Ctrl+%s", keyNames[i]);
        } else {
            snprintf(bindBuf, sizeof(bindBuf), "Shift+%s", keyNames[i]);
        }
        m_slots[i].keyBind = bindBuf;
    }
}

void HUDQuickBar::SetSlot(int slotIndex, QuickBarSlotType type, uint32_t actionId, const std::string& name, const std::string& icon) {
    if (slotIndex < 0 || slotIndex >= NUM_SLOTS) return;
    m_slots[slotIndex].type = type;
    m_slots[slotIndex].actionId = actionId;
    m_slots[slotIndex].name = name;
    m_slots[slotIndex].icon = icon;
    m_slots[slotIndex].cooldownRemainingMs = 0;
    m_slots[slotIndex].cooldownTotalMs = 0;
}

void HUDQuickBar::ClearSlot(int slotIndex) {
    if (slotIndex < 0 || slotIndex >= NUM_SLOTS) return;
    m_slots[slotIndex].type = QuickBarSlotType::Empty;
    m_slots[slotIndex].actionId = 0;
    m_slots[slotIndex].name.clear();
    m_slots[slotIndex].icon.clear();
    m_slots[slotIndex].cooldownRemainingMs = 0;
    m_slots[slotIndex].cooldownTotalMs = 0;
}

const QuickBarSlot* HUDQuickBar::GetSlot(int slotIndex) const {
    if (slotIndex < 0 || slotIndex >= NUM_SLOTS) return nullptr;
    return &m_slots[slotIndex];
}

void HUDQuickBar::SetKeyBind(int slotIndex, const std::string& bindKey) {
    if (slotIndex < 0 || slotIndex >= NUM_SLOTS) return;
    m_slots[slotIndex].keyBind = bindKey;
}

bool HUDQuickBar::TriggerSlot(int slotIndex) {
    if (slotIndex < 0 || slotIndex >= NUM_SLOTS) return false;
    QuickBarSlot& slot = m_slots[slotIndex];
    if (slot.type == QuickBarSlotType::Empty) return false;
    if (!slot.IsReady()) {
        GameLog_Info("QuickBar[%d] Slot[%d] (%s) em tempo de recarga: %d ms", m_barIndex, slotIndex, slot.name.c_str(), slot.cooldownRemainingMs);
        return false;
    }
    GameLog_Info("QuickBar[%d] Slot[%d] Acionado com sucesso: %s (ID=%u)", m_barIndex, slotIndex, slot.name.c_str(), slot.actionId);
    return true;
}

void HUDQuickBar::StartCooldown(int slotIndex, int32_t durationMs) {
    if (slotIndex < 0 || slotIndex >= NUM_SLOTS) return;
    m_slots[slotIndex].cooldownTotalMs = durationMs;
    m_slots[slotIndex].cooldownRemainingMs = durationMs;
}

void HUDQuickBar::UpdateCooldowns(int32_t elapsedMs) {
    for (int i = 0; i < NUM_SLOTS; ++i) {
        if (m_slots[i].cooldownRemainingMs > 0) {
            m_slots[i].cooldownRemainingMs -= elapsedMs;
            if (m_slots[i].cooldownRemainingMs < 0) {
                m_slots[i].cooldownRemainingMs = 0;
            }
        }
    }
}

// =======================================================================
// HUDMinimap
// =======================================================================
HUDMinimap::HUDMinimap()
    : AddonFrame("HUD_Minimap")
{
}

HUDMinimap::~HUDMinimap() {}

void HUDMinimap::SetPlayerPosition(float x, float y, float z, float headingDeg) {
    m_playerX = x;
    m_playerY = y;
    m_playerZ = z;
    m_playerHeading = headingDeg;
}

void HUDMinimap::AddOrUpdateBlip(const MinimapBlip& blip) {
    for (auto& b : m_blips) {
        if (b.entityId == blip.entityId) {
            b = blip;
            return;
        }
    }
    m_blips.push_back(blip);
}

void HUDMinimap::RemoveBlip(uint32_t entityId) {
    for (auto it = m_blips.begin(); it != m_blips.end(); ++it) {
        if (it->entityId == entityId) {
            m_blips.erase(it);
            return;
        }
    }
}

void HUDMinimap::ClearBlips() {
    m_blips.clear();
}

void HUDMinimap::SetZoom(float zoom) {
    if (zoom < 0.5f) zoom = 0.5f;
    if (zoom > 3.0f) zoom = 3.0f;
    m_zoom = zoom;
}

int HUDMinimap::CountVisibleBlips(MinimapBlipType type) const {
    int count = 0;
    float maxDistSq = m_maxRadius * m_maxRadius;
    for (const auto& blip : m_blips) {
        if (blip.type == type) {
            float dx = blip.posX - m_playerX;
            float dy = blip.posY - m_playerY;
            if ((dx * dx + dy * dy) <= maxDistSq) {
                count++;
            }
        }
    }
    return count;
}

// =======================================================================
// HUDTargetFrame
// =======================================================================
HUDTargetFrame::HUDTargetFrame()
    : AddonFrame("HUD_TargetFrame")
    , m_hpGauge("Target_HP_Gauge")
{
    m_hpGauge.SetRange(0, 100);
    m_hpGauge.SetValue(100);
}

HUDTargetFrame::~HUDTargetFrame() {}

void HUDTargetFrame::SetTarget(uint32_t entityId, const std::string& name, int level, int rank, int64_t curHp, int64_t maxHp) {
    m_hasTarget = true;
    m_targetId = entityId;
    m_targetName = name;
    m_targetLevel = level;
    m_targetRank = rank;
    m_hpGauge.SetRange(0, maxHp);
    m_hpGauge.SetValue(curHp);
    m_effects.clear();
    m_castBar.isCasting = false;
}

void HUDTargetFrame::ClearTarget() {
    m_hasTarget = false;
    m_targetId = 0;
    m_targetName.clear();
    m_targetLevel = 0;
    m_targetRank = 0;
    m_effects.clear();
    m_castBar.isCasting = false;
}

void HUDTargetFrame::AddEffect(const TargetEffect& effect) {
    for (auto& eff : m_effects) {
        if (eff.effectId == effect.effectId) {
            eff = effect;
            return;
        }
    }
    m_effects.push_back(effect);
}

void HUDTargetFrame::RemoveEffect(uint32_t effectId) {
    for (auto it = m_effects.begin(); it != m_effects.end(); ++it) {
        if (it->effectId == effectId) {
            m_effects.erase(it);
            return;
        }
    }
}

void HUDTargetFrame::ClearEffects() {
    m_effects.clear();
}

void HUDTargetFrame::StartCast(uint32_t skillId, const std::string& skillName, float durationSec, bool interruptible) {
    m_castBar.isCasting = true;
    m_castBar.skillId = skillId;
    m_castBar.skillName = skillName;
    m_castBar.castDurationSec = durationSec;
    m_castBar.elapsedSec = 0.0f;
    m_castBar.isInterruptible = interruptible;
}

void HUDTargetFrame::InterruptCast() {
    if (m_castBar.isCasting && m_castBar.isInterruptible) {
        m_castBar.isCasting = false;
        m_castBar.elapsedSec = 0.0f;
    }
}

void HUDTargetFrame::FinishCast() {
    m_castBar.isCasting = false;
    m_castBar.elapsedSec = 0.0f;
}

void HUDTargetFrame::UpdateCast(float deltaSec) {
    if (m_castBar.isCasting) {
        m_castBar.elapsedSec += deltaSec;
        if (m_castBar.elapsedSec >= m_castBar.castDurationSec) {
            FinishCast();
        }
    }
}

// =======================================================================
// HUDManager
// =======================================================================
HUDManager& HUDManager::GetInstance() {
    static HUDManager s_instance;
    return s_instance;
}

HUDManager::HUDManager()
    : m_hpGauge("HUD_HP_Gauge")
    , m_mpGauge("HUD_MP_Gauge")
    , m_dpGauge("HUD_DP_Gauge")
    , m_flightGauge("HUD_Flight_Gauge")
    , m_expGauge("HUD_Exp_Gauge")
{
    m_quickBars.reserve(NUM_QUICKBARS);
    for (int i = 0; i < NUM_QUICKBARS; ++i) {
        m_quickBars.emplace_back(i);
    }

    // Configurações canônicas de alertas de voo: aviso com 10 segundos restantes
    m_flightGauge.SetWarningThreshold(10, true);
}

HUDManager::~HUDManager() {}

bool HUDManager::Initialize() {
    // Inicialização canônica dos medidores
    SetHP(1000, 1000);
    SetMP(1000, 1000);
    SetDP(0, 4000);
    SetFlightTime(120, 120);
    SetExp(0, 10000);

    GameLog_Info("HUDManager inicializado com sucesso (4 QuickBars, Minimap e TargetFrame).");
    return true;
}

void HUDManager::Update(float deltaSec) {
    int32_t elapsedMs = static_cast<int32_t>(deltaSec * 1000.0f);
    for (auto& bar : m_quickBars) {
        bar.UpdateCooldowns(elapsedMs);
    }
    m_targetFrame.UpdateCast(deltaSec);
}

void HUDManager::SetHP(int64_t current, int64_t max) {
    m_hpGauge.SetRange(0, max);
    m_hpGauge.SetValue(current);
}

void HUDManager::SetMP(int64_t current, int64_t max) {
    m_mpGauge.SetRange(0, max);
    m_mpGauge.SetValue(current);
}

void HUDManager::SetDP(int64_t current, int64_t max) {
    m_dpGauge.SetRange(0, max);
    m_dpGauge.SetValue(current);
}

void HUDManager::SetFlightTime(int64_t currentSec, int64_t maxSec) {
    m_flightGauge.SetRange(0, maxSec);
    m_flightGauge.SetValue(currentSec);
}

void HUDManager::SetExp(int64_t current, int64_t max) {
    m_expGauge.SetRange(0, max);
    m_expGauge.SetValue(current);
}

HUDQuickBar& HUDManager::GetQuickBar(int index) {
    if (index < 0) index = 0;
    if (index >= NUM_QUICKBARS) index = NUM_QUICKBARS - 1;
    return m_quickBars[index];
}

bool HUDManager::TriggerKeyBind(const std::string& keyBind) {
    for (auto& bar : m_quickBars) {
        for (int i = 0; i < HUDQuickBar::NUM_SLOTS; ++i) {
            const QuickBarSlot* slot = bar.GetSlot(i);
            if (slot && slot->keyBind == keyBind) {
                return bar.TriggerSlot(i);
            }
        }
    }
    return false;
}
