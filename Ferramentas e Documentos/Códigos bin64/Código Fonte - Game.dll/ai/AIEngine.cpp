#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include "AIEngine.h"
#include "../core/GameLog.h"

// -------------------------------------------------------------
// 4.2 HateTable
// -------------------------------------------------------------
HateTable::HateTable() {}
HateTable::~HateTable() {}

void HateTable::AddDamageHate(uint32_t attackerId, int32_t damage) {
    if (damage <= 0) return;
    auto& entry = m_hateMap[attackerId];
    entry.targetId = attackerId;
    entry.hatePoints += damage; // 1 Dano = 1 Ponto de Hate
    entry.totalDamageDealt += damage;
}

void HateTable::AddHealHate(uint32_t healerId, int32_t healAmount) {
    if (healAmount <= 0) return;
    auto& entry = m_hateMap[healerId];
    entry.targetId = healerId;
    int32_t healHate = static_cast<int32_t>(healAmount * 0.5f); // 1 Cura = 0.5 Ponto de Hate
    if (healHate < 1) healHate = 1;
    entry.hatePoints += healHate;
    entry.totalHealDealt += healAmount;
}

void HateTable::AddTauntHate(uint32_t tankId, int32_t tauntBonus) {
    auto& entry = m_hateMap[tankId];
    entry.targetId = tankId;
    entry.hatePoints += tauntBonus; // +5000 Hate imediato
}

void HateTable::ReduceHate(uint32_t targetId, float percentageReduction) {
    auto it = m_hateMap.find(targetId);
    if (it != m_hateMap.end()) {
        if (percentageReduction >= 1.0f) {
            it->second.hatePoints = 0;
        } else {
            it->second.hatePoints = static_cast<int32_t>(it->second.hatePoints * (1.0f - percentageReduction));
        }
    }
}

void HateTable::ClearHate(uint32_t targetId) {
    m_hateMap.erase(targetId);
}

void HateTable::Reset() {
    m_hateMap.clear();
}

uint32_t HateTable::GetMostHatedTarget() const {
    uint32_t topTarget = 0;
    int32_t maxHate = 0;
    for (const auto& pair : m_hateMap) {
        if (pair.second.hatePoints > maxHate) {
            maxHate = pair.second.hatePoints;
            topTarget = pair.first;
        }
    }
    return topTarget;
}

uint32_t HateTable::GetTopHealerTarget() const {
    uint32_t topHealer = 0;
    int32_t maxHeal = 0;
    for (const auto& pair : m_hateMap) {
        if (pair.second.totalHealDealt > maxHeal) {
            maxHeal = pair.second.totalHealDealt;
            topHealer = pair.first;
        }
    }
    return topHealer;
}

int32_t HateTable::GetHate(uint32_t targetId) const {
    auto it = m_hateMap.find(targetId);
    if (it != m_hateMap.end()) {
        return it->second.hatePoints;
    }
    return 0;
}

// -------------------------------------------------------------
// AIEngine Singleton
// -------------------------------------------------------------
AIEngine& AIEngine::GetInstance() {
    static AIEngine s_instance;
    return s_instance;
}

AIEngine::AIEngine() {
    GameLog_Info("AIEngine: Motor de FSM, Hate/Threat, Bosses e ToyPets inicializado.");
}

AIEngine::~AIEngine() {}

void AIEngine::RegisterNpc(const NpcAiEntity& npc) {
    m_npcs[npc.objectId] = npc;
}

NpcAiEntity* AIEngine::GetNpc(uint32_t objectId) {
    auto it = m_npcs.find(objectId);
    if (it != m_npcs.end()) {
        return &it->second;
    }
    return nullptr;
}

void AIEngine::UnregisterNpc(uint32_t objectId) {
    m_npcs.erase(objectId);
}

