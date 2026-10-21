#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include "WorldManager.h"
#include "../core/GameLog.h"
#include <cmath>

WorldManager& WorldManager::GetInstance() {
    static WorldManager s_instance;
    return s_instance;
}

WorldManager::WorldManager()
    : m_currentWorldId(210010000) // Poeta por padrão
    , m_currentChannelId(1)
    , m_currentWeather(WeatherType::Clear)
    , m_timeOfDay(12.0f) // Meio-dia inicial
{
}

WorldManager::~WorldManager() {
    Shutdown();
}

bool WorldManager::Initialize() {
    m_zones.clear();
    m_rifts.clear();

    // ---------------------------------------------------------
    // 7.1.1 Capitais
    // ---------------------------------------------------------
    m_zones[110010000] = { 110010000, "Sanctum", false, false, false, true, 500.0f, 0.0f };
    m_zones[120010000] = { 120010000, "Pandaemonium", false, false, false, true, 500.0f, 0.0f };

    // ---------------------------------------------------------
    // 7.1.2 Zonas Elyos
    // ---------------------------------------------------------
    m_zones[210010000] = { 210010000, "Poeta", false, false, false, true, 800.0f, 0.0f };
    m_zones[210030000] = { 210030000, "Verteron", false, true, false, true, 1200.0f, 0.0f };
    m_zones[210020000] = { 210020000, "Eltnen", false, true, false, true, 1500.0f, 0.0f };
    m_zones[210040000] = { 210040000, "Heiron", false, true, true, false, 1800.0f, 0.0f };
    m_zones[210060000] = { 210060000, "Theobomos", false, true, false, true, 1600.0f, 0.0f };

    // ---------------------------------------------------------
    // 7.1.3 Zonas Asmodian
    // ---------------------------------------------------------
    m_zones[220010000] = { 220010000, "Ishalgen", false, false, false, true, 800.0f, 0.0f };
    m_zones[220030000] = { 220030000, "Altgard", false, true, false, true, 1200.0f, 0.0f };
    m_zones[220020000] = { 220020000, "Morheim", false, true, false, true, 1500.0f, 0.0f };
    m_zones[220040000] = { 220040000, "Beluslan", false, true, true, false, 1800.0f, 0.0f };
    m_zones[220050000] = { 220050000, "Brusthonin", false, true, false, true, 1600.0f, 0.0f };

    // ---------------------------------------------------------
    // 7.1.4 Zonas de Conflito e Abyss
    // ---------------------------------------------------------
    m_zones[400010000] = { 400010000, "Reshanta (Core Abyss)", true, true, true, false, 3000.0f, 500.0f };
    m_zones[600010000] = { 600010000, "Silentera Canyon", false, true, false, true, 800.0f, 100.0f };
    m_zones[210050000] = { 210050000, "Inggison", false, true, true, false, 2000.0f, 0.0f };
    m_zones[220070000] = { 220070000, "Gelkmaros", false, true, true, false, 2000.0f, 0.0f };

    // ---------------------------------------------------------
    // 7.1.5 Instâncias Canônicas
    // ---------------------------------------------------------
    m_zones[300040000] = { 300040000, "Dark Poeta", false, false, false, true, 1000.0f, 0.0f };
    m_zones[300140000] = { 300140000, "Chantra Dredgion", true, true, false, true, 1500.0f, 200.0f };
    m_zones[300280000] = { 300280000, "Tiak Research Base", true, true, false, true, 1200.0f, 100.0f };
    m_zones[300020000] = { 300020000, "Fire Temple", false, false, false, true, 800.0f, 0.0f };
    m_zones[300170000] = { 300170000, "Beshmundir Temple", false, false, false, true, 1200.0f, 0.0f };

    // ---------------------------------------------------------
    // 7.2.2 Sistema de Rifts
    // ---------------------------------------------------------
    // Rift 1: Eltnen -> Morheim (Level 20-28, max 12 jogadores)
    RiftInfo rift1 = {};
    rift1.riftId = 1;
    rift1.name = "Fenda de Eltnen para Morheim";
    rift1.originWorldId = 210020000;
    rift1.destWorldId = 220020000;
    rift1.minLevel = 20;
    rift1.maxLevel = 28;
    rift1.maxEntries = 12;
    rift1.currentEntries = 0;
    rift1.isOpen = true;
    rift1.originPos = { 1520.0f, 850.0f, 210.0f };
    rift1.destPos = { 1350.0f, 920.0f, 230.0f };
    m_rifts.push_back(rift1);

    // Rift 2: Heiron -> Beluslan (Level 30-45, max 24 jogadores)
    RiftInfo rift2 = {};
    rift2.riftId = 2;
    rift2.name = "Fenda Maior de Heiron para Beluslan";
    rift2.originWorldId = 210040000;
    rift2.destWorldId = 220040000;
    rift2.minLevel = 30;
    rift2.maxLevel = 45;
    rift2.maxEntries = 24;
    rift2.currentEntries = 0;
    rift2.isOpen = true;
    rift2.originPos = { 2100.0f, 1600.0f, 350.0f };
    rift2.destPos = { 2050.0f, 1580.0f, 340.0f };
    m_rifts.push_back(rift2);

    GameLog_Info("WorldManager inicializado com sucesso (%zu mapas, %zu rifts registrados).", m_zones.size(), m_rifts.size());
    return true;
}

void WorldManager::Shutdown() {
    m_zones.clear();
    m_rifts.clear();
}

void WorldManager::Update(float deltaTime) {
    // 7.2.4 Ciclo Dia/Noite (1 hora real = 24 horas no mundo de Atreia)
    m_timeOfDay += deltaTime * (24.0f / 3600.0f);
    if (m_timeOfDay >= 24.0f) {
        m_timeOfDay -= 24.0f;
    }
}

