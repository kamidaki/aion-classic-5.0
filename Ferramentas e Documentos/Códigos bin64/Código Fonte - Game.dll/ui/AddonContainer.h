#pragma once
#include "AddonFrame.h"
#include <vector>
#include <memory>

// Contêiner de controles e janelas canônico extraído do RTTI (.?AVAddonContainer@@)
class AddonContainer : public AddonFrame {
public:
    AddonContainer(const std::string& name);
    virtual ~AddonContainer();

    void AddChild(std::shared_ptr<AddonFrame> child);
    void RemoveChild(const std::string& childName);
    AddonFrame* FindChild(const std::string& childName) const;

    virtual void Show(bool bShow) override;
    virtual void Update() override;

    size_t GetChildCount() const { return m_children.size(); }

private:
    std::vector<std::shared_ptr<AddonFrame>> m_children;
};
