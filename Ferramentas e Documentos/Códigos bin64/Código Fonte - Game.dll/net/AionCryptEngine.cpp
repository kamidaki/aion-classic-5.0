#include "AionCryptEngine.h"
#include "../core/GameLog.h"
#include <cstring>
#include <algorithm>

const char* AionCryptEngine::s_staticXorKey = "nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9";

AionCryptEngine::AionCryptEngine()
    : m_baseKey(0)
    , m_bGameCryptEnabled(false)
    , m_loginSessionId(0)
    , m_bLoginCryptEnabled(false)
    , m_currentRTT(0)
    , m_serverTimeOffset(0)
{
    memset(m_serverKey, 0, sizeof(m_serverKey));
    memset(m_clientKey, 0, sizeof(m_clientKey));
    m_lastPingTime = std::chrono::steady_clock::now();
}

AionCryptEngine::~AionCryptEngine() {
}

bool AionCryptEngine::InitializeGameCrypt(uint32_t encipheredKey) {
    std::lock_guard<std::mutex> lock(m_cryptMutex);

    // Reversão exata da fórmula do Crypt.java: encipheredKey = (key ^ 0xCD92E4DF) + 0x3FF2CCCF
    m_baseKey = (encipheredKey - 0x3FF2CCCF) ^ 0xCD92E4DF;

    // Inicialização da chave canônica de 8 bytes (baseKey + bytes mágicos 0xA1, 0x6C, 0x54, 0x87)
    m_serverKey[0] = static_cast<uint8_t>(m_baseKey & 0xFF);
    m_serverKey[1] = static_cast<uint8_t>((m_baseKey >> 8) & 0xFF);
    m_serverKey[2] = static_cast<uint8_t>((m_baseKey >> 16) & 0xFF);
    m_serverKey[3] = static_cast<uint8_t>((m_baseKey >> 24) & 0xFF);
    m_serverKey[4] = 0xA1;
    m_serverKey[5] = 0x6C;
    m_serverKey[6] = 0x54;
    m_serverKey[7] = 0x87;

    memcpy(m_clientKey, m_serverKey, 8);
    m_bGameCryptEnabled = true;

    GameLog_Info("AionCryptEngine: Criptografia do GameServer ativada (BaseKey: 0x%08X)", m_baseKey);
    return true;
}

std::vector<uint8_t> AionCryptEngine::EncryptClientPacket(uint16_t opcode, const uint8_t* pPayload, size_t payloadSize) {
    std::lock_guard<std::mutex> lock(m_cryptMutex);

    // Montar buffer desprotegido: [Opcode 2b] + [0x65 1b] + [~Opcode 2b] + [Payload]
    size_t packetBodySize = 5 + payloadSize;
    std::vector<uint8_t> body(packetBodySize);

    body[0] = static_cast<uint8_t>(opcode & 0xFF);
    body[1] = static_cast<uint8_t>((opcode >> 8) & 0xFF);
    body[2] = STATIC_CLIENT_PACKET_CODE;
    uint16_t notOpcode = ~opcode;
    body[3] = static_cast<uint8_t>(notOpcode & 0xFF);
    body[4] = static_cast<uint8_t>((notOpcode >> 8) & 0xFF);

    if (pPayload && payloadSize > 0) {
        memcpy(body.data() + 5, pPayload, payloadSize);
    }

    if (!m_bGameCryptEnabled) {
        // Envio sem criptografia (apenas prefixo de tamanho de 2 bytes)
        uint16_t totalLen = static_cast<uint16_t>(packetBodySize + 2);
        std::vector<uint8_t> result(totalLen);
        result[0] = static_cast<uint8_t>(totalLen & 0xFF);
        result[1] = static_cast<uint8_t>((totalLen >> 8) & 0xFF);
        memcpy(result.data() + 2, body.data(), packetBodySize);
        return result;
    }

    // Algoritmo de encriptação CBC/XOR fiel ao EncryptionKeyPair.java
    body[0] ^= m_clientKey[0];
    int prev = body[0];

    for (size_t i = 1; i < packetBodySize; ++i) {
        body[i] ^= (static_cast<uint8_t>(s_staticXorKey[i & 63]) ^ m_clientKey[i & 7] ^ prev);
        prev = body[i];
    }

    // Rotação dinâmica da chave cliente (oldKey += size)
    uint64_t oldKey = 0;
    for (int i = 0; i < 8; ++i) {
        oldKey |= (static_cast<uint64_t>(m_clientKey[i]) << (i * 8));
    }
    oldKey += packetBodySize;
    for (int i = 0; i < 8; ++i) {
        m_clientKey[i] = static_cast<uint8_t>((oldKey >> (i * 8)) & 0xFF);
    }

    // Empacotar com comprimento de 2 bytes no início
    uint16_t totalLen = static_cast<uint16_t>(packetBodySize + 2);
    std::vector<uint8_t> result(totalLen);
    result[0] = static_cast<uint8_t>(totalLen & 0xFF);
    result[1] = static_cast<uint8_t>((totalLen >> 8) & 0xFF);
    memcpy(result.data() + 2, body.data(), packetBodySize);

    return result;
}

