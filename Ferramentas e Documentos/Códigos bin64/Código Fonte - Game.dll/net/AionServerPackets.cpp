#include "AionServerPackets.h"
#include "AionPacketOpcodes.h"
#include "ClientToServerRouter.h"
#include "AionClientPackets.h"
#include "../core/GameLog.h"
#include <cmath>
#include <vector>

namespace AionServerPackets {

void RegisterAllHandlers() {
    auto& router = ClientToServerRouter::GetInstance();

    // 1. Autenticação e Entrada no Mundo
    router.RegisterServerPacketHandler(S_VERSION_CHECK, HandleVersionCheck);
    router.RegisterServerPacketHandler(S_KEY, HandleKey);
    router.RegisterServerPacketHandler(S_LOGIN_CHECK, HandleLoginCheck);
    router.RegisterServerPacketHandler(S_ENTER_WORLD_NOTIFY, HandleEnterWorldCheck);
    router.RegisterServerPacketHandler(S_WORLD, HandlePlayerSpawn);
    router.RegisterServerPacketHandler(S_WAIT_LIST, HandleWaitList);

    // 2. Entidades do Mundo (Spawn e Despawn)
    router.RegisterServerPacketHandler(S_PUT_NPC, HandleNpcInfo);
    router.RegisterServerPacketHandler(S_PUT_USER, HandlePlayerInfo);
    router.RegisterServerPacketHandler(S_PUT_OBJECT, HandleGatherableInfo);
    router.RegisterServerPacketHandler(S_REMOVE_OBJECT, HandleRemoveObject);

    // 3. Movimentação e Orientação
    router.RegisterServerPacketHandler(S_MOVE_NEW, HandleMoveNew);
    router.RegisterServerPacketHandler(S_CHANGE_DIRECTION, HandleChangeDirection);
    router.RegisterServerPacketHandler(S_BLINK, HandleBlink);
    router.RegisterServerPacketHandler(S_REQUEST_TELEPORT, HandleRequestTeleport);

    // 4. Combate e Habilidades
    router.RegisterServerPacketHandler(S_ATTACK, HandleAttack);
    router.RegisterServerPacketHandler(S_USE_SKILL, HandleUseSkill);
    router.RegisterServerPacketHandler(S_SKILL_SUCCEDED, HandleSkillSucceeded);
    router.RegisterServerPacketHandler(S_SKILL_CANCELED, HandleSkillCanceled);
    router.RegisterServerPacketHandler(S_ADD_SKILL, HandleSkillList);
    router.RegisterServerPacketHandler(S_DELETE_SKILL, HandleDeleteSkill);
    router.RegisterServerPacketHandler(S_LOAD_SKILL_COOLTIME, HandleSkillCooldown);
    router.RegisterServerPacketHandler(S_ABNORMAL_STATUS, HandleAbnormalStatus);
    router.RegisterServerPacketHandler(S_ABNORMAL_STATUS_OTHER, HandleAbnormalStatusOther);

    // 5. Atributos, Vida, Mana, DP, EXP e Abyss
    router.RegisterServerPacketHandler(S_STATUS, HandleStatus);
    router.RegisterServerPacketHandler(S_STATUS_OTHER, HandleStatusOther);
    router.RegisterServerPacketHandler(S_HIT_POINT, HandleHitPoint);
    router.RegisterServerPacketHandler(S_MANA_POINT, HandleManaPoint);
    router.RegisterServerPacketHandler(S_DP, HandleDp);
    router.RegisterServerPacketHandler(S_EXP, HandleExp);
    router.RegisterServerPacketHandler(S_ABYSS_POINT, HandleStatus); // SM_ABYSS_RANK

    // 6. Inventário e Armazém
    router.RegisterServerPacketHandler(S_LOAD_INVENTORY, HandleInventoryInfo);
    router.RegisterServerPacketHandler(S_ADD_INVENTORY, HandleAddInventory);
    router.RegisterServerPacketHandler(S_REMOVE_INVENTORY, HandleRemoveInventory);
    router.RegisterServerPacketHandler(S_CHANGE_ITEM_DESC, HandleChangeItemDesc);
    router.RegisterServerPacketHandler(S_ITEM_LIST, HandleItemList);

    // 7. Diálogos, Mensagens e Social
    router.RegisterServerPacketHandler(S_MESSAGE, HandleMessage);
    router.RegisterServerPacketHandler(S_MESSAGE_CODE, HandleMessageCode);
    router.RegisterServerPacketHandler(S_NPC_HTML_MESSAGE, HandleNpcHtmlMessage);
    router.RegisterServerPacketHandler(S_ASK, HandleAsk);
    router.RegisterServerPacketHandler(S_CANCEL_ASK, HandleCancelAsk);
    router.RegisterServerPacketHandler(S_TIME, HandleGameTime);
    router.RegisterServerPacketHandler(S_PARTY_INFO, HandlePartyInfo);
    router.RegisterServerPacketHandler(S_GUILD_INFO, HandleGuildInfo);
    router.RegisterServerPacketHandler(S_LOAD_WORKINGQUEST, HandleQuestList);
    router.RegisterServerPacketHandler(S_XCHG_START, HandleTrade);
    router.RegisterServerPacketHandler(S_WEATHER, HandleWeather);
    router.RegisterServerPacketHandler(S_RESURRECT_INFO, HandleResurrectDialog);

    GameLog_Info("AionServerPackets: 36 manipuladores canonicos do Classic registrados com sucesso.");
}

// 1. Autenticação e Sessão
void HandleVersionCheck(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint8_t result = reader.ReadByte();
    uint8_t serverId = reader.ReadByte();
    uint32_t buildDate = reader.ReadUInt32();
    GameLog_Info("[S_VERSION_CHECK] Versao do servidor: %u (ServerId=%u, BuildDate=%u)", result, serverId, buildDate);
}

void HandleKey(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t encipheredKey = reader.ReadUInt32();
    GameLog_Info("[S_KEY] Chave de sessao criptografada: 0x%08X", encipheredKey);
}

void HandleLoginCheck(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(5)) return;
    uint32_t accountId = reader.ReadUInt32();
    uint8_t loginResult = reader.ReadByte();
    GameLog_Info("[S_LOGIN_CHECK] Autenticacao de conta ID=%u (Resultado=%u)", accountId, loginResult);
}

