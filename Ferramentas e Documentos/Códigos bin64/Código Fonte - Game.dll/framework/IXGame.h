#pragma once
#include "IGame.h"

// Interface canônica de extensão de jogo CryEngine / NCSoft (.?AUIXGame@@)
// Herança canônica validada via RTTI: IXGame -> IGame (mdisp=0)
struct IXGame : public IGame {
    virtual ~IXGame() override {}
};
