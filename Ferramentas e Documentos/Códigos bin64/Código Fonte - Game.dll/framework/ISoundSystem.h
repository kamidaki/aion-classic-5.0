#pragma once
#include <string>
#include <cstdint>

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

// Interface pura canônica do Sistema de Áudio CryEngine (CrySoundSystem)
CRY_INTERFACE ISoundSystem {
    virtual ~ISoundSystem() = default;
    virtual void Update(float deltaSec) = 0;
};
