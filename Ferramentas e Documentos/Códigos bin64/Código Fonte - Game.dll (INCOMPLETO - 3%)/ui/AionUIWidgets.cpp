#include "AionUIWidgets.h"
#include "../core/GameLog.h"

// WidgetContainer
WidgetContainer::WidgetContainer() {}
WidgetContainer::~WidgetContainer() {
    m_widgets.clear();
}
void WidgetContainer::AddWidget(void* pWidget) {
    if (pWidget) m_widgets.push_back(pWidget);
}
size_t WidgetContainer::GetWidgetCount() const {
    return m_widgets.size();
}

// AccumulateWidgetContainer
AccumulateWidgetContainer::AccumulateWidgetContainer() : WidgetContainer() {}
AccumulateWidgetContainer::~AccumulateWidgetContainer() {}

// StampWidgetContainer
StampWidgetContainer::StampWidgetContainer() : WidgetContainer() {}
StampWidgetContainer::~StampWidgetContainer() {}

// Bubble
Bubble::Bubble() {}
Bubble::~Bubble() {}
void Bubble::SetText(const std::string& text) { m_text = text; }
const std::string& Bubble::GetText() const { return m_text; }

// UIDialogEx
UIDialogEx::UIDialogEx(const std::string& name) : AddonFrame(name) {}
UIDialogEx::~UIDialogEx() {}
void UIDialogEx::Show(bool bShow) { AddonFrame::Show(bShow); }
void UIDialogEx::Update() { AddonFrame::Update(); }

// DlgIDArenaPvP
DlgIDArenaPvP::DlgIDArenaPvP(const std::string& name) : UIDialogEx(name) {}
DlgIDArenaPvP::~DlgIDArenaPvP() {}

// DlgTooltip
DlgTooltip::DlgTooltip(const std::string& name) : AddonFrame(name) {}
DlgTooltip::~DlgTooltip() {}
void DlgTooltip::SetTooltipText(const std::string& text) { m_tooltipText = text; }
const std::string& DlgTooltip::GetTooltipText() const { return m_tooltipText; }

// QuestNumHandler
QuestNumHandler::QuestNumHandler() : m_count(0) {}
QuestNumHandler::~QuestNumHandler() {}
void QuestNumHandler::SetCount(int count) { m_count = count; }
int QuestNumHandler::GetCount() const { return m_count; }

// QuestTabFrame
QuestTabFrame::QuestTabFrame() : m_selectedTab(0) {}
QuestTabFrame::~QuestTabFrame() {}
void QuestTabFrame::SelectTab(int tabIndex) { m_selectedTab = tabIndex; }
int QuestTabFrame::GetSelectedTab() const { return m_selectedTab; }

// QuestTabFrame_Finished
QuestTabFrame_Finished::QuestTabFrame_Finished() : QuestTabFrame() {}
QuestTabFrame_Finished::~QuestTabFrame_Finished() {}

// QuestTabFrame_Working
QuestTabFrame_Working::QuestTabFrame_Working() : QuestTabFrame() {}
QuestTabFrame_Working::~QuestTabFrame_Working() {}
