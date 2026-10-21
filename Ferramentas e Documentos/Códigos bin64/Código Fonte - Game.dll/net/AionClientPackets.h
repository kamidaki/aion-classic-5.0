#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>
#include "AionPacketOpcodes.h"

// Buffer utilitário para serialização binária de pacotes do cliente
class ByteBufferWriter {
public:
    ByteBufferWriter(uint16_t opcode) {
        WriteUInt16(opcode);
    }

    void WriteByte(uint8_t val) {
        m_buffer.push_back(val);
    }

    void WriteUInt16(uint16_t val) {
        m_buffer.push_back(static_cast<uint8_t>(val & 0xFF));
        m_buffer.push_back(static_cast<uint8_t>((val >> 8) & 0xFF));
    }

    void WriteUInt32(uint32_t val) {
        m_buffer.push_back(static_cast<uint8_t>(val & 0xFF));
        m_buffer.push_back(static_cast<uint8_t>((val >> 8) & 0xFF));
        m_buffer.push_back(static_cast<uint8_t>((val >> 16) & 0xFF));
        m_buffer.push_back(static_cast<uint8_t>((val >> 24) & 0xFF));
    }

    void WriteUInt64(uint64_t val) {
        for (int i = 0; i < 8; ++i) {
            m_buffer.push_back(static_cast<uint8_t>((val >> (i * 8)) & 0xFF));
        }
    }

    void WriteFloat(float val) {
        union { float f; uint32_t u; } converter;
        converter.f = val;
        WriteUInt32(converter.u);
    }

    void WriteString(const std::string& str) {
        for (char c : str) {
            WriteByte(static_cast<uint8_t>(c));
        }
        WriteByte(0);
    }

    void WriteWString(const std::wstring& str) {
        for (wchar_t wc : str) {
            WriteUInt16(static_cast<uint16_t>(wc));
        }
        WriteUInt16(0);
    }

    void WriteBytes(const uint8_t* pData, size_t len) {
        m_buffer.insert(m_buffer.end(), pData, pData + len);
    }

    const uint8_t* GetData() const { return m_buffer.data(); }
    size_t GetSize() const { return m_buffer.size(); }
    const std::vector<uint8_t>& GetBuffer() const { return m_buffer; }

private:
    std::vector<uint8_t> m_buffer;
};

// --- Máscaras Canônicas de Movimento (MovementMask.java) ---
namespace MovementMask {
#ifdef ABSOLUTE
#undef ABSOLUTE
#endif
    constexpr uint8_t IMMEDIATE = 0x00; // Parado / Ação Instantânea
    constexpr uint8_t GLIDE     = 0x04; // Planando com Asas
    constexpr uint8_t FALL      = 0x08; // Queda Livre
    constexpr uint8_t VEHICLE   = 0x10; // Sobre Objeto em Movimento / Elevador
    constexpr uint8_t ABSOLUTE  = 0x20; // Destino Absoluto (Click-to-Move)
    constexpr uint8_t MANUAL    = 0x40; // Mudança Manual de Vetor / WASD
    constexpr uint8_t POSITION  = 0x80; // Atualização de Coordenadas
}

// --- Tipos Canônicos de Chat (ChatType.java) ---
enum class EChatType : uint8_t {
    Normal      = 0,  // Say (Branco)
    Npc         = 1,  // Diálogo NPC
    Shout       = 3,  // Grito / Região (Laranja)
    Whisper     = 4,  // Sussurro (Verde)
    Group       = 5,  // Grupo (Azul)
    Alliance    = 6,  // Aliança / Force (Aqua)
    GroupLeader = 7,  // Alerta de Líder (Laranja)
    League      = 8,  // Liga / União (Azul Escuro)
    Legion      = 10, // Legião / Clã (Verde)
    Command     = 24  // Comando de Comandante (Amarelo)
};

