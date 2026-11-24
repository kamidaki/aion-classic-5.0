#pragma once
#include "CryModuleDefs.h"
#include "ISystem.h"
#include <cstdint>

// Interface canônica de motor de jogo CryEngine Classic 5.0 (.?AUIGame@@)
// Contém exatamente 132 slots virtuais correspondendo à VTable de Game.dll
struct IGame {
    // Slot 0 - 7: Ciclo de vida e núcleo CryEngine
    virtual bool Init(ISystem* pSystem, bool bInEditor, bool bDedicated) = 0; // 0 (0x00)
    virtual bool InitUISystem(void* pParam = nullptr) = 0;                    // 1 (0x08)
    virtual bool Update() = 0;                                               // 2 (0x10)
    virtual void Shutdown() = 0;                                             // 3 (0x18)
    virtual void Reset() = 0;                                                // 4 (0x20)
    virtual bool LoadLevel(const char* szLevel, const char* szMission) = 0;  // 5 (0x28)
    virtual const char* GetName() = 0;                                       // 6 (0x30)
    virtual void Process() = 0;                                              // 7 (0x38)

    // Slot 8 - 15: Subsistemas de entidades e rede
    virtual bool IsClient() = 0;                                             // 8 (0x40)
    virtual bool GetFootPoint(int index, void* pOutPoint) = 0;               // 9 (0x48)
    virtual void SetFootPoint(int index, void* pInPoint) = 0;                // 10 (0x50)
    virtual int GetFootPointCount() = 0;                                     // 11 (0x58)
    virtual void* GetSubObject(int subId) = 0;                               // 12 (0x60)
    virtual void TestRoutine13(int a1, void* a2) = 0;                        // 13 (0x68)
    virtual bool SendAboutToPlay() = 0;                                      // 14 (0x70)
    virtual void ProcessMovements() = 0;                                     // 15 (0x78)

    // Slot 16 - 23: Níveis, materiais e áudio
    virtual void OnLevelPreload() = 0;                                       // 16 (0x80)
    virtual bool LoadMaterialDB(const char* szPath) = 0;                     // 17 (0x88)
    virtual void* GetCharactersFromEntitySystem() = 0;                       // 18 (0x90)
    virtual void OnWeaponSwitch() = 0;                                       // 19 (0x98)
    virtual void OnPlayerAction(int actionId) = 0;                           // 20 (0xa0)
    virtual void PlaySystemSound(const char* szSoundName, int id = 0) = 0;   // 21 (0xa8)
    virtual void StopSystemSound(int soundId = 0) = 0;                       // 22 (0xb0)
    virtual void OnQuitYes() = 0;                                            // 23 (0xb8)

    // Slot 24 - 31: Interface de Login e Display
    virtual bool LoadLoginUI() = 0;                                          // 24 (0xc0)
    virtual void UnloadLoginUI() = 0;                                        // 25 (0xc8)
    virtual void SetTargetCharScale(float scale, float armScale = 1.0f, float legScale = 1.0f) = 0; // 26 (0xd0)
    virtual void SetPseudoFullscreen(bool bEnable) = 0;                      // 27 (0xd8)
    virtual void UpdateDisplayMode() = 0;                                    // 28 (0xe0)
    virtual const char* GetDebugStatus() = 0;                                // 29 (0xe8)
    virtual void ClearEntityLists() = 0;                                     // 30 (0xf0)
    virtual bool SendAuthTicket() = 0;                                       // 31 (0xf8)

    // Slot 32 - 39: Sessão, Coding Path e Versão
    virtual void OnDisconnect() = 0;                                         // 32 (0x100)
    virtual void OnCodingPathFinish() = 0;                                   // 33 (0x108)
    virtual bool SendAuxAuthAck() = 0;                                       // 34 (0x110)
    virtual void OnActionComplete() = 0;                                     // 35 (0x118)
    virtual void UpdateCameraMode() = 0;                                     // 36 (0x120)
    virtual void OnEnvironmentUpdate() = 0;                                  // 37 (0x128)
    virtual const char* GetAccountID() = 0;                                  // 38 (0x130)
    virtual const char* GetGameVersion() = 0;                                // 39 (0x138)

    // Slot 40 - 47: Versão e Tokens de Segurança
    virtual int GetBuildNumber() = 0;                                        // 40 (0x140)
    virtual const char* GetPatchVersion() = 0;                               // 41 (0x148)
    virtual const char* GetSecurityToken(int tokenType = 0) = 0;             // 42 (0x150)
    virtual bool ValidateSecurityToken(const char* token) = 0;               // 43 (0x158)
    virtual void RefreshSecurityToken() = 0;                                 // 44 (0x160)
    virtual int GetSecurityTokenStatus() = 0;                                // 45 (0x168)
    virtual void ClearSecurityToken() = 0;                                   // 46 (0x170)
    virtual void SetSecurityToken(const char* token) = 0;                    // 47 (0x178)

