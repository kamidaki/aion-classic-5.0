#pragma once
#include "AddonFrame.h"
#include <string>
#include <vector>

// Caixa de texto editável (.?AVAddonEditBox@@)
class AddonEditBox : public AddonFrame {
public:
    AddonEditBox(const std::string& name);
    virtual ~AddonEditBox();

    void SetText(const std::string& text) { m_text = text; }
    const std::string& GetText() const { return m_text; }

    void SetMaxChars(size_t maxChars) { m_maxChars = maxChars; }
    size_t GetMaxChars() const { return m_maxChars; }

private:
    std::string m_text;
    size_t m_maxChars;
};

// Rótulo estático de texto (.?AVAddonStatic@@)
class AddonStatic : public AddonFrame {
public:
    AddonStatic(const std::string& name);
    virtual ~AddonStatic();

    void SetText(const std::string& text) { m_text = text; }
    const std::string& GetText() const { return m_text; }

private:
    std::string m_text;
};

// Imagem / Ícone estático (.?AVAddonStaticImage@@)
class AddonStaticImage : public AddonFrame {
public:
    AddonStaticImage(const std::string& name);
    virtual ~AddonStaticImage();

    void SetImagePath(const std::string& path) { m_imagePath = path; }
    const std::string& GetImagePath() const { return m_imagePath; }

private:
    std::string m_imagePath;
};

// Lista de itens simples (.?AVAddonListBox@@)
class AddonListBox : public AddonFrame {
public:
    AddonListBox(const std::string& name);
    virtual ~AddonListBox();

    void AddItem(const std::string& item);
    void Clear();
    int GetSelectedIndex() const { return m_selectedIndex; }
    void SetSelectedIndex(int index) { m_selectedIndex = index; }

private:
    std::vector<std::string> m_items;
    int m_selectedIndex;
};

// Lista com múltiplas colunas (.?AVAddonListViewEx@@)
class AddonListViewEx : public AddonFrame {
public:
    AddonListViewEx(const std::string& name);
    virtual ~AddonListViewEx();

    void AddColumn(const std::string& header, int width);
    void AddRow(const std::vector<std::string>& row);
    void Clear();

private:
    std::vector<std::pair<std::string, int>> m_columns;
    std::vector<std::vector<std::string>> m_rows;
};

// Área com barra de rolagem (.?AVAddonScrollable@@)
class AddonScrollable : public AddonFrame {
public:
    AddonScrollable(const std::string& name);
    virtual ~AddonScrollable();

    void SetScrollPos(int pos) { m_scrollPos = pos; }
    int GetScrollPos() const { return m_scrollPos; }

private:
    int m_scrollPos;
};

// Janela de nível superior (Top Level Window) (.?AVAddonTopLevelFrame@@)
class AddonTopLevelFrame : public AddonFrame {
public:
    AddonTopLevelFrame(const std::string& name);
    virtual ~AddonTopLevelFrame();

    void BringToFront();
    void BringToFront(AddonFrame* pFrame);
    void SendToBack(AddonFrame* pFrame);
    bool IsActive() const { return m_bActive; }

    void RegisterWindow(AddonFrame* pFrame);
    void UnregisterWindow(AddonFrame* pFrame);
    AddonFrame* FindTopWindowAt(int screenX, int screenY) const;
    AddonFrame* GetFocusedWindow() const { return m_pFocusedFrame; }
    void SetFocusedWindow(AddonFrame* pFrame);

    bool DispatchKeyEvent(uint32_t vKey, bool bDown);
    bool DispatchMouseEvent(int screenX, int screenY, uint32_t eventFlags);

    void RenderAllVisibleWindows();

private:
    bool m_bActive;
    AddonFrame* m_pFocusedFrame;
    std::vector<AddonFrame*> m_windowStack;
};
