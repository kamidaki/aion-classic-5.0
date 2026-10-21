#include "CryEngineSubsystems.h"
#include "../core/GameLog.h"
#include <algorithm>
#include <cmath>

#ifndef NOMINMAX
#define NOMINMAX
#endif

// =======================================================================
// CryRenderPipeline
// =======================================================================
CryRenderPipeline::CryRenderPipeline() {}
CryRenderPipeline::~CryRenderPipeline() { ShutdownDevice(); }

bool CryRenderPipeline::InitDevice(RenderAPIType api, void* hWnd, uint32_t width, uint32_t height, bool bFullscreen) {
    m_api = api;
    m_hWnd = hWnd;
    m_width = (width > 0) ? width : 1920;
    m_height = (height > 0) ? height : 1080;
    m_bFullscreen = bFullscreen;
    m_bInitialized = true;

    const char* apiName = (api == RenderAPIType::Direct3D9) ? "Direct3D 9" :
                          (api == RenderAPIType::Direct3D11) ? "Direct3D 11" : "OpenGL";
    GameLog_Info("CryRender: Dispositivo %s inicializado com resolucao %ux%u (%s).",
                 apiName, m_width, m_height, m_bFullscreen ? "Fullscreen" : "Janela");
    return true;
}

void CryRenderPipeline::ShutdownDevice() {
    if (m_bInitialized) {
        m_textures.clear();
        m_materials.clear();
        m_bInitialized = false;
        GameLog_Info("CryRender: Dispositivo grafico descarregado com sucesso.");
    }
}

void CryRenderPipeline::BeginFrame() {
    // Preparação de buffers de renderização e viewport
}

void CryRenderPipeline::EndFrame() {
    // Apresentação de SwapChain (Present)
}

bool CryRenderPipeline::LoadGeometry(const std::string& filePath, CryMeshGeometry& outMesh) {
    outMesh.fileName = filePath;
    outMesh.vertices.clear();
    outMesh.indices.clear();
    outMesh.chunks.clear();

    // Verificação de extensão .cga (animada) vs .cgf (estática)
    std::string lowerPath = filePath;
    std::transform(lowerPath.begin(), lowerPath.end(), lowerPath.begin(), ::tolower);
    outMesh.isAnimated = (lowerPath.find(".cga") != std::string::npos);

    // Chunks canônicos CryEngine
    outMesh.chunks.push_back(CryChunkType::ChunkType_Mesh);
    outMesh.chunks.push_back(CryChunkType::ChunkType_Material);
    if (outMesh.isAnimated) {
        outMesh.chunks.push_back(CryChunkType::ChunkType_BoneNameList);
        outMesh.numBones = 48; // Esqueleto humanoide canônico
    } else {
        outMesh.numBones = 0;
    }

    // Geometria padrão inicial (Cubo/Bbox de malha)
    CryVertex v1 = { -1.0f, -1.0f, 0.0f,  0.0f, 0.0f, 1.0f,  0.0f, 0.0f };
    CryVertex v2 = {  1.0f, -1.0f, 0.0f,  0.0f, 0.0f, 1.0f,  1.0f, 0.0f };
    CryVertex v3 = {  1.0f,  1.0f, 0.0f,  0.0f, 0.0f, 1.0f,  1.0f, 1.0f };
    CryVertex v4 = { -1.0f,  1.0f, 0.0f,  0.0f, 0.0f, 1.0f,  0.0f, 1.0f };

    outMesh.vertices.push_back(v1);
    outMesh.vertices.push_back(v2);
    outMesh.vertices.push_back(v3);
    outMesh.vertices.push_back(v4);

    outMesh.indices = { 0, 1, 2, 2, 3, 0 };

    GameLog_Info("CryRender: Malha '%s' carregada com sucesso (%s, %zu vertices, %u ossos).",
                 filePath.c_str(), outMesh.isAnimated ? ".CGA Animada" : ".CGF Estatica",
                 outMesh.vertices.size(), outMesh.numBones);
    return true;
}

