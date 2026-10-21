#pragma once
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <cstdint>
#include "AddonGauge.h"
#include "AddonFrame.h"

// Tipos de elementos rápidos da QuickBar
enum class QuickBarSlotType {
    Empty = 0,
    Skill,
    Item,
    Macro
};

// Slot individual de Quickbar com suporte a binds de teclado e tempo de recarga
struct QuickBarSlot {
    int slotIndex = 0;
    QuickBarSlotType type = QuickBarSlotType::Empty;
    uint32_t actionId = 0;
    std::string name;
    std::string icon;
    std::string keyBind; // Ex: "1", "Alt+1", "Ctrl+1", "F1"
    int32_t cooldownRemainingMs = 0;
    int32_t cooldownTotalMs = 0;

    bool IsReady() const { return cooldownRemainingMs <= 0; }
    float GetCooldownPercent() const {
        if (cooldownTotalMs <= 0) return 0.0f;
        return static_cast<float>(cooldownRemainingMs) / static_cast<float>(cooldownTotalMs);
    }
};

// QuickBar individual contendo 12 slots canônicos
class HUDQuickBar {
public:
    static constexpr int NUM_SLOTS = 12;

    HUDQuickBar(int barIndex);
    void SetSlot(int slotIndex, QuickBarSlotType type, uint32_t actionId, const std::string& name, const std::string& icon);
    void ClearSlot(int slotIndex);
    const QuickBarSlot* GetSlot(int slotIndex) const;
    void SetKeyBind(int slotIndex, const std::string& bindKey);
    bool TriggerSlot(int slotIndex);
    void StartCooldown(int slotIndex, int32_t durationMs);
    void UpdateCooldowns(int32_t elapsedMs);

    int GetBarIndex() const { return m_barIndex; }

private:
    int m_barIndex;
    QuickBarSlot m_slots[NUM_SLOTS];
};

// Tipos de pontos exibidos no Radar / Minimapa
enum class MinimapBlipType {
    FriendlyNPC = 0,     // Azul claro / Verde
    HostileMonster,      // Vermelho
    FriendlyPlayer,     // Azul
    EnemyPlayer,        // Laranja / Vermelho vivo
    NeutralNPC,         // Branco / Amarelo
    GatheringNode,      // Ponto de coleta (Ervas, Minérios) - Verde
    PartyMember         // Ciano
};

// Representação de um marcador no minimapa
struct MinimapBlip {
    uint32_t entityId = 0;
    MinimapBlipType type = MinimapBlipType::NeutralNPC;
    float posX = 0.0f;
    float posY = 0.0f;
    float posZ = 0.0f;
    std::string name;
    bool isAggressive = false;
};

// Radar / Minimapa do Aion Classic
class HUDMinimap : public AddonFrame {
public:
    HUDMinimap();
    virtual ~HUDMinimap();

    void SetPlayerPosition(float x, float y, float z, float headingDeg);
    void AddOrUpdateBlip(const MinimapBlip& blip);
    void RemoveBlip(uint32_t entityId);
    void ClearBlips();

    const std::vector<MinimapBlip>& GetBlips() const { return m_blips; }
    float GetZoom() const { return m_zoom; }
    void SetZoom(float zoom);
    float GetMaxRadius() const { return m_maxRadius; }
    void SetMaxRadius(float radius) { m_maxRadius = radius; }

    int CountVisibleBlips(MinimapBlipType type) const;

private:
    float m_playerX = 0.0f;
    float m_playerY = 0.0f;
    float m_playerZ = 0.0f;
    float m_playerHeading = 0.0f;
    float m_zoom = 1.0f;
    float m_maxRadius = 50.0f; // 50 metros de raio padrão de detecção
    std::vector<MinimapBlip> m_blips;
};

// Informação de Buff/Debuff para a moldura de alvo
struct TargetEffect {
    uint32_t effectId = 0;
    std::string name;
    std::string icon;
    float durationRemainingSec = 0.0f;
    int32_t stackCount = 1;
    bool isDebuff = false;
};

