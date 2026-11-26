#include "AiStatesExt.h"
#include "../core/GameLog.h"

CCalcUnit::CCalcUnit() {}
CCalcUnit::~CCalcUnit() {}

EventHandleUnit::EventHandleUnit() {}
EventHandleUnit::~EventHandleUnit() {}

FindHelperFlock::FindHelperFlock() {}
FindHelperFlock::~FindHelperFlock() {}

FindHelperUnit::FindHelperUnit() {}
FindHelperUnit::~FindHelperUnit() {}

FishFlock::FishFlock() {}
FishFlock::~FishFlock() {}

FishUnit::FishUnit() {}
FishUnit::~FishUnit() {}

FlockObject::FlockObject() {}
FlockObject::~FlockObject() {}

void RegisterAllAiStatesExt() {
    GameLog_Info("Registrando 28 classes de AI...");
    static AiCharStateAlarm s_AiCharStateAlarm;
    static AiCharStateAttack s_AiCharStateAttack;
    static AiCharStateAttack_Healer s_AiCharStateAttack_Healer;
    static AiCharStateAttack_Tank s_AiCharStateAttack_Tank;
    static AiCharStateDoping s_AiCharStateDoping;
    static AiCharStateEatFeed s_AiCharStateEatFeed;
    static AiCharStateEmotion s_AiCharStateEmotion;
    static AiCharStateEndJump s_AiCharStateEndJump;
    static AiCharStateFollow s_AiCharStateFollow;
    static AiCharStateFollow_Healer s_AiCharStateFollow_Healer;
    static AiCharStateFollow_Tank s_AiCharStateFollow_Tank;
    static AiCharStateFollow_ToyPet s_AiCharStateFollow_ToyPet;
    static AiCharStateJump s_AiCharStateJump;
    static AiCharStateLand s_AiCharStateLand;
    static AiCharStateLooting s_AiCharStateLooting;
    static AiCharStateRest s_AiCharStateRest;
    static AiCharStateRoam s_AiCharStateRoam;
    static AiCharStateSearch s_AiCharStateSearch;
    static AiCharStateTakeOff s_AiCharStateTakeOff;
    static AiCharStateThreaten s_AiCharStateThreaten;
    static AiCharStateTremble s_AiCharStateTremble;
    static CCalcUnit s_CCalcUnit;
    static EventHandleUnit s_EventHandleUnit;
    static FindHelperFlock s_FindHelperFlock;
    static FindHelperUnit s_FindHelperUnit;
    static FishFlock s_FishFlock;
    static FishUnit s_FishUnit;
    static FlockObject s_FlockObject;
}