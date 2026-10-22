#include "AddonWidgets.h"
#include "../core/GameLog.h"

// AddonEditBox
AddonEditBox::AddonEditBox(const std::string& name) : AddonFrame(name), m_maxChars(256) {}
AddonEditBox::~AddonEditBox() {}

// AddonStatic
AddonStatic::AddonStatic(const std::string& name) : AddonFrame(name) {}
AddonStatic::~AddonStatic() {}

// AddonStaticImage
AddonStaticImage::AddonStaticImage(const std::string& name) : AddonFrame(name) {}
AddonStaticImage::~AddonStaticImage() {}

// AddonListBox
AddonListBox::AddonListBox(const std::string& name) : AddonFrame(name), m_selectedIndex(-1) {}
AddonListBox::~AddonListBox() { m_items.clear(); }
void AddonListBox::AddItem(const std::string& item) { m_items.push_back(item); }
void AddonListBox::Clear() { m_items.clear(); m_selectedIndex = -1; }

// AddonListViewEx
AddonListViewEx::AddonListViewEx(const std::string& name) : AddonFrame(name) {}
AddonListViewEx::~AddonListViewEx() { Clear(); }
void AddonListViewEx::AddColumn(const std::string& header, int width) { m_columns.push_back({ header, width }); }
void AddonListViewEx::AddRow(const std::vector<std::string>& row) { m_rows.push_back(row); }
void AddonListViewEx::Clear() { m_columns.clear(); m_rows.clear(); }

// AddonScrollable
AddonScrollable::AddonScrollable(const std::string& name) : AddonFrame(name), m_scrollPos(0) {}
AddonScrollable::~AddonScrollable() {}

#include <algorithm>

// AddonTopLevelFrame
AddonTopLevelFrame::AddonTopLevelFrame(const std::string& name) 
    : AddonFrame(name)
    , m_bActive(false)
    , m_pFocusedFrame(nullptr)
{
}

AddonTopLevelFrame::~AddonTopLevelFrame() {
    m_windowStack.clear();
}

void AddonTopLevelFrame::BringToFront() {
    m_bActive = true;
    GameLog_Info("AddonTopLevelFrame [%s] trazido para primeiro plano.", GetFrameName().c_str());
}

void AddonTopLevelFrame::BringToFront(AddonFrame* pFrame) {
    if (!pFrame) return;
    auto it = std::find(m_windowStack.begin(), m_windowStack.end(), pFrame);
    if (it != m_windowStack.end()) {
        m_windowStack.erase(it);
    }
    m_windowStack.push_back(pFrame);
    SetFocusedWindow(pFrame);
    GameLog_Info("AddonTopLevelFrame: Janela [%s] elevada ao topo do Z-Order.", pFrame->GetFrameName().c_str());
}

void AddonTopLevelFrame::SendToBack(AddonFrame* pFrame) {
    if (!pFrame) return;
    auto it = std::find(m_windowStack.begin(), m_windowStack.end(), pFrame);
    if (it != m_windowStack.end()) {
        m_windowStack.erase(it);
    }
    m_windowStack.insert(m_windowStack.begin(), pFrame);
}

void AddonTopLevelFrame::RegisterWindow(AddonFrame* pFrame) {
    if (!pFrame) return;
    auto it = std::find(m_windowStack.begin(), m_windowStack.end(), pFrame);
    if (it == m_windowStack.end()) {
        m_windowStack.push_back(pFrame);
    }
}

void AddonTopLevelFrame::UnregisterWindow(AddonFrame* pFrame) {
    if (!pFrame) return;
    auto it = std::find(m_windowStack.begin(), m_windowStack.end(), pFrame);
    if (it != m_windowStack.end()) {
        m_windowStack.erase(it);
    }
    if (m_pFocusedFrame == pFrame) {
        m_pFocusedFrame = m_windowStack.empty() ? nullptr : m_windowStack.back();
    }
}

AddonFrame* AddonTopLevelFrame::FindTopWindowAt(int screenX, int screenY) const {
    for (auto it = m_windowStack.rbegin(); it != m_windowStack.rend(); ++it) {
        AddonFrame* pFrame = *it;
        if (pFrame && pFrame->IsVisible() && pFrame->HitTest(screenX, screenY)) {
            return pFrame;
        }
    }
    return nullptr;
}

void AddonTopLevelFrame::SetFocusedWindow(AddonFrame* pFrame) {
    m_pFocusedFrame = pFrame;
}

bool AddonTopLevelFrame::DispatchKeyEvent(uint32_t vKey, bool bDown) {
    if (!bDown) return false;

    if (m_pFocusedFrame && m_pFocusedFrame->IsVisible()) {
        m_pFocusedFrame->OnKeyDown(vKey, UI_EVENT_NONE);
    }

    if (vKey == VK_ESCAPE) {
        for (auto it = m_windowStack.rbegin(); it != m_windowStack.rend(); ++it) {
            AddonFrame* pFrame = *it;
            if (pFrame && pFrame->IsVisible()) {
                pFrame->Show(false);
                GameLog_Info("AddonTopLevelFrame: Janela [%s] fechada via ESC.", pFrame->GetFrameName().c_str());
                return true;
            }
        }
    }

    return false;
}

bool AddonTopLevelFrame::DispatchMouseEvent(int screenX, int screenY, uint32_t eventFlags) {
    AddonFrame* pTarget = FindTopWindowAt(screenX, screenY);
    if (pTarget) {
        if (eventFlags & UI_EVENT_LBUTTON) {
            BringToFront(pTarget);
            pTarget->OnLButtonDown(screenX, screenY, eventFlags);
        } else if (eventFlags & UI_EVENT_RBUTTON) {
            pTarget->OnRButtonDown(screenX, screenY, eventFlags);
        } else {
            pTarget->OnMouseMove(screenX, screenY, eventFlags);
        }
        return true;
    }
    return false;
}

void AddonTopLevelFrame::RenderAllVisibleWindows() {
    for (AddonFrame* pFrame : m_windowStack) {
        if (pFrame && pFrame->IsVisible()) {
            pFrame->OnRender();
        }
    }
}
