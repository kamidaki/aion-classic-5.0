#include "AddonButton.h"
#include "../core/GameLog.h"

// AddonButton
AddonButton::AddonButton(const std::string& name)
    : AddonFrame(name)
    , m_bEnabled(true)
    , m_bHovered(false)
    , m_bPressed(false)
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

bool AddonButton::OnLButtonDown(int x, int y, uint32_t flags) {
    (void)flags;
    if (!m_bEnabled || !IsVisible()) return false;
    if (HitTest(x, y)) {
        m_bPressed = true;
        return true;
    }
    return false;
}

bool AddonButton::OnLButtonUp(int x, int y, uint32_t flags) {
    (void)flags;
    if (!m_bEnabled || !IsVisible()) return false;
    if (m_bPressed && HitTest(x, y)) {
        m_bPressed = false;
        OnClick();
        return true;
    }
    m_bPressed = false;
    return false;
}

bool AddonButton::OnMouseMove(int x, int y, uint32_t flags) {
    (void)flags;
    if (!IsVisible()) return false;
    m_bHovered = HitTest(x, y);
    return m_bHovered;
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
