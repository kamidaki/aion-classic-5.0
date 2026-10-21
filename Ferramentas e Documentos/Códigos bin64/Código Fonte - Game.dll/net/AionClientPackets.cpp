#include "AionClientPackets.h"

namespace AionPackets {

// --- 1. Autenticação, Ciclo de Vida e Sessão ---
ByteBufferWriter BuildVersionPacket(uint32_t version, uint32_t subVersion) {
    ByteBufferWriter writer(C_VERSION);
    writer.WriteUInt16(static_cast<uint16_t>(version));
    writer.WriteUInt16(static_cast<uint16_t>(subVersion));
    writer.WriteUInt32(0);     // windowsEncoding
    writer.WriteUInt32(10);    // windowsVersion (Windows 10/11)
    writer.WriteUInt32(19045); // windowsSubVersion
    writer.WriteByte(2);       // liteInfo (2 = Essential/Full client)
    return writer;
}

ByteBufferWriter BuildLogoutPacket() {
    ByteBufferWriter writer(C_LOGOUT);
    return writer;
}

ByteBufferWriter BuildAskQuitPacket() {
    ByteBufferWriter writer(C_ASK_QUIT);
    return writer;
}

ByteBufferWriter BuildReadyToQuitPacket() {
    ByteBufferWriter writer(C_READY_TO_QUIT);
    return writer;
}

ByteBufferWriter BuildDeadRestartPacket() {
    ByteBufferWriter writer(C_DEAD_RESTART);
    return writer;
}

ByteBufferWriter BuildL2AuthLoginPacket(const std::string& account, const std::string& token) {
    ByteBufferWriter writer(C_L2AUTH_LOGIN);
    writer.WriteString(account);
    writer.WriteString(token);
    return writer;
}

ByteBufferWriter BuildAlivePacket(uint32_t clientTime) {
    ByteBufferWriter writer(C_ALIVE);
    writer.WriteUInt32(clientTime);
    return writer;
}

ByteBufferWriter BuildSyncTimePacket(uint32_t clientTime) {
    ByteBufferWriter writer(C_SYNC_TIME);
    writer.WriteUInt32(clientTime);
    return writer;
}

ByteBufferWriter BuildReconnectAuthPacket(uint32_t accountId, const std::string& token) {
    ByteBufferWriter writer(C_RECONNECT_AUTH);
    writer.WriteUInt32(accountId);
    writer.WriteString(token);
    return writer;
}

// --- 2. Seleção e Criação de Personagem ---
ByteBufferWriter BuildCharacterListPacket() {
    ByteBufferWriter writer(C_CHARACTER_LIST);
    return writer;
}

ByteBufferWriter BuildCheckNicknamePacket(const std::string& name) {
    ByteBufferWriter writer(C_CHECK_EXIST);
    writer.WriteString(name);
    return writer;
}

ByteBufferWriter BuildCreateCharacterPacket(const std::string& name, uint8_t race, uint8_t gender, uint8_t playerClass, uint8_t voice, const std::vector<uint8_t>& appearanceData) {
    ByteBufferWriter writer(C_CREATE_CHARACTER);
    writer.WriteString(name);
    writer.WriteByte(race);
    writer.WriteByte(gender);
    writer.WriteByte(playerClass);
    writer.WriteByte(voice);
    writer.WriteBytes(appearanceData.data(), appearanceData.size());
    return writer;
}

ByteBufferWriter BuildDeleteCharacterPacket(uint32_t characterId) {
    ByteBufferWriter writer(C_DELETE_CHARACTER);
    writer.WriteUInt32(characterId);
    return writer;
}

ByteBufferWriter BuildRestoreCharacterPacket(uint32_t characterId) {
    ByteBufferWriter writer(C_RESTORE_CHARACTER);
    writer.WriteUInt32(characterId);
    return writer;
}

ByteBufferWriter BuildEnterWorldPacket(uint32_t characterId) {
    ByteBufferWriter writer(C_ENTER_WORLD);
    writer.WriteUInt32(characterId);
    return writer;
}

ByteBufferWriter BuildLevelReadyPacket() {
    ByteBufferWriter writer(C_LEVEL_READY);
    return writer;
}

// --- 3. Movimentação, Posição e Voo ---
ByteBufferWriter BuildMoveNewPacket(float x, float y, float z, uint8_t heading, uint8_t moveMask, float vectorX, float vectorY, float vectorZ) {
    ByteBufferWriter writer(C_MOVE_NEW);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(heading);
    writer.WriteByte(moveMask);

    if ((moveMask & MovementMask::POSITION) && (moveMask & MovementMask::MANUAL)) {
        writer.WriteFloat(vectorX);
        writer.WriteFloat(vectorY);
        writer.WriteFloat(vectorZ);
    }
    return writer;
}

ByteBufferWriter BuildMoveNewAbsolutePacket(float x, float y, float z, uint8_t heading, float targetX, float targetY, float targetZ) {
    ByteBufferWriter writer(C_MOVE_NEW);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(heading);
    uint8_t moveMask = MovementMask::POSITION | MovementMask::MANUAL | MovementMask::ABSOLUTE;
    writer.WriteByte(moveMask);
    writer.WriteFloat(targetX);
    writer.WriteFloat(targetY);
    writer.WriteFloat(targetZ);
    return writer;
}

ByteBufferWriter BuildMoveNewGlidePacket(float x, float y, float z, uint8_t heading, float vectorX, float vectorY, float vectorZ, uint8_t glideFlag, uint8_t geyserLocationId) {
    ByteBufferWriter writer(C_MOVE_NEW);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(heading);
    uint8_t moveMask = MovementMask::POSITION | MovementMask::MANUAL | MovementMask::GLIDE;
    writer.WriteByte(moveMask);
    writer.WriteFloat(vectorX);
    writer.WriteFloat(vectorY);
    writer.WriteFloat(vectorZ);
    writer.WriteByte(glideFlag);
    if (glideFlag == 2) { // GEYSER
        writer.WriteByte(geyserLocationId);
    }
    return writer;
}

ByteBufferWriter BuildMoveNewVehiclePacket(float x, float y, float z, uint8_t heading, float vehicleX, float vehicleY, float vehicleZ, uint32_t unk1, uint32_t unk2) {
    ByteBufferWriter writer(C_MOVE_NEW);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(heading);
    uint8_t moveMask = MovementMask::VEHICLE;
    writer.WriteByte(moveMask);
    writer.WriteUInt32(unk1);
    writer.WriteUInt32(unk2);
    writer.WriteFloat(vehicleX);
    writer.WriteFloat(vehicleY);
    writer.WriteFloat(vehicleZ);
    return writer;
}

ByteBufferWriter BuildPathFlyPacket(float x, float y, float z, uint8_t flyState) {
    ByteBufferWriter writer(C_PATH_FLY);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(flyState);
    return writer;
}

ByteBufferWriter BuildWindPathPacket(uint32_t windStreamId, uint32_t distance, uint8_t state) {
    ByteBufferWriter writer(C_WIND_PATH);
    writer.WriteUInt32(windStreamId);
    writer.WriteUInt32(distance);
    writer.WriteByte(state);
    return writer;
}

ByteBufferWriter BuildBlinkPacket(float x, float y, float z, uint8_t heading) {
    ByteBufferWriter writer(C_BLINK);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(heading);
    return writer;
}

ByteBufferWriter BuildChangeDirectionPacket(uint8_t heading) {
    ByteBufferWriter writer(C_CHANGE_DIRECTION);
    writer.WriteByte(heading);
    return writer;
}

// --- 4. Combate, Habilidades e Alvos ---
ByteBufferWriter BuildChangeTargetPacket(uint32_t targetObjectId) {
    ByteBufferWriter writer(C_CHANGE_TARGET);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildAttackPacket(uint32_t targetObjectId, uint8_t attackType, uint32_t time) {
    ByteBufferWriter writer(C_ATTACK);
    writer.WriteUInt32(targetObjectId);
    writer.WriteByte(attackType);
    writer.WriteUInt32(time);
    return writer;
}

ByteBufferWriter BuildUseSkillPacket(uint32_t skillId, uint32_t skillLevel, uint32_t targetObjectId) {
    ByteBufferWriter writer(C_USE_SKILL);
    writer.WriteUInt32(skillId);
    writer.WriteUInt32(skillLevel);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildTurnOffToggleSkillPacket(uint32_t skillId) {
    ByteBufferWriter writer(C_TURN_OFF_TOGGLE_SKILL);
    writer.WriteUInt32(skillId);
    return writer;
}

ByteBufferWriter BuildTurnOffAbnormalStatusPacket(uint32_t effectId) {
    ByteBufferWriter writer(C_TURN_OFF_ABNORMAL_STATUS);
    writer.WriteUInt32(effectId);
    return writer;
}

// --- 5. Inventário, Itens e Equipamento ---
ByteBufferWriter BuildUseItemPacket(uint32_t itemUniqueId) {
    ByteBufferWriter writer(C_USE_ITEM);
    writer.WriteUInt32(itemUniqueId);
    return writer;
}

ByteBufferWriter BuildUseEquipmentItemPacket(uint32_t itemUniqueId) {
    ByteBufferWriter writer(C_USE_EQUIPMENT_ITEM);
    writer.WriteUInt32(itemUniqueId);
    return writer;
}

ByteBufferWriter BuildMoveItemSlotPacket(uint32_t itemUniqueId, uint8_t destSlot) {
    ByteBufferWriter writer(C_MOVE_ITEM_TO_ANOTHER_SLOT);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteByte(destSlot);
    return writer;
}

ByteBufferWriter BuildMoveStackableItemPacket(uint32_t itemUniqueId, uint32_t count, uint8_t destSlot) {
    ByteBufferWriter writer(C_MOVE_STACKABLE_ITEM);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteUInt32(count);
    writer.WriteByte(destSlot);
    return writer;
}

ByteBufferWriter BuildSwapItemSlotPacket(uint8_t slot1, uint8_t slot2) {
    ByteBufferWriter writer(C_SWAP_ITEM_SLOT);
    writer.WriteByte(slot1);
    writer.WriteByte(slot2);
    return writer;
}

ByteBufferWriter BuildDestroyItemPacket(uint32_t itemUniqueId, uint32_t count) {
    ByteBufferWriter writer(C_DESTROY_ITEM);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteUInt32(count);
    return writer;
}

ByteBufferWriter BuildEnchantItemPacket(uint32_t targetItemUniqueId, uint32_t stoneItemUniqueId, uint32_t supplementUniqueId) {
    ByteBufferWriter writer(C_ENCHANT_ITEM);
    writer.WriteUInt32(targetItemUniqueId);
    writer.WriteUInt32(stoneItemUniqueId);
    writer.WriteUInt32(supplementUniqueId);
    return writer;
}

// --- 6. Diálogos com NPCs e Missões ---
ByteBufferWriter BuildStartDialogPacket(uint32_t targetObjectId) {
    ByteBufferWriter writer(C_START_DIALOG);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildEndDialogPacket(uint32_t targetObjectId) {
    ByteBufferWriter writer(C_END_DIALOG);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildHActionPacket(uint32_t targetObjectId, uint32_t dialogId, uint32_t questId) {
    ByteBufferWriter writer(C_HACTION);
    writer.WriteUInt32(targetObjectId);
    writer.WriteUInt32(dialogId);
    writer.WriteUInt32(questId);
    return writer;
}

ByteBufferWriter BuildGiveUpQuestPacket(uint32_t questId) {
    ByteBufferWriter writer(C_GIVE_UP_QUEST);
    writer.WriteUInt32(questId);
    return writer;
}

ByteBufferWriter BuildShareQuestPacket(uint32_t questId) {
    ByteBufferWriter writer(C_SHARE_QUEST);
    writer.WriteUInt32(questId);
    return writer;
}

// --- 7. Comunicação, Chat e Emoções ---
ByteBufferWriter BuildSayPacket(uint8_t chatType, const std::string& message) {
    ByteBufferWriter writer(C_SAY);
    writer.WriteByte(chatType);
    writer.WriteString(message);
    return writer;
}

ByteBufferWriter BuildWhisperPacket(const std::string& recipient, const std::string& message) {
    ByteBufferWriter writer(C_WHISPER);
    writer.WriteString(recipient);
    writer.WriteString(message);
    return writer;
}

ByteBufferWriter BuildActionPacket(uint32_t emotionId, uint32_t targetObjectId) {
    ByteBufferWriter writer(C_ACTION);
    writer.WriteUInt32(emotionId);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

// --- 8. Coleta e Crafting ---
ByteBufferWriter BuildGatherPacket(uint32_t targetObjectId) {
    ByteBufferWriter writer(C_GATHER);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildCombinePacket(uint32_t recipeId, uint32_t targetObjectId) {
    ByteBufferWriter writer(C_COMBINE);
    writer.WriteUInt32(recipeId);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

// --- 9. Saque (Loot) ---
ByteBufferWriter BuildLootPacket(uint32_t targetObjectId) {
    ByteBufferWriter writer(C_LOOT);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildLootItemPacket(uint32_t targetObjectId, uint32_t itemIndex) {
    ByteBufferWriter writer(C_LOOT_ITEM);
    writer.WriteUInt32(targetObjectId);
    writer.WriteUInt32(itemIndex);
    return writer;
}

// --- 10. Trocas e Comércio ---
ByteBufferWriter BuildAskExchangePacket(uint32_t targetObjectId) {
    ByteBufferWriter writer(C_ASK_XCHG);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

ByteBufferWriter BuildAddExchangeItemPacket(uint32_t itemUniqueId, uint32_t count) {
    ByteBufferWriter writer(C_ADD_XCHG);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteUInt32(count);
    return writer;
}

ByteBufferWriter BuildExchangeGoldPacket(uint64_t kinahAmount) {
    ByteBufferWriter writer(C_XCHG_GOLD);
    writer.WriteUInt64(kinahAmount);
    return writer;
}

ByteBufferWriter BuildCheckExchangePacket() {
    ByteBufferWriter writer(C_CHECK_XCHG);
    return writer;
}

ByteBufferWriter BuildAcceptExchangePacket() {
    ByteBufferWriter writer(C_ACCEPT_XCHG);
    return writer;
}

ByteBufferWriter BuildCancelExchangePacket() {
    ByteBufferWriter writer(C_CANCEL_XCHG);
    return writer;
}

ByteBufferWriter BuildBuySellPacket(uint32_t npcObjectId, const std::vector<std::pair<uint32_t, uint32_t>>& itemsToBuy) {
    ByteBufferWriter writer(C_BUY_SELL);
    writer.WriteUInt32(npcObjectId);
    writer.WriteUInt16(static_cast<uint16_t>(itemsToBuy.size()));
    for (const auto& item : itemsToBuy) {
        writer.WriteUInt32(item.first);   // itemId
        writer.WriteUInt32(item.second);  // count
    }
    return writer;
}

// Formatadores canônicos de hiperlinks no chat
std::string FormatItemLink(uint32_t itemId, const std::string& itemName) {
    return "[item:" + std::to_string(itemId) + ";ffffffff;" + itemName + "]";
}

std::string FormatPosLink(uint32_t mapId, float x, float y, float z) {
    return "[pos:" + std::to_string(mapId) + ";" + std::to_string(static_cast<int>(x)) + ";" + 
           std::to_string(static_cast<int>(y)) + ";" + std::to_string(static_cast<int>(z)) + "]";
}

std::string FormatQuestLink(uint32_t questId, const std::string& questTitle) {
    return "[quest:" + std::to_string(questId) + ";" + questTitle + "]";
}

// --- 8. Grupos, Alianças e Marcação Tática ---
ByteBufferWriter BuildInviteToGroupPacket(const std::string& targetPlayerName, uint8_t inviteType) {
    ByteBufferWriter writer(C_PARTY_BY_NAME);
    writer.WriteByte(inviteType);
    writer.WriteString(targetPlayerName);
    return writer;
}

ByteBufferWriter BuildGroupLootPacket(uint32_t groupId, uint32_t itemId, uint32_t npcObjId, uint8_t distMode, uint32_t roll, uint64_t bid) {
    ByteBufferWriter writer(C_GROUP_ITEM_DIST);
    writer.WriteUInt32(groupId);
    writer.WriteUInt32(0); // index
    writer.WriteUInt32(0); // unk1
    writer.WriteUInt32(itemId);
    writer.WriteByte(0);   // unk2
    writer.WriteByte(0);   // unk3
    writer.WriteByte(0);   // unk4
    writer.WriteUInt32(npcObjId);
    writer.WriteByte(distMode); // 2: Roll, 3: Bid
    writer.WriteUInt32(roll);
    writer.WriteUInt64(bid);
    return writer;
}

ByteBufferWriter BuildShowBrandPacket(uint32_t brandId, uint32_t targetObjectId, uint32_t action) {
    ByteBufferWriter writer(C_TACTICS_SIGN);
    writer.WriteUInt32(action);
    writer.WriteUInt32(brandId);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

}