void HandleEnterWorldCheck(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t worldId = reader.ReadUInt32();
    GameLog_Info("[S_ENTER_WORLD_NOTIFY] Entrada confirmada no Mundo ID=%u", worldId);
}

void HandlePlayerSpawn(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(17)) return;
    uint32_t objectId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    uint8_t heading = reader.ReadByte();
    GameLog_Info("[S_WORLD] Jogador Local Spawnado ObjId=%u Pos=(%.2f, %.2f, %.2f) Heading=%u",
        objectId, x, y, z, heading);
}

void HandleWaitList(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint32_t queuePosition = reader.ReadUInt32();
    uint16_t estimatedMinutes = reader.ReadUInt16();
    GameLog_Info("[S_WAIT_LIST] Fila de espera do servidor: Posicao #%u (Tempo estimado: %u min)",
        queuePosition, estimatedMinutes);
}

// 2. Entidades do Mundo
void HandleNpcInfo(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(20)) return;
    uint32_t npcObjectId = reader.ReadUInt32();
    uint32_t npcTemplateId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    GameLog_Info("[S_PUT_NPC] NPC Spawnado ObjId=%u (TplId=%u) Pos=(%.2f, %.2f, %.2f)",
        npcObjectId, npcTemplateId, x, y, z);
}

void HandlePlayerInfo(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(20)) return;
    uint32_t playerObjectId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    uint8_t heading = reader.ReadByte();
    uint8_t playerClass = reader.ReadByte();
    uint8_t race = reader.ReadByte();
    GameLog_Info("[S_PUT_USER] Outro Jogador Visivel ObjId=%u Classe=%u Raca=%u Pos=(%.2f, %.2f, %.2f)",
        playerObjectId, playerClass, race, x, y, z);
}

void HandleGatherableInfo(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(20)) return;
    uint32_t objectId = reader.ReadUInt32();
    uint32_t templateId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    GameLog_Info("[S_PUT_OBJECT] Recurso Coletavel Spawnado ObjId=%u (Tpl=%u) Pos=(%.2f, %.2f, %.2f)",
        objectId, templateId, x, y, z);
}

void HandleRemoveObject(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t objectId = reader.ReadUInt32();
    GameLog_Info("[S_REMOVE_OBJECT] Entidade Despawnada do Mundo ObjId=%u", objectId);
}

