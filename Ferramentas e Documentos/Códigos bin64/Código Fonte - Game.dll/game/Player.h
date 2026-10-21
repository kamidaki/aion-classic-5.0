#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include "../ai/AIObject.h"
#include "GameplayExt.h"

// Objeto base genérico (.?AVBasicObject@@)
class BasicObject {
public:
    BasicObject(uint32_t id, const std::string& name);
    virtual ~BasicObject();

    uint32_t GetId() const { return m_id; }
    const std::string& GetName() const { return m_name; }

private:
    uint32_t m_id;
    std::string m_name;
};

// Gerenciador de scripts de NPCs (.?AVNpcScriptMgr@@)
class NpcScriptMgr {
public:
    NpcScriptMgr();
    ~NpcScriptMgr();

    bool ExecuteScript(uint32_t npcId, const std::string& eventName);
};

// Classe canônica do jogador (Player) extraída do RTTI (.?AVPlayer@@)
class Player : public AIObject, public CharacterObject {
public:
    Player(uint32_t objectId, const std::string& name, uint8_t playerClass, uint8_t race, uint8_t gender);
    virtual ~Player();


    virtual void Update() override;

    uint8_t GetPlayerClass() const { return m_playerClass; }
    uint8_t GetRace() const { return m_race; }
    uint8_t GetGender() const { return m_gender; }
    uint32_t GetLevel() const { return m_level; }
    void SetLevel(uint32_t level) { m_level = level; }

    int64_t GetKinah() const { return m_kinah; }
    void SetKinah(int64_t kinah) { m_kinah = kinah; }

    uint32_t GetAp() const { return m_ap; }
    void SetAp(uint32_t ap) { m_ap = ap; }

    int32_t GetHp() const { return m_hp; }
    int32_t GetMaxHp() const { return m_maxHp; }
    void SetHp(int32_t hp, int32_t maxHp) { m_hp = hp; m_maxHp = maxHp; }

    int32_t GetMp() const { return m_mp; }
    int32_t GetMaxMp() const { return m_maxMp; }
    void SetMp(int32_t mp, int32_t maxMp) { m_mp = mp; m_maxMp = maxMp; }

    int32_t GetDp() const { return m_dp; }
    int32_t GetMaxDp() const { return 4000; }
    void SetDp(int32_t dp);
    void AddDp(int32_t amount);
    bool ConsumeDp(int32_t amount);
    void ResetDp();

    // Missões de Estigma
    bool HasCompletedRegularStigmaQuest() const { return m_bRegularStigmaQuest; }
    void SetCompletedRegularStigmaQuest(bool done) { m_bRegularStigmaQuest = done; }

    bool HasCompletedGreaterStigmaQuest() const { return m_bGreaterStigmaQuest; }
    void SetCompletedGreaterStigmaQuest(bool done) { m_bGreaterStigmaQuest = done; }

    // Fragmentos de Estigma (Stigma Shards)
    uint32_t GetStigmaShards() const { return m_stigmaShards; }
    void SetStigmaShards(uint32_t shards) { m_stigmaShards = shards; }

    // Mantras Ativos (Chanter)
    const std::vector<uint32_t>& GetActiveMantras() const { return m_activeMantras; }
    std::vector<uint32_t>& GetActiveMantras() { return m_activeMantras; }

    bool IsFlying() const { return m_bFlying; }
    void SetFlying(bool flying) { m_bFlying = flying; }

private:
    uint8_t  m_playerClass;
    uint8_t  m_race;
    uint8_t  m_gender;
    uint32_t m_level;
    int64_t  m_kinah;
    uint32_t m_ap;
    int32_t  m_hp;
    int32_t  m_maxHp;
    int32_t  m_mp;
    int32_t  m_maxMp;
    int32_t  m_dp;
    bool     m_bFlying;
    bool     m_bRegularStigmaQuest;
    bool     m_bGreaterStigmaQuest;
    uint32_t m_stigmaShards;
    std::vector<uint32_t> m_activeMantras;
};
