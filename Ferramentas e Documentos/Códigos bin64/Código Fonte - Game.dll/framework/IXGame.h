#pragma once
#include "IGame.h"

// Interface canônica de extensão de jogo CryEngine / NCSoft (.?AUIXGame@@)
struct IXGame {
    virtual ~IXGame() {}
    virtual bool Init() = 0;
    virtual void Reset() = 0;
    virtual bool Update() = 0;
};
