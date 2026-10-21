#pragma once
#include "AddonFrame.h"

// Componente canônico de navegador embutido do Aion extraído do RTTI (.?AVAddonBrowser@@)
// Utiliza a Awesomium.dll para renderização Web (Ingame Shop / Avisos / Notícias)
class AddonBrowser : public AddonFrame {
public:
    AddonBrowser();
    virtual ~AddonBrowser();

    virtual void Show(bool bShow) override;
    virtual void Update() override;

    bool NavigateTo(const std::string& url);

private:
    bool m_bAwesomiumReady;
    std::string m_currentUrl;
};
