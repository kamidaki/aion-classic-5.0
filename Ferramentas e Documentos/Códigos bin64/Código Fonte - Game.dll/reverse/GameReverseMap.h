#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>

// Estrutura de mapeamento de RVA canônica
struct RvaMapping {
    uint32_t rva;
    const char* symbol;
    const char* description;
    uint32_t patchSize;
    uint8_t originalBytes[8];
    uint8_t patchedBytes[8];
    bool isApplied;
};

// Configuração de redirecionamento de rede para o Hook Proxy (version.dll)
struct NetworkRedirectConfig {
    bool enableRedirect = true;
    std::string targetLoginHost = "192.168.3.16";
    uint16_t targetLoginPort = 2120;
    std::string targetGameHost = "192.168.3.16";
    uint16_t targetGamePort = 7787;
    bool enableAntiTamperBypass = true;
    bool enableMemoryHooks = true;
};

class GameReverseMap {
public:
    static GameReverseMap& GetInstance() {
        static GameReverseMap instance;
        return instance;
    }

    bool Initialize();
    void Shutdown();

    void* GetFunctionByRva(uint32_t rva);
    const std::vector<RvaMapping>& GetKnownRvas() const { return m_knownRvas; }

    // Aplicação de patches em memória para RVAs canônicas
    bool ApplyMemoryPatch(uint32_t rva);
    bool RevertMemoryPatch(uint32_t rva);
    bool ApplyAllKnownPatches();

    // Verificações específicas do Roadmap 11.1
    bool PatchRegionCheck();         // 0x0008ED14 (77 55 -> EB 55)
    bool PatchIndispensableCheck();   // 0x00048F5F (Ignora falhas de arquivos indispensáveis)
    bool PatchNullCheckFix();         // 0x00553139 (Neutraliza crash de ponteiro nulo de interface)

    // Integração com version.dll (Hook Proxy) 11.2
    bool InstallNetworkProxy(const NetworkRedirectConfig& config);
    bool DisableAntiTamper();
    const NetworkRedirectConfig& GetNetworkConfig() const { return m_netConfig; }
    bool IsAntiTamperDisabled() const { return m_bAntiTamperDisabled; }
    bool IsNetworkRedirectActive() const { return m_bNetworkRedirectActive; }

private:
    GameReverseMap();
    ~GameReverseMap();

    HMODULE m_hOriginalGameDll = nullptr;
    std::vector<RvaMapping> m_knownRvas;
    NetworkRedirectConfig m_netConfig;
    bool m_bAntiTamperDisabled = false;
    bool m_bNetworkRedirectActive = false;
};
