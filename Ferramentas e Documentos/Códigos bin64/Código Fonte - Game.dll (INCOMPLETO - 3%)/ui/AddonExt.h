#pragma once
#include "AddonFrame.h"
#include <string>
#include <vector>

// RTTI .?AVAddonComboBox@@
class AddonComboBox : public AddonFrame {
public:
    AddonComboBox(const std::string& name = "AddonComboBox");
    virtual ~AddonComboBox();
    virtual void Update() override;
};

// RTTI .?AVAddonMessageFrame@@
class AddonMessageFrame : public AddonFrame {
public:
    AddonMessageFrame(const std::string& name = "AddonMessageFrame");
    virtual ~AddonMessageFrame();
    virtual void Update() override;
};

// RTTI .?AVAddonSimpleHTML@@
class AddonSimpleHTML : public AddonFrame {
public:
    AddonSimpleHTML(const std::string& name = "AddonSimpleHTML");
    virtual ~AddonSimpleHTML();
    virtual void Update() override;
};

// RTTI .?AVAddonSpin@@
class AddonSpin : public AddonFrame {
public:
    AddonSpin(const std::string& name = "AddonSpin");
    virtual ~AddonSpin();
    virtual void Update() override;
};

// RTTI .?AVAddonTab@@
class AddonTab : public AddonFrame {
public:
    AddonTab(const std::string& name = "AddonTab");
    virtual ~AddonTab();
    virtual void Update() override;
};

// RTTI .?AVAddonTabButton@@
class AddonTabButton : public AddonFrame {
public:
    AddonTabButton(const std::string& name = "AddonTabButton");
    virtual ~AddonTabButton();
    virtual void Update() override;
};

// RTTI .?AVAddonTabPage@@
class AddonTabPage : public AddonFrame {
public:
    AddonTabPage(const std::string& name = "AddonTabPage");
    virtual ~AddonTabPage();
    virtual void Update() override;
};

// RTTI .?AVAddonTabSheet@@
class AddonTabSheet : public AddonFrame {
public:
    AddonTabSheet(const std::string& name = "AddonTabSheet");
    virtual ~AddonTabSheet();
    virtual void Update() override;
};

namespace ATL {
    // RTTI .?AVCAxFrameWindow@ATL@@
    class CAxFrameWindow : public AddonFrame {
    public:
        CAxFrameWindow(const std::string& name = "CAxFrameWindow");
        virtual ~CAxFrameWindow();
        virtual void Update() override;
    };
}

namespace ATL {
    // RTTI .?AVCAxHostWindow@ATL@@
    class CAxHostWindow : public AddonFrame {
    public:
        CAxHostWindow(const std::string& name = "CAxHostWindow");
        virtual ~CAxHostWindow();
        virtual void Update() override;
    };
}

namespace ATL {
    // RTTI .?AVCAxUIWindow@ATL@@
    class CAxUIWindow : public AddonFrame {
    public:
        CAxUIWindow(const std::string& name = "CAxUIWindow");
        virtual ~CAxUIWindow();
        virtual void Update() override;
    };
}

// RTTI .?AVCEFView@@
class CEFView : public AddonFrame {
public:
    CEFView(const std::string& name = "CEFView");
    virtual ~CEFView();
    virtual void Update() override;
};

namespace ATL {
    // RTTI .?AVCWindow@ATL@@
    class CWindow : public AddonFrame {
    public:
        CWindow(const std::string& name = "CWindow");
        virtual ~CWindow();
        virtual void Update() override;
    };
}

// RTTI .?AVCefContextMenuHandler@@
class CefContextMenuHandler : public AddonFrame {
public:
    CefContextMenuHandler(const std::string& name = "CefContextMenuHandler");
    virtual ~CefContextMenuHandler();
    virtual void Update() override;
};

// RTTI .?AVCefWindowInfo@@
class CefWindowInfo : public AddonFrame {
public:
    CefWindowInfo(const std::string& name = "CefWindowInfo");
    virtual ~CefWindowInfo();
    virtual void Update() override;
};

namespace MixerLib {
    // RTTI .?AVControl@MixerLib@@
    class Control : public AddonFrame {
    public:
        Control(const std::string& name = "Control");
        virtual ~Control();
        virtual void Update() override;
    };
}

// RTTI .?AVOptionClearCommonWidget@@
class OptionClearCommonWidget : public AddonFrame {
public:
    OptionClearCommonWidget(const std::string& name = "OptionClearCommonWidget");
    virtual ~OptionClearCommonWidget();
    virtual void Update() override;
};

// RTTI .?AVProcWidget@@
class ProcWidget : public AddonFrame {
public:
    ProcWidget(const std::string& name = "ProcWidget");
    virtual ~ProcWidget();
    virtual void Update() override;
};

