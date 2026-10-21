#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>

// Leitor binário para decodificação de pacotes recebidos do servidor (S_*)
class ByteBufferReader {
public:
    ByteBufferReader(const uint8_t* pData, size_t size)
        : m_pData(pData)
        , m_size(size)
        , m_offset(0)
    {}

    bool HasBytes(size_t count) const {
        return (m_offset + count) <= m_size;
    }

    uint8_t ReadByte() {
        if (!HasBytes(1)) return 0;
        return m_pData[m_offset++];
    }

    uint16_t ReadUInt16() {
        if (!HasBytes(2)) return 0;
        uint16_t val = static_cast<uint16_t>(m_pData[m_offset]) |
                       (static_cast<uint16_t>(m_pData[m_offset + 1]) << 8);
        m_offset += 2;
        return val;
    }

    uint32_t ReadUInt32() {
        if (!HasBytes(4)) return 0;
        uint32_t val = static_cast<uint32_t>(m_pData[m_offset]) |
                       (static_cast<uint32_t>(m_pData[m_offset + 1]) << 8) |
                       (static_cast<uint32_t>(m_pData[m_offset + 2]) << 16) |
                       (static_cast<uint32_t>(m_pData[m_offset + 3]) << 24);
        m_offset += 4;
        return val;
    }

    uint64_t ReadUInt64() {
        if (!HasBytes(8)) return 0;
        uint64_t val = 0;
        for (int i = 0; i < 8; ++i) {
            val |= (static_cast<uint64_t>(m_pData[m_offset + i]) << (i * 8));
        }
        m_offset += 8;
        return val;
    }

    float ReadFloat() {
        union { float f; uint32_t u; } converter;
        converter.u = ReadUInt32();
        return converter.f;
    }

    std::string ReadString() {
        std::string str;
        while (HasBytes(1)) {
            char c = static_cast<char>(ReadByte());
            if (c == 0) break;
            str.push_back(c);
        }
        return str;
    }

    std::wstring ReadWString() {
        std::wstring str;
        while (HasBytes(2)) {
            wchar_t wc = static_cast<wchar_t>(ReadUInt16());
            if (wc == 0) break;
            str.push_back(wc);
        }
        return str;
    }

    size_t GetRemaining() const {
        return (m_offset < m_size) ? (m_size - m_offset) : 0;
    }

private:
    const uint8_t* m_pData;
    size_t m_size;
    size_t m_offset;
};

namespace AionServerPackets {

// Registra todos os manipuladores de pacotes de servidor no ClientToServerRouter
void RegisterAllHandlers();

// Manipuladores de pacotes específicos extraídos de ServerPacketsOpcodes.java
void HandleVersionCheck(const uint8_t* pData, size_t size);
void HandleEnterWorldCheck(const uint8_t* pData, size_t size);
void HandlePlayerSpawn(const uint8_t* pData, size_t size);
void HandleNpcInfo(const uint8_t* pData, size_t size);
void HandlePlayerInfo(const uint8_t* pData, size_t size);
void HandleMoveNew(const uint8_t* pData, size_t size);
void HandleAttack(const uint8_t* pData, size_t size);
void HandleUseSkill(const uint8_t* pData, size_t size);
void HandleStatus(const uint8_t* pData, size_t size);
void HandleHitPoint(const uint8_t* pData, size_t size);
void HandleManaPoint(const uint8_t* pData, size_t size);
void HandleInventoryInfo(const uint8_t* pData, size_t size);
void HandleMessage(const uint8_t* pData, size_t size);
void HandleNpcHtmlMessage(const uint8_t* pData, size_t size);
void HandleKey(const uint8_t* pData, size_t size);
void HandleTacticsSign(const uint8_t* pData, size_t size);

}