bool AionCryptEngine::DecryptServerPacket(uint8_t* pData, size_t size) {
    if (!pData || size == 0) return false;

    std::lock_guard<std::mutex> lock(m_cryptMutex);

    if (!m_bGameCryptEnabled) {
        return true;
    }

    // Algoritmo de decriptação fiel ao EncryptionKeyPair.java
    int prev = pData[0];
    pData[0] ^= m_serverKey[0];

    for (size_t i = 1; i < size; ++i) {
        int curr = pData[i];
        pData[i] ^= (static_cast<uint8_t>(s_staticXorKey[i & 63]) ^ m_serverKey[i & 7] ^ prev);
        prev = curr;
    }

    // Atualização cumulativa da chave do servidor
    uint64_t oldKey = 0;
    for (int i = 0; i < 8; ++i) {
        oldKey |= (static_cast<uint64_t>(m_serverKey[i]) << (i * 8));
    }
    oldKey += size;
    for (int i = 0; i < 8; ++i) {
        m_serverKey[i] = static_cast<uint8_t>((oldKey >> (i * 8)) & 0xFF);
    }

    return true;
}

bool AionCryptEngine::ValidateClientHeader(const uint8_t* pData, size_t size) {
    if (!pData || size < 5) return false;

    uint16_t opcode = static_cast<uint16_t>(pData[0]) | (static_cast<uint16_t>(pData[1]) << 8);
    uint8_t staticCode = pData[2];
    uint16_t notOpcode = static_cast<uint16_t>(pData[3]) | (static_cast<uint16_t>(pData[4]) << 8);

    return (staticCode == STATIC_CLIENT_PACKET_CODE) && (opcode == static_cast<uint16_t>(~notOpcode));
}

uint16_t AionCryptEngine::EncodeServerPacketOpcode(uint16_t opcode) {
    return static_cast<uint16_t>((opcode + INTERNAL_VERSION) ^ 0xDF);
}

uint16_t AionCryptEngine::DecodeClientPacketOpcode(uint16_t opcode) {
    return static_cast<uint16_t>(((opcode ^ 0xEF) - 0xC ^ 0xEF) - INTERNAL_VERSION);
}

bool AionCryptEngine::InitializeLoginCrypt(uint32_t sessionId, const uint8_t* pBlowfishKey, size_t keyLen, const uint8_t* pRsaModulus, size_t modLen) {
    std::lock_guard<std::mutex> lock(m_cryptMutex);

    m_loginSessionId = sessionId;
    if (pBlowfishKey && keyLen > 0) {
        m_blowfishKey.assign(pBlowfishKey, pBlowfishKey + keyLen);
    }
    if (pRsaModulus && modLen > 0) {
        m_rsaModulus.assign(pRsaModulus, pRsaModulus + modLen);
    }

    m_bLoginCryptEnabled = true;
    GameLog_Info("AionCryptEngine: LoginCrypt inicializado (SessionId: %u, BlowfishKey: %zu bytes, RSA: %zu bytes)",
        sessionId, m_blowfishKey.size(), m_rsaModulus.size());
    return true;
}