// RTTI .?AVStatEnchantWidget@@
class StatEnchantWidget : public AddonFrame {
public:
    StatEnchantWidget(const std::string& name = "StatEnchantWidget");
    virtual ~StatEnchantWidget();
    virtual void Update() override;
};

// RTTI .?AVUI3DView@@
class UI3DView : public AddonFrame {
public:
    UI3DView(const std::string& name = "UI3DView");
    virtual ~UI3DView();
    virtual void Update() override;
};

// RTTI .?AVUIButton@@
class UIButton : public AddonFrame {
public:
    UIButton(const std::string& name = "UIButton");
    virtual ~UIButton();
    virtual void Update() override;
};

// RTTI .?AVUIEditBox@@
class UIEditBox : public AddonFrame {
public:
    UIEditBox(const std::string& name = "UIEditBox");
    virtual ~UIEditBox();
    virtual void Update() override;
};

// RTTI .?AVUIEditBoxEx@@
class UIEditBoxEx : public AddonFrame {
public:
    UIEditBoxEx(const std::string& name = "UIEditBoxEx");
    virtual ~UIEditBoxEx();
    virtual void Update() override;
};

// RTTI .?AVUIEditBoxExList@@
class UIEditBoxExList : public AddonFrame {
public:
    UIEditBoxExList(const std::string& name = "UIEditBoxExList");
    virtual ~UIEditBoxExList();
    virtual void Update() override;
};

// RTTI .?AVUIFlyGauge@@
class UIFlyGauge : public AddonFrame {
public:
    UIFlyGauge(const std::string& name = "UIFlyGauge");
    virtual ~UIFlyGauge();
    virtual void Update() override;
};

// RTTI .?AVUIGauge@@
class UIGauge : public AddonFrame {
public:
    UIGauge(const std::string& name = "UIGauge");
    virtual ~UIGauge();
    virtual void Update() override;
};

// RTTI .?AVUIHTMLView@@
class UIHTMLView : public AddonFrame {
public:
    UIHTMLView(const std::string& name = "UIHTMLView");
    virtual ~UIHTMLView();
    virtual void Update() override;
};

// RTTI .?AVUIItemView@@
class UIItemView : public AddonFrame {
public:
    UIItemView(const std::string& name = "UIItemView");
    virtual ~UIItemView();
    virtual void Update() override;
};

// RTTI .?AVUIListView@@
class UIListView : public AddonFrame {
public:
    UIListView(const std::string& name = "UIListView");
    virtual ~UIListView();
    virtual void Update() override;
};

// RTTI .?AVUIListViewEx@@
class UIListViewEx : public AddonFrame {
public:
    UIListViewEx(const std::string& name = "UIListViewEx");
    virtual ~UIListViewEx();
    virtual void Update() override;
};

// RTTI .?AVUIPageControl@@
class UIPageControl : public AddonFrame {
public:
    UIPageControl(const std::string& name = "UIPageControl");
    virtual ~UIPageControl();
    virtual void Update() override;
};

// RTTI .?AVUIPopupMenu@@
class UIPopupMenu : public AddonFrame {
public:
    UIPopupMenu(const std::string& name = "UIPopupMenu");
    virtual ~UIPopupMenu();
    virtual void Update() override;
};

// RTTI .?AVUIScreenVideoPanel@@
class UIScreenVideoPanel : public AddonFrame {
public:
    UIScreenVideoPanel(const std::string& name = "UIScreenVideoPanel");
    virtual ~UIScreenVideoPanel();
    virtual void Update() override;
};

// RTTI .?AVUIScrollBar@@
class UIScrollBar : public AddonFrame {
public:
    UIScrollBar(const std::string& name = "UIScrollBar");
    virtual ~UIScrollBar();
    virtual void Update() override;
};

// RTTI .?AVUITabButton@@
class UITabButton : public AddonFrame {
public:
    UITabButton(const std::string& name = "UITabButton");
    virtual ~UITabButton();
    virtual void Update() override;
};

// RTTI .?AVUITooltip@@
class UITooltip : public AddonFrame {
public:
    UITooltip(const std::string& name = "UITooltip");
    virtual ~UITooltip();
    virtual void Update() override;
};

// RTTI .?AVUITreeView@@
class UITreeView : public AddonFrame {
public:
    UITreeView(const std::string& name = "UITreeView");
    virtual ~UITreeView();
    virtual void Update() override;
};

// RTTI .?AVUIWidget@@
class UIWidget : public AddonFrame {
public:
    UIWidget(const std::string& name = "UIWidget");
    virtual ~UIWidget();
    virtual void Update() override;
};

// RTTI .?AVUIWidgetFxManager@@
class UIWidgetFxManager : public AddonFrame {
public:
    UIWidgetFxManager(const std::string& name = "UIWidgetFxManager");
    virtual ~UIWidgetFxManager();
    virtual void Update() override;
};

void RegisterAllAddonExt();