#include "AddonButton.h"
#include "../core/GameLog.h"

// AddonButton
AddonButton::AddonButton(const std::string& name)
    : AddonFrame(name)
    , m_bEnabled(true)
{
}

AddonButton::~AddonButton() {
}

void AddonButton::OnClick() {
    if (!m_bEnabled) return;
    GameLog_Info("AddonButton [%s] clicado.", GetFrameName().c_str());
    if (m_clickHandler) {
        m_clickHandler();
    }
}

// AddonCheckButton
AddonCheckButton::AddonCheckButton(const std::string& name)
    : AddonButton(name)
    , m_bChecked(false)
{
}

AddonCheckButton::~AddonCheckButton() {
}

void AddonCheckButton::SetChecked(bool checked) {
    m_bChecked = checked;
    GameLog_Info("AddonCheckButton [%s] checked=%d", GetFrameName().c_str(), checked ? 1 : 0);
}

void AddonCheckButton::OnClick() {
    if (!m_bEnabled) return;
    SetChecked(!m_bChecked);
    AddonButton::OnClick();
}

// AddonRadioButton
AddonRadioButton::AddonRadioButton(const std::string& name, int groupId)
    : AddonButton(name)
    , m_groupId(groupId)
    , m_bSelected(false)
{
}

AddonRadioButton::~AddonRadioButton() {
}

void AddonRadioButton::SetSelected(bool selected) {
    m_bSelected = selected;
    GameLog_Info("AddonRadioButton [%s] selected=%d grupo=%d", GetFrameName().c_str(), selected ? 1 : 0, m_groupId);
}

void AddonRadioButton::OnClick() {
    if (!m_bEnabled) return;
    SetSelected(true);
    AddonButton::OnClick();
}
