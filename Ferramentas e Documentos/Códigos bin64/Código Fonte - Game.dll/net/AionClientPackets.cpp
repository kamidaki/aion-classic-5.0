#include "AionClientPackets.h"

namespace AionPackets {

// --- 1. Autenticação, Ciclo de Vida e Sessão ---
PacketParser BuildVersionPacket(uint32_t version, uint32_t subVersion) {
    PacketParser writer(C_VERSION);
    writer.WriteUInt16(static_cast<uint16_t>(version));
    writer.WriteUInt16(static_cast<uint16_t>(subVersion));
    writer.WriteUInt32(0);     // windowsEncoding
    writer.WriteUInt32(10);    // windowsVersion (Windows 10/11)
    writer.WriteUInt32(19045); // windowsSubVersion
    writer.WriteByte(2);       // liteInfo (2 = Essential/Full client)
    return writer;
}

PacketParser BuildLogoutPacket() {
    PacketParser writer(C_LOGOUT);
    return writer;
}

PacketParser BuildAskQuitPacket() {
    PacketParser writer(C_ASK_QUIT);
    return writer;
}

PacketParser BuildReadyToQuitPacket() {
    PacketParser writer(C_READY_TO_QUIT);
    return writer;
}

PacketParser BuildDeadRestartPacket() {
    PacketParser writer(C_DEAD_RESTART);
    return writer;
}

PacketParser BuildL2AuthLoginPacket(const std::string& account, const std::string& token) {
    PacketParser writer(C_L2AUTH_LOGIN);
    writer.WriteString(account);
    writer.WriteString(token);
    return writer;
}

PacketParser BuildAlivePacket(uint32_t clientTime) {
    PacketParser writer(C_ALIVE);
    writer.WriteUInt32(clientTime);
    return writer;
}

PacketParser BuildSyncTimePacket(uint32_t clientTime) {
    PacketParser writer(C_SYNC_TIME);
    writer.WriteUInt32(clientTime);
    return writer;
}

PacketParser BuildReconnectAuthPacket(uint32_t accountId, const std::string& token) {
    PacketParser writer(C_RECONNECT_AUTH);
    writer.WriteUInt32(accountId);
    writer.WriteString(token);
    return writer;
}

// --- 2. Seleção e Criação de Personagem ---
PacketParser BuildCharacterListPacket() {
    PacketParser writer(C_CHARACTER_LIST);
    return writer;
}

PacketParser BuildCheckNicknamePacket(const std::string& name) {
    PacketParser writer(C_CHECK_EXIST);
    writer.WriteString(name);
    return writer;
}

PacketParser BuildEnterCharCreationScreenPacket(uint32_t accountId, const std::string& accountName) {
    PacketParser writer(C_CREATE_CHARACTER);
    writer.WriteUInt32(accountId);
    writer.WriteString(accountName);
    // basicInfo em branco (50 bytes nome, gender=0, race=0, class=0)
    writer.WriteWStringFixed(L"", 25);
    writer.WriteUInt32(0);
    writer.WriteUInt32(0);
    writer.WriteUInt32(0);
    // appearance zerada
    PlayerAppearance emptyApp;
    memset(&emptyApp, 0, sizeof(emptyApp));
    emptyApp.height = 1.0f;
    writer.WriteBytes(reinterpret_cast<const uint8_t*>(&emptyApp), sizeof(emptyApp));
    // type = 1 para abrir a tela de criacao
    writer.WriteByte(1);
    return writer;
}

PacketParser BuildCreateCharacterPacket(uint32_t accountId, const std::string& accountName, const std::string& charName, uint32_t race, uint32_t gender, uint32_t playerClass, const PlayerAppearance& appearance, uint8_t createType) {
    PacketParser writer(C_CREATE_CHARACTER);
    writer.WriteUInt32(accountId);
    writer.WriteString(accountName);
    // Nome do personagem em UTF-16 com max 25 caracteres (50 bytes)
    std::wstring wsCharName;
    wsCharName.reserve(charName.size());
    for (char c : charName) {
        wsCharName.push_back(static_cast<wchar_t>(static_cast<uint8_t>(c)));
    }
    writer.WriteWStringFixed(wsCharName, 25);
    writer.WriteUInt32(gender);
    writer.WriteUInt32(race);
    writer.WriteUInt32(playerClass);
    // Bloco binario oficial de aparencia (PlayerAppearance)
    writer.WriteBytes(reinterpret_cast<const uint8_t*>(&appearance), sizeof(appearance));
    // Flag de criacao (0 = submissao de criacao final)
    writer.WriteByte(createType);
    return writer;
}

PacketParser BuildCreateCharacterPacket(const std::string& name, uint8_t race, uint8_t gender, uint8_t playerClass, uint8_t voice, const std::vector<uint8_t>& appearanceData) {
    PlayerAppearance app;
    memset(&app, 0, sizeof(app));
    app.voice = voice;
    app.height = 1.0f;
    if (!appearanceData.empty()) {
        size_t copyLen = (std::min)(sizeof(app), appearanceData.size());
        memcpy(&app, appearanceData.data(), copyLen);
    }
    return BuildCreateCharacterPacket(0, "", name, race, gender, playerClass, app, 0);
}

PacketParser BuildDeleteCharacterPacket(uint32_t characterId) {
    PacketParser writer(C_DELETE_CHARACTER);
    writer.WriteUInt32(characterId);
    return writer;
}

PacketParser BuildRestoreCharacterPacket(uint32_t characterId) {
    PacketParser writer(C_RESTORE_CHARACTER);
    writer.WriteUInt32(characterId);
    return writer;
}

PacketParser BuildEnterWorldPacket(uint32_t characterId) {
    PacketParser writer(C_ENTER_WORLD);
    writer.WriteUInt32(characterId);
    return writer;
}

PacketParser BuildLevelReadyPacket() {
    PacketParser writer(C_LEVEL_READY);
    return writer;
}

// --- 3. Movimentação, Posição e Voo ---
PacketParser BuildMoveNewPacket(float x, float y, float z, uint8_t heading, uint8_t moveMask, float vectorX, float vectorY, float vectorZ) {
    PacketParser writer(C_MOVE_NEW);
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

PacketParser BuildMoveNewAbsolutePacket(float x, float y, float z, uint8_t heading, float targetX, float targetY, float targetZ) {
    PacketParser writer(C_MOVE_NEW);
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

PacketParser BuildMoveNewGlidePacket(float x, float y, float z, uint8_t heading, float vectorX, float vectorY, float vectorZ, uint8_t glideFlag, uint8_t geyserLocationId) {
    PacketParser writer(C_MOVE_NEW);
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

PacketParser BuildMoveNewVehiclePacket(float x, float y, float z, uint8_t heading, float vehicleX, float vehicleY, float vehicleZ, uint32_t unk1, uint32_t unk2) {
    PacketParser writer(C_MOVE_NEW);
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

PacketParser BuildPathFlyPacket(float x, float y, float z, uint8_t flyState) {
    PacketParser writer(C_PATH_FLY);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(flyState);
    return writer;
}

PacketParser BuildWindPathPacket(uint32_t windStreamId, uint32_t distance, uint8_t state) {
    PacketParser writer(C_WIND_PATH);
    writer.WriteUInt32(windStreamId);
    writer.WriteUInt32(distance);
    writer.WriteByte(state);
    return writer;
}

PacketParser BuildBlinkPacket(float x, float y, float z, uint8_t heading) {
    PacketParser writer(C_BLINK);
    writer.WriteFloat(x);
    writer.WriteFloat(y);
    writer.WriteFloat(z);
    writer.WriteByte(heading);
    return writer;
}

PacketParser BuildChangeDirectionPacket(uint8_t heading) {
    PacketParser writer(C_CHANGE_DIRECTION);
    writer.WriteByte(heading);
    return writer;
}

// --- 4. Combate, Habilidades e Alvos ---
PacketParser BuildChangeTargetPacket(uint32_t targetObjectId) {
    PacketParser writer(C_CHANGE_TARGET);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildAttackPacket(uint32_t targetObjectId, uint8_t attackType, uint32_t time) {
    PacketParser writer(C_ATTACK);
    writer.WriteUInt32(targetObjectId);
    writer.WriteByte(attackType);
    writer.WriteUInt32(time);
    return writer;
}

PacketParser BuildUseSkillPacket(uint32_t skillId, uint32_t skillLevel, uint32_t targetObjectId) {
    PacketParser writer(C_USE_SKILL);
    writer.WriteUInt32(skillId);
    writer.WriteUInt32(skillLevel);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildTurnOffToggleSkillPacket(uint32_t skillId) {
    PacketParser writer(C_TURN_OFF_TOGGLE_SKILL);
    writer.WriteUInt32(skillId);
    return writer;
}

PacketParser BuildTurnOffAbnormalStatusPacket(uint32_t effectId) {
    PacketParser writer(C_TURN_OFF_ABNORMAL_STATUS);
    writer.WriteUInt32(effectId);
    return writer;
}

// --- 5. Inventário, Itens e Equipamento ---
PacketParser BuildUseItemPacket(uint32_t itemUniqueId) {
    PacketParser writer(C_USE_ITEM);
    writer.WriteUInt32(itemUniqueId);
    return writer;
}

PacketParser BuildUseEquipmentItemPacket(uint32_t itemUniqueId) {
    PacketParser writer(C_USE_EQUIPMENT_ITEM);
    writer.WriteUInt32(itemUniqueId);
    return writer;
}

PacketParser BuildMoveItemSlotPacket(uint32_t itemUniqueId, uint8_t destSlot) {
    PacketParser writer(C_MOVE_ITEM_TO_ANOTHER_SLOT);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteByte(destSlot);
    return writer;
}

PacketParser BuildMoveStackableItemPacket(uint32_t itemUniqueId, uint32_t count, uint8_t destSlot) {
    PacketParser writer(C_MOVE_STACKABLE_ITEM);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteUInt32(count);
    writer.WriteByte(destSlot);
    return writer;
}

PacketParser BuildSwapItemSlotPacket(uint8_t slot1, uint8_t slot2) {
    PacketParser writer(C_SWAP_ITEM_SLOT);
    writer.WriteByte(slot1);
    writer.WriteByte(slot2);
    return writer;
}

PacketParser BuildDestroyItemPacket(uint32_t itemUniqueId, uint32_t count) {
    PacketParser writer(C_DESTROY_ITEM);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteUInt32(count);
    return writer;
}

PacketParser BuildEnchantItemPacket(uint32_t targetItemUniqueId, uint32_t stoneItemUniqueId, uint32_t supplementUniqueId) {
    PacketParser writer(C_ENCHANT_ITEM);
    writer.WriteUInt32(targetItemUniqueId);
    writer.WriteUInt32(stoneItemUniqueId);
    writer.WriteUInt32(supplementUniqueId);
    return writer;
}

// --- 6. Diálogos com NPCs e Missões ---
PacketParser BuildStartDialogPacket(uint32_t targetObjectId) {
    PacketParser writer(C_START_DIALOG);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildEndDialogPacket(uint32_t targetObjectId) {
    PacketParser writer(C_END_DIALOG);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildHActionPacket(uint32_t targetObjectId, uint32_t dialogId, uint32_t questId) {
    PacketParser writer(C_HACTION);
    writer.WriteUInt32(targetObjectId);
    writer.WriteUInt32(dialogId);
    writer.WriteUInt32(questId);
    return writer;
}

PacketParser BuildGiveUpQuestPacket(uint32_t questId) {
    PacketParser writer(C_GIVE_UP_QUEST);
    writer.WriteUInt32(questId);
    return writer;
}

PacketParser BuildShareQuestPacket(uint32_t questId) {
    PacketParser writer(C_SHARE_QUEST);
    writer.WriteUInt32(questId);
    return writer;
}

// --- 7. Comunicação, Chat e Emoções ---
PacketParser BuildSayPacket(uint8_t chatType, const std::string& message) {
    PacketParser writer(C_SAY);
    writer.WriteByte(chatType);
    writer.WriteString(message);
    return writer;
}

PacketParser BuildWhisperPacket(const std::string& recipient, const std::string& message) {
    PacketParser writer(C_WHISPER);
    writer.WriteString(recipient);
    writer.WriteString(message);
    return writer;
}

PacketParser BuildActionPacket(uint32_t emotionId, uint32_t targetObjectId) {
    PacketParser writer(C_ACTION);
    writer.WriteUInt32(emotionId);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

// --- 8. Coleta e Crafting ---
PacketParser BuildGatherPacket(uint32_t targetObjectId) {
    PacketParser writer(C_GATHER);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildCombinePacket(uint32_t recipeId, uint32_t targetObjectId) {
    PacketParser writer(C_COMBINE);
    writer.WriteUInt32(recipeId);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

// --- 9. Saque (Loot) ---
PacketParser BuildLootPacket(uint32_t targetObjectId) {
    PacketParser writer(C_LOOT);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildLootItemPacket(uint32_t targetObjectId, uint32_t itemIndex) {
    PacketParser writer(C_LOOT_ITEM);
    writer.WriteUInt32(targetObjectId);
    writer.WriteUInt32(itemIndex);
    return writer;
}

// --- 10. Trocas e Comércio ---
PacketParser BuildAskExchangePacket(uint32_t targetObjectId) {
    PacketParser writer(C_ASK_XCHG);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

PacketParser BuildAddExchangeItemPacket(uint32_t itemUniqueId, uint32_t count) {
    PacketParser writer(C_ADD_XCHG);
    writer.WriteUInt32(itemUniqueId);
    writer.WriteUInt32(count);
    return writer;
}

PacketParser BuildExchangeGoldPacket(uint64_t kinahAmount) {
    PacketParser writer(C_XCHG_GOLD);
    writer.WriteUInt64(kinahAmount);
    return writer;
}

PacketParser BuildCheckExchangePacket() {
    PacketParser writer(C_CHECK_XCHG);
    return writer;
}

PacketParser BuildAcceptExchangePacket() {
    PacketParser writer(C_ACCEPT_XCHG);
    return writer;
}

PacketParser BuildCancelExchangePacket() {
    PacketParser writer(C_CANCEL_XCHG);
    return writer;
}

PacketParser BuildBuySellPacket(uint32_t npcObjectId, const std::vector<std::pair<uint32_t, uint32_t>>& itemsToBuy) {
    PacketParser writer(C_BUY_SELL);
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
PacketParser BuildInviteToGroupPacket(const std::string& targetPlayerName, uint8_t inviteType) {
    PacketParser writer(C_PARTY_BY_NAME);
    writer.WriteByte(inviteType);
    writer.WriteString(targetPlayerName);
    return writer;
}

PacketParser BuildGroupLootPacket(uint32_t groupId, uint32_t itemId, uint32_t npcObjId, uint8_t distMode, uint32_t roll, uint64_t bid) {
    PacketParser writer(C_GROUP_ITEM_DIST);
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

PacketParser BuildShowBrandPacket(uint32_t brandId, uint32_t targetObjectId, uint32_t action) {
    PacketParser writer(C_TACTICS_SIGN);
    writer.WriteUInt32(action);
    writer.WriteUInt32(brandId);
    writer.WriteUInt32(targetObjectId);
    return writer;
}

}

