#pragma once
#include <string>
#include <cstdint>

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

// Interface pura canônica do Sistema de Animação CryEngine (CryAnimation)
CRY_INTERFACE IAnimationSystem {
    virtual ~IAnimationSystem() = default;
    virtual void Update(float deltaSec) = 0;
};
