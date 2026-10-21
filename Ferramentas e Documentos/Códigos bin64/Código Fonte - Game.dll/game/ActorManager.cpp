#include "ActorManager.h"
#include "../core/GameLog.h"
#include <cmath>

ActorManager& ActorManager::GetInstance() {
    static ActorManager s_instance;
    return s_instance;
}

ActorManager::ActorManager() 
    : m_targetObjectId(0)
{
}

ActorManager::~ActorManager() {
    Shutdown();
}

bool ActorManager::Initialize() {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    m_actors.clear();
    m_targetObjectId = 0;
    GameLog_Info("ActorManager inicializado com sucesso.");
    return true;
}

void ActorManager::Shutdown() {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    m_actors.clear();
    m_targetObjectId = 0;
    GameLog_Info("ActorManager finalizado.");
}

void ActorManager::Update(float deltaTime) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    for (auto& pair : m_actors) {
        if (pair.second) {
            pair.second->Update();
        }
    }
}

bool ActorManager::SpawnPlayer(uint32_t objectId, const std::string& name, uint8_t playerClass, uint8_t race, uint8_t gender, const Vec3F& pos, float heading) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    auto player = std::make_shared<Player>(objectId, name, playerClass, race, gender);
    player->SetPosition(pos);
    m_actors[objectId] = player;
    GameLog_Info("ActorManager: Spawn Player Obj=%u Nome='%s' Classe=%u Pos=(%.1f, %.1f, %.1f)", 
        objectId, name.c_str(), playerClass, pos.x, pos.y, pos.z);
    return true;
}

bool ActorManager::SpawnNpc(uint32_t objectId, uint32_t npcTemplateId, const std::string& name, const Vec3F& pos, float heading) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    auto npc = std::make_shared<AIObject>(objectId, name);
    npc->SetPosition(pos);
    m_actors[objectId] = npc;
    GameLog_Info("ActorManager: Spawn NPC Obj=%u Template=%u Nome='%s' Pos=(%.1f, %.1f, %.1f)", 
        objectId, npcTemplateId, name.c_str(), pos.x, pos.y, pos.z);
    return true;
}

bool ActorManager::DespawnActor(uint32_t objectId) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    auto it = m_actors.find(objectId);
    if (it != m_actors.end()) {
        GameLog_Info("ActorManager: Despawn Actor Obj=%u Nome='%s'", objectId, it->second->GetName().c_str());
        if (m_targetObjectId == objectId) {
            m_targetObjectId = 0;
        }
        m_actors.erase(it);
        return true;
    }
    return false;
}

void ActorManager::ClearAllActors() {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    m_actors.clear();
    m_targetObjectId = 0;
    GameLog_Info("ActorManager: Todos os atores foram limpos da cena.");
}

AIObject* ActorManager::GetActor(uint32_t objectId) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    auto it = m_actors.find(objectId);
    return it != m_actors.end() ? it->second.get() : nullptr;
}

Player* ActorManager::GetPlayer(uint32_t objectId) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    auto it = m_actors.find(objectId);
    if (it != m_actors.end()) {
        return dynamic_cast<Player*>(it->second.get());
    }
    return nullptr;
}

size_t ActorManager::GetActorCount() const {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    return m_actors.size();
}

void ActorManager::SetTarget(uint32_t targetObjectId) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    m_targetObjectId = targetObjectId;
    GameLog_Info("ActorManager: Alvo selecionado -> Obj=%u", targetObjectId);
}

void ActorManager::ClearTarget() {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    m_targetObjectId = 0;
    GameLog_Info("ActorManager: Alvo cancelado.");
}

std::vector<AIObject*> ActorManager::GetActorsInRange(const Vec3F& center, float radius) {
    std::lock_guard<std::mutex> lock(m_actorMutex);
    std::vector<AIObject*> results;
    float radiusSq = radius * radius;

    for (auto& pair : m_actors) {
        if (!pair.second) continue;
        const Vec3F& pos = pair.second->GetPosition();
        float dx = pos.x - center.x;
        float dy = pos.y - center.y;
        float dz = pos.z - center.z;
        float distSq = dx * dx + dy * dy + dz * dz;
        if (distSq <= radiusSq) {
            results.push_back(pair.second.get());
        }
    }
    return results;
}