// 3. Movimentação e Orientação
void HandleMoveNew(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(18)) return;
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
        if (reader.HasBytes(12)) {
            targetX = reader.ReadFloat();
            targetY = reader.ReadFloat();
            targetZ = reader.ReadFloat();
        }
    }

    // Interpolação de vetor de movimento
    float lerp = 0.5f;
    float smoothX = startX + (targetX - startX) * lerp;
    float smoothY = startY + (targetY - startY) * lerp;
    float smoothZ = startZ + (targetZ - startZ) * lerp;

    GameLog_Info("[S_MOVE_NEW] Movimento Entidade ID=%u Mask=0x%02X Pos=(%.1f, %.1f, %.1f) Heading=%u",
        objectId, movementMask, smoothX, smoothY, smoothZ, heading);
}

void HandleChangeDirection(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(5)) return;
    uint32_t objectId = reader.ReadUInt32();
    uint8_t heading = reader.ReadByte();
    GameLog_Info("[S_CHANGE_DIRECTION] ObjId=%u nova orientacao heading=%u", objectId, heading);
}

void HandleBlink(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(16)) return;
    uint32_t objectId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    GameLog_Info("[S_BLINK] Teleporte Instantaneo (Blink) ObjId=%u para (%.2f, %.2f, %.2f)", objectId, x, y, z);
}

void HandleRequestTeleport(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(20)) return;
    uint32_t worldId = reader.ReadUInt32();
    float x = reader.ReadFloat();
    float y = reader.ReadFloat();
    float z = reader.ReadFloat();
    uint8_t heading = reader.ReadByte();
    GameLog_Info("[S_REQUEST_TELEPORT] Teleporte de Mapa para WorldID=%u Pos=(%.1f, %.1f, %.1f)", worldId, x, y, z);
}

// 4. Combate e Habilidades
void HandleAttack(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(13)) return;
    uint32_t attackerId = reader.ReadUInt32();
    uint32_t targetId = reader.ReadUInt32();
    uint32_t damage = reader.ReadUInt32();
    uint8_t attackStatus = reader.ReadByte(); // Normal, Crit, Block, Parry, Dodge
    GameLog_Info("[S_ATTACK] Atacante ID=%u -> Alvo ID=%u Dano=%u Status=%u", attackerId, targetId, damage, attackStatus);
}

void HandleUseSkill(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(13)) return;
    uint32_t casterId = reader.ReadUInt32();
    uint32_t targetId = reader.ReadUInt32();
    uint32_t skillId = reader.ReadUInt32();
    uint8_t skillLevel = reader.ReadByte();
    GameLog_Info("[S_USE_SKILL] Conjurando SkillId=%u (Nivel %u): Caster=%u -> Target=%u",
        skillId, skillLevel, casterId, targetId);
}

void HandleSkillSucceeded(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(17)) return;
    uint32_t casterId = reader.ReadUInt32();
    uint32_t targetId = reader.ReadUInt32();
    uint32_t skillId = reader.ReadUInt32();
    uint32_t damage = reader.ReadUInt32();
    uint8_t hitType = reader.ReadByte();
    GameLog_Info("[S_SKILL_SUCCEDED] SkillId=%u executada com sucesso! Dano=%u (HitType=%u)", skillId, damage, hitType);
}

void HandleSkillCanceled(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(8)) return;
    uint32_t skillId = reader.ReadUInt32();
    uint32_t reason = reader.ReadUInt32(); // 0 = Movimento, 1 = Silenciado, 2 = Interrompido por Dano
    GameLog_Info("[S_SKILL_CANCELED] Conjuracao de SkillId=%u cancelada (Motivo=%u)", skillId, reason);
}

void HandleSkillList(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(2)) return;
    uint16_t skillCount = reader.ReadUInt16();
    GameLog_Info("[S_ADD_SKILL] Lista de Habilidades aprendidas recebida (%u skills)", skillCount);
    for (uint16_t i = 0; i < skillCount; ++i) {
        if (!reader.HasBytes(5)) break;
        uint32_t skillId = reader.ReadUInt32();
        uint8_t skillLevel = reader.ReadByte();
        // Registra no grafo de habilidades
    }
}

void HandleDeleteSkill(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t skillId = reader.ReadUInt32();
    GameLog_Info("[S_DELETE_SKILL] Habilidade ID=%u desaprendida", skillId);
}

