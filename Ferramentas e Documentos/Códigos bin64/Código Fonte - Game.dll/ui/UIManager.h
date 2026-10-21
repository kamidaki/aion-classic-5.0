#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include "AddonFrame.h"
#include "AddonContainer.h"

// Gerenciador central de Interface de Usuário (HUD, Janelas, Menus) do Aion Classic
class UIManager {
public:
    static UIManager& GetInstance();

    UIManager();
    ~UIManager();

    bool Initialize();
    void Shutdown();
    void Update();

    // Gestão de Janelas da UI
    bool RegisterFrame(std::shared_ptr<AddonFrame> frame);
    bool ToggleWindow(const std::string& frameName);
    bool OpenWindow(const std::string& frameName);
    bool CloseWindow(const std::string& frameName);
    bool IsWindowOpen(const std::string& frameName) const;

    // Mensagens e Notificações no HUD
    void ShowSystemMessage(const std::string& message);
    void ShowFloatingDamage(uint32_t targetId, int32_t damage, bool isCrit);

private:
    std::unordered_map<std::string, std::shared_ptr<AddonFrame>> m_frames;
};
