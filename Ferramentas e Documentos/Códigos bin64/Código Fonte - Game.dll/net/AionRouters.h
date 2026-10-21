#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>
#include <functional>

// Classes canônicas de roteamento e sockets extraídas do RTTI
// .?AVBaseRouter@@
class BaseRouter {
public:
    BaseRouter();
    virtual ~BaseRouter();

    virtual bool Initialize();
    virtual void Shutdown();
    virtual bool IsActive() const { return m_bActive; }

protected:
    bool m_bActive;
};

// .?AVBaseSendRouter@@
class BaseSendRouter : public BaseRouter {
public:
    BaseSendRouter();
    virtual ~BaseSendRouter();

    virtual bool SendRaw(const uint8_t* pData, size_t size);

protected:
    uint64_t m_bytesSent;
};

// .?AVBaseReceiveRouter@@
class BaseReceiveRouter : public BaseRouter {
public:
    BaseReceiveRouter();
    virtual ~BaseReceiveRouter();

    virtual void OnReceive(const uint8_t* pData, size_t size);

protected:
    uint64_t m_bytesReceived;
};

// .?AVAuthRouter@@
class AuthRouter : public BaseRouter {
public:
    AuthRouter();
    virtual ~AuthRouter();

    bool Authenticate(const std::string& account, const std::string& token);
    bool IsAuthenticated() const { return m_bAuthenticated; }

private:
    bool m_bAuthenticated;
    std::string m_account;
};

// .?AVServerToClientRouter@@
class ServerToClientRouter : public BaseReceiveRouter {
public:
    ServerToClientRouter();
    virtual ~ServerToClientRouter();

    virtual void OnReceive(const uint8_t* pData, size_t size) override;
    void RegisterHandler(uint16_t opcode, std::function<void(const uint8_t*, size_t)> handler);

private:
    std::unordered_map<uint16_t, std::function<void(const uint8_t*, size_t)>> m_handlers;
};

// .?AVIOSocket@@
class IOSocket {
public:
    IOSocket();
    virtual ~IOSocket();

    virtual bool Connect(const char* host, uint16_t port);
    virtual void Disconnect();
    virtual bool Send(const uint8_t* pData, size_t size);
    virtual int Receive(uint8_t* pBuffer, size_t maxLen);

    bool IsConnected() const { return m_bConnected; }

protected:
    SOCKET m_socket;
    bool m_bConnected;
};

// .?AVSocketHandler@@
class SocketHandler {
public:
    SocketHandler();
    virtual ~SocketHandler();

    virtual void OnConnect();
    virtual void OnDisconnect();
    virtual void OnData(const uint8_t* pData, size_t size);
};

// .?AVGameSocketHandler@@
class GameSocketHandler : public SocketHandler {
public:
    GameSocketHandler();
    virtual ~GameSocketHandler();

    virtual void OnConnect() override;
    virtual void OnDisconnect() override;
    virtual void OnData(const uint8_t* pData, size_t size) override;

    IOSocket* GetSocket() { return &m_socket; }

private:
    IOSocket m_socket;
};

// .?AVPacketParserHandler@@
class PacketParserHandler {
public:
    PacketParserHandler();
    virtual ~PacketParserHandler();

    bool ParsePacket(const uint8_t* pData, size_t size, uint16_t& outOpcode, const uint8_t*& outPayload, size_t& outPayloadSize);
};
