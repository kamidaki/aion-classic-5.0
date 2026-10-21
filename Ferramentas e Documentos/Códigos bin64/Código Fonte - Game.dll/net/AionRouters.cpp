#include "AionRouters.h"
#include "../core/GameLog.h"

// BaseRouter
BaseRouter::BaseRouter() : m_bActive(false) {}
BaseRouter::~BaseRouter() {}
bool BaseRouter::Initialize() { m_bActive = true; return true; }
void BaseRouter::Shutdown() { m_bActive = false; }

// BaseSendRouter
BaseSendRouter::BaseSendRouter() : m_bytesSent(0) {}
BaseSendRouter::~BaseSendRouter() {}
bool BaseSendRouter::SendRaw(const uint8_t* pData, size_t size) {
    if (!m_bActive || !pData || size == 0) return false;
    m_bytesSent += size;
    return true;
}

// BaseReceiveRouter
BaseReceiveRouter::BaseReceiveRouter() : m_bytesReceived(0) {}
BaseReceiveRouter::~BaseReceiveRouter() {}
void BaseReceiveRouter::OnReceive(const uint8_t* pData, size_t size) {
    if (!m_bActive || !pData || size == 0) return;
    m_bytesReceived += size;
}

// AuthRouter
AuthRouter::AuthRouter() : m_bAuthenticated(false) {}
AuthRouter::~AuthRouter() {}
bool AuthRouter::Authenticate(const std::string& account, const std::string& token) {
    m_account = account;
    m_bAuthenticated = true;
    GameLog_Info("AuthRouter: Conta [%s] autenticada via token de sessao.", account.c_str());
    return true;
}

// ServerToClientRouter
ServerToClientRouter::ServerToClientRouter() {}
ServerToClientRouter::~ServerToClientRouter() { m_handlers.clear(); }
void ServerToClientRouter::RegisterHandler(uint16_t opcode, std::function<void(const uint8_t*, size_t)> handler) {
    m_handlers[opcode] = handler;
}
void ServerToClientRouter::OnReceive(const uint8_t* pData, size_t size) {
    BaseReceiveRouter::OnReceive(pData, size);
    if (size < 2) return;
    uint16_t opcode = *reinterpret_cast<const uint16_t*>(pData);
    auto it = m_handlers.find(opcode);
    if (it != m_handlers.end() && it->second) {
        it->second(pData + 2, size - 2);
    }
}

// SocketHandler
SocketHandler::SocketHandler() {}
SocketHandler::~SocketHandler() {}
void SocketHandler::OnConnect() { GameLog_Info("SocketHandler: OnConnect"); }
void SocketHandler::OnDisconnect() { GameLog_Info("SocketHandler: OnDisconnect"); }
void SocketHandler::OnData(const uint8_t* pData, size_t size) {}

// GameSocketHandler
GameSocketHandler::GameSocketHandler() : m_socket(INVALID_SOCKET), m_bConnected(false) {}
GameSocketHandler::~GameSocketHandler() { Disconnect(); }
void GameSocketHandler::OnConnect() {
    SocketHandler::OnConnect();
    GameLog_Info("GameSocketHandler: Conexão de jogo estabelecida.");
}
void GameSocketHandler::OnDisconnect() {
    SocketHandler::OnDisconnect();
    GameLog_Info("GameSocketHandler: Conexão de jogo encerrada.");
}
void GameSocketHandler::OnData(const uint8_t* pData, size_t size) {
    SocketHandler::OnData(pData, size);
}
bool GameSocketHandler::Connect(const char* host, uint16_t port) {
    m_bConnected = true;
    GameLog_Info("GameSocketHandler conectado a %s:%u", host, port);
    return true;
}
void GameSocketHandler::Disconnect() {
    if (m_bConnected) {
        m_bConnected = false;
        GameLog_Info("GameSocketHandler desconectado.");
    }
}
bool GameSocketHandler::Send(const uint8_t* pData, size_t size) {
    return m_bConnected && pData && size > 0;
}

// PacketParserHandler
PacketParserHandler::PacketParserHandler() : m_pData(nullptr), m_size(0), m_offset(0) {}
PacketParserHandler::PacketParserHandler(const uint8_t* pData, size_t size) : m_pData(pData), m_size(size), m_offset(0) {}
PacketParserHandler::~PacketParserHandler() {}
bool PacketParserHandler::ParsePacket(const uint8_t* pData, size_t size, uint16_t& outOpcode, const uint8_t*& outPayload, size_t& outPayloadSize) {
    if (!pData || size < 4) return false;
    uint16_t packetSize = *reinterpret_cast<const uint16_t*>(pData);
    if (size < packetSize) return false;
    outOpcode = *reinterpret_cast<const uint16_t*>(pData + 2);
    outPayload = pData + 4;
    outPayloadSize = packetSize - 4;
    return true;
}