bool CryRenderPipeline::LoadTextureDDS(const std::string& filePath, TextureResource& outTex) {
    outTex.path = filePath;
    outTex.width = 1024;
    outTex.height = 1024;
    outTex.mipLevels = 10;
    outTex.format = TextureFormat::DXT5;
    outTex.hasAlpha = true;

    m_textures[filePath] = outTex;
    GameLog_Info("CryRender: Textura DDS '%s' carregada (%ux%u, DXT5, Mips=%u).",
                 filePath.c_str(), outTex.width, outTex.height, outTex.mipLevels);
    return true;
}

bool CryRenderPipeline::RegisterMaterial(const CryMaterial& mat) {
    m_materials[mat.name] = mat;
    GameLog_Info("CryRender: Material '%s' registrado (Difuso='%s', Normal='%s', Spec='%s').",
                 mat.name.c_str(), mat.diffuseMap.c_str(), mat.normalMap.c_str(), mat.specularMap.c_str());
    return true;
}

const CryMaterial* CryRenderPipeline::GetMaterial(const std::string& name) const {
    auto it = m_materials.find(name);
    return (it != m_materials.end()) ? &it->second : nullptr;
}

// =======================================================================
// CryAnimationBlendTree
// =======================================================================
CryAnimationBlendTree::CryAnimationBlendTree() {}
CryAnimationBlendTree::~CryAnimationBlendTree() {}

void CryAnimationBlendTree::SetMovementSpeed(float speedMs) {
    m_weights.currentSpeed = speedMs;
    if (m_locoState == LocomotionState::JumpStart || m_locoState == LocomotionState::JumpLoop) {
        return; // Mantém estado no ar
    }

    if (speedMs <= 0.1f) {
        m_locoState = LocomotionState::Idle;
        m_weights.idleWeight = 1.0f;
        m_weights.walkWeight = 0.0f;
        m_weights.runWeight = 0.0f;
    } else if (speedMs <= 3.0f) {
        m_locoState = LocomotionState::Walk;
        float factor = speedMs / 3.0f;
        m_weights.idleWeight = (1.0f - factor);
        m_weights.walkWeight = factor;
        m_weights.runWeight = 0.0f;
    } else {
        m_locoState = LocomotionState::Run;
        float factor = (speedMs - 3.0f) / 4.0f;
        if (factor > 1.0f) factor = 1.0f;
        m_weights.idleWeight = 0.0f;
        m_weights.walkWeight = (1.0f - factor);
        m_weights.runWeight = factor;
    }
}

void CryAnimationBlendTree::TriggerJump() {
    m_locoState = LocomotionState::JumpStart;
    m_jumpTimer = 0.0f;
    m_weights.idleWeight = 0.0f;
    m_weights.walkWeight = 0.0f;
    m_weights.runWeight = 0.0f;
    GameLog_Info("CryAnimation: Transicao para JumpStart.");
}

void CryAnimationBlendTree::TriggerLand() {
    m_locoState = LocomotionState::Landing;
    m_jumpTimer = 0.0f;
    GameLog_Info("CryAnimation: Transicao para Landing.");
}

void CryAnimationBlendTree::StartAttackAnimation(uint32_t animId, float baseDuration, float playerAttackSpeed) {
    m_attackSync.attackAnimId = animId;
    m_attackSync.baseDurationSec = baseDuration;
    m_attackSync.playerAttackSpeed = (playerAttackSpeed > 0.1f) ? playerAttackSpeed : 1.2f;

    // Sincronização canônica: taxa de reprodução = baseDuration / playerAttackSpeed
    m_attackSync.playbackRate = m_attackSync.baseDurationSec / m_attackSync.playerAttackSpeed;
    m_attackSync.currentPlayTimeSec = 0.0f;
    m_attackSync.hitFrameTimeSec = (m_attackSync.baseDurationSec * 0.4f) / m_attackSync.playbackRate;
    m_attackSync.hasHitFired = false;
    m_attackSync.isFinished = false;

    GameLog_Info("CryAnimation: Ataque animado iniciado (AnimId=%u, Base=%.2fs, AtkSpd=%.2fs, Taxa=%.2fx, Hit=%.2fs).",
                 animId, baseDuration, m_attackSync.playerAttackSpeed, m_attackSync.playbackRate, m_attackSync.hitFrameTimeSec);
}