void HandleSkillCooldown(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(2)) return;
    uint16_t count = reader.ReadUInt16();
    GameLog_Info("[S_LOAD_SKILL_COOLTIME] Sincronizando tempo de recarga de %u habilidades", count);
    for (uint16_t i = 0; i < count; ++i) {
        if (!reader.HasBytes(8)) break;
        uint32_t skillId = reader.ReadUInt32();
        uint32_t remainingMs = reader.ReadUInt32();
    }
}

void HandleAbnormalStatus(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(2)) return;
    uint16_t count = reader.ReadUInt16();
    GameLog_Info("[S_ABNORMAL_STATUS] Efeitos ativos no jogador: %u efeitos", count);
}

void HandleAbnormalStatusOther(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint32_t targetId = reader.ReadUInt32();
    uint16_t count = reader.ReadUInt16();
    GameLog_Info("[S_ABNORMAL_STATUS_OTHER] Efeitos em Entidade ID=%u (%u efeitos)", targetId, count);
}

// 5. Atributos, Vida, Mana, DP, EXP e Abyss
void HandleStatus(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    GameLog_Info("[S_STATUS / S_ABYSS_POINT] Pacote de Atributos/Abyss recebido (%zu bytes)", size);
}

void HandleStatusOther(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t targetId = reader.ReadUInt32();
    GameLog_Info("[S_STATUS_OTHER] Status de entidade ID=%u atualizado", targetId);
}

void HandleHitPoint(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(8)) return;
    uint32_t curHp = reader.ReadUInt32();
    uint32_t maxHp = reader.ReadUInt32();
    GameLog_Info("[S_HIT_POINT] Vida: %u / %u", curHp, maxHp);
}

void HandleManaPoint(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(8)) return;
    uint32_t curMp = reader.ReadUInt32();
    uint32_t maxMp = reader.ReadUInt32();
    GameLog_Info("[S_MANA_POINT] Mana: %u / %u", curMp, maxMp);
}

void HandleDp(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t curDp = reader.ReadUInt32();
    GameLog_Info("[S_DP] Pontos Divinos: %u / 4000", curDp);
}

void HandleExp(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(16)) return;
    uint64_t curExp = reader.ReadUInt64();
    uint64_t neededExp = reader.ReadUInt64();
    GameLog_Info("[S_EXP] Experiencia: %llu / %llu", curExp, neededExp);
}

// 6. Inventário e Armazém
void HandleInventoryInfo(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(2)) return;
    uint16_t itemCount = reader.ReadUInt16();
    GameLog_Info("[S_LOAD_INVENTORY] Inventario carregado (%u itens)", itemCount);
    for (uint16_t i = 0; i < itemCount; ++i) {
        if (!reader.HasBytes(14)) break;
        uint32_t objectId = reader.ReadUInt32();
        uint32_t itemId = reader.ReadUInt32();
        uint32_t count = reader.ReadUInt32();
        int16_t slot = static_cast<int16_t>(reader.ReadUInt16());
    }
}

void HandleAddInventory(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(14)) return;
    uint32_t objectId = reader.ReadUInt32();
    uint32_t itemId = reader.ReadUInt32();
    uint32_t count = reader.ReadUInt32();
    int16_t slot = static_cast<int16_t>(reader.ReadUInt16());
    GameLog_Info("[S_ADD_INVENTORY] Item adicionado ao slot %d: ItemId=%u (Qtd=%u)", slot, itemId, count);
}

void HandleRemoveInventory(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t objectId = reader.ReadUInt32();
    GameLog_Info("[S_REMOVE_INVENTORY] Item removido ObjId=%u", objectId);
}

void HandleChangeItemDesc(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint32_t objectId = reader.ReadUInt32();
    uint8_t enchantLevel = reader.ReadByte();
    uint8_t socketCount = reader.ReadByte();
    GameLog_Info("[S_CHANGE_ITEM_DESC] Item ObjId=%u atualizado: Encantamento=+%u, Pedras=%u",
        objectId, enchantLevel, socketCount);
}

void HandleItemList(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t targetPlayerId = reader.ReadUInt32();
    GameLog_Info("[S_ITEM_LIST] Detalhes de equipamento inspecionado de Player ID=%u", targetPlayerId);
}

