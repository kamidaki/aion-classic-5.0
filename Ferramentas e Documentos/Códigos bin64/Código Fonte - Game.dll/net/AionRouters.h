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
class AuthRouter : public BaseReceiveRouter, public BaseSendRouter {
public:
    AuthRouter();
    virtual ~AuthRouter();

    virtual bool Initialize() override;
    virtual void Shutdown() override;
    virtual void OnReceive(const uint8_t* pData, size_t size) override;
    virtual bool SendRaw(const uint8_t* pData, size_t size) override;

    bool Authenticate(const std::string& account, const std::string& token);
    bool IsAuthenticated() const { return m_bAuthenticated; }

private:
    bool m_bAuthenticated;
    std::string m_account;
};

// .?AVHQRouter@@
class HQRouter : public BaseReceiveRouter, public BaseSendRouter {
public:
    HQRouter();
    virtual ~HQRouter();

    virtual bool Initialize() override;
    virtual void Shutdown() override;
    virtual void OnReceive(const uint8_t* pData, size_t size) override;
    virtual bool SendRaw(const uint8_t* pData, size_t size) override;

    bool SendHQMessage(uint32_t guildId, uint16_t opcode, const uint8_t* pData, size_t size);
    void RegisterHQHandler(uint16_t opcode, std::function<void(uint32_t, const uint8_t*, size_t)> handler);

private:
    std::unordered_map<uint16_t, std::function<void(uint32_t, const uint8_t*, size_t)>> m_hqHandlers;
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

    bool Connect(const char* host, uint16_t port);
    void Disconnect();
    bool Send(const uint8_t* pData, size_t size);
    bool IsConnected() const { return m_bConnected; }

private:
    SOCKET m_socket;
    bool m_bConnected;
};

// .?AVPacketParserHandler@@
class PacketParserHandler {
public:
    PacketParserHandler();
    PacketParserHandler(const uint8_t* pData, size_t size);
    virtual ~PacketParserHandler();

    bool ParsePacket(const uint8_t* pData, size_t size, uint16_t& outOpcode, const uint8_t*& outPayload, size_t& outPayloadSize);

    bool HasBytes(size_t count) const { return (m_offset + count) <= m_size; }
    uint8_t ReadByte() { return HasBytes(1) ? m_pData[m_offset++] : 0; }
    uint16_t ReadUInt16() {
        if (!HasBytes(2)) return 0;
        uint16_t val = (uint16_t)m_pData[m_offset] | ((uint16_t)m_pData[m_offset + 1] << 8);
        m_offset += 2;
        return val;
    }
    uint32_t ReadUInt32() {
        if (!HasBytes(4)) return 0;
        uint32_t val = (uint32_t)m_pData[m_offset] | ((uint32_t)m_pData[m_offset + 1] << 8) |
                       ((uint32_t)m_pData[m_offset + 2] << 16) | ((uint32_t)m_pData[m_offset + 3] << 24);
        m_offset += 4;
        return val;
    }
    uint64_t ReadUInt64() {
        if (!HasBytes(8)) return 0;
        uint64_t val = 0;
        for (int i = 0; i < 8; ++i) val |= ((uint64_t)m_pData[m_offset + i] << (i * 8));
        m_offset += 8;
        return val;
    }
    float ReadFloat() {
        union { float f; uint32_t u; } c;
        c.u = ReadUInt32();
        return c.f;
    }
    std::string ReadString() {
        std::string s;
        while (HasBytes(1)) {
            char ch = (char)ReadByte();
            if (ch == 0) break;
            s.push_back(ch);
        }
        return s;
    }

private:
    const uint8_t* m_pData;
    size_t m_size;
    size_t m_offset;
};