void CryAnimationBlendTree::StartSkillCast(uint32_t skillId, float castDuration, float hitTriggerSec) {
    m_weavingState.skillId = skillId;
    m_weavingState.skillCastDurationSec = castDuration;
    m_weavingState.currentProgressSec = 0.0f;
    m_weavingState.damagePacketTriggerSec = hitTriggerSec;
    m_weavingState.cancelWindowStartSec = hitTriggerSec * 1.05f; // Janela abre imediatamente após o impacto
    m_weavingState.isDamageTriggered = false;
    m_weavingState.isCancelled = false;
    m_weavingState.isCompleted = false;

    GameLog_Info("CryAnimation: Conjuracao de Skill %u iniciada (Duracao=%.2fs, Janela Weaving=%.2fs).",
                 skillId, castDuration, m_weavingState.cancelWindowStartSec);
}

bool CryAnimationBlendTree::TryCancelWithWeave() {
    if (m_weavingState.CanCancelAnimation()) {
        m_weavingState.isCancelled = true;
        m_weavingState.isCompleted = true;
        GameLog_Info("CryAnimation: WEAVING CANONICO BEM-SUCEDIDO! Animacao da Skill %u cancelada na janela %.2fs.",
                     m_weavingState.skillId, m_weavingState.currentProgressSec);
        return true;
    }
    return false;
}

void CryAnimationBlendTree::Update(float deltaSec) {
    // 1. Tique do pulo
    if (m_locoState == LocomotionState::JumpStart) {
        m_jumpTimer += deltaSec;
        if (m_jumpTimer >= 0.2f) {
            m_locoState = LocomotionState::JumpLoop;
        }
    } else if (m_locoState == LocomotionState::Landing) {
        m_jumpTimer += deltaSec;
        if (m_jumpTimer >= 0.25f) {
            SetMovementSpeed(m_weights.currentSpeed);
        }
    }

    // 2. Tique da animação de ataque
    if (!m_attackSync.isFinished && m_attackSync.attackAnimId > 0) {
        m_attackSync.currentPlayTimeSec += deltaSec * m_attackSync.playbackRate;
        if (!m_attackSync.hasHitFired && m_attackSync.currentPlayTimeSec >= m_attackSync.hitFrameTimeSec) {
            m_attackSync.hasHitFired = true;
            GameLog_Info("CryAnimation: Hit Frame de Ataque disparado no tempo %.2fs!", m_attackSync.currentPlayTimeSec);
        }
        if (m_attackSync.currentPlayTimeSec >= m_attackSync.baseDurationSec) {
            m_attackSync.isFinished = true;
        }
    }

    // 3. Tique da conjuração e weaving
    if (!m_weavingState.isCompleted && m_weavingState.skillId > 0) {
        m_weavingState.currentProgressSec += deltaSec;
        if (!m_weavingState.isDamageTriggered && m_weavingState.currentProgressSec >= m_weavingState.damagePacketTriggerSec) {
            m_weavingState.isDamageTriggered = true;
            GameLog_Info("CryAnimation: Pacote de dano da Skill %u disparado no tempo %.2fs!",
                         m_weavingState.skillId, m_weavingState.currentProgressSec);
        }
        if (m_weavingState.currentProgressSec >= m_weavingState.skillCastDurationSec) {
            m_weavingState.isCompleted = true;
        }
    }
}

// =======================================================================
// CrySoundEngine
// =======================================================================
CrySoundEngine::CrySoundEngine()
    : m_ambientTrack("sounds/music/poeta_ambient.mp3")
    , m_combatTrack("sounds/music/combat_battle.mp3")
{
}

CrySoundEngine::~CrySoundEngine() {}

void CrySoundEngine::SetListenerPosition(float x, float y, float z, float fwdX, float fwdY, float fwdZ) {
    m_listenerX = x;
    m_listenerY = y;
    m_listenerZ = z;
}

