#include "AddonFrame.h"
#include "../core/GameLog.h"

AddonFrame::AddonFrame(const std::string& frameName)
    : m_frameName(frameName)
    , m_bVisible(false)
{
}

AddonFrame::~AddonFrame() {
}

void AddonFrame::Show(bool bShow) {
    m_bVisible = bShow;
    GameLog_Info("AddonFrame [%s] -> %s", m_frameName.c_str(), bShow ? "VISIBLE" : "HIDDEN");
}

void AddonFrame::Update() {
}
