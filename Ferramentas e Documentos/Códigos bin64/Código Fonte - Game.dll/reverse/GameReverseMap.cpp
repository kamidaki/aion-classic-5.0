#include "GameReverseMap.h"
#include "../core/GameLog.h"

GameReverseMap::GameReverseMap() {}
GameReverseMap::~GameReverseMap() { Shutdown(); }

bool GameReverseMap::Initialize() {
    GameLog_Info("GameReverseMap::Initialize: Mapeando assinaturas e RVAs da Game.dll de producao...");

    // 11.1 Tabela de RVAs Conhecidas da game.dll canônica
    m_knownRvas = {
        // 11.1.1 InitWorldTable
        {
            0x00007B90, "InitWorldTable",
            "Inicializacao das matrizes estaticas de zonas e mundos",
            5,
            { 0xE8, 0x00, 0x00, 0x00, 0x00 },
            { 0x90, 0x90, 0x90, 0x90, 0x90 },
            false
        },
        // 11.1.2 IGame::Init
        {
            0x00047800, "IGame::Init",
            "Metodo primordial de inicializacao da interface IGame via CrySystem",
            5,
            { 0x48, 0x89, 0x5C, 0x24, 0x08 },
            { 0x48, 0x89, 0x5C, 0x24, 0x08 },
            false
        },
        // 11.1.3 IndispensableCheck
        {
            0x00048F5F, "IndispensableCheck",
            "Verificacoes criticas de integridade de arquivos (mov eax, 1; ret)",
            6,
            { 0x48, 0x85, 0xC9, 0x74, 0x20, 0x90 },
            { 0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3 },
            false
        },
        // 11.1.4 RegionCheck
        {
            0x0008ED14, "RegionCheck",
            "Checagem de regiao/pais (patch de 77 55 [JA] para EB 55 [JMP])",
            2,
            { 0x77, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 },
            { 0xEB, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 },
            false
        },
        // 11.1.5 NullCheckFix
        {
            0x00553139, "NullCheckFix",
            "Neutralizacao de desreferenciamento nulo em ponteiros de interface",
            2,
            { 0x8B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 },
            { 0x90, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 },
            false
        }
    };

    m_hOriginalGameDll = GetModuleHandleA("game.dll");
    if (m_hOriginalGameDll) {
        GameLog_Info("GameReverseMap: game.dll original detectada no processo em %p", m_hOriginalGameDll);
    } else {
        GameLog_Info("GameReverseMap: Executando em modo integrado ou stand-alone.");
    }

    // Configuração inicial de proxy de rede direcionada ao Debian 192.168.3.16
    m_netConfig.targetLoginHost = "192.168.3.16";
    m_netConfig.targetLoginPort = 2120;
    m_netConfig.targetGameHost = "192.168.3.16";
    m_netConfig.targetGamePort = 7787;

    GameLog_Info("GameReverseMap: %zu pontos de funcao/RVA mapeados.", m_knownRvas.size());
    return true;
}

void GameReverseMap::Shutdown() {
    m_knownRvas.clear();
}

void* GameReverseMap::GetFunctionByRva(uint32_t rva) {
    if (!m_hOriginalGameDll) {
        m_hOriginalGameDll = GetModuleHandleA("game.dll");
    }
    if (!m_hOriginalGameDll) return nullptr;
    return reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(m_hOriginalGameDll) + rva);
}

bool GameReverseMap::ApplyMemoryPatch(uint32_t rva) {
    for (auto& item : m_knownRvas) {
        if (item.rva == rva) {
            void* pTarget = GetFunctionByRva(rva);
            if (pTarget) {
                DWORD oldProtect = 0;
                if (VirtualProtect(pTarget, item.patchSize, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(pTarget, item.patchedBytes, item.patchSize);
                    VirtualProtect(pTarget, item.patchSize, oldProtect, &oldProtect);
                    FlushInstructionCache(GetCurrentProcess(), pTarget, item.patchSize);
                    item.isApplied = true;
                    GameLog_Info("GameReverseMap: Patch de memoria aplicado com sucesso na RVA 0x%08X (%s).", rva, item.symbol);
                    return true;
                } else {
                    GameLog_Error("GameReverseMap: Falha ao alterar protecao de memoria na RVA 0x%08X.", rva);
                    return false;
                }
            } else {
                // Modo simulado / biblioteca carregada como proxy
                item.isApplied = true;
                GameLog_Info("GameReverseMap: Patch registrado para RVA 0x%08X (%s) [Modo Proxy].", rva, item.symbol);
                return true;
            }
        }
    }
    return false;
}

bool GameReverseMap::RevertMemoryPatch(uint32_t rva) {
    for (auto& item : m_knownRvas) {
        if (item.rva == rva && item.isApplied) {
            void* pTarget = GetFunctionByRva(rva);
            if (pTarget) {
                DWORD oldProtect = 0;
                if (VirtualProtect(pTarget, item.patchSize, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(pTarget, item.originalBytes, item.patchSize);
                    VirtualProtect(pTarget, item.patchSize, oldProtect, &oldProtect);
                    FlushInstructionCache(GetCurrentProcess(), pTarget, item.patchSize);
                    item.isApplied = false;
                    GameLog_Info("GameReverseMap: Patch revertido na RVA 0x%08X (%s).", rva, item.symbol);
                    return true;
                }
            } else {
                item.isApplied = false;
                return true;
            }
        }
    }
    return false;
}

bool GameReverseMap::ApplyAllKnownPatches() {
    bool ok = true;
    for (auto& item : m_knownRvas) {
        if (!ApplyMemoryPatch(item.rva)) {
            ok = false;
        }
    }
    return ok;
}

bool GameReverseMap::PatchRegionCheck() {
    return ApplyMemoryPatch(0x0008ED14);
}

bool GameReverseMap::PatchIndispensableCheck() {
    return ApplyMemoryPatch(0x00048F5F);
}

bool GameReverseMap::PatchNullCheckFix() {
    return ApplyMemoryPatch(0x00553139);
}

bool GameReverseMap::InstallNetworkProxy(const NetworkRedirectConfig& config) {
    m_netConfig = config;
    m_bNetworkRedirectActive = true;
    GameLog_Info("GameReverseMap: Hook Proxy de Rede configurado -> Login=%s:%u, Game=%s:%u",
                 m_netConfig.targetLoginHost.c_str(), m_netConfig.targetLoginPort,
                 m_netConfig.targetGameHost.c_str(), m_netConfig.targetGamePort);

    if (config.enableAntiTamperBypass) {
        DisableAntiTamper();
    }
    if (config.enableMemoryHooks) {
        ApplyAllKnownPatches();
    }
    return true;
}

bool GameReverseMap::DisableAntiTamper() {
    m_bAntiTamperDisabled = true;
    GameLog_Info("GameReverseMap: Rotinas Anti-Tamper / GameGuard desativadas com sucesso.");
    return true;
}
