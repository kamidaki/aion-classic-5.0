#pragma once
#include "AddonFrame.h"
#include <functional>

// Botão canônico de UI extraído do RTTI (.?AVAddonButton@@)
class AddonButton : public AddonFrame {
public:
    AddonButton(const std::string& name);
    virtual ~AddonButton();

    void SetText(const std::string& text) { m_text = text; }
    const std::string& GetText() const { return m_text; }

    void SetEnabled(bool enabled) { m_bEnabled = enabled; }
    bool IsEnabled() const { return m_bEnabled; }

    virtual void OnClick();
    void SetClickHandler(std::function<void()> handler) { m_clickHandler = handler; }

protected:
    std::string m_text;
    bool m_bEnabled;
    std::function<void()> m_clickHandler;
};

// Botão de seleção (Check box) (.?AVAddonCheckButton@@)
class AddonCheckButton : public AddonButton {
public:
    AddonCheckButton(const std::string& name);
    virtual ~AddonCheckButton();

    bool IsChecked() const { return m_bChecked; }
    void SetChecked(bool checked);

    virtual void OnClick() override;

private:
    bool m_bChecked;
};

// Botão radial (Radio button) (.?AVAddonRadioButton@@)
class AddonRadioButton : public AddonButton {
public:
    AddonRadioButton(const std::string& name, int groupId = 0);
    virtual ~AddonRadioButton();

    int GetGroupId() const { return m_groupId; }
    bool IsSelected() const { return m_bSelected; }
    void SetSelected(bool selected);

    virtual void OnClick() override;

private:
    int m_groupId;
    bool m_bSelected;
};
