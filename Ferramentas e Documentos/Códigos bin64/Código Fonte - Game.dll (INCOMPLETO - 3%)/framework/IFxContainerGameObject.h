#pragma once

// Container canônico de efeitos de GameObject (.?AUIFxContainerGameObject@@)
struct IFxContainerGameObject {
    virtual ~IFxContainerGameObject() {}
    virtual void UpdateFx() = 0;
};
