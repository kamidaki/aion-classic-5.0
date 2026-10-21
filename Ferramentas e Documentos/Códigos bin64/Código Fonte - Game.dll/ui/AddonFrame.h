#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>

// Forward declarations
class AddonContainer;

// Flags de eventos de mouse e teclado do motor CryEngine / Aion
enum EUIEventFlags {
    UI_EVENT_NONE        = 0x0000,
    UI_EVENT_LBUTTON     = 0x0001,
    UI_EVENT_RBUTTON     = 0x0002,
    UI_EVENT_MBUTTON     = 0x0004,
    UI_EVENT_SHIFT       = 0x0008,
    UI_EVENT_CONTROL     = 0x0010,
    UI_EVENT_ALT         = 0x0020
};

// Classe base canônica de janelas e componentes de interface do Aion (.?AVAddonFrame@@)
class AddonFrame {
public:
    AddonFrame(const std::string& frameName);
    virtual ~AddonFrame();

    // 1. Ciclo de Vida Virtual Canônico
    virtual bool OnCreate();
    virtual void OnDestroy();
    virtual void OnShow(bool bShow);
    virtual void OnUpdate(float deltaTime);
    virtual void OnRender();

    // 2. Métodos de compatibilidade existentes
    virtual void Show(bool bShow);
    virtual bool IsVisible() const { return m_bVisible; }
    virtual void Update();

    // 3. Geometria, Posição e Dimensões 2D
    void SetPos(int x, int y);
    void GetPos(int& x, int& y) const { x = m_x; y = m_y; }
    int GetX() const { return m_x; }
    int GetY() const { return m_y; }

    void SetSize(int width, int height);
    void GetSize(int& width, int& height) const { width = m_width; height = m_height; }
    int GetWidth() const { return m_width; }
    int GetHeight() const { return m_height; }

    void SetRect(int x, int y, int width, int height);
    bool HitTest(int screenX, int screenY) const;

    // 4. Estados e Propriedades
    void SetEnabled(bool bEnabled) { m_bEnabled = bEnabled; }
    bool IsEnabled() const { return m_bEnabled; }

    void SetAlpha(float alpha);
    float GetAlpha() const { return m_alpha; }

    void SetDraggable(bool bDraggable) { m_bDraggable = bDraggable; }
    bool IsDraggable() const { return m_bDraggable; }

    void SetModal(bool bModal) { m_bModal = bModal; }
    bool IsModal() const { return m_bModal; }

    bool IsFocused() const { return m_bFocused; }

    const std::string& GetFrameName() const { return m_frameName; }
    void SetFrameName(const std::string& name) { m_frameName = name; }

    // 5. Hierarquia Pai-Filho
    void SetParent(AddonFrame* pParent);
    AddonFrame* GetParent() const { return m_pParent; }
    void AddChild(AddonFrame* pChild);
    void RemoveChild(AddonFrame* pChild);
    AddonFrame* FindChild(const std::string& name) const;
    const std::vector<AddonFrame*>& GetChildren() const { return m_children; }
    void RemoveAllChildren();

    // 6. Despacho de Eventos Virtuais de Mouse
    virtual bool OnMouseMove(int x, int y, uint32_t flags);
    virtual bool OnLButtonDown(int x, int y, uint32_t flags);
    virtual bool OnLButtonUp(int x, int y, uint32_t flags);
    virtual bool OnRButtonDown(int x, int y, uint32_t flags);
    virtual bool OnRButtonUp(int x, int y, uint32_t flags);
    virtual bool OnMouseWheel(short delta, int x, int y);

    // 7. Despacho de Eventos Virtuais de Teclado e Foco
    virtual bool OnKeyDown(uint32_t vkCode, uint32_t flags);
    virtual bool OnKeyUp(uint32_t vkCode, uint32_t flags);
    virtual void OnSetFocus();
    virtual void OnKillFocus();

    // 8. Despacho de Eventos de Drag & Drop
    virtual bool OnDragBegin(int startX, int startY);
    virtual void OnDragMove(int curX, int curY);
    virtual void OnDragEnd(int endX, int endY);
    virtual bool OnDrop(AddonFrame* pSource, void* pPayload);

    // 9. Comandos e Notificações de Controles Filhos
    virtual bool OnCommand(uint32_t cmdId, void* pParam);
    virtual void OnChildNotify(AddonFrame* pChild, uint32_t eventId);

protected:
    std::string m_frameName;
    int m_x;
    int m_y;
    int m_width;
    int m_height;
    float m_alpha;

    bool m_bVisible;
    bool m_bEnabled;
    bool m_bDraggable;
    bool m_bModal;
    bool m_bFocused;
    bool m_bDragging;

    int m_dragOffsetX;
    int m_dragOffsetY;

    AddonFrame* m_pParent;
    std::vector<AddonFrame*> m_children;
};