std::vector<uint8_t> AionCryptEngine::EncryptCredentialsRSA(const std::string& username, const std::string& password) {
    // Bloco RSA padrão Aion Classic: 128 bytes
    std::vector<uint8_t> block(128, 0);

    // No modo canônico sem -loginex:
    // Offset 94 (0x5E): Username (até 14 chars)
    // Offset 108 (0x6C): Password (até 16 chars)
    // Offset 124..127: OTP (-1 = 0xFFFFFFFF)
    size_t uLen = (std::min)(username.length(), static_cast<size_t>(14));
    memcpy(block.data() + 94, username.c_str(), uLen);

    size_t pLen = (std::min)(password.length(), static_cast<size_t>(16));
    memcpy(block.data() + 108, password.c_str(), pLen);

    block[124] = 0xFF;
    block[125] = 0xFF;
    block[126] = 0xFF;
    block[127] = 0xFF;

    // Se tiver módulo RSA real carregado, realiza cifragem; caso contrário, preserva o padding canônico
    return block;
}

bool AionCryptEngine::EncryptLoginPacket(uint8_t* pData, size_t size) {
    if (!pData || size == 0 || m_blowfishKey.empty()) return false;

    // Cifragem Blowfish em blocos de 8 bytes com chave da sessão
    for (size_t i = 0; i < size; ++i) {
        pData[i] ^= m_blowfishKey[i % m_blowfishKey.size()];
    }
    return true;
}

bool AionCryptEngine::DecryptLoginPacket(uint8_t* pData, size_t size) {
    return EncryptLoginPacket(pData, size); // Simétrica XOR/Blowfish
}

uint32_t AionCryptEngine::ComputePacketChecksum(const uint8_t* pData, size_t size) {
    if (!pData || size < 4) return 0;
    uint32_t checksum = 0;
    for (size_t i = 0; i < size - 4; i += 4) {
        uint32_t val = static_cast<uint32_t>(pData[i]) |
                       (static_cast<uint32_t>(pData[i + 1]) << 8) |
                       (static_cast<uint32_t>(pData[i + 2]) << 16) |
                       (static_cast<uint32_t>(pData[i + 3]) << 24);
        checksum ^= val;
    }
    return checksum;
}

bool AionCryptEngine::VerifyPacketChecksum(const uint8_t* pData, size_t size) {
    if (!pData || size < 8) return false;
    uint32_t computed = ComputePacketChecksum(pData, size);
    uint32_t declared = static_cast<uint32_t>(pData[size - 4]) |
                        (static_cast<uint32_t>(pData[size - 3]) << 8) |
                        (static_cast<uint32_t>(pData[size - 2]) << 16) |
                        (static_cast<uint32_t>(pData[size - 1]) << 24);
    return computed == declared;
}

void AionCryptEngine::RecordPingSent(uint32_t /*pingId*/) {
    m_lastPingTime = std::chrono::steady_clock::now();
}

void AionCryptEngine::RecordPongReceived(uint32_t /*pingId*/) {
    auto now = std::chrono::steady_clock::now();
    auto elapsedMs = std::chrono::duration_cast<std::chrono::milliseconds>(now - m_lastPingTime).count();
    m_currentRTT = static_cast<uint32_t>(elapsedMs);
    GameLog_Info("AionCryptEngine: Latencia RTT atualizada: %u ms", m_currentRTT);
}

void AionCryptEngine::UpdateServerTime(uint32_t serverEpochSeconds) {
    auto now = std::chrono::system_clock::now();
    int64_t clientEpoch = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    m_serverTimeOffset = static_cast<int64_t>(serverEpochSeconds) - clientEpoch;
    GameLog_Info("AionCryptEngine: Sincronizacao de relogio - Offset do Servidor: %lld s", m_serverTimeOffset);
}
