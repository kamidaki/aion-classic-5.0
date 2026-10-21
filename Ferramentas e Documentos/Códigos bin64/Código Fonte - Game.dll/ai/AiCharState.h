#pragma once
#include <string>

class AiCharContext;

// Classe base canônica de estados de personagens extraída do RTTI do game.dll (.?AVAiCharState@@)
class AiCharState {
public:
    virtual ~AiCharState() {}
    virtual const char* GetStateName() const = 0;
    virtual void OnEnter(AiCharContext* pContext) = 0;
    virtual void OnUpdate(AiCharContext* pContext) = 0;
    virtual void OnExit(AiCharContext* pContext) = 0;
};

// --- Estados Básicos de Ação ---
class AiCharStateAttack : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateAttack"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateFollow : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateFollow"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateRest : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateRest"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateLooting : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateLooting"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateAlarm : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateAlarm"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateDoping : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateDoping"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateEatFeed : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateEatFeed"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateEmotion : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateEmotion"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

// --- Estados Especializados de Função de Combate (Dealer / Healer / Tank) ---
class AiCharStateAttack_Dealer : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateAttack_Dealer"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateAttack_Healer : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateAttack_Healer"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateAttack_Tank : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateAttack_Tank"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateFollow_Dealer : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateFollow_Dealer"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateFollow_Healer : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateFollow_Healer"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateFollow_Tank : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateFollow_Tank"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateFollow_ToyPet : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateFollow_ToyPet"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

// --- Estados de Movimentação Física e Voo ---
class AiCharStateJump : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateJump"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateLand : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateLand"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateEndJump : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateEndJump"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateRoam : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateRoam"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateSearch : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateSearch"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateTakeOff : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateTakeOff"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateThreaten : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateThreaten"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};

class AiCharStateTremble : public AiCharState {
public:
    virtual const char* GetStateName() const override { return "AiCharStateTremble"; }
    virtual void OnEnter(AiCharContext* pContext) override;
    virtual void OnUpdate(AiCharContext* pContext) override;
    virtual void OnExit(AiCharContext* pContext) override;
};
