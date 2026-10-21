#pragma once
#include <string>
#include <vector>
#include <cstdint>

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

// Estados da Blend Tree de Locomoção Canônica
enum class LocomotionState {
    Idle = 0,
    Walk,
    Run,
    JumpStart,
    JumpLoop,
    Landing
};

// Pesos de interpolação da locomoção
struct LocomotionBlendWeights {
    float idleWeight = 1.0f;
    float walkWeight = 0.0f;
    float runWeight = 0.0f;
    float currentSpeed = 0.0f; // Metros por segundo
};

// Estado de animação de combate e ataque
struct AttackAnimSync {
    uint32_t attackAnimId = 0;
    float baseDurationSec = 1.2f;       // Tempo base da animação com velocidade 1.0
    float playerAttackSpeed = 1.2f;     // Atributo do jogador (ex: 1.2s base, 0.8s buffado)
    float playbackRate = 1.0f;          // Taxa calculada (baseDuration / playerAttackSpeed)
    float currentPlayTimeSec = 0.0f;
    float hitFrameTimeSec = 0.4f;       // Momento do impacto do golpe
    bool hasHitFired = false;
    bool isFinished = false;
};

// Informação de Habilidade e Janela de Weaving (Cancelamento de Animação Canônico)
struct WeavingAnimState {
    uint32_t skillId = 0;
    float skillCastDurationSec = 1.5f;
    float currentProgressSec = 0.0f;
    float damagePacketTriggerSec = 0.6f; // Ponto de emissão do pacote de dano
    float cancelWindowStartSec = 0.65f;   // Janela onde é permitido intercalar auto-ataque
    bool isDamageTriggered = false;
    bool isCancelled = false;
    bool isCompleted = false;

    bool CanCancelAnimation() const {
        return (currentProgressSec >= cancelWindowStartSec) && !isCompleted;
    }
};

// Interface do Sistema de Animação e Esqueletos da CryEngine (CryAnimation)
CRY_INTERFACE IAnimationSystem {
    virtual ~IAnimationSystem() = default;

    // Locomoção e Blend Tree
    virtual void SetMovementSpeed(float speedMs) = 0;
    virtual LocomotionState GetLocomotionState() const = 0;
    virtual LocomotionBlendWeights GetBlendWeights() const = 0;
    virtual void TriggerJump() = 0;
    virtual void TriggerLand() = 0;

    // Sincronização de Ataques
    virtual void StartAttackAnimation(uint32_t animId, float baseDuration, float playerAttackSpeed) = 0;
    virtual const AttackAnimSync& GetAttackSync() const = 0;
    virtual bool HasAttackHit() const = 0;

    // Conjuração e Cancelamento de Animação (Weaving)
    virtual void StartSkillCast(uint32_t skillId, float castDuration, float hitTriggerSec) = 0;
    virtual bool TryCancelWithWeave() = 0;
    virtual const WeavingAnimState& GetWeavingState() const = 0;

    // Atualização de quadros
    virtual void Update(float deltaSec) = 0;
};
