#include "AddonFrame.h"
#include "../core/GameLog.h"
#include <algorithm>

AddonFrame::AddonFrame(const std::string& frameName)
    : m_frameName(frameName)
    , m_x(0)
    , m_y(0)
    , m_width(100)
    , m_height(100)
    , m_alpha(1.0f)
    , m_bVisible(false)
    , m_bEnabled(true)
    , m_bDraggable(false)
    , m_bModal(false)
    , m_bFocused(false)
    , m_bDragging(false)
    , m_dragOffsetX(0)
    , m_dragOffsetY(0)
    , m_pParent(nullptr)
{
}

AddonFrame::~AddonFrame() {
    OnDestroy();
    RemoveAllChildren();
    if (m_pParent) {
        m_pParent->RemoveChild(this);
        m_pParent = nullptr;
    }
}

// 1. Ciclo de Vida Virtual Canônico
bool AddonFrame::OnCreate() {
    return true;
}

void AddonFrame::OnDestroy() {
}

void AddonFrame::OnShow(bool bShow) {
    m_bVisible = bShow;
    for (auto* child : m_children) {
        if (child) {
            child->OnShow(bShow);
        }
    }
}

void AddonFrame::OnUpdate(float deltaTime) {
    if (!m_bVisible) return;

    for (auto* child : m_children) {
        if (child && child->IsVisible()) {
            child->OnUpdate(deltaTime);
        }
    }
}

void AddonFrame::OnRender() {
    if (!m_bVisible) return;

    for (auto* child : m_children) {
        if (child && child->IsVisible()) {
            child->OnRender();
        }
    }
}

// 2. Métodos de compatibilidade
void AddonFrame::Show(bool bShow) {
    OnShow(bShow);
}

void AddonFrame::Update() {
    OnUpdate(0.016f); // ~60fps delta
}

// 3. Geometria, Posição e Dimensões 2D
void AddonFrame::SetPos(int x, int y) {
    m_x = x;
    m_y = y;
}

void AddonFrame::SetSize(int width, int height) {
    m_width = (width >= 0) ? width : 0;
    m_height = (height >= 0) ? height : 0;
}

void AddonFrame::SetRect(int x, int y, int width, int height) {
    SetPos(x, y);
    SetSize(width, height);
}

bool AddonFrame::HitTest(int screenX, int screenY) const {
    if (!m_bVisible) return false;

    int absX = m_x;
    int absY = m_y;
    AddonFrame* pCur = m_pParent;
    while (pCur) {
        absX += pCur->GetX();
        absY += pCur->GetY();
        pCur = pCur->GetParent();
    }

    return (screenX >= absX && screenX <= (absX + m_width) &&
            screenY >= absY && screenY <= (absY + m_height));
}

// 4. Estados e Propriedades
void AddonFrame::SetAlpha(float alpha) {
    if (alpha < 0.0f) alpha = 0.0f;
    if (alpha > 1.0f) alpha = 1.0f;
    m_alpha = alpha;
}

// 5. Hierarquia Pai-Filho
void AddonFrame::SetParent(AddonFrame* pParent) {
    m_pParent = pParent;
}

void AddonFrame::AddChild(AddonFrame* pChild) {
    if (!pChild || pChild == this) return;

    auto it = std::find(m_children.begin(), m_children.end(), pChild);
    if (it == m_children.end()) {
        m_children.push_back(pChild);
        pChild->SetParent(this);
    }
}

void AddonFrame::RemoveChild(AddonFrame* pChild) {
    if (!pChild) return;

    auto it = std::find(m_children.begin(), m_children.end(), pChild);
    if (it != m_children.end()) {
        m_children.erase(it);
        pChild->SetParent(nullptr);
    }
}

AddonFrame* AddonFrame::FindChild(const std::string& name) const {
    for (auto* child : m_children) {
        if (child) {
            if (child->GetFrameName() == name) return child;
            AddonFrame* pSub = child->FindChild(name);
            if (pSub) return pSub;
        }
    }
    return nullptr;
}

void AddonFrame::RemoveAllChildren() {
    for (auto* child : m_children) {
        if (child) {
            child->SetParent(nullptr);
        }
    }
    m_children.clear();
}

