#pragma once
#include <windows.h>
#include <cstdint>
#include <memory>
#include "AiCharState.h"

class AIObject;

// Contexto canônico de IA e estado de personagens extraído do RTTI (.?AVAiCharContext@@)
class AiCharContext {
public:
    AiCharContext(AIObject* pOwner);
    ~AiCharContext();

    void ChangeState(std::unique_ptr<AiCharState> newState);
    void Update();

    AiCharState* GetCurrentState() const { return m_pCurrentState.get(); }
    AIObject* GetOwner() const { return m_pOwner; }

private:
    AIObject* m_pOwner;
    std::unique_ptr<AiCharState> m_pCurrentState;
};