// Barra de Conjuração (Cast Bar)
struct CastBarInfo {
    bool isCasting = false;
    uint32_t skillId = 0;
    std::string skillName;
    float castDurationSec = 0.0f;
    float elapsedSec = 0.0f;
    bool isInterruptible = true;

    float GetProgress() const {
        if (castDurationSec <= 0.0f) return 0.0f;
        float p = elapsedSec / castDurationSec;
        return (p > 1.0f) ? 1.0f : p;
    }
};

// Moldura de Alvo (Target Frame)
class HUDTargetFrame : public AddonFrame {
public:
    HUDTargetFrame();
    virtual ~HUDTargetFrame();

    void SetTarget(uint32_t entityId, const std::string& name, int level, int rank, int64_t curHp, int64_t maxHp);
    void ClearTarget();
    bool HasTarget() const { return m_hasTarget; }

    uint32_t GetTargetId() const { return m_targetId; }
    const std::string& GetTargetName() const { return m_targetName; }
    int GetTargetLevel() const { return m_targetLevel; }
    int GetTargetRank() const { return m_targetRank; } // 0=Normal, 1=Elite, 2=Hero, 3=Legendary

    AddonGauge& GetHpGauge() { return m_hpGauge; }
    const AddonGauge& GetHpGauge() const { return m_hpGauge; }

    void AddEffect(const TargetEffect& effect);
    void RemoveEffect(uint32_t effectId);
    void ClearEffects();
    const std::vector<TargetEffect>& GetEffects() const { return m_effects; }

    // Cast bar
    void StartCast(uint32_t skillId, const std::string& skillName, float durationSec, bool interruptible = true);
    void InterruptCast();
    void FinishCast();
    void UpdateCast(float deltaSec);
    const CastBarInfo& GetCastBar() const { return m_castBar; }

private:
    bool m_hasTarget = false;
    uint32_t m_targetId = 0;
    std::string m_targetName;
    int m_targetLevel = 0;
    int m_targetRank = 0;
    AddonGauge m_hpGauge;
    std::vector<TargetEffect> m_effects;
    CastBarInfo m_castBar;
};

// Gerenciador Central de HUD do Aion Classic
class HUDManager {
public:
    static constexpr int NUM_QUICKBARS = 4;

    static HUDManager& GetInstance();

    HUDManager();
    ~HUDManager();

    bool Initialize();
    void Update(float deltaSec);

    // Medidores vitais (Gauges)
    AddonGauge& GetHpGauge() { return m_hpGauge; }
    AddonGauge& GetMpGauge() { return m_mpGauge; }
    AddonGauge& GetDpGauge() { return m_dpGauge; }
    AddonGauge& GetFlightGauge() { return m_flightGauge; }
    AddonGauge& GetExpGauge() { return m_expGauge; }

    void SetHP(int64_t current, int64_t max);
    void SetMP(int64_t current, int64_t max);
    void SetDP(int64_t current, int64_t max = 4000);
    void SetFlightTime(int64_t currentSec, int64_t maxSec);
    void SetExp(int64_t current, int64_t max);

    bool IsFlightWarningActive() const { return m_flightGauge.IsWarningActive(); }

    // QuickBars
    HUDQuickBar& GetQuickBar(int index);
    bool TriggerKeyBind(const std::string& keyBind);

    // Minimap / Radar
    HUDMinimap& GetMinimap() { return m_minimap; }

    // Target Frame
    HUDTargetFrame& GetTargetFrame() { return m_targetFrame; }

private:
    AddonGauge m_hpGauge;
    AddonGauge m_mpGauge;
    AddonGauge m_dpGauge;
    AddonGauge m_flightGauge;
    AddonGauge m_expGauge;

    std::vector<HUDQuickBar> m_quickBars;
    HUDMinimap m_minimap;
    HUDTargetFrame m_targetFrame;
};