// 6. Despacho de Eventos Virtuais de Mouse
bool AddonFrame::OnMouseMove(int x, int y, uint32_t flags) {
    if (!m_bVisible || !m_bEnabled) return false;

    if (m_bDragging) {
        OnDragMove(x - m_dragOffsetX, y - m_dragOffsetY);
        return true;
    }

    // Processar filhos do topo para o fundo (Z-order reverso)
    for (auto it = m_children.rbegin(); it != m_children.rend(); ++it) {
        AddonFrame* child = *it;
        if (child && child->IsVisible() && child->HitTest(x, y)) {
            if (child->OnMouseMove(x, y, flags)) return true;
        }
    }

    return false;
}

bool AddonFrame::OnLButtonDown(int x, int y, uint32_t flags) {
    if (!m_bVisible || !m_bEnabled) return false;

    for (auto it = m_children.rbegin(); it != m_children.rend(); ++it) {
        AddonFrame* child = *it;
        if (child && child->IsVisible() && child->HitTest(x, y)) {
            if (child->OnLButtonDown(x, y, flags)) {
                return true;
            }
        }
    }

    if (HitTest(x, y)) {
        OnSetFocus();
        if (m_bDraggable) {
            OnDragBegin(x, y);
            return true;
        }
        return true;
    }

    return false;
}

bool AddonFrame::OnLButtonUp(int x, int y, uint32_t flags) {
    if (m_bDragging) {
        OnDragEnd(x, y);
        return true;
    }

    for (auto it = m_children.rbegin(); it != m_children.rend(); ++it) {
        AddonFrame* child = *it;
        if (child && child->IsVisible() && child->HitTest(x, y)) {
            if (child->OnLButtonUp(x, y, flags)) return true;
        }
    }

    return false;
}

bool AddonFrame::OnRButtonDown(int x, int y, uint32_t flags) {
    if (!m_bVisible || !m_bEnabled) return false;

    for (auto it = m_children.rbegin(); it != m_children.rend(); ++it) {
        AddonFrame* child = *it;
        if (child && child->IsVisible() && child->HitTest(x, y)) {
            if (child->OnRButtonDown(x, y, flags)) return true;
        }
    }

    return HitTest(x, y);
}

bool AddonFrame::OnRButtonUp(int x, int y, uint32_t flags) {
    for (auto it = m_children.rbegin(); it != m_children.rend(); ++it) {
        AddonFrame* child = *it;
        if (child && child->IsVisible() && child->HitTest(x, y)) {
            if (child->OnRButtonUp(x, y, flags)) return true;
        }
    }
    return false;
}

bool AddonFrame::OnMouseWheel(short delta, int x, int y) {
    if (!m_bVisible || !m_bEnabled) return false;

    for (auto it = m_children.rbegin(); it != m_children.rend(); ++it) {
        AddonFrame* child = *it;
        if (child && child->IsVisible() && child->HitTest(x, y)) {
            if (child->OnMouseWheel(delta, x, y)) return true;
        }
    }
    return false;
}

// 7. Despacho de Eventos Virtuais de Teclado e Foco
bool AddonFrame::OnKeyDown(uint32_t vkCode, uint32_t flags) {
    (void)flags;
    if (!m_bVisible || !m_bEnabled) return false;

    // Se pressionar ESC em janela não-modal fechável, fecha a janela
    if (vkCode == VK_ESCAPE && !m_bModal) {
        Show(false);
        return true;
    }
    return false;
}

bool AddonFrame::OnKeyUp(uint32_t vkCode, uint32_t flags) {
    (void)vkCode;
    (void)flags;
    return false;
}

void AddonFrame::OnSetFocus() {
    m_bFocused = true;
}

void AddonFrame::OnKillFocus() {
    m_bFocused = false;
}

// 8. Despacho de Eventos de Drag & Drop
bool AddonFrame::OnDragBegin(int startX, int startY) {
    m_bDragging = true;
    m_dragOffsetX = startX - m_x;
    m_dragOffsetY = startY - m_y;
    return true;
}

void AddonFrame::OnDragMove(int curX, int curY) {
    if (m_bDragging) {
        SetPos(curX, curY);
    }
}

void AddonFrame::OnDragEnd(int endX, int endY) {
    (void)endX;
    (void)endY;
    m_bDragging = false;
}

bool AddonFrame::OnDrop(AddonFrame* pSource, void* pPayload) {
    (void)pSource;
    (void)pPayload;
    return false;
}

// 9. Comandos e Notificações de Controles Filhos
bool AddonFrame::OnCommand(uint32_t cmdId, void* pParam) {
    (void)cmdId;
    (void)pParam;
    return false;
}

void AddonFrame::OnChildNotify(AddonFrame* pChild, uint32_t eventId) {
    (void)pChild;
    (void)eventId;
}
