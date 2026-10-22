#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>

namespace AionServerPackets {

// Registra todos os manipuladores de pacotes de servidor no ClientToServerRouter
void RegisterAllHandlers();

// Autenticação e Entrada no Mundo
void HandleVersionCheck(const uint8_t* pData, size_t size);
void HandleKey(const uint8_t* pData, size_t size);
void HandleLoginCheck(const uint8_t* pData, size_t size);
void HandleEnterWorldCheck(const uint8_t* pData, size_t size);
void HandlePlayerSpawn(const uint8_t* pData, size_t size);
void HandleWaitList(const uint8_t* pData, size_t size);

// Entidades do Mundo (Spawn e Despawn)
void HandleNpcInfo(const uint8_t* pData, size_t size);
void HandlePlayerInfo(const uint8_t* pData, size_t size);
void HandleGatherableInfo(const uint8_t* pData, size_t size);
void HandleRemoveObject(const uint8_t* pData, size_t size);

// Movimento e Orientação
void HandleMoveNew(const uint8_t* pData, size_t size);
void HandleChangeDirection(const uint8_t* pData, size_t size);
void HandleBlink(const uint8_t* pData, size_t size);
void HandleRequestTeleport(const uint8_t* pData, size_t size);

// Combate e Ações
void HandleAttack(const uint8_t* pData, size_t size);
void HandleUseSkill(const uint8_t* pData, size_t size);
void HandleSkillSucceeded(const uint8_t* pData, size_t size);
void HandleSkillCanceled(const uint8_t* pData, size_t size);
void HandleSkillList(const uint8_t* pData, size_t size);
void HandleDeleteSkill(const uint8_t* pData, size_t size);
void HandleSkillCooldown(const uint8_t* pData, size_t size);
void HandleAbnormalStatus(const uint8_t* pData, size_t size);
void HandleAbnormalStatusOther(const uint8_t* pData, size_t size);
void HandleTacticsSign(const uint8_t* pData, size_t size);

// Atributos, Vida, Mana, DP, EXP
void HandleStatus(const uint8_t* pData, size_t size);
void HandleStatusOther(const uint8_t* pData, size_t size);
void HandleHitPoint(const uint8_t* pData, size_t size);
void HandleManaPoint(const uint8_t* pData, size_t size);
void HandleDp(const uint8_t* pData, size_t size);
void HandleExp(const uint8_t* pData, size_t size);

// Inventário e Itens
void HandleInventoryInfo(const uint8_t* pData, size_t size);
void HandleAddInventory(const uint8_t* pData, size_t size);
void HandleRemoveInventory(const uint8_t* pData, size_t size);
void HandleChangeItemDesc(const uint8_t* pData, size_t size);
void HandleItemList(const uint8_t* pData, size_t size);

// Mensagens, Diálogos, Quests e Interface
void HandleMessage(const uint8_t* pData, size_t size);
void HandleMessageCode(const uint8_t* pData, size_t size);
void HandleNpcHtmlMessage(const uint8_t* pData, size_t size);
void HandleAsk(const uint8_t* pData, size_t size);
void HandleCancelAsk(const uint8_t* pData, size_t size);
void HandleGameTime(const uint8_t* pData, size_t size);

// Sistemas Sociais e Ambiente
void HandlePartyInfo(const uint8_t* pData, size_t size);
void HandleGuildInfo(const uint8_t* pData, size_t size);
void HandleQuestList(const uint8_t* pData, size_t size);
void HandleTrade(const uint8_t* pData, size_t size);
void HandleWeather(const uint8_t* pData, size_t size);
void HandleResurrectDialog(const uint8_t* pData, size_t size);

}