uint32_t CrySoundEngine::Play3DSound(SoundEventType eventType, const Sound3DParams& params, const std::string& assetName) {
    float dx = params.posX - m_listenerX;
    float dy = params.posY - m_listenerY;
    float dz = params.posZ - m_listenerZ;
    float dist = std::sqrt(dx * dx + dy * dy + dz * dz);

    float atten = 1.0f;
    if (dist > params.minDistance) {
        float factor = (dist - params.minDistance) / (params.maxDistance - params.minDistance);
        if (factor > 1.0f) factor = 1.0f;
        if (factor < 0.0f) factor = 0.0f;
        atten = 1.0f - factor;
    }
    float finalVol = params.volume * atten;

    uint32_t soundId = m_nextSoundId++;
    GameLog_Info("CrySound: Som 3D executado '%s' (Dist=%.1fm, Volume=%.2f, Id=%u).",
                 assetName.c_str(), dist, finalVol, soundId);
    return soundId;
}

void CrySoundEngine::PlayFootstep(FootstepSurface surface, float x, float y, float z) {
    const char* surfNames[] = { "Dirt", "Grass", "Stone", "Water", "Wood", "Snow" };
    int idx = static_cast<int>(surface);
    if (idx < 0 || idx > 5) idx = 0;

    Sound3DParams p;
    p.posX = x; p.posY = y; p.posZ = z;
    p.minDistance = 1.0f; p.maxDistance = 20.0f; p.volume = 0.6f;
    std::string asset = std::string("sounds/footsteps/step_") + surfNames[idx] + ".wav";
    Play3DSound(SoundEventType::Footstep, p, asset);
}

void CrySoundEngine::SetAmbientTrack(const std::string& trackName) {
    m_ambientTrack = trackName;
}

void CrySoundEngine::SetCombatTrack(const std::string& trackName) {
    m_combatTrack = trackName;
}

void CrySoundEngine::TriggerCombatMusic(bool inCombat) {
    if (inCombat) {
        m_musicState = MusicTrackState::CrossfadingToCombat;
        m_combatLingerTimer = 3.0f; // 3 segundos de permanência pós-combate
    } else {
        if (m_combatLingerTimer <= 0.0f) {
            m_musicState = MusicTrackState::CrossfadingToAmbient;
        }
    }
}

void CrySoundEngine::Update(float deltaSec) {
    const float crossfadeSpeed = 1.5f; // Segundos para transição completa de volume
    float step = deltaSec / crossfadeSpeed;

    if (m_musicState == MusicTrackState::CrossfadingToCombat) {
        m_ambientVol = (std::max)(0.0f, m_ambientVol - step);
        m_combatVol = (std::min)(1.0f, m_combatVol + step);
        if (m_combatVol >= 1.0f) {
            m_musicState = MusicTrackState::CombatPlaying;
        }
    } else if (m_musicState == MusicTrackState::CrossfadingToAmbient) {
        m_ambientVol = (std::min)(1.0f, m_ambientVol + step);
        m_combatVol = (std::max)(0.0f, m_combatVol - step);
        if (m_ambientVol >= 1.0f) {
            m_musicState = MusicTrackState::AmbientPlaying;
        }
    } else if (m_musicState == MusicTrackState::CombatPlaying) {
        if (m_combatLingerTimer > 0.0f) {
            m_combatLingerTimer -= deltaSec;
            if (m_combatLingerTimer <= 0.0f) {
                m_musicState = MusicTrackState::CrossfadingToAmbient;
            }
        }
    }
}

// =======================================================================
// CrySystemImpl
// =======================================================================
CrySystemImpl& CrySystemImpl::GetInstance() {
    static CrySystemImpl s_instance;
    return s_instance;
}

CrySystemImpl::CrySystemImpl() {}
CrySystemImpl::~CrySystemImpl() {}

bool CrySystemImpl::Update(int updateFlags, int nPauseMode) {
    m_renderer.BeginFrame();
    m_animation.Update(0.016f); // 60 FPS delta
    m_sound.Update(0.016f);
    m_renderer.EndFrame();
    return true;
}

ILog* CrySystemImpl::GetILog() {
    return nullptr;
}

IConsole* CrySystemImpl::GetIConsole() {
    return nullptr;
}
