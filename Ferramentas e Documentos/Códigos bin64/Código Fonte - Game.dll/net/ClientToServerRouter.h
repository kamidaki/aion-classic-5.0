#pragma once
#include <windows.h>
#include <cstdint>
#include <unordered_map>
#include <functional>
#include "AionPacketOpcodes.h"
#include "AionClientPackets.h"
#include "AionRouters.h"

// Classe canônica de roteamento de pacotes do cliente para o servidor extraída do RTTI do game.dll (.?AVClientToServerRouter@@)
class ClientToServerRouter : public BaseSendRouter {
public:
    static ClientToServerRouter& GetInstance() {
        static ClientToServerRouter instance;
        return instance;
    }

    virtual bool Initialize() override;
    virtual void Shutdown() override;

    // Envio de pacotes do cliente para o servidor
    bool Send(const PacketParser& writer);
    virtual bool SendRaw(const uint8_t* pData, size_t size) override;
    bool SendOpcode(uint16_t opcode, const uint8_t* pData, size_t size);

    // Despacho de pacotes recebidos do servidor
    void RouteIncomingPacket(uint16_t opcode, const uint8_t* pData, size_t size);
    void RegisterServerPacketHandler(uint16_t opcode, std::function<void(const uint8_t*, size_t)> handler);

    bool IsConnected() const { return m_bConnected; }

private:
    ClientToServerRouter() : m_bConnected(false) {}
    bool m_bConnected;
    std::unordered_map<uint16_t, std::function<void(const uint8_t*, size_t)>> m_serverPacketHandlers;
};

