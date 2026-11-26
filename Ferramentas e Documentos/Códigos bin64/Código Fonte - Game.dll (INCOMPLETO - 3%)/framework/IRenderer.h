#pragma once
#include <string>
#include <cstdint>

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

// Interface pura canônica do Renderizador CryEngine (CryRender / XRenderD3D9)
CRY_INTERFACE IRenderer {
    virtual ~IRenderer() = default;
    virtual void BeginFrame() = 0;
    virtual void EndFrame() = 0;
    virtual uint32_t GetWidth() const = 0;
    virtual uint32_t GetHeight() const = 0;
};
