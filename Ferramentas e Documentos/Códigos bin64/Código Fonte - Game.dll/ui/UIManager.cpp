#include "UIManager.h"
#include "../core/GameLog.h"

UIManager& UIManager::GetInstance() {
    static UIManager s_instance;
    return s_instance;
}

UIManager::UIManager() {}
UIManager::~UIManager() { Shutdown(); }

bool UIManager::Initialize() {
    m_frames.clear();

    // Criação e registro das janelas primordiais do HUD
    RegisterFrame(std::make_shared<AddonContainer>("HUD_MainBar"));
    RegisterFrame(std::make_shared<AddonContainer>("HUD_QuickBar_1"));
    RegisterFrame(std::make_shared<AddonContainer>("HUD_QuickBar_2"));
    RegisterFrame(std::make_shared<AddonContainer>("HUD_ChatFrame"));
    RegisterFrame(std::make_shared<AddonContainer>("HUD_TargetFrame"));
    RegisterFrame(std::make_shared<AddonContainer>("HUD_Minimap"));
    RegisterFrame(std::make_shared<AddonContainer>("Dlg_Inventory"));
    RegisterFrame(std::make_shared<AddonContainer>("Dlg_SkillBook"));
    RegisterFrame(std::make_shared<AddonContainer>("Dlg_QuestList"));

    // Exibe HUD principal por padrão
    OpenWindow("HUD_MainBar");
    OpenWindow("HUD_QuickBar_1");
    OpenWindow("HUD_ChatFrame");
    OpenWindow("HUD_Minimap");

    GameLog_Info("UIManager inicializado com sucesso (%zu janelas registradas).", m_frames.size());
    return true;
}

void UIManager::Shutdown() {
    m_frames.clear();
}

void UIManager::Update() {
    for (auto& pair : m_frames) {
        if (pair.second && pair.second->IsVisible()) {
            pair.second->Update();
        }
    }
}

bool UIManager::RegisterFrame(std::shared_ptr<AddonFrame> frame) {
    if (!frame) return false;
    m_frames[frame->GetFrameName()] = frame;
    return true;
}

bool UIManager::ToggleWindow(const std::string& frameName) {
    auto it = m_frames.find(frameName);
    if (it != m_frames.end() && it->second) {
        bool newState = !it->second->IsVisible();
        it->second->Show(newState);
        GameLog_Info("UIManager: Alternada janela [%s] -> %s", frameName.c_str(), newState ? "ABERTA" : "FECHADA");
        return true;
    }
    return false;
}

bool UIManager::OpenWindow(const std::string& frameName) {
    auto it = m_frames.find(frameName);
    if (it != m_frames.end() && it->second) {
        it->second->Show(true);
        GameLog_Info("UIManager: Aberta janela [%s]", frameName.c_str());
        return true;
    }
    return false;
}

bool UIManager::CloseWindow(const std::string& frameName) {
    auto it = m_frames.find(frameName);
    if (it != m_frames.end() && it->second) {
        it->second->Show(false);
        GameLog_Info("UIManager: Fechada janela [%s]", frameName.c_str());
        return true;
    }
    return false;
}

bool UIManager::IsWindowOpen(const std::string& frameName) const {
    auto it = m_frames.find(frameName);
    return it != m_frames.end() && it->second ? it->second->IsVisible() : false;
}

void UIManager::ShowSystemMessage(const std::string& message) {
    GameLog_Info("[SYSTEM MSG] %s", message.c_str());
}

void UIManager::ShowFloatingDamage(uint32_t targetId, int32_t damage, bool isCrit) {
    GameLog_Info("[DAMAGE FLOAT] Alvo=%u Dano=%d (%s)", targetId, damage, isCrit ? "CRIT!" : "NORMAL");
}
