#include "ClientToServerRouter.h"
#include "../core/GameLog.h"

typedef bool (*LA_SendNativePacket_t)(uint16_t opcode, const uint8_t* data, size_t len);
static LA_SendNativePacket_t s_pfnSendNative = nullptr;

bool ClientToServerRouter::Initialize() {
    GameLog_Info("ClientToServerRouter::Initialize vinculando rede de baixo nivel...");

    HMODULE hVersion = GetModuleHandleA("Version.dll");
    if (!hVersion) hVersion = GetModuleHandleA("LostSocket.dll");

    if (hVersion) {
        s_pfnSendNative = (LA_SendNativePacket_t)GetProcAddress(hVersion, "LA_SendNativePacket");
        if (s_pfnSendNative) {
            GameLog_Info("ClientToServerRouter: Ponte LA_SendNativePacket resolvida com sucesso.");
        }
    }

    m_bConnected = true;
    GameLog_Info("ClientToServerRouter inicializado com sucesso.");
    return true;
}

bool ClientToServerRouter::Send(const PacketParser& writer) {
    if (writer.GetSize() < 2) return false;
    uint16_t opcode = *reinterpret_cast<const uint16_t*>(writer.GetData());
    return SendOpcode(opcode, writer.GetData() + 2, writer.GetSize() - 2);
}

bool ClientToServerRouter::SendRaw(const uint8_t* pData, size_t size) {
    if (!pData || size < 2) return false;
    uint16_t opcode = *reinterpret_cast<const uint16_t*>(pData);
    return SendOpcode(opcode, pData + 2, size - 2);
}

bool ClientToServerRouter::SendOpcode(uint16_t opcode, const uint8_t* pData, size_t size) {
    BaseSendRouter::SendRaw(pData, size);
    if (s_pfnSendNative) {
        return s_pfnSendNative(opcode, pData, size);
    }
    GameLog_Info("ClientToServerRouter::SendOpcode [Opcode: 0x%04X, Size: %zu]", opcode, size);
    return true;
}

void ClientToServerRouter::RouteIncomingPacket(uint16_t opcode, const uint8_t* pData, size_t size) {
    auto it = m_serverPacketHandlers.find(opcode);
    if (it != m_serverPacketHandlers.end()) {
        it->second(pData, size);
    }
}

void ClientToServerRouter::RegisterServerPacketHandler(uint16_t opcode, std::function<void(const uint8_t*, size_t)> handler) {
    m_serverPacketHandlers[opcode] = handler;
}

void ClientToServerRouter::Shutdown() {
    m_serverPacketHandlers.clear();
    m_bConnected = false;
    GameLog_Info("ClientToServerRouter finalizado.");
}
