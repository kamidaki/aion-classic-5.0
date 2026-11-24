#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>
#include "AionPacketOpcodes.h"
#include "../game/Player.h"

// Buffer utilitário para serialização binária de pacotes do cliente
class PacketParser {
public:
    PacketParser(uint16_t opcode) {
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

    void WriteWStringFixed(const std::wstring& str, size_t maxChars) {
        size_t count = 0;
        for (wchar_t wc : str) {
            if (count >= maxChars) break;
            WriteUInt16(static_cast<uint16_t>(wc));
            count++;
        }
        while (count < maxChars) {
            WriteUInt16(0);
            count++;
        }
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
PacketParser BuildVersionPacket(uint32_t version = 207, uint32_t subVersion = 207);
PacketParser BuildLogoutPacket();
PacketParser BuildAskQuitPacket();
PacketParser BuildReadyToQuitPacket();
PacketParser BuildDeadRestartPacket();
PacketParser BuildL2AuthLoginPacket(const std::string& account, const std::string& token);
PacketParser BuildAlivePacket(uint32_t clientTime);
PacketParser BuildSyncTimePacket(uint32_t clientTime);
PacketParser BuildReconnectAuthPacket(uint32_t accountId, const std::string& token);

// --- 2. Seleção e Criação de Personagem ---
PacketParser BuildCharacterListPacket();
PacketParser BuildCheckNicknamePacket(const std::string& name);
PacketParser BuildEnterCharCreationScreenPacket(uint32_t accountId, const std::string& accountName);
PacketParser BuildCreateCharacterPacket(uint32_t accountId, const std::string& accountName, const std::string& charName, uint32_t race, uint32_t gender, uint32_t playerClass, const PlayerAppearance& appearance, uint8_t createType = 0);
PacketParser BuildCreateCharacterPacket(const std::string& name, uint8_t race, uint8_t gender, uint8_t playerClass, uint8_t voice, const std::vector<uint8_t>& appearanceData);
PacketParser BuildDeleteCharacterPacket(uint32_t characterId);
PacketParser BuildRestoreCharacterPacket(uint32_t characterId);
PacketParser BuildEnterWorldPacket(uint32_t characterId);
PacketParser BuildLevelReadyPacket();

// --- 3. Movimentação, Posição e Voo ---
// Movimentação WASD vetorial e parada
PacketParser BuildMoveNewPacket(float x, float y, float z, uint8_t heading, uint8_t moveMask = MovementMask::IMMEDIATE, float vectorX = 0.0f, float vectorY = 0.0f, float vectorZ = 0.0f);
// Movimentação click-to-move absoluta
PacketParser BuildMoveNewAbsolutePacket(float x, float y, float z, uint8_t heading, float targetX, float targetY, float targetZ);
// Voo e planeio (Glide)
PacketParser BuildMoveNewGlidePacket(float x, float y, float z, uint8_t heading, float vectorX, float vectorY, float vectorZ, uint8_t glideFlag, uint8_t geyserLocationId = 0);
// Elevadores e veículos
PacketParser BuildMoveNewVehiclePacket(float x, float y, float z, uint8_t heading, float vehicleX, float vehicleY, float vehicleZ, uint32_t unk1 = 0, uint32_t unk2 = 0);

PacketParser BuildPathFlyPacket(float x, float y, float z, uint8_t flyState);
PacketParser BuildWindPathPacket(uint32_t windStreamId, uint32_t distance, uint8_t state = 1);
PacketParser BuildBlinkPacket(float x, float y, float z, uint8_t heading);
PacketParser BuildChangeDirectionPacket(uint8_t heading);

// --- 4. Combate, Habilidades e Alvos ---
PacketParser BuildChangeTargetPacket(uint32_t targetObjectId);
PacketParser BuildAttackPacket(uint32_t targetObjectId, uint8_t attackType, uint32_t time);
PacketParser BuildUseSkillPacket(uint32_t skillId, uint32_t skillLevel, uint32_t targetObjectId);
PacketParser BuildTurnOffToggleSkillPacket(uint32_t skillId);
PacketParser BuildTurnOffAbnormalStatusPacket(uint32_t effectId);

// --- 5. Inventário, Itens e Equipamento ---
PacketParser BuildUseItemPacket(uint32_t itemUniqueId);
PacketParser BuildUseEquipmentItemPacket(uint32_t itemUniqueId);
PacketParser BuildMoveItemSlotPacket(uint32_t itemUniqueId, uint8_t destSlot);
PacketParser BuildMoveStackableItemPacket(uint32_t itemUniqueId, uint32_t count, uint8_t destSlot);
PacketParser BuildSwapItemSlotPacket(uint8_t slot1, uint8_t slot2);
PacketParser BuildDestroyItemPacket(uint32_t itemUniqueId, uint32_t count);
PacketParser BuildEnchantItemPacket(uint32_t targetItemUniqueId, uint32_t stoneItemUniqueId, uint32_t supplementUniqueId);

// --- 6. Diálogos com NPCs e Missões ---
PacketParser BuildStartDialogPacket(uint32_t targetObjectId);
PacketParser BuildEndDialogPacket(uint32_t targetObjectId);
PacketParser BuildHActionPacket(uint32_t targetObjectId, uint32_t dialogId, uint32_t questId);
PacketParser BuildGiveUpQuestPacket(uint32_t questId);
PacketParser BuildShareQuestPacket(uint32_t questId);

// --- 7. Comunicação, Chat e Emoções ---
PacketParser BuildSayPacket(uint8_t chatType, const std::string& message);
PacketParser BuildWhisperPacket(const std::string& recipient, const std::string& message);
PacketParser BuildActionPacket(uint32_t emotionId, uint32_t targetObjectId);

// Formatadores canônicos de hiperlinks no chat
std::string FormatItemLink(uint32_t itemId, const std::string& itemName);
std::string FormatPosLink(uint32_t mapId, float x, float y, float z);
std::string FormatQuestLink(uint32_t questId, const std::string& questTitle);

// --- 8. Grupos, Alianças e Marcação Tática ---
PacketParser BuildInviteToGroupPacket(const std::string& targetPlayerName, uint8_t inviteType = 0);
PacketParser BuildGroupLootPacket(uint32_t groupId, uint32_t itemId, uint32_t npcObjId, uint8_t distMode, uint32_t roll, uint64_t bid);
PacketParser BuildShowBrandPacket(uint32_t brandId, uint32_t targetObjectId, uint32_t action = 0);

// --- 9. Coleta e Crafting ---
PacketParser BuildGatherPacket(uint32_t targetObjectId);
PacketParser BuildCombinePacket(uint32_t recipeId, uint32_t targetObjectId);

// --- 10. Saque (Loot) ---
PacketParser BuildLootPacket(uint32_t targetObjectId);
PacketParser BuildLootItemPacket(uint32_t targetObjectId, uint32_t itemIndex);

// --- 11. Trocas e Comércio ---
PacketParser BuildAskExchangePacket(uint32_t targetObjectId);
PacketParser BuildAddExchangeItemPacket(uint32_t itemUniqueId, uint32_t count);
PacketParser BuildExchangeGoldPacket(uint64_t kinahAmount);
PacketParser BuildCheckExchangePacket();
PacketParser BuildAcceptExchangePacket();
PacketParser BuildCancelExchangePacket();
PacketParser BuildBuySellPacket(uint32_t npcObjectId, const std::vector<std::pair<uint32_t, uint32_t>>& itemsToBuy);

}

