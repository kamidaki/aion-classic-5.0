#pragma once
#include <windows.h>
#include <string>

// Classe base canônica de janelas e componentes de interface do Aion (.?AVAddonFrame@@)
class AddonFrame {
public:
    AddonFrame(const std::string& frameName);
    virtual ~AddonFrame();

    virtual void Show(bool bShow);
    virtual bool IsVisible() const { return m_bVisible; }
    virtual void Update();

    const std::string& GetFrameName() const { return m_frameName; }

private:
    std::string m_frameName;
    bool m_bVisible;
};