// -------------------------------------------------------------
// 4.1 FSM Completa
// -------------------------------------------------------------
void AIEngine::UpdateFSM(uint32_t npcId, const std::vector<std::pair<uint32_t, AIVector3>>& nearbyPlayers, uint64_t currentTimeMs) {
    NpcAiEntity* npc = GetNpc(npcId);
    if (!npc) return;

    // Se for Boss, atualiza fases e timer de enrage
    if (npc->isBoss && (npc->state == NpcAiState::ATTACK || npc->state == NpcAiState::FOLLOW)) {
        ProcessBossPhases(*npc, currentTimeMs);
    }

    switch (npc->state) {
        case NpcAiState::REST: {
            // Regeneração de vida fora de combate
            if (npc->currentHp < npc->maxHp) {
                npc->currentHp = (std::min)(npc->maxHp, npc->currentHp + static_cast<int32_t>(npc->maxHp * 0.05f));
            }

            // Varredura de alvos hostis em raio de aggro (15m)
            for (const auto& p : nearbyPlayers) {
                if (npc->currentPosition.DistanceTo(p.second) <= npc->aggroRadius) {
                    npc->currentTargetId = p.first;
                    npc->targetPosition = p.second;
                    npc->state = NpcAiState::THREATEN;
                    npc->stateEnterTimeMs = currentTimeMs;
                    GameLog_Info("NPC %u (%s) detectou alvo %u -> THREATEN", npc->objectId, npc->name.c_str(), p.first);
                    return;
                }
            }

            // Se tiver waypoints e nenhum alvo detectado, entra em patrulha
            if (!npc->waypoints.empty()) {
                npc->state = NpcAiState::ROAM;
                npc->stateEnterTimeMs = currentTimeMs;
            }
            break;
        }

        case NpcAiState::ROAM: {
            // Patrulhamento ao longo de waypoints
            if (!npc->waypoints.empty()) {
                const AIVector3& dest = npc->waypoints[npc->currentWaypointIdx];
                if (npc->currentPosition.DistanceTo(dest) < 1.0f) {
                    npc->currentWaypointIdx = (npc->currentWaypointIdx + 1) % npc->waypoints.size();
                } else {
                    // Avança em direção ao waypoint
                    npc->currentPosition.x += (dest.x - npc->currentPosition.x) * 0.1f;
                    npc->currentPosition.y += (dest.y - npc->currentPosition.y) * 0.1f;
                    npc->currentPosition.z += (dest.z - npc->currentPosition.z) * 0.1f;
                }
            }

            // Varredura de agressividade durante patrulha
            for (const auto& p : nearbyPlayers) {
                if (npc->currentPosition.DistanceTo(p.second) <= npc->aggroRadius) {
                    npc->currentTargetId = p.first;
                    npc->targetPosition = p.second;
                    npc->state = NpcAiState::THREATEN;
                    npc->stateEnterTimeMs = currentTimeMs;
                    return;
                }
            }
            break;
        }

        case NpcAiState::SEARCH: {
            // Varredura periódica
            for (const auto& p : nearbyPlayers) {
                if (npc->currentPosition.DistanceTo(p.second) <= npc->aggroRadius) {
                    npc->currentTargetId = p.first;
                    npc->targetPosition = p.second;
                    npc->state = NpcAiState::THREATEN;
                    npc->stateEnterTimeMs = currentTimeMs;
                    return;
                }
            }
            npc->state = NpcAiState::REST;
            break;
        }

        case NpcAiState::THREATEN: {
            // Provocação/aviso sonoro antes de atacar (1.5 segundos)
            if (currentTimeMs - npc->stateEnterTimeMs >= npc->threatenDurationMs) {
                npc->state = NpcAiState::ATTACK;
                npc->hateTable.AddDamageHate(npc->currentTargetId, 100); // Hate inicial de engajamento
                if (npc->isBoss && npc->bossInfo.combatStartTimeMs == 0) {
                    npc->bossInfo.combatStartTimeMs = currentTimeMs;
                }
                GameLog_Info("NPC %u (%s) terminou provocacao -> ATTACK", npc->objectId, npc->name.c_str());
            }
            break;
        }

        case NpcAiState::ATTACK: {
            // 4.1.7 Verificação de Leash (Coleira): afastou mais de 50 metros da spawn?
            if (npc->currentPosition.DistanceTo(npc->spawnPosition) > npc->leashMaxRadius) {
                npc->state = NpcAiState::RETURN_LEASH;
                npc->isInvulnerable = true;
                npc->hateTable.Reset();
                GameLog_Info("NPC %u (%s) excedeu raio de 50m -> LEASH RETURN!", npc->objectId, npc->name.c_str());
                return;
            }

            // Seleção de alvo mais odiado
            uint32_t topTarget = npc->hateTable.GetMostHatedTarget();
            if (topTarget == 0) {
                npc->state = NpcAiState::RETURN_LEASH;
                npc->isInvulnerable = true;
                return;
            }
            npc->currentTargetId = topTarget;

            // Busca posição do alvo
            for (const auto& p : nearbyPlayers) {
                if (p.first == topTarget) {
                    npc->targetPosition = p.second;
                    break;
                }
            }

            // Distância para o alvo
            float distToTarget = npc->currentPosition.DistanceTo(npc->targetPosition);
            if (distToTarget > npc->attackRange) {
                // Alvo saiu do alcance de golpe -> Entra em perseguição (FOLLOW)
                npc->state = NpcAiState::FOLLOW;
            } else {
                // Executa ataque / golpe contra o alvo
            }
            break;
        }

        case NpcAiState::FOLLOW: {
            // Perseguição ao alvo
            if (npc->currentPosition.DistanceTo(npc->spawnPosition) > npc->leashMaxRadius) {
                npc->state = NpcAiState::RETURN_LEASH;
                npc->isInvulnerable = true;
                npc->hateTable.Reset();
                GameLog_Info("NPC %u (%s) excedeu raio durante perseguição -> LEASH RETURN!", npc->objectId, npc->name.c_str());
                return;
            }

            // Atualiza posição do alvo
            for (const auto& p : nearbyPlayers) {
                if (p.first == npc->currentTargetId) {
                    npc->targetPosition = p.second;
                    break;
                }
            }

            // Movimento suave em direção ao alvo
            npc->currentPosition.x += (npc->targetPosition.x - npc->currentPosition.x) * 0.15f;
            npc->currentPosition.y += (npc->targetPosition.y - npc->currentPosition.y) * 0.15f;
            npc->currentPosition.z += (npc->targetPosition.z - npc->currentPosition.z) * 0.15f;

            if (npc->currentPosition.DistanceTo(npc->targetPosition) <= npc->attackRange) {
                npc->state = NpcAiState::ATTACK;
            }
            break;
        }

        case NpcAiState::RETURN_LEASH: {
            // Retorno veloz ao ponto de spawn
            npc->isInvulnerable = true;
            float distToSpawn = npc->currentPosition.DistanceTo(npc->spawnPosition);
            if (distToSpawn <= 1.0f) {
                // Chegou em casa: restaura 100% do HP e volta a descansar
                npc->currentPosition = npc->spawnPosition;
                npc->currentHp = npc->maxHp;
                npc->isInvulnerable = false;
                npc->state = NpcAiState::REST;
                if (npc->isBoss) {
                    npc->bossInfo.currentPhase = BossPhase::PHASE_1_100;
                    npc->bossInfo.addsSpawned = false;
                    npc->bossInfo.isEnraged = false;
                    npc->bossInfo.damageMultiplier = 1.0f;
                    npc->bossInfo.combatStartTimeMs = 0;
                }
                GameLog_Info("NPC %u (%s) retornou a spawn: HP 100%% restaurado.", npc->objectId, npc->name.c_str());
            } else {
                // Teleporte/caminhada acelerada de volta
                npc->currentPosition.x += (npc->spawnPosition.x - npc->currentPosition.x) * 0.3f;
                npc->currentPosition.y += (npc->spawnPosition.y - npc->currentPosition.y) * 0.3f;
                npc->currentPosition.z += (npc->spawnPosition.z - npc->currentPosition.z) * 0.3f;
            }
            break;
        }
    }
}

