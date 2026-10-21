#pragma once
#include "AddonFrame.h"
#include <string>

// Cenário de fundo da criação de personagem (.?AVDlgCreateCharBackstage@@)
class DlgCreateCharBackstage : public AddonFrame {
public:
    DlgCreateCharBackstage();
    virtual ~DlgCreateCharBackstage();

    void SetRace(uint32_t raceId); // Elyos = 0, Asmodian = 1
    void SetClass(uint32_t classId);

    virtual void Show(bool bShow) override;
    virtual void Update() override;

private:
    uint32_t m_raceId;
    uint32_t m_classId;
};

// Interface de personalização visual de personagem (.?AVDlgCreateCharEdit@@)
class DlgCreateCharEdit : public AddonFrame {
public:
    DlgCreateCharEdit();
    virtual ~DlgCreateCharEdit();

    void SetCharacterName(const std::string& name) { m_charName = name; }
    const std::string& GetCharacterName() const { return m_charName; }

    void SetGender(uint8_t gender) { m_gender = gender; }
    uint8_t GetGender() const { return m_gender; }

    void SetCustomizationParam(int index, float val);
    float GetCustomizationParam(int index) const;

private:
    std::string m_charName;
    uint8_t m_gender;
    float m_params[64];
};

// Tooltip canônico (.?AVDlgTooltip@@)
class DlgTooltip : public AddonFrame {
public:
    DlgTooltip();
    virtual ~DlgTooltip();

    void SetItemTooltip(uint32_t itemId);
    void SetSkillTooltip(uint32_t skillId, uint32_t level);
    void SetCustomText(const std::string& title, const std::string& desc);

private:
    std::string m_title;
    std::string m_description;
};

// Diálogo de Arena PvP (.?AVDlgIDArenaPvP@@)
class DlgIDArenaPvP : public AddonFrame {
public:
    DlgIDArenaPvP();
    virtual ~DlgIDArenaPvP();

    void RequestMatch(uint32_t arenaType);
    void CancelMatch();

    bool IsSearching() const { return m_bSearching; }
    uint32_t GetArenaType() const { return m_arenaType; }

    void StartMatch(int round);
    void EndMatch();
    void RecordKill(int points = 1000);
    void RecordDeath(int penalty = 300);

    int GetRound() const { return m_round; }
    int GetScore() const { return m_score; }
    int GetKills() const { return m_kills; }
    int GetDeaths() const { return m_deaths; }

private:
    bool m_bSearching;
    uint32_t m_arenaType;
    bool m_bInMatch;
    int m_round;
    int m_score;
    int m_kills;
    int m_deaths;
};
