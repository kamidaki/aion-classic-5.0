#include "AddonWidgets.h"
#include "../core/GameLog.h"

// AddonEditBox
AddonEditBox::AddonEditBox(const std::string& name) : AddonFrame(name), m_maxChars(256) {}
AddonEditBox::~AddonEditBox() {}

// AddonStatic
AddonStatic::AddonStatic(const std::string& name) : AddonFrame(name) {}
AddonStatic::~AddonStatic() {}

// AddonStaticImage
AddonStaticImage::AddonStaticImage(const std::string& name) : AddonFrame(name) {}
AddonStaticImage::~AddonStaticImage() {}

// AddonListBox
AddonListBox::AddonListBox(const std::string& name) : AddonFrame(name), m_selectedIndex(-1) {}
AddonListBox::~AddonListBox() { m_items.clear(); }
void AddonListBox::AddItem(const std::string& item) { m_items.push_back(item); }
void AddonListBox::Clear() { m_items.clear(); m_selectedIndex = -1; }

// AddonListViewEx
AddonListViewEx::AddonListViewEx(const std::string& name) : AddonFrame(name) {}
AddonListViewEx::~AddonListViewEx() { Clear(); }
void AddonListViewEx::AddColumn(const std::string& header, int width) { m_columns.push_back({ header, width }); }
void AddonListViewEx::AddRow(const std::vector<std::string>& row) { m_rows.push_back(row); }
void AddonListViewEx::Clear() { m_columns.clear(); m_rows.clear(); }

// AddonScrollable
AddonScrollable::AddonScrollable(const std::string& name) : AddonFrame(name), m_scrollPos(0) {}
AddonScrollable::~AddonScrollable() {}

// AddonTopLevelFrame
AddonTopLevelFrame::AddonTopLevelFrame(const std::string& name) : AddonFrame(name), m_bActive(false) {}
AddonTopLevelFrame::~AddonTopLevelFrame() {}
void AddonTopLevelFrame::BringToFront() {
    m_bActive = true;
    GameLog_Info("AddonTopLevelFrame [%s] trazido para primeiro plano.", GetFrameName().c_str());
}