// -------------------------------------------------------------
// 4.2 Notificações de Hate
// -------------------------------------------------------------
void AIEngine::NotifyDamageDealt(uint32_t npcId, uint32_t attackerId, int32_t damage) {
    NpcAiEntity* npc = GetNpc(npcId);
    if (!npc || npc->isInvulnerable) return;

    npc->currentHp = (std::max)(0, npc->currentHp - damage);
    npc->hateTable.AddDamageHate(attackerId, damage);

    // Se estiver em descanso ou patrulha, reage imediatamente entrando em combate
    if (npc->state == NpcAiState::REST || npc->state == NpcAiState::ROAM || npc->state == NpcAiState::SEARCH) {
        npc->currentTargetId = attackerId;
        npc->state = NpcAiState::ATTACK;
    }
}

void AIEngine::NotifyHealApplied(uint32_t npcId, uint32_t healerId, int32_t healAmount) {
    NpcAiEntity* npc = GetNpc(npcId);
    if (!npc || npc->isInvulnerable) return;

    // Se o monstro estiver em combate, adiciona hate no curandeiro
    if (npc->state == NpcAiState::ATTACK || npc->state == NpcAiState::FOLLOW) {
        npc->hateTable.AddHealHate(healerId, healAmount);
    }
}

void AIEngine::NotifyTauntUsed(uint32_t npcId, uint32_t tankId, int32_t tauntHate) {
    NpcAiEntity* npc = GetNpc(npcId);
    if (!npc || npc->isInvulnerable) return;

    npc->hateTable.AddTauntHate(tankId, tauntHate);
    npc->currentTargetId = tankId;
    npc->state = NpcAiState::ATTACK;
}

