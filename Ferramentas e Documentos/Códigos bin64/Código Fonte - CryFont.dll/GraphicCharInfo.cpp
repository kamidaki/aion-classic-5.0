#include "stdafx.h"
#include "GraphicCharInfo.h"

// Ensure RTTI and symbols are generated
void InitGraphicCharInfoAion() {
    static GraphicCharInfo s_charInfo;
    static GraphicCharInfo_billboard s_billboard;
    s_charInfo.Render(nullptr, nullptr);
    s_billboard.Render(nullptr, nullptr);
}