    // Slot 48 - 55: Segurança, HUD e Mensagens
    virtual bool HasValidSecurityToken() = 0;                                // 48 (0x180)
    virtual void OnSecurityTokenExpired() = 0;                               // 49 (0x188)
    virtual void LogSecurityEvent(int eventId) = 0;                          // 50 (0x190)
    virtual void OnPlayerStanceChanged() = 0;                                // 51 (0x198)
    virtual void QuitGame(int exitCode = 0) = 0;                             // 52 (0x1a0)
    virtual void CancelQuitGame() = 0;                                       // 53 (0x1a8)
    virtual bool IsQuittingGame() = 0;                                       // 54 (0x1b0)
    virtual void PostSystemMessage(const char* szMsg, int msgType = 0) = 0;  // 55 (0x1b8)

    // Slot 56 - 63: Sistema de Teclas de Atalho e SSD
    virtual void ClearSystemMessages() = 0;                                  // 56 (0x1c0)
    virtual void UpdateHUDState() = 0;                                       // 57 (0x1c8)
    virtual void SetAccountID(const char* szAccount) = 0;                    // 58 (0x1d0)
    virtual void OnNetworkLatencyUpdate(int pingMs) = 0;                     // 59 (0x1d8)
    virtual void SetSSDMode(bool bSSD) = 0;                                  // 60 (0x1e0)
    virtual bool IsSSDMode() = 0;                                            // 61 (0x1e8)
    virtual bool SendPlayPacket() = 0;                                       // 62 (0x1f0)
    virtual bool RegisterHotKey(uint32_t keyId, uint32_t modifiers) = 0;     // 63 (0x1f8)

    // Slot 64 - 71: Pacotes e Rastreamento de Missões
    virtual bool UnregisterHotKey(uint32_t keyId) = 0;                       // 64 (0x200)
    virtual void ProcessHotKey(uint32_t keyId) = 0;                          // 65 (0x208)
    virtual void OnFocusChanged(bool bFocused) = 0;                          // 66 (0x210)
    virtual bool RecvPacket(uint16_t opcode, const uint8_t* pData, uint32_t size) = 0; // 67 (0x218)
    virtual void FlushPackets() = 0;                                         // 68 (0x220)
    virtual void SetQuestIndicatorTitle(const char* szTitle, float fps = 60.0f) = 0; // 69 (0x228)
    virtual void UpdateQuestTracker() = 0;                                   // 70 (0x230)
    virtual bool SendGameEnterRequest() = 0;                                 // 71 (0x238)

    // Slot 72 - 79: Cenário do Mundo e Cinemáticas
    virtual void OnWorldLoaded() = 0;                                        // 72 (0x240)
    virtual void OnWorldUnloaded() = 0;                                      // 73 (0x248)
    virtual void UpdateTerrainStreaming() = 0;                               // 74 (0x250)
    virtual void UpdateEntityStreaming() = 0;                                // 75 (0x258)
    virtual void TestShugoNPC(const char* name) = 0;                         // 76 (0x260)
    virtual void TriggerCinematic(int seqId) = 0;                            // 77 (0x268)
    virtual void StopCinematic() = 0;                                        // 78 (0x270)
    virtual bool IsInCinematic() = 0;                                        // 79 (0x278)

    // Slot 80 - 87: Interações com Shugos e Níveis Listen
    virtual void SetCinematicSpeed(float speed) = 0;                         // 80 (0x280)
    virtual void OnCinematicEnd() = 0;                                       // 81 (0x288)
    virtual bool SendWorldEnterAck() = 0;                                    // 82 (0x290)
    virtual bool SendPlayerReady() = 0;                                      // 83 (0x298)
    virtual void ProcessShugoDialog(int npcId) = 0;                          // 84 (0x2a0)
    virtual void ProcessShugoTrade(int npcId) = 0;                           // 85 (0x2a8)
    virtual bool LoadLevelListen(const char* szLevel) = 0;                   // 86 (0x2b0)
    virtual void ProcessShugoQuest(int npcId) = 0;                           // 87 (0x2b8)