void AIEngine::NotifyHateDrop(uint32_t npcId, uint32_t targetId, float percentage) {
    NpcAiEntity* npc = GetNpc(npcId);
    if (!npc) return;

    npc->hateTable.ReduceHate(targetId, percentage);
}

// -------------------------------------------------------------
// 4.3 Mecânicas de Boss
// -------------------------------------------------------------
void AIEngine::ProcessBossPhases(NpcAiEntity& npc, uint64_t currentTimeMs) {
    if (!npc.isBoss || npc.maxHp <= 0) return;

    float hpPct = static_cast<float>(npc.currentHp) / static_cast<float>(npc.maxHp);

    // Transição de fases
    if (hpPct > 0.75f) {
        npc.bossInfo.currentPhase = BossPhase::PHASE_1_100;
    } else if (hpPct > 0.50f) {
        if (npc.bossInfo.currentPhase != BossPhase::PHASE_2_75) {
            npc.bossInfo.currentPhase = BossPhase::PHASE_2_75;
            // 4.3.2 Convocação de tropas de apoio (Add Spawns)
            if (!npc.bossInfo.addsSpawned) {
                npc.bossInfo.addsSpawned = true;
                uint32_t topHealer = npc.hateTable.GetTopHealerTarget();
                GameLog_Info("BOSS %u (%s) FASE 2: Convocando Adds contra curandeiro %u!", npc.objectId, npc.name.c_str(), topHealer);
            }
        }
    } else if (hpPct > 0.25f) {
        if (npc.bossInfo.currentPhase != BossPhase::PHASE_3_50) {
            npc.bossInfo.currentPhase = BossPhase::PHASE_3_50;
            GameLog_Info("BOSS %u (%s) FASE 3: Preparando Habilidade Suprema AoE!", npc.objectId, npc.name.c_str());
        }
    } else {
        if (npc.bossInfo.currentPhase != BossPhase::PHASE_4_25) {
            npc.bossInfo.currentPhase = BossPhase::PHASE_4_25;
            GameLog_Info("BOSS %u (%s) FASE 4: FASE FINAL DE FÚRIA!", npc.objectId, npc.name.c_str());
        }
    }

    // 4.3.3 Modo Enrage (Berserk) ao exceder tempo limite
    if (!npc.bossInfo.isEnraged && npc.bossInfo.combatStartTimeMs > 0) {
        if (currentTimeMs - npc.bossInfo.combatStartTimeMs >= npc.bossInfo.enrageTimeoutMs) {
            npc.bossInfo.isEnraged = true;
            npc.bossInfo.damageMultiplier = 5.0f; // Dano aumentado em 500%
            GameLog_Info("BOSS %u (%s) ENRAGE ATIVADO! Multiplicador de dano 5.0x!", npc.objectId, npc.name.c_str());
        }
    }
}

