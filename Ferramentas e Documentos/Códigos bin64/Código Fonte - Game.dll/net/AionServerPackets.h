#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>

#include "AionRouters.h"

namespace AionServerPackets {

// Registra todos os manipuladores de pacotes de servidor no ClientToServerRouter
void RegisterAllHandlers();

// Manipuladores de pacotes específicos extraídos de ServerPacketsOpcodes.java
void HandleVersionCheck(const uint8_t* pData, size_t size);
void HandleEnterWorldCheck(const uint8_t* pData, size_t size);
void HandlePlayerSpawn(const uint8_t* pData, size_t size);
void HandleNpcInfo(const uint8_t* pData, size_t size);
void HandlePlayerInfo(const uint8_t* pData, size_t size);
void HandleMoveNew(const uint8_t* pData, size_t size);
void HandleAttack(const uint8_t* pData, size_t size);
void HandleUseSkill(const uint8_t* pData, size_t size);
void HandleStatus(const uint8_t* pData, size_t size);
void HandleHitPoint(const uint8_t* pData, size_t size);
void HandleManaPoint(const uint8_t* pData, size_t size);
void HandleInventoryInfo(const uint8_t* pData, size_t size);
void HandleMessage(const uint8_t* pData, size_t size);
void HandleNpcHtmlMessage(const uint8_t* pData, size_t size);
void HandleKey(const uint8_t* pData, size_t size);
void HandleTacticsSign(const uint8_t* pData, size_t size);

}