namespace AionPackets {

// --- 1. Autenticação, Ciclo de Vida e Sessão ---
ByteBufferWriter BuildVersionPacket(uint32_t version = 207, uint32_t subVersion = 207);
ByteBufferWriter BuildLogoutPacket();
ByteBufferWriter BuildAskQuitPacket();
ByteBufferWriter BuildReadyToQuitPacket();
ByteBufferWriter BuildDeadRestartPacket();
ByteBufferWriter BuildL2AuthLoginPacket(const std::string& account, const std::string& token);
ByteBufferWriter BuildAlivePacket(uint32_t clientTime);
ByteBufferWriter BuildSyncTimePacket(uint32_t clientTime);
ByteBufferWriter BuildReconnectAuthPacket(uint32_t accountId, const std::string& token);

// --- 2. Seleção e Criação de Personagem ---
ByteBufferWriter BuildCharacterListPacket();
ByteBufferWriter BuildCheckNicknamePacket(const std::string& name);
ByteBufferWriter BuildCreateCharacterPacket(const std::string& name, uint8_t race, uint8_t gender, uint8_t playerClass, uint8_t voice, const std::vector<uint8_t>& appearanceData);
ByteBufferWriter BuildDeleteCharacterPacket(uint32_t characterId);
ByteBufferWriter BuildRestoreCharacterPacket(uint32_t characterId);
ByteBufferWriter BuildEnterWorldPacket(uint32_t characterId);
ByteBufferWriter BuildLevelReadyPacket();

// --- 3. Movimentação, Posição e Voo ---
// Movimentação WASD vetorial e parada
ByteBufferWriter BuildMoveNewPacket(float x, float y, float z, uint8_t heading, uint8_t moveMask = MovementMask::IMMEDIATE, float vectorX = 0.0f, float vectorY = 0.0f, float vectorZ = 0.0f);
// Movimentação click-to-move absoluta
ByteBufferWriter BuildMoveNewAbsolutePacket(float x, float y, float z, uint8_t heading, float targetX, float targetY, float targetZ);
// Voo e planeio (Glide)
ByteBufferWriter BuildMoveNewGlidePacket(float x, float y, float z, uint8_t heading, float vectorX, float vectorY, float vectorZ, uint8_t glideFlag, uint8_t geyserLocationId = 0);
// Elevadores e veículos
ByteBufferWriter BuildMoveNewVehiclePacket(float x, float y, float z, uint8_t heading, float vehicleX, float vehicleY, float vehicleZ, uint32_t unk1 = 0, uint32_t unk2 = 0);

ByteBufferWriter BuildPathFlyPacket(float x, float y, float z, uint8_t flyState);
ByteBufferWriter BuildWindPathPacket(uint32_t windStreamId, uint32_t distance, uint8_t state = 1);
ByteBufferWriter BuildBlinkPacket(float x, float y, float z, uint8_t heading);
ByteBufferWriter BuildChangeDirectionPacket(uint8_t heading);

// --- 4. Combate, Habilidades e Alvos ---
ByteBufferWriter BuildChangeTargetPacket(uint32_t targetObjectId);
ByteBufferWriter BuildAttackPacket(uint32_t targetObjectId, uint8_t attackType, uint32_t time);
ByteBufferWriter BuildUseSkillPacket(uint32_t skillId, uint32_t skillLevel, uint32_t targetObjectId);
ByteBufferWriter BuildTurnOffToggleSkillPacket(uint32_t skillId);
ByteBufferWriter BuildTurnOffAbnormalStatusPacket(uint32_t effectId);

// --- 5. Inventário, Itens e Equipamento ---
ByteBufferWriter BuildUseItemPacket(uint32_t itemUniqueId);
ByteBufferWriter BuildUseEquipmentItemPacket(uint32_t itemUniqueId);
ByteBufferWriter BuildMoveItemSlotPacket(uint32_t itemUniqueId, uint8_t destSlot);
ByteBufferWriter BuildMoveStackableItemPacket(uint32_t itemUniqueId, uint32_t count, uint8_t destSlot);
ByteBufferWriter BuildSwapItemSlotPacket(uint8_t slot1, uint8_t slot2);
ByteBufferWriter BuildDestroyItemPacket(uint32_t itemUniqueId, uint32_t count);
ByteBufferWriter BuildEnchantItemPacket(uint32_t targetItemUniqueId, uint32_t stoneItemUniqueId, uint32_t supplementUniqueId);

// --- 6. Diálogos com NPCs e Missões ---
ByteBufferWriter BuildStartDialogPacket(uint32_t targetObjectId);
ByteBufferWriter BuildEndDialogPacket(uint32_t targetObjectId);
ByteBufferWriter BuildHActionPacket(uint32_t targetObjectId, uint32_t dialogId, uint32_t questId);
ByteBufferWriter BuildGiveUpQuestPacket(uint32_t questId);
ByteBufferWriter BuildShareQuestPacket(uint32_t questId);

// --- 7. Comunicação, Chat e Emoções ---
ByteBufferWriter BuildSayPacket(uint8_t chatType, const std::string& message);
ByteBufferWriter BuildWhisperPacket(const std::string& recipient, const std::string& message);
ByteBufferWriter BuildActionPacket(uint32_t emotionId, uint32_t targetObjectId);

// Formatadores canônicos de hiperlinks no chat
std::string FormatItemLink(uint32_t itemId, const std::string& itemName);
std::string FormatPosLink(uint32_t mapId, float x, float y, float z);
std::string FormatQuestLink(uint32_t questId, const std::string& questTitle);

// --- 8. Grupos, Alianças e Marcação Tática ---
ByteBufferWriter BuildInviteToGroupPacket(const std::string& targetPlayerName, uint8_t inviteType = 0);
ByteBufferWriter BuildGroupLootPacket(uint32_t groupId, uint32_t itemId, uint32_t npcObjId, uint8_t distMode, uint32_t roll, uint64_t bid);
ByteBufferWriter BuildShowBrandPacket(uint32_t brandId, uint32_t targetObjectId, uint32_t action = 0);

// --- 9. Coleta e Crafting ---
ByteBufferWriter BuildGatherPacket(uint32_t targetObjectId);
ByteBufferWriter BuildCombinePacket(uint32_t recipeId, uint32_t targetObjectId);

// --- 10. Saque (Loot) ---
ByteBufferWriter BuildLootPacket(uint32_t targetObjectId);
ByteBufferWriter BuildLootItemPacket(uint32_t targetObjectId, uint32_t itemIndex);

// --- 11. Trocas e Comércio ---
ByteBufferWriter BuildAskExchangePacket(uint32_t targetObjectId);
ByteBufferWriter BuildAddExchangeItemPacket(uint32_t itemUniqueId, uint32_t count);
ByteBufferWriter BuildExchangeGoldPacket(uint64_t kinahAmount);
ByteBufferWriter BuildCheckExchangePacket();
ByteBufferWriter BuildAcceptExchangePacket();
ByteBufferWriter BuildCancelExchangePacket();
ByteBufferWriter BuildBuySellPacket(uint32_t npcObjectId, const std::vector<std::pair<uint32_t, uint32_t>>& itemsToBuy);

}