// -------------------------------------------------------------
// 4.4 Mascotes Funcionais (ToyPets)
// -------------------------------------------------------------
void AIEngine::RegisterToyPet(const ToyPetEntity& pet) {
    m_toyPets[pet.petId] = pet;
}

ToyPetEntity* AIEngine::GetToyPet(uint32_t petId) {
    auto it = m_toyPets.find(petId);
    if (it != m_toyPets.end()) {
        return &it->second;
    }
    return nullptr;
}

bool AIEngine::ProcessPetAutoLoot(uint32_t petId, std::vector<GroundDropItem>& groundItems) {
    ToyPetEntity* pet = GetToyPet(petId);
    if (!pet || !pet->hasAutoLoot) return false;

    bool lootedAny = false;
    for (auto it = groundItems.begin(); it != groundItems.end(); ) {
        if (pet->position.DistanceTo(it->position) <= 10.0f) { // Raio de coleta 10m
            if (pet->petBag.size() < pet->petBagCapacity) {
                PetBagSlot slot = {};
                slot.slotIndex = static_cast<uint8_t>(pet->petBag.size());
                slot.itemId = it->itemId;
                slot.count = it->count;
                pet->petBag.push_back(slot);
                it = groundItems.erase(it);
                lootedAny = true;
                continue;
            }
        }
        ++it;
    }
    return lootedAny;
}

bool AIEngine::ProcessPetAutoDoping(uint32_t petId, const std::vector<uint32_t>& activeMasterBuffs, std::vector<uint32_t>& consumedItems) {
    ToyPetEntity* pet = GetToyPet(petId);
    if (!pet || !pet->hasAutoDoping) return false;

    bool consumedAny = false;
    for (uint32_t neededItemId : pet->dopingItemIds) {
        bool hasBuff = (std::find(activeMasterBuffs.begin(), activeMasterBuffs.end(), neededItemId) != activeMasterBuffs.end());
        if (!hasBuff) {
            // Procura o item na bolsa do pet
            for (auto it = pet->petBag.begin(); it != pet->petBag.end(); ++it) {
                if (it->itemId == neededItemId && it->count > 0) {
                    it->count--;
                    consumedItems.push_back(neededItemId);
                    consumedAny = true;
                    if (it->count == 0) {
                        pet->petBag.erase(it);
                    }
                    break;
                }
            }
        }
    }
    return consumedAny;
}

bool AIEngine::ProcessPetEnemyAlarm(uint32_t petId, const std::vector<std::pair<uint32_t, std::pair<AIVector3, uint8_t>>>& playersInArea) {
    ToyPetEntity* pet = GetToyPet(petId);
    if (!pet || !pet->hasEnemyAlarm) return false;

    pet->enemyAlarmTriggered = false;
    pet->detectedEnemyId = 0;

    for (const auto& entry : playersInArea) {
        uint32_t otherId = entry.first;
        const AIVector3& otherPos = entry.second.first;
        uint8_t otherRace = entry.second.second;

        // Se for da raça inimiga e estiver a menos de 30 metros
        if (otherRace != pet->masterRace && pet->position.DistanceTo(otherPos) <= 30.0f) {
            pet->enemyAlarmTriggered = true;
            pet->detectedEnemyId = otherId;
            GameLog_Info("TOYPET %u: ALERTA DE INIMIGO DETECTADO! Inimigo Obj=%u a %.1fm!", pet->petId, otherId, pet->position.DistanceTo(otherPos));
            return true;
        }
    }
    return false;
}
