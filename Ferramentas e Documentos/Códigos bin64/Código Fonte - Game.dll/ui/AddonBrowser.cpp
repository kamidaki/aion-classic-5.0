#include "AddonFrame.h"
#include "AddonBrowser.h"
#include "../core/GameLog.h"

AddonBrowser::AddonBrowser()
    : AddonFrame("AddonBrowser")
    , m_bAwesomiumReady(false)
{
    HMODULE hAwesomium = GetModuleHandleA("Awesomium.dll");
    if (hAwesomium) {
        m_bAwesomiumReady = true;
        GameLog_Info("AddonBrowser: Awesomium.dll vinculada com sucesso.");
    }
}

AddonBrowser::~AddonBrowser() {
}

void AddonBrowser::Show(bool bShow) {
    AddonFrame::Show(bShow);
}

void AddonBrowser::Update() {
}

bool AddonBrowser::NavigateTo(const std::string& url) {
    m_currentUrl = url;
    GameLog_Info("AddonBrowser: Navegando para URL: '%s'", url.c_str());
    return true;
}
