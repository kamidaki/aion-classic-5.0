#include "DlgCreateChar.h"
#include "../core/GameLog.h"

// DlgCreateCharBackstage
DlgCreateCharBackstage::DlgCreateCharBackstage()
    : AddonFrame("DlgCreateCharBackstage")
    , m_raceId(0)
    , m_classId(0)
{
}

DlgCreateCharBackstage::~DlgCreateCharBackstage() {}

void DlgCreateCharBackstage::SetRace(uint32_t raceId) {
    m_raceId = raceId;
    GameLog_Info("DlgCreateCharBackstage: Raça selecionada: %u (%s)", raceId, raceId == 0 ? "Elyos" : "Asmodian");
}

void DlgCreateCharBackstage::SetClass(uint32_t classId) {
    m_classId = classId;
    GameLog_Info("DlgCreateCharBackstage: Classe selecionada: %u", classId);
}

void DlgCreateCharBackstage::Show(bool bShow) {
    AddonFrame::Show(bShow);
}

void DlgCreateCharBackstage::Update() {
    AddonFrame::Update();
}

// DlgCreateCharEdit
DlgCreateCharEdit::DlgCreateCharEdit()
    : AddonFrame("DlgCreateCharEdit")
    , m_charName("Player")
    , m_gender(0)
{
    for (int i = 0; i < 64; ++i) m_params[i] = 0.5f;
}

DlgCreateCharEdit::~DlgCreateCharEdit() {}

void DlgCreateCharEdit::SetCustomizationParam(int index, float val) {
    if (index >= 0 && index < 64) {
        m_params[index] = val;
    }
}

float DlgCreateCharEdit::GetCustomizationParam(int index) const {
    if (index >= 0 && index < 64) {
        return m_params[index];
    }
    return 0.5f;
}

// DlgTooltip
DlgTooltip::DlgTooltip() : AddonFrame("DlgTooltip") {}
DlgTooltip::~DlgTooltip() {}

void DlgTooltip::SetItemTooltip(uint32_t itemId) {
    m_title = "Item #" + std::to_string(itemId);
    m_description = "Descrição detalhada do item extraído do client.";
    GameLog_Info("DlgTooltip exibido para ItemId=%u", itemId);
}

void DlgTooltip::SetSkillTooltip(uint32_t skillId, uint32_t level) {
    m_title = "Skill #" + std::to_string(skillId) + " Nível " + std::to_string(level);
    m_description = "Descrição dos efeitos e dano da habilidade.";
    GameLog_Info("DlgTooltip exibido para SkillId=%u Lv=%u", skillId, level);
}

void DlgTooltip::SetCustomText(const std::string& title, const std::string& desc) {
    m_title = title;
    m_description = desc;
}

// DlgIDArenaPvP
DlgIDArenaPvP::DlgIDArenaPvP()
    : AddonFrame("DlgIDArenaPvP")
    , m_bSearching(false)
    , m_arenaType(0)
    , m_bInMatch(false)
    , m_round(1)
    , m_score(0)
    , m_kills(0)
    , m_deaths(0)
{
}

DlgIDArenaPvP::~DlgIDArenaPvP() {}

void DlgIDArenaPvP::RequestMatch(uint32_t arenaType) {
    m_arenaType = arenaType;
    m_bSearching = true;
    m_bInMatch = false;
    GameLog_Info("DlgIDArenaPvP: Busca de partida iniciada para ArenaTipo=%u", arenaType);
}

void DlgIDArenaPvP::CancelMatch() {
    m_bSearching = false;
    GameLog_Info("DlgIDArenaPvP: Busca de partida cancelada.");
}

void DlgIDArenaPvP::StartMatch(int round) {
    m_bSearching = false;
    m_bInMatch = true;
    m_round = round;
    m_score = 0;
    m_kills = 0;
    m_deaths = 0;
}

void DlgIDArenaPvP::EndMatch() {
    m_bInMatch = false;
}

void DlgIDArenaPvP::RecordKill(int points) {
    m_kills++;
    m_score += points;
}

void DlgIDArenaPvP::RecordDeath(int penalty) {
    m_deaths++;
    m_score -= penalty;
    if (m_score < 0) m_score = 0;
}
