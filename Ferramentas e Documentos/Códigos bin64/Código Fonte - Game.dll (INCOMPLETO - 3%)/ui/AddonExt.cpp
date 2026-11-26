#include "AddonExt.h"
#include "../core/GameLog.h"

AddonComboBox::AddonComboBox(const std::string& name) : AddonFrame(name) {}
AddonComboBox::~AddonComboBox() {}
void AddonComboBox::Update() { AddonFrame::Update(); }

AddonMessageFrame::AddonMessageFrame(const std::string& name) : AddonFrame(name) {}
AddonMessageFrame::~AddonMessageFrame() {}
void AddonMessageFrame::Update() { AddonFrame::Update(); }

AddonSimpleHTML::AddonSimpleHTML(const std::string& name) : AddonFrame(name) {}
AddonSimpleHTML::~AddonSimpleHTML() {}
void AddonSimpleHTML::Update() { AddonFrame::Update(); }

AddonSpin::AddonSpin(const std::string& name) : AddonFrame(name) {}
AddonSpin::~AddonSpin() {}
void AddonSpin::Update() { AddonFrame::Update(); }

AddonTab::AddonTab(const std::string& name) : AddonFrame(name) {}
AddonTab::~AddonTab() {}
void AddonTab::Update() { AddonFrame::Update(); }

AddonTabButton::AddonTabButton(const std::string& name) : AddonFrame(name) {}
AddonTabButton::~AddonTabButton() {}
void AddonTabButton::Update() { AddonFrame::Update(); }

AddonTabPage::AddonTabPage(const std::string& name) : AddonFrame(name) {}
AddonTabPage::~AddonTabPage() {}
void AddonTabPage::Update() { AddonFrame::Update(); }

AddonTabSheet::AddonTabSheet(const std::string& name) : AddonFrame(name) {}
AddonTabSheet::~AddonTabSheet() {}
void AddonTabSheet::Update() { AddonFrame::Update(); }

ATL::CAxFrameWindow::CAxFrameWindow(const std::string& name) : AddonFrame(name) {}
ATL::CAxFrameWindow::~CAxFrameWindow() {}
void ATL::CAxFrameWindow::Update() { AddonFrame::Update(); }

ATL::CAxHostWindow::CAxHostWindow(const std::string& name) : AddonFrame(name) {}
ATL::CAxHostWindow::~CAxHostWindow() {}
void ATL::CAxHostWindow::Update() { AddonFrame::Update(); }

ATL::CAxUIWindow::CAxUIWindow(const std::string& name) : AddonFrame(name) {}
ATL::CAxUIWindow::~CAxUIWindow() {}
void ATL::CAxUIWindow::Update() { AddonFrame::Update(); }

CEFView::CEFView(const std::string& name) : AddonFrame(name) {}
CEFView::~CEFView() {}
void CEFView::Update() { AddonFrame::Update(); }

ATL::CWindow::CWindow(const std::string& name) : AddonFrame(name) {}
ATL::CWindow::~CWindow() {}
void ATL::CWindow::Update() { AddonFrame::Update(); }

CefContextMenuHandler::CefContextMenuHandler(const std::string& name) : AddonFrame(name) {}
CefContextMenuHandler::~CefContextMenuHandler() {}
void CefContextMenuHandler::Update() { AddonFrame::Update(); }

CefWindowInfo::CefWindowInfo(const std::string& name) : AddonFrame(name) {}
CefWindowInfo::~CefWindowInfo() {}
void CefWindowInfo::Update() { AddonFrame::Update(); }

MixerLib::Control::Control(const std::string& name) : AddonFrame(name) {}
MixerLib::Control::~Control() {}
void MixerLib::Control::Update() { AddonFrame::Update(); }

OptionClearCommonWidget::OptionClearCommonWidget(const std::string& name) : AddonFrame(name) {}
OptionClearCommonWidget::~OptionClearCommonWidget() {}
void OptionClearCommonWidget::Update() { AddonFrame::Update(); }

ProcWidget::ProcWidget(const std::string& name) : AddonFrame(name) {}
ProcWidget::~ProcWidget() {}
void ProcWidget::Update() { AddonFrame::Update(); }

StatEnchantWidget::StatEnchantWidget(const std::string& name) : AddonFrame(name) {}
StatEnchantWidget::~StatEnchantWidget() {}
void StatEnchantWidget::Update() { AddonFrame::Update(); }

UI3DView::UI3DView(const std::string& name) : AddonFrame(name) {}
UI3DView::~UI3DView() {}
void UI3DView::Update() { AddonFrame::Update(); }

UIButton::UIButton(const std::string& name) : AddonFrame(name) {}
UIButton::~UIButton() {}
void UIButton::Update() { AddonFrame::Update(); }

UIEditBox::UIEditBox(const std::string& name) : AddonFrame(name) {}
UIEditBox::~UIEditBox() {}
void UIEditBox::Update() { AddonFrame::Update(); }

UIEditBoxEx::UIEditBoxEx(const std::string& name) : AddonFrame(name) {}
UIEditBoxEx::~UIEditBoxEx() {}
void UIEditBoxEx::Update() { AddonFrame::Update(); }

