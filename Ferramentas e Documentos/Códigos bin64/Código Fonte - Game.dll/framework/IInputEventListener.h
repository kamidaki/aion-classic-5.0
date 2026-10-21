#pragma once

// Interface canônica de escuta de eventos de entrada CryEngine (.?AUIInputEventListener@@)
struct IInputEventListener {
    virtual ~IInputEventListener() {}
    virtual bool OnInputEvent(void* pEvent) = 0;
};
