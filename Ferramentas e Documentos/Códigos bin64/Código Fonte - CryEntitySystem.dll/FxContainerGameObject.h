#ifndef FX_CONTAINER_GAME_OBJECT_H
#define FX_CONTAINER_GAME_OBJECT_H

#pragma once

class CFxContainerGameObject {
public:
    CFxContainerGameObject();
    virtual ~CFxContainerGameObject();

    virtual void Update(float fDeltaTime);
    virtual void Reset();
};

#endif // FX_CONTAINER_GAME_OBJECT_H
