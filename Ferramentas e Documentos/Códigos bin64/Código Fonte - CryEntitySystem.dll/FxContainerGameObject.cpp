#include "stdafx.h"
#include "FxContainerGameObject.h"

CFxContainerGameObject::CFxContainerGameObject() {}

CFxContainerGameObject::~CFxContainerGameObject() {}

void CFxContainerGameObject::Update(float fDeltaTime) {
    (void)fDeltaTime;
}

void CFxContainerGameObject::Reset() {}

void InitFxContainerAion() {
    static CFxContainerGameObject s_fxContainer;
    s_fxContainer.Update(0.0f);
}