// 7. Diálogos, Mensagens e Social
void HandleMessage(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint8_t chatType = reader.ReadByte();
    uint8_t senderRace = reader.ReadByte();
    uint32_t senderObjId = reader.ReadUInt32();
    std::string senderName = reader.ReadString();
    std::string message = reader.ReadString();

    bool hasItemLink = (message.find("[item:") != std::string::npos);
    bool hasPosLink = (message.find("[pos:") != std::string::npos);

    GameLog_Info("[S_MESSAGE] [Canal %u] <%s>: %s %s%s",
        chatType, senderName.c_str(), message.c_str(),
        hasItemLink ? "[ITEM]" : "", hasPosLink ? "[POS]" : "");
}

void HandleMessageCode(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t messageCode = reader.ReadUInt32();
    GameLog_Info("[S_MESSAGE_CODE] Mensagem de Sistema: Code=%u", messageCode);
}

void HandleNpcHtmlMessage(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(8)) return;
    uint32_t npcObjectId = reader.ReadUInt32();
    uint32_t dialogId = reader.ReadUInt32();
    GameLog_Info("[S_NPC_HTML_MESSAGE] Dialogo HTML com NPC ObjId=%u (DialogId=%u)", npcObjectId, dialogId);
}

void HandleAsk(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(8)) return;
    uint32_t questionId = reader.ReadUInt32();
    uint32_t senderId = reader.ReadUInt32();
    GameLog_Info("[S_ASK] Janela de Confirmacao/Pergunta ID=%u de ObjId=%u", questionId, senderId);
}

void HandleCancelAsk(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t questionId = reader.ReadUInt32();
    GameLog_Info("[S_CANCEL_ASK] Pergunta ID=%u cancelada/expirada", questionId);
}

void HandleGameTime(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(4)) return;
    uint32_t gameMinutes = reader.ReadUInt32();
    uint32_t hour = (gameMinutes / 60) % 24;
    uint32_t minute = gameMinutes % 60;
    GameLog_Info("[S_TIME] Relogio de Atreia: %02u:%02u (Minutos: %u)", hour, minute, gameMinutes);
}

void HandlePartyInfo(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint32_t partyId = reader.ReadUInt32();
    uint8_t lootRule = reader.ReadByte();
    uint8_t memberCount = reader.ReadByte();
    GameLog_Info("[S_PARTY_INFO] Grupo ID=%u (Regra Loot=%u, Membros=%u)", partyId, lootRule, memberCount);
}

void HandleGuildInfo(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(10)) return;
    uint32_t legionId = reader.ReadUInt32();
    uint16_t legionLevel = reader.ReadUInt16();
    uint32_t memberCount = reader.ReadUInt32();
    std::string legionName = reader.ReadString();
    GameLog_Info("[S_GUILD_INFO] Legiao '%s' ID=%u Nivel=%u (Membros: %u)",
        legionName.c_str(), legionId, legionLevel, memberCount);
}

void HandleQuestList(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(2)) return;
    uint16_t questCount = reader.ReadUInt16();
    GameLog_Info("[S_LOAD_WORKINGQUEST] Quests ativas carregadas (%u quests)", questCount);
}

void HandleTrade(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(5)) return;
    uint32_t partnerId = reader.ReadUInt32();
    uint8_t action = reader.ReadByte();
    GameLog_Info("[S_XCHG_START] Negociacao de Comercio com ObjId=%u (Action=%u)", partnerId, action);
}

void HandleWeather(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint32_t zoneId = reader.ReadUInt32();
    uint8_t weatherType = reader.ReadByte();
    uint8_t intensity = reader.ReadByte();
    GameLog_Info("[S_WEATHER] Clima na Zona ID=%u: Tipo=%u Intensidade=%u", zoneId, weatherType, intensity);
}

void HandleResurrectDialog(const uint8_t* pData, size_t size) {
    PacketParserHandler reader(pData, size);
    if (!reader.HasBytes(6)) return;
    uint8_t resurrectType = reader.ReadByte(); // 0 = Obelisco, 1 = Kisk, 2 = Habilidade de Cleric/Chanter
    uint32_t casterId = reader.ReadUInt32();
    uint8_t expRecoveryPercent = reader.ReadByte();
    GameLog_Info("[S_RESURRECT_INFO] Dialogo de Ressurreicao: Tipo=%u, Caster=%u, Recuperacao EXP=%u%%",
        resurrectType, casterId, expRecoveryPercent);
}

}
