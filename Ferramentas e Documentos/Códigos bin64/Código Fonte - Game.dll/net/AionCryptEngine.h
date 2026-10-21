#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>
#include <chrono>
#include <mutex>

// ============================================================================
// MOTOR CANÔNICO DE CRIPTOGRAFIA E INTEGRIDADE DE REDE (AION CLASSIC PROTOCOL)
// Fiel aos algoritmos de baixo nível de Crypt.java e EncryptionKeyPair.java
// ============================================================================

class AionCryptEngine {
public:
    static const uint8_t STATIC_CLIENT_PACKET_CODE = 0x65;
    static const uint8_t STATIC_SERVER_PACKET_CODE = 0x44;
    static const int INTERNAL_VERSION = 207;

    AionCryptEngine();
    ~AionCryptEngine();

    // --- 1. Criptografia de Pacotes do GameServer ---
    // Inicializa as chaves simétricas a partir do encipheredKey recebido em SM_KEY
    bool InitializeGameCrypt(uint32_t encipheredKey);
    bool IsGameCryptEnabled() const { return m_bGameCryptEnabled; }

    // Encripta um pacote de saída do cliente para o GameServer
    // Insere o cabeçalho canônico: [Opcode (16)] + [0x65] + [~Opcode (16)] + Payload
    std::vector<uint8_t> EncryptClientPacket(uint16_t opcode, const uint8_t* pPayload, size_t payloadSize);

    // Decripta um pacote recebido do GameServer
    bool DecryptServerPacket(uint8_t* pData, size_t size);

    // Validação de integridade do cabeçalho de cliente
    static bool ValidateClientHeader(const uint8_t* pData, size_t size);

    // Ofuscação / Deofuscação de Opcodes
    static uint16_t EncodeServerPacketOpcode(uint16_t opcode);
    static uint16_t DecodeClientPacketOpcode(uint16_t opcode);

    // --- 2. Criptografia e Autenticação do LoginServer ---
    // Inicializa a sessão com a chave Blowfish (16 bytes) e módulo RSA (128 bytes)
    bool InitializeLoginCrypt(uint32_t sessionId, const uint8_t* pBlowfishKey, size_t keyLen, const uint8_t* pRsaModulus, size_t modLen);
    
    // Criptografa credenciais de usuário via RSA para o pacote CM_LOGIN
    std::vector<uint8_t> EncryptCredentialsRSA(const std::string& username, const std::string& password);

    // Criptografia simétrica Blowfish para pacotes do LoginServer
    bool EncryptLoginPacket(uint8_t* pData, size_t size);
    bool DecryptLoginPacket(uint8_t* pData, size_t size);

    // Verificação e cálculo de Checksum XOR cumulativo de integridade
    static uint32_t ComputePacketChecksum(const uint8_t* pData, size_t size);
    static bool VerifyPacketChecksum(const uint8_t* pData, size_t size);

    // --- 3. Telemetria de Ping, Sincronização de Relógio e Latência (RTT) ---
    void RecordPingSent(uint32_t pingId);
    void RecordPongReceived(uint32_t pingId);
    uint32_t GetCurrentRTT() const { return m_currentRTT; }
    int64_t GetServerTimeOffset() const { return m_serverTimeOffset; }
    void UpdateServerTime(uint32_t serverEpochSeconds);

private:
    // GameServer Keys (8 bytes cada)
    uint8_t m_serverKey[8];
    uint8_t m_clientKey[8];
    uint32_t m_baseKey;
    bool m_bGameCryptEnabled;

    // LoginServer Keys
    uint32_t m_loginSessionId;
    std::vector<uint8_t> m_blowfishKey;
    std::vector<uint8_t> m_rsaModulus;
    bool m_bLoginCryptEnabled;

    // RTT & Time sync
    uint32_t m_currentRTT;
    int64_t m_serverTimeOffset;
    std::chrono::steady_clock::time_point m_lastPingTime;
    mutable std::mutex m_cryptMutex;

    static const char* s_staticXorKey;
};
