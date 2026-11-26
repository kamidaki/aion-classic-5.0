#pragma once
#include <cstdint>

// Sink canônico do sistema de entidades CryEngine (.?AUIEntitySystemSink@@)
struct IEntitySystemSink {
    virtual ~IEntitySystemSink() {}
    virtual void OnSpawn(void* pEntity, void* pSpawnParams) = 0;
    virtual void OnRemove(void* pEntity) = 0;
};

// Container canônico de entidades CryEngine (.?AUIEntityContainer@@)
struct IEntityContainer {
    virtual ~IEntityContainer() {}
    virtual void Update() = 0;
};

// Objeto canônico de evento de entidade (.?AUIEntityEventObject@@)
struct IEntityEventObject {
    virtual ~IEntityEventObject() {}
    virtual void OnEntityEvent(uint32_t eventId, void* pParams) = 0;
};

// Sink canônico de instância de personagem / ator (.?AUICharInstanceSink@@)
struct ICharInstanceSink {
    virtual ~ICharInstanceSink() {}
    virtual void OnCharInstanceUpdate() = 0;
};
