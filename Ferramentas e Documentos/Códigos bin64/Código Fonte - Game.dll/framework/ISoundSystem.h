#pragma once
#include <string>
#include <vector>
#include <cstdint>

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

// Tipos de Eventos Sonoros 3D
enum class SoundEventType {
    Footstep = 0,
    WeaponSwing,
    WeaponImpact,
    SpellCast,
    SpellImpact,
    UI_Click,
    UI_Alarm
};

// Superfície de terreno para passos
enum class FootstepSurface {
    Dirt = 0,
    Grass,
    Stone,
    Water,
    Wood,
    Snow
};

// Parâmetros de Áudio Posicional 3D
struct Sound3DParams {
    float posX = 0.0f;
    float posY = 0.0f;
    float posZ = 0.0f;
    float minDistance = 2.0f;
    float maxDistance = 45.0f;
    float volume = 1.0f;
};

// Estado da Trilha Sonora Dinâmica
enum class MusicTrackState {
    AmbientPlaying = 0,
    CrossfadingToCombat,
    CombatPlaying,
    CrossfadingToAmbient
};

// Interface do Sistema de Áudio FMOD / CrySound
CRY_INTERFACE ISoundSystem {
    virtual ~ISoundSystem() = default;

    // Atualização do ouvinte 3D (Câmera / Jogador)
    virtual void SetListenerPosition(float x, float y, float z, float fwdX, float fwdY, float fwdZ) = 0;

    // Execução de Eventos Posicionais 3D
    virtual uint32_t Play3DSound(SoundEventType eventType, const Sound3DParams& params, const std::string& assetName) = 0;
    virtual void PlayFootstep(FootstepSurface surface, float x, float y, float z) = 0;

    // Trilha Sonora Dinâmica (Ambiente <-> Combate)
    virtual void SetAmbientTrack(const std::string& trackName) = 0;
    virtual void SetCombatTrack(const std::string& trackName) = 0;
    virtual void TriggerCombatMusic(bool inCombat) = 0;

    virtual MusicTrackState GetMusicState() const = 0;
    virtual float GetAmbientVolume() const = 0;
    virtual float GetCombatVolume() const = 0;

    // Atualização de quadros
    virtual void Update(float deltaSec) = 0;
};
