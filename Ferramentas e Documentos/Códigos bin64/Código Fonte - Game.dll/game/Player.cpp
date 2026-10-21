#include "Player.h"
#include "../core/GameLog.h"

// BasicObject
BasicObject::BasicObject(uint32_t id, const std::string& name) : m_id(id), m_name(name) {}
BasicObject::~BasicObject() {}

// NpcScriptMgr
NpcScriptMgr::NpcScriptMgr() {}
NpcScriptMgr::~NpcScriptMgr() {}
bool NpcScriptMgr::ExecuteScript(uint32_t npcId, const std::string& eventName) {
    GameLog_Info("NpcScriptMgr: Executando script para NPC=%u Evento='%s'", npcId, eventName.c_str());
    return true;
}

// Player
Player::Player(uint32_t objectId, const std::string& name, uint8_t playerClass, uint8_t race, uint8_t gender)
    : AIObject(objectId, name)
    , m_playerClass(playerClass)
    , m_race(race)
    , m_gender(gender)
    , m_level(1)
    , m_kinah(0)
    , m_ap(0)
    , m_hp(100)
    , m_maxHp(100)
    , m_mp(100)
    , m_maxMp(100)
    , m_dp(0)
    , m_bFlying(false)
    , m_bRegularStigmaQuest(false)
    , m_bGreaterStigmaQuest(false)
    , m_stigmaShards(0)
{
    GameLog_Info("Player instanciado: Obj=%u Nome='%s' Classe=%u Raca=%u", objectId, name.c_str(), playerClass, race);
}

Player::~Player() {
    GameLog_Info("Player destruído: Obj=%u", GetObjectId());
}

void Player::SetDp(int32_t dp) {
    if (dp < 0) dp = 0;
    if (dp > 4000) dp = 4000;
    m_dp = dp;
}

void Player::AddDp(int32_t amount) {
    SetDp(m_dp + amount);
}

bool Player::ConsumeDp(int32_t amount) {
    if (amount <= 0) return true;
    if (m_dp >= amount) {
        m_dp -= amount;
        return true;
    }
    return false;
}

void Player::ResetDp() {
    m_dp = 0;
    GameLog_Info("Player::ResetDp: DP resetado para 0 no jogador Obj=%u", GetObjectId());
}

void Player::Update() {
    AIObject::Update();
}