bool WorldManager::ChangeWorld(uint32_t newWorldId, uint32_t channelId, const Vec3F& spawnPos) {
    auto it = m_zones.find(newWorldId);
    if (it == m_zones.end()) {
        GameLog_Info("WorldManager: Mapa desconhecido WorldId=%u!", newWorldId);
        return false;
    }

    m_currentWorldId = newWorldId;
    m_currentChannelId = channelId;
    GameLog_Info("WorldManager: Teleporte para Mapa=%u (%s) Ch=%u Pos=(%.1f, %.1f, %.1f)", 
        newWorldId, it->second.name.c_str(), channelId, spawnPos.x, spawnPos.y, spawnPos.z);
    return true;
}

const std::string& WorldManager::GetCurrentWorldName() const {
    static const std::string s_unknown = "Unknown World";
    auto it = m_zones.find(m_currentWorldId);
    return it != m_zones.end() ? it->second.name : s_unknown;
}

const WorldZoneInfo* WorldManager::GetZoneInfo(uint32_t worldId) const {
    auto it = m_zones.find(worldId);
    if (it != m_zones.end()) {
        return &it->second;
    }
    return nullptr;
}

bool WorldManager::IsFlightAllowed() const {
    auto it = m_zones.find(m_currentWorldId);
    return it != m_zones.end() ? it->second.isFlightAllowed : false;
}

bool WorldManager::IsGlidingOnly() const {
    auto it = m_zones.find(m_currentWorldId);
    return it != m_zones.end() ? it->second.isGlidingOnly : false;
}

bool WorldManager::IsPvPAllowed() const {
    auto it = m_zones.find(m_currentWorldId);
    return it != m_zones.end() ? it->second.isPvPAllowed : false;
}

// -------------------------------------------------------------
// 7.2.2 Sistema de Rifts
// -------------------------------------------------------------
bool WorldManager::OpenRift(uint32_t riftId) {
    for (auto& r : m_rifts) {
        if (r.riftId == riftId) {
            r.isOpen = true;
            r.currentEntries = 0;
            GameLog_Info("WorldManager: Rift %u ('%s') ABERTO!", riftId, r.name.c_str());
            return true;
        }
    }
    return false;
}

bool WorldManager::CloseRift(uint32_t riftId) {
    for (auto& r : m_rifts) {
        if (r.riftId == riftId) {
            r.isOpen = false;
            GameLog_Info("WorldManager: Rift %u ('%s') FECHADO!", riftId, r.name.c_str());
            return true;
        }
    }
    return false;
}

bool WorldManager::CanEnterRift(uint32_t riftId, uint32_t playerLevel, uint8_t playerRace, std::string& outMsg) const {
    for (const auto& r : m_rifts) {
        if (r.riftId == riftId) {
            if (!r.isOpen) {
                outMsg = "A fenda dimensional se encontra fechada.";
                return false;
            }
            if (playerLevel < r.minLevel || playerLevel > r.maxLevel) {
                outMsg = "Nivel do personagem fora do limite permitido da fenda.";
                return false;
            }
            if (r.currentEntries >= r.maxEntries) {
                outMsg = "Limite maximo de jogadores na fenda esgotado.";
                return false;
            }
            return true;
        }
    }
    outMsg = "Fenda inexistente.";
    return false;
}

bool WorldManager::EnterRift(uint32_t riftId, uint32_t playerLevel, uint8_t playerRace, Vec3F& outDestPos, uint32_t& outDestWorldId) {
    for (auto& r : m_rifts) {
        if (r.riftId == riftId) {
            std::string reason;
            if (!CanEnterRift(riftId, playerLevel, playerRace, reason)) {
                return false;
            }
            r.currentEntries++;
            outDestPos = r.destPos;
            outDestWorldId = r.destWorldId;
            ChangeWorld(r.destWorldId, 1, r.destPos);
            GameLog_Info("WorldManager: Jogador entrou na Fenda %u (%u/%u entradas)", riftId, r.currentEntries, r.maxEntries);
            return true;
        }
    }
    return false;
}

// -------------------------------------------------------------
// 7.2.3 Clima Dinâmico
// -------------------------------------------------------------
void WorldManager::SetWeather(WeatherType weather) {
    m_currentWeather = weather;
    GameLog_Info("WorldManager: Clima alterado para Tipo=%u", static_cast<uint8_t>(weather));
}

float WorldManager::GetWeatherVisibilityMultiplier() const {
    switch (m_currentWeather) {
        case WeatherType::Clear:     return 1.0f;
        case WeatherType::Rain:      return 0.75f;
        case WeatherType::Snow:      return 0.70f;
        case WeatherType::Storm:     return 0.55f;
        case WeatherType::Fog:       return 0.40f;
        case WeatherType::Sandstorm: return 0.35f;
        default:                     return 1.0f;
    }
}

// -------------------------------------------------------------
// 7.2.4 Ciclo Dia/Noite (24 horas de Atreia)
// -------------------------------------------------------------
float WorldManager::GetSunAngleDegrees() const {
    // 360 graus distribuídos em 24 horas: 1 hora = 15 graus
    return m_timeOfDay * 15.0f;
}

float WorldManager::GetAmbientLightMultiplier() const {
    // 0.2 à meia-noite (00:00), 1.0 ao meio-dia (12:00)
    // Curva senoidal suave baseada na hora do dia
    float normalizedTime = (m_timeOfDay / 24.0f) * 6.2831853f; // 2 * PI
    float factor = (std::sin(normalizedTime - 1.5707963f) + 1.0f) * 0.5f; // -PI/2 alinha 12h com pico
    return 0.2f + 0.8f * factor;
}
