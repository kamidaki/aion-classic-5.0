#pragma once
#include "IRenderer.h"
#include "IAnimationSystem.h"
#include "ISoundSystem.h"
#include "ISystem.h"
#include <unordered_map>
#include <memory>

// =======================================================================
// Implementação do Pipeline Gráfico CryRender
// =======================================================================
class CryRenderPipeline : public IRenderer {
public:
    CryRenderPipeline();
    virtual ~CryRenderPipeline();

    virtual bool InitDevice(RenderAPIType api, void* hWnd, uint32_t width, uint32_t height, bool bFullscreen) override;
    virtual void ShutdownDevice() override;
    virtual void BeginFrame() override;
    virtual void EndFrame() override;

    virtual RenderAPIType GetCurrentAPI() const override { return m_api; }
    virtual uint32_t GetWidth() const override { return m_width; }
    virtual uint32_t GetHeight() const override { return m_height; }

    virtual bool LoadGeometry(const std::string& filePath, CryMeshGeometry& outMesh) override;
    virtual bool LoadTextureDDS(const std::string& filePath, TextureResource& outTex) override;
    virtual bool RegisterMaterial(const CryMaterial& mat) override;
    virtual const CryMaterial* GetMaterial(const std::string& name) const override;

    virtual void SetPostProcessSettings(const PostProcessSettings& settings) override { m_postProcess = settings; }
    virtual const PostProcessSettings& GetPostProcessSettings() const override { return m_postProcess; }

    bool IsDeviceInitialized() const { return m_bInitialized; }

private:
    RenderAPIType m_api = RenderAPIType::Direct3D11;
    void* m_hWnd = nullptr;
    uint32_t m_width = 1920;
    uint32_t m_height = 1080;
    bool m_bFullscreen = false;
    bool m_bInitialized = false;

    std::unordered_map<std::string, CryMaterial> m_materials;
    std::unordered_map<std::string, TextureResource> m_textures;
    PostProcessSettings m_postProcess;
};

// =======================================================================
// Implementação do Sistema de Animações e Blend Tree CryAnimation
// =======================================================================
class CryAnimationBlendTree : public IAnimationSystem {
public:
    CryAnimationBlendTree();
    virtual ~CryAnimationBlendTree();

    virtual void SetMovementSpeed(float speedMs) override;
    virtual LocomotionState GetLocomotionState() const override { return m_locoState; }
    virtual LocomotionBlendWeights GetBlendWeights() const override { return m_weights; }
    virtual void TriggerJump() override;
    virtual void TriggerLand() override;

    virtual void StartAttackAnimation(uint32_t animId, float baseDuration, float playerAttackSpeed) override;
    virtual const AttackAnimSync& GetAttackSync() const override { return m_attackSync; }
    virtual bool HasAttackHit() const override { return m_attackSync.hasHitFired; }

    virtual void StartSkillCast(uint32_t skillId, float castDuration, float hitTriggerSec) override;
    virtual bool TryCancelWithWeave() override;
    virtual const WeavingAnimState& GetWeavingState() const override { return m_weavingState; }

    virtual void Update(float deltaSec) override;

private:
    LocomotionState m_locoState = LocomotionState::Idle;
    LocomotionBlendWeights m_weights;
    AttackAnimSync m_attackSync;
    WeavingAnimState m_weavingState;
    float m_jumpTimer = 0.0f;
};

// =======================================================================
// Implementação do Motor de Áudio CrySound / FMOD
// =======================================================================
class CrySoundEngine : public ISoundSystem {
public:
    CrySoundEngine();
    virtual ~CrySoundEngine();

    virtual void SetListenerPosition(float x, float y, float z, float fwdX, float fwdY, float fwdZ) override;
    virtual uint32_t Play3DSound(SoundEventType eventType, const Sound3DParams& params, const std::string& assetName) override;
    virtual void PlayFootstep(FootstepSurface surface, float x, float y, float z) override;

    virtual void SetAmbientTrack(const std::string& trackName) override;
    virtual void SetCombatTrack(const std::string& trackName) override;
    virtual void TriggerCombatMusic(bool inCombat) override;

    virtual MusicTrackState GetMusicState() const override { return m_musicState; }
    virtual float GetAmbientVolume() const override { return m_ambientVol; }
    virtual float GetCombatVolume() const override { return m_combatVol; }

    virtual void Update(float deltaSec) override;

private:
    float m_listenerX = 0.0f, m_listenerY = 0.0f, m_listenerZ = 0.0f;
    std::string m_ambientTrack;
    std::string m_combatTrack;
    MusicTrackState m_musicState = MusicTrackState::AmbientPlaying;
    float m_ambientVol = 1.0f;
    float m_combatVol = 0.0f;
    float m_combatLingerTimer = 0.0f;
    uint32_t m_nextSoundId = 1;
};

// =======================================================================
// Implementação do ISystem que conecta todos os subsistemas CryEngine
// =======================================================================
class CrySystemImpl : public ISystem {
public:
    static CrySystemImpl& GetInstance();

    CrySystemImpl();
    virtual ~CrySystemImpl();

    virtual void Release() override {}
    virtual bool Update(int updateFlags = 0, int nPauseMode = 0) override;
    virtual ILog* GetILog() override;
    virtual IConsole* GetIConsole() override;
    virtual IEntitySystem* GetIEntitySystem() override { return nullptr; }
    virtual IScriptSystem* GetIScriptSystem() override { return nullptr; }
    virtual I3DEngine* GetI3DEngine() override { return nullptr; }
    virtual IPhysicalWorld* GetIPhysicalWorld() override { return nullptr; }
    virtual IRenderer* GetIRenderer() override { return &m_renderer; }
    virtual IAnimationSystem* GetIAnimationSystem() override { return &m_animation; }
    virtual ISoundSystem* GetISoundSystem() override { return &m_sound; }
    virtual const char* GetRootFolder() override { return ""; }
    virtual void Quit() override {}

    CryRenderPipeline& GetRenderer() { return m_renderer; }
    CryAnimationBlendTree& GetAnimation() { return m_animation; }
    CrySoundEngine& GetSound() { return m_sound; }

private:
    CryRenderPipeline m_renderer;
    CryAnimationBlendTree m_animation;
    CrySoundEngine m_sound;
};
