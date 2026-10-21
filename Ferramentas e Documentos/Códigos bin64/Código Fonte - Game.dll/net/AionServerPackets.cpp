#include "AionServerPackets.h"
#include "AionPacketOpcodes.h"
#include "ClientToServerRouter.h"
#include "AionCryptEngine.h"
#include "AionClientPackets.h"
#include "../game/ActorManager.h"
#include "../core/GameLog.h"
#include <cmath>

namespace AionServerPackets {

void RegisterAllHandlers() {
    auto& router = ClientToServerRouter::GetInstance();

    router.RegisterServerPacketHandler(S_VERSION_CHECK, HandleVersionCheck);
    router.RegisterServerPacketHandler(S_KEY, HandleKey);
    router.RegisterServerPacketHandler(S_ENTER_WORLD_CHECK, HandleEnterWorldCheck);
    router.RegisterServerPacketHandler(S_WORLD, HandlePlayerSpawn);
    router.RegisterServerPacketHandler(S_PUT_NPC, HandleNpcInfo);
    router.RegisterServerPacketHandler(S_PUT_USER, HandlePlayerInfo);
    router.RegisterServerPacketHandler(S_MOVE_NEW, HandleMoveNew);
    router.RegisterServerPacketHandler(S_ATTACK, HandleAttack);
    router.RegisterServerPacketHandler(S_USE_SKILL, HandleUseSkill);
    router.RegisterServerPacketHandler(S_STATUS, HandleStatus);
    router.RegisterServerPacketHandler(S_HIT_POINT, HandleHitPoint);
    router.RegisterServerPacketHandler(S_MANA_POINT, HandleManaPoint);
    router.RegisterServerPacketHandler(S_LOAD_INVENTORY, HandleInventoryInfo);
    router.RegisterServerPacketHandler(S_MESSAGE, HandleMessage);
    router.RegisterServerPacketHandler(S_NPC_HTML_MESSAGE, HandleNpcHtmlMessage);
    router.RegisterServerPacketHandler(S_TACTICS_SIGN, HandleTacticsSign);

    GameLog_Info("AionServerPackets: 16 manipuladores canônicos de pacotes S_* registrados no ClientToServerRouter.");
}

void HandleVersionCheck(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint8_t result = reader.ReadByte();
    uint8_t serverId = reader.ReadByte();
    uint32_t buildDate = reader.ReadUInt32();
    GameLog_Info("[S_VERSION_CHECK] Resposta de versao do servidor: %u (ServerId=%u, BuildDate=%u)", result, serverId, buildDate);
}

void HandleKey(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t encipheredKey = reader.ReadUInt32();
    GameLog_Info("[S_KEY] Recebida chave enciphered do GameServer: 0x%08X", encipheredKey);
}

void HandleEnterWorldCheck(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t worldId = reader.ReadUInt32();
    GameLog_Info("[S_ENTER_WORLD_CHECK] Aprovada entrada no mundo ID=%u", worldId);
}

void HandlePlayerSpawn(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t objectId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    uint8_t heading = reader.ReadByte();
    GameLog_Info("[S_WORLD] Jogador Spawnado ID=%u pos=(%.2f, %.2f, %.2f, h=%u)", objectId, x, y, z, heading);
}

void HandleNpcInfo(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t npcObjectId = reader.ReadUInt32();
    uint32_t npcTemplateId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    GameLog_Info("[S_PUT_NPC] NPC Spawnado ObjId=%u (TplId=%u) pos=(%.2f, %.2f, %.2f)", npcObjectId, npcTemplateId, x, y, z);
}

void HandlePlayerInfo(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t playerObjectId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    GameLog_Info("[S_PUT_USER] Outro Jogador Visivel ID=%u pos=(%.2f, %.2f, %.2f)", playerObjectId, x, y, z);
}

void HandleMoveNew(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t objectId = reader.ReadUInt32();
    float startX = reader.ReadFloat();
    float startY = reader.ReadFloat();
    float startZ = reader.ReadFloat();
    uint8_t heading = reader.ReadByte();
    uint8_t movementMask = reader.ReadByte();

    float targetX = startX;
    float targetY = startY;
    float targetZ = startZ;

    if ((movementMask & MovementMask::POSITION) && (movementMask & MovementMask::MANUAL)) {
        targetX = reader.ReadFloat();
        targetY = reader.ReadFloat();
        targetZ = reader.ReadFloat();
    }

    // Interpolação suave (Lerp) para renderização sem saltos visuais
    float lerpFactor = 0.5f;
    float smoothX = startX + (targetX - startX) * lerpFactor;
    float smoothY = startY + (targetY - startY) * lerpFactor;
    float smoothZ = startZ + (targetZ - startZ) * lerpFactor;

    // Tratamento de queda física gravitacional da CryEngine (-9.81 m/s²)
    if (movementMask & MovementMask::FALL) {
        float fallDistance = startZ - targetZ;
        if (fallDistance > 10.0f) {
            GameLog_Info("[S_MOVE_NEW] Alerta de Queda: Entidade ID=%u caindo %.1fm (Gravidade: -9.81m/s2)", objectId, fallDistance);
        }
    }

    // Atualização de posição da entidade no ActorManager
    AIObject* pActor = ActorManager::GetInstance().GetActor(objectId);
    if (pActor) {
        pActor->SetPosition(Vec3F(smoothX, smoothY, smoothZ));
    }

    GameLog_Info("[S_MOVE_NEW] Movimento Entidade ID=%u Mask=0x%02X Pos=(%.1f, %.1f, %.1f) Heading=%u",
        objectId, movementMask, smoothX, smoothY, smoothZ, heading);
}

void HandleAttack(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t attackerId = reader.ReadUInt32();
    uint32_t targetId = reader.ReadUInt32();
    uint32_t damage = reader.ReadUInt32();
    uint8_t attackStatus = reader.ReadByte();
    GameLog_Info("[S_ATTACK] Atacante ID=%u -> Alvo ID=%u Dano=%u Status=%u", attackerId, targetId, damage, attackStatus);
}

void HandleUseSkill(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t casterId = reader.ReadUInt32();
    uint32_t targetId = reader.ReadUInt32();
    uint32_t skillId = reader.ReadUInt32();
    uint8_t skillLevel = reader.ReadByte();
    GameLog_Info("[S_USE_SKILL] Conjurador ID=%u -> Alvo ID=%u SkillId=%u Nivel=%u", casterId, targetId, skillId, skillLevel);
}

void HandleStatus(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    GameLog_Info("[S_STATUS] Atualizacao de status do jogador recebida (%zu bytes)", size);
}

void HandleHitPoint(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t curHp = reader.ReadUInt32();
    uint32_t maxHp = reader.ReadUInt32();
    GameLog_Info("[S_HIT_POINT] Vida atualizada: %u / %u", curHp, maxHp);
}

void HandleManaPoint(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t curMp = reader.ReadUInt32();
    uint32_t maxMp = reader.ReadUInt32();
    GameLog_Info("[S_MANA_POINT] Mana atualizada: %u / %u", curMp, maxMp);
}

void HandleInventoryInfo(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint16_t itemCount = reader.ReadUInt16();
    GameLog_Info("[S_LOAD_INVENTORY] Inventario carregado (%u itens)", itemCount);
}

void HandleMessage(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint8_t chatType = reader.ReadByte();
    uint8_t senderRace = reader.ReadByte();
    uint32_t senderObjId = reader.ReadUInt32();
    std::string senderName = reader.ReadString();
    std::string message = reader.ReadString();

    float posX = 0.0f, posY = 0.0f, posZ = 0.0f;
    if (chatType == 3) { // SHOUT
        posX = reader.ReadFloat();
        posY = reader.ReadFloat();
        posZ = reader.ReadFloat();
    }

    // Identificação de hiperlinks no corpo da mensagem
    bool hasItemLink = (message.find("[item:") != std::string::npos);
    bool hasPosLink = (message.find("[pos:") != std::string::npos);
    bool hasQuestLink = (message.find("[quest:") != std::string::npos);

    GameLog_Info("[S_MESSAGE] [Canal %u, Raca %u] <%s (ObjId=%u)>: %s %s%s%s",
        chatType, senderRace, senderName.c_str(), senderObjId, message.c_str(),
        hasItemLink ? "[ITEM_LINK] " : "",
        hasPosLink ? "[POS_LINK] " : "",
        hasQuestLink ? "[QUEST_LINK]" : "");
}

void HandleNpcHtmlMessage(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t npcObjectId = reader.ReadUInt32();
    uint32_t dialogId = reader.ReadUInt32();
    GameLog_Info("[S_NPC_HTML_MESSAGE] Dialogo com NPC ObjId=%u (DialogId=%u)", npcObjectId, dialogId);
}

void HandleTacticsSign(const uint8_t* pData, size_t size) {
    ByteBufferReader reader(pData, size);
    uint32_t action = reader.ReadUInt32();
    uint32_t brandId = reader.ReadUInt32();
    uint32_t targetObjectId = reader.ReadUInt32();
    GameLog_Info("[S_TACTICS_SIGN] Marcador de Alvo de Lider: BrandId=%u sobre ObjId=%u (Action=%u)",
        brandId, targetObjectId, action);
}

}

