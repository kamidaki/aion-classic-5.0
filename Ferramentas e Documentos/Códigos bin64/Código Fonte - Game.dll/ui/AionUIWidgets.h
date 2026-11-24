#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include "AddonFrame.h"

// Interface canônica de gerenciador de efeitos visuais de widgets (.?AUIUIWidgetFxManager@@)
struct IUIWidgetFxManager {
    virtual ~IUIWidgetFxManager() {}
    virtual void PlayWidgetFx(int fxId) { (void)fxId; }
};

// Container base de widgets (.?AVWidgetContainer@@)
class WidgetContainer {
public:
    WidgetContainer();
    virtual ~WidgetContainer();
    virtual void AddWidget(void* pWidget);
    virtual size_t GetWidgetCount() const;

protected:
    std::vector<void*> m_widgets;
};

// Container de widgets acumulados (.?AVAccumulateWidgetContainer@@)
class AccumulateWidgetContainer : public WidgetContainer {
public:
    AccumulateWidgetContainer();
    virtual ~AccumulateWidgetContainer();
};

// Container de widgets de selos / estênceis (.?AVStampWidgetContainer@@)
class StampWidgetContainer : public WidgetContainer {
public:
    StampWidgetContainer();
    virtual ~StampWidgetContainer();
};

// Balão de diálogo e fala de NPCs / jogadores (.?AVBubble@@)
class Bubble {
public:
    Bubble();
    virtual ~Bubble();

    void SetText(const std::string& text);
    const std::string& GetText() const;

private:
    std::string m_text;
};

// Diálogo base estendido (.?AVUIDialogEx@@)
class UIDialogEx : public AddonFrame {
public:
    UIDialogEx(const std::string& name = "UIDialogEx");
    virtual ~UIDialogEx();

    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// Diálogo de Arena PvP (.?AVDlgIDArenaPvP@@)
class DlgIDArenaPvP : public UIDialogEx {
public:
    DlgIDArenaPvP(const std::string& name = "DlgIDArenaPvP");
    virtual ~DlgIDArenaPvP();
};

// Diálogo canônico base de Tooltip (.?AVDlgTooltip@@)
class DlgTooltip : public AddonFrame {
public:
    DlgTooltip(const std::string& name = "DlgTooltip");
    virtual ~DlgTooltip();

    virtual void SetTooltipText(const std::string& text);
    const std::string& GetTooltipText() const;

private:
    std::string m_tooltipText;
};

// Manipulador numérico de objetivos de quests (.?AVQuestNumHandler@@)
class QuestNumHandler {
public:
    QuestNumHandler();
    virtual ~QuestNumHandler();

    void SetCount(int count);
    int GetCount() const;

private:
    int m_count;
};

// Painel canônico de abas de quests (.?AVQuestTabFrame@@)
class QuestTabFrame {
public:
    QuestTabFrame();
    virtual ~QuestTabFrame();

    virtual void SelectTab(int tabIndex);
    int GetSelectedTab() const;

protected:
    int m_selectedTab;
};

// Aba de missões finalizadas (.?AVQuestTabFrame_Finished@@)
class QuestTabFrame_Finished : public QuestTabFrame {
public:
    QuestTabFrame_Finished();
    virtual ~QuestTabFrame_Finished();
};

// Aba de missões em andamento (.?AVQuestTabFrame_Working@@)
class QuestTabFrame_Working : public QuestTabFrame {
public:
    QuestTabFrame_Working();
    virtual ~QuestTabFrame_Working();
};
