#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include "../ai/AIObject.h"
#include "Player.h"

enum class ActorType : uint8_t {
    Player = 0,
    Npc = 1,
    Monster = 2,
    ToyPet = 3,
    Gatherable = 4
};

// Gerenciador central de atores, entidades e visibilidade espacial do Aion Classic
class ActorManager {
public:
    static ActorManager& GetInstance();

    ActorManager();
    ~ActorManager();

    bool Initialize();
    void Shutdown();
    void Update(float deltaTime);

    // Gestão de Ciclo de Vida de Atores (Spawn / Despawn)
    bool SpawnPlayer(uint32_t objectId, const std::string& name, uint8_t playerClass, uint8_t race, uint8_t gender, const Vec3F& pos, float heading);
    bool SpawnNpc(uint32_t objectId, uint32_t npcTemplateId, const std::string& name, const Vec3F& pos, float heading);
    bool DespawnActor(uint32_t objectId);
    void ClearAllActors();

    // Consulta e Acesso
    AIObject* GetActor(uint32_t objectId);
    Player* GetPlayer(uint32_t objectId);
    size_t GetActorCount() const;

    // Gestão de Alvo do Jogador Local
    void SetTarget(uint32_t targetObjectId);
    uint32_t GetTarget() const { return m_targetObjectId; }
    void ClearTarget();

    // Consultas Espaciais (Raio de Visão de 100m)
    std::vector<AIObject*> GetActorsInRange(const Vec3F& center, float radius);

private:
    std::unordered_map<uint32_t, std::shared_ptr<AIObject>> m_actors;
    uint32_t m_targetObjectId;
    mutable std::mutex m_actorMutex;
};
