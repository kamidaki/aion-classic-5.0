#pragma once
#include <windows.h>
#include <cstdint>
#include <unordered_map>
#include <functional>
#include "AionPacketOpcodes.h"
#include "AionClientPackets.h"

// Classe canônica de roteamento de pacotes do cliente para o servidor extraída do RTTI do game.dll (.?AVClientToServerRouter@@)
class ClientToServerRouter {
public:
    static ClientToServerRouter& GetInstance() {
        static ClientToServerRouter instance;
        return instance;
    }

    bool Initialize();
    void Shutdown();

    // Envio de pacotes do cliente para o servidor
    bool Send(const ByteBufferWriter& writer);
    bool SendRaw(uint16_t opcode, const uint8_t* pData, size_t size);

    // Despacho de pacotes recebidos do servidor
    void RouteIncomingPacket(uint16_t opcode, const uint8_t* pData, size_t size);
    void RegisterServerPacketHandler(uint16_t opcode, std::function<void(const uint8_t*, size_t)> handler);

    bool IsConnected() const { return m_bConnected; }

private:
    ClientToServerRouter() : m_bConnected(false) {}
    bool m_bConnected;
    std::unordered_map<uint16_t, std::function<void(const uint8_t*, size_t)>> m_serverPacketHandlers;
};
