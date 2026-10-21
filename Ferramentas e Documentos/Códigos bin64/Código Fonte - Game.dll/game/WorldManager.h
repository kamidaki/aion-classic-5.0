#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
#include "../ai/AIObject.h" // Vec3F

enum class WeatherType : uint8_t {
    Clear     = 0,
    Rain      = 1,
    Snow      = 2,
    Storm     = 3,
    Fog       = 4,
    Sandstorm = 5
};

struct WorldZoneInfo {
    uint32_t    worldId;
    std::string name;
    bool        isAbyss;
    bool        isPvPAllowed;
    bool        isFlightAllowed;  // Voo livre 3D (ex: Abyss, Heiron, Beluslan)
    bool        isGlidingOnly;    // Apenas planar (ex: Poeta, Ishalgen)
    float       maxZ;
    float       minZ;
};

// -------------------------------------------------------------
// 7.2.2 Sistema de Rifts (Fendas Dimensionais Elysea <-> Asmodae)
// -------------------------------------------------------------
struct RiftInfo {
    uint32_t    riftId;
    std::string name;
    uint32_t    originWorldId;
    uint32_t    destWorldId;
    uint32_t    minLevel;
    uint32_t    maxLevel;
    uint32_t    maxEntries;
    uint32_t    currentEntries;
    bool        isOpen;
    Vec3F       originPos;
    Vec3F       destPos;
};

// Gerenciador de mundo, mapas, zonas, clima e rifts do Aion Classic
class WorldManager {
public:
    static WorldManager& GetInstance();

    WorldManager();
    ~WorldManager();

    bool Initialize();
    void Shutdown();
    void Update(float deltaTime);

    // 7.1 Gestão de Mapa e Canal
    bool ChangeWorld(uint32_t newWorldId, uint32_t channelId, const Vec3F& spawnPos);
    uint32_t GetCurrentWorldId() const { return m_currentWorldId; }
    uint32_t GetCurrentChannelId() const { return m_currentChannelId; }
    const std::string& GetCurrentWorldName() const;
    const WorldZoneInfo* GetZoneInfo(uint32_t worldId) const;

    // 7.2 Regras de Zona (Voo, Gliding, PvP)
    bool IsFlightAllowed() const;
    bool IsGlidingOnly() const;
    bool IsPvPAllowed() const;

    // 7.2.2 Sistema de Rifts
    bool OpenRift(uint32_t riftId);
    bool CloseRift(uint32_t riftId);
    bool CanEnterRift(uint32_t riftId, uint32_t playerLevel, uint8_t playerRace, std::string& outMsg) const;
    bool EnterRift(uint32_t riftId, uint32_t playerLevel, uint8_t playerRace, Vec3F& outDestPos, uint32_t& outDestWorldId);
    const std::vector<RiftInfo>& GetRifts() const { return m_rifts; }

    // 7.2.3 Clima Dinâmico
    WeatherType GetWeather() const { return m_currentWeather; }
    void SetWeather(WeatherType weather);
    float GetWeatherVisibilityMultiplier() const;

    // 7.2.4 Ciclo Dia/Noite (24 horas de Atreia)
    float GetWorldTimeOfDay() const { return m_timeOfDay; } // 0.0 a 24.0
    void SetWorldTimeOfDay(float time) { m_timeOfDay = time; }
    bool IsDaytime() const { return (m_timeOfDay >= 6.0f && m_timeOfDay < 20.0f); }
    bool IsNighttime() const { return !IsDaytime(); }
    float GetSunAngleDegrees() const;
    float GetAmbientLightMultiplier() const;

private:
    uint32_t m_currentWorldId;
    uint32_t m_currentChannelId;
    WeatherType m_currentWeather;
    float m_timeOfDay; // 0.0f a 24.0f
    std::unordered_map<uint32_t, WorldZoneInfo> m_zones;
    std::vector<RiftInfo> m_rifts;
};
