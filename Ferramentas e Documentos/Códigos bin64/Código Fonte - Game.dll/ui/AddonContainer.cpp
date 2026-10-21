#include "AddonContainer.h"
#include "../core/GameLog.h"
#include <algorithm>

AddonContainer::AddonContainer(const std::string& name)
    : AddonFrame(name)
{
}

AddonContainer::~AddonContainer() {
    m_children.clear();
}

void AddonContainer::AddChild(std::shared_ptr<AddonFrame> child) {
    if (child) {
        m_children.push_back(child);
    }
}

void AddonContainer::RemoveChild(const std::string& childName) {
    m_children.erase(
        std::remove_if(m_children.begin(), m_children.end(),
            [&](const std::shared_ptr<AddonFrame>& child) {
                return child && child->GetFrameName() == childName;
            }),
        m_children.end());
}

AddonFrame* AddonContainer::FindChild(const std::string& childName) const {
    for (const auto& child : m_children) {
        if (child && child->GetFrameName() == childName) {
            return child.get();
        }
    }
    return nullptr;
}

void AddonContainer::Show(bool bShow) {
    AddonFrame::Show(bShow);
    for (auto& child : m_children) {
        if (child) {
            child->Show(bShow);
        }
    }
}

void AddonContainer::Update() {
    AddonFrame::Update();
    for (auto& child : m_children) {
        if (child && child->IsVisible()) {
            child->Update();
        }
    }
}