    // Slot 88 - 95: Voo, Sons e Equipamentos
    virtual void OnPlayerFlyStart() = 0;                                     // 88 (0x2c0)
    virtual void OnPlayerFlyEnd() = 0;                                       // 89 (0x2c8)
    virtual void ShowEndingUI(const char* szEnding = "UI_Ending.xml") = 0;   // 90 (0x2d0)
    virtual void HideEndingUI() = 0;                                         // 91 (0x2d8)
    virtual void OnWeatherChangeImmediate(int weatherId) = 0;                // 92 (0x2e0)
    virtual bool LoadEventSoundTable(const char* szPath) = 0;                // 93 (0x2e8)
    virtual void GetPlayerWeapons(void* pSlot1, void* pSlot2, void* pTorso) = 0; // 94 (0x2f0)
    virtual void PlayGossipSound(const char* szNpcVoice) = 0;                // 95 (0x2f8)

    // Slot 96 - 103: Mundo, Spawn e Progressão
    virtual void ShowFPSCounter(bool bShow) = 0;                             // 96 (0x300)
    virtual bool LoadWorldLevel(const char* szLevel, const char* szWorldXml) = 0; // 97 (0x308)
    virtual void OnNpcSpawn(uint32_t npcId) = 0;                             // 98 (0x310)
    virtual void OnNpcDespawn(uint32_t npcId) = 0;                           // 99 (0x318)
    virtual void OnNpcAction(uint32_t npcId, int action) = 0;                // 100 (0x320)
    virtual void OnNpcSay(uint32_t npcId, const char* szText) = 0;           // 101 (0x328)
    virtual void OnPlayerLevelUp(int newLevel) = 0;                          // 102 (0x330)
    virtual void OnPlayerDeath() = 0;                                        // 103 (0x338)

    // Slot 104 - 111: HUDs de Grupo/Legião e Gráficos
    virtual void OnPlayerResurrect() = 0;                                    // 104 (0x340)
    virtual void UpdatePartyHUD() = 0;                                       // 105 (0x348)
    virtual void UpdateAllianceHUD() = 0;                                    // 106 (0x350)
    virtual void UpdateLegionHUD() = 0;                                      // 107 (0x358)
    virtual void SpawnMobTest(const char* mobName, int count) = 0;           // 108 (0x360)
    virtual bool GetPseudoFullscreen() = 0;                                  // 109 (0x368)
    virtual void TogglePseudoFullscreen() = 0;                               // 110 (0x370)
    virtual void ConfigureMRTDOF(bool bAuto, float amount) = 0;              // 111 (0x378)

    // Slot 112 - 119: Configurações, Teclas e NPCs
    virtual void OnGraphicSettingsChanged() = 0;                             // 112 (0x380)
    virtual void OnSoundSettingsChanged() = 0;                               // 113 (0x388)
    virtual bool LoadShortcutKeys(const char* szXml = "ShortcutKeys.xml") = 0; // 114 (0x390)
    virtual void OnShugoGreeting(int npcId) = 0;                             // 115 (0x398)
    virtual void OnShugoFarewell(int npcId) = 0;                             // 116 (0x3a0)
    virtual void UpdateMinimap() = 0;                                        // 117 (0x3a8)
    virtual void OnShugoTradeSuccess(int npcId) = 0;                         // 118 (0x3b0)
    virtual void OnShugoTradeCancel(int npcId) = 0;                          // 119 (0x3b8)

    // Slot 120 - 127: Ofertas, Áudio e Rede Interna
    virtual void OnShugoSpecialOffer(int npcId) = 0;                         // 120 (0x3c0)
    virtual void OnShugoInventoryFull(int npcId) = 0;                        // 121 (0x3c8)
    virtual void UpdateAmbientSounds() = 0;                                  // 122 (0x3d0)
    virtual void OnShugoVoice(const char* szVoice) = 0;                      // 123 (0x3d8)
    virtual void SetDuckingSound(bool bEnable) = 0;                          // 124 (0x3e0)
    virtual bool GetDuckingSound() = 0;                                      // 125 (0x3e8)
    virtual const char* GetInternalNetworkRange() = 0;                       // 126 (0x3f0)
    virtual bool IsInternalNetworkAddress(const char* szIp) = 0;             // 127 (0x3f8)

    // Slot 128 - 130: Background e Teclas de Jogo
    virtual void ProcessBackgroundTasks() = 0;                               // 128 (0x400)
    virtual bool RegisterGameHotKey(uint32_t hotkeyId, uint32_t key, uint32_t mod) = 0; // 129 (0x408)
    virtual bool UnregisterGameHotKey(uint32_t hotkeyId) = 0;                // 130 (0x410)

    // Slot 131: Destrutor virtual canônico scalar deleting destructor (0x418)
    virtual ~IGame() {}
};