UIEditBoxExList::UIEditBoxExList(const std::string& name) : AddonFrame(name) {}
UIEditBoxExList::~UIEditBoxExList() {}
void UIEditBoxExList::Update() { AddonFrame::Update(); }

UIFlyGauge::UIFlyGauge(const std::string& name) : AddonFrame(name) {}
UIFlyGauge::~UIFlyGauge() {}
void UIFlyGauge::Update() { AddonFrame::Update(); }

UIGauge::UIGauge(const std::string& name) : AddonFrame(name) {}
UIGauge::~UIGauge() {}
void UIGauge::Update() { AddonFrame::Update(); }

UIHTMLView::UIHTMLView(const std::string& name) : AddonFrame(name) {}
UIHTMLView::~UIHTMLView() {}
void UIHTMLView::Update() { AddonFrame::Update(); }

UIItemView::UIItemView(const std::string& name) : AddonFrame(name) {}
UIItemView::~UIItemView() {}
void UIItemView::Update() { AddonFrame::Update(); }

UIListView::UIListView(const std::string& name) : AddonFrame(name) {}
UIListView::~UIListView() {}
void UIListView::Update() { AddonFrame::Update(); }

UIListViewEx::UIListViewEx(const std::string& name) : AddonFrame(name) {}
UIListViewEx::~UIListViewEx() {}
void UIListViewEx::Update() { AddonFrame::Update(); }

UIPageControl::UIPageControl(const std::string& name) : AddonFrame(name) {}
UIPageControl::~UIPageControl() {}
void UIPageControl::Update() { AddonFrame::Update(); }

UIPopupMenu::UIPopupMenu(const std::string& name) : AddonFrame(name) {}
UIPopupMenu::~UIPopupMenu() {}
void UIPopupMenu::Update() { AddonFrame::Update(); }

UIScreenVideoPanel::UIScreenVideoPanel(const std::string& name) : AddonFrame(name) {}
UIScreenVideoPanel::~UIScreenVideoPanel() {}
void UIScreenVideoPanel::Update() { AddonFrame::Update(); }

UIScrollBar::UIScrollBar(const std::string& name) : AddonFrame(name) {}
UIScrollBar::~UIScrollBar() {}
void UIScrollBar::Update() { AddonFrame::Update(); }

UITabButton::UITabButton(const std::string& name) : AddonFrame(name) {}
UITabButton::~UITabButton() {}
void UITabButton::Update() { AddonFrame::Update(); }

UITooltip::UITooltip(const std::string& name) : AddonFrame(name) {}
UITooltip::~UITooltip() {}
void UITooltip::Update() { AddonFrame::Update(); }

UITreeView::UITreeView(const std::string& name) : AddonFrame(name) {}
UITreeView::~UITreeView() {}
void UITreeView::Update() { AddonFrame::Update(); }

UIWidget::UIWidget(const std::string& name) : AddonFrame(name) {}
UIWidget::~UIWidget() {}
void UIWidget::Update() { AddonFrame::Update(); }

UIWidgetFxManager::UIWidgetFxManager(const std::string& name) : AddonFrame(name) {}
UIWidgetFxManager::~UIWidgetFxManager() {}
void UIWidgetFxManager::Update() { AddonFrame::Update(); }

void RegisterAllAddonExt() {
    GameLog_Info("Registrando 39 controles de UI e addons...");
    static AddonComboBox s_AddonComboBox;
    static AddonMessageFrame s_AddonMessageFrame;
    static AddonSimpleHTML s_AddonSimpleHTML;
    static AddonSpin s_AddonSpin;
    static AddonTab s_AddonTab;
    static AddonTabButton s_AddonTabButton;
    static AddonTabPage s_AddonTabPage;
    static AddonTabSheet s_AddonTabSheet;
    static ATL::CAxFrameWindow s_ATL_CAxFrameWindow;
    static ATL::CAxHostWindow s_ATL_CAxHostWindow;
    static ATL::CAxUIWindow s_ATL_CAxUIWindow;
    static CEFView s_CEFView;
    static ATL::CWindow s_ATL_CWindow;
    static CefContextMenuHandler s_CefContextMenuHandler;
    static CefWindowInfo s_CefWindowInfo;
    static MixerLib::Control s_MixerLib_Control;
    static OptionClearCommonWidget s_OptionClearCommonWidget;
    static ProcWidget s_ProcWidget;
    static StatEnchantWidget s_StatEnchantWidget;
    static UI3DView s_UI3DView;
    static UIButton s_UIButton;
    static UIEditBox s_UIEditBox;
    static UIEditBoxEx s_UIEditBoxEx;
    static UIEditBoxExList s_UIEditBoxExList;
    static UIFlyGauge s_UIFlyGauge;
    static UIGauge s_UIGauge;
    static UIHTMLView s_UIHTMLView;
    static UIItemView s_UIItemView;
    static UIListView s_UIListView;
    static UIListViewEx s_UIListViewEx;
    static UIPageControl s_UIPageControl;
    static UIPopupMenu s_UIPopupMenu;
    static UIScreenVideoPanel s_UIScreenVideoPanel;
    static UIScrollBar s_UIScrollBar;
    static UITabButton s_UITabButton;
    static UITooltip s_UITooltip;
    static UITreeView s_UITreeView;
    static UIWidget s_UIWidget;
    static UIWidgetFxManager s_UIWidgetFxManager;
}