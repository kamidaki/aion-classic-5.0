#pragma once
#include "../framework/IGame.h"
#include "../framework/IXGame.h"
#include "../framework/IConsoleSink.h"
#include "../framework/IInputEventListener.h"
#include <string>

// Objeto de jogo canônico mestre do Aion Classic (.?AVCXGame@@)
// Herança canônica validada via RTTI:
//   Base[0]: CXGame (mdisp=0)
//   Base[1]: IXGame (mdisp=0)
//   Base[2]: IGame (mdisp=0)
//   Base[3]: IConsoleSink (mdisp=8)
//   Base[4]: IInputEventListener (mdisp=16)
class CXGame : public IXGame, public IConsoleSink, public IInputEventListener {
public:
    CXGame();
    virtual ~CXGame() override;

    // Slot 0 - 7: Ciclo de vida e núcleo CryEngine
    virtual bool Init(ISystem* pSystem, bool bInEditor, bool bDedicated) override;
    virtual bool InitUISystem(void* pParam = nullptr) override;
    virtual bool Update() override;
    virtual void Shutdown() override;
    virtual void Reset() override;
    virtual bool LoadLevel(const char* szLevel, const char* szMission) override;
    virtual const char* GetName() override;
    virtual void Process() override;

    // Slot 8 - 15: Subsistemas de entidades e rede
    virtual bool IsClient() override;
    virtual bool GetFootPoint(int index, void* pOutPoint) override;
    virtual void SetFootPoint(int index, void* pInPoint) override;
    virtual int GetFootPointCount() override;
    virtual void* GetSubObject(int subId) override;
    virtual void TestRoutine13(int a1, void* a2) override;
    virtual bool SendAboutToPlay() override;
    virtual void ProcessMovements() override;

    // Slot 16 - 23: Níveis, materiais e áudio
    virtual void OnLevelPreload() override;
    virtual bool LoadMaterialDB(const char* szPath) override;
    virtual void* GetCharactersFromEntitySystem() override;
    virtual void OnWeaponSwitch() override;
    virtual void OnPlayerAction(int actionId) override;
    virtual void PlaySystemSound(const char* szSoundName, int id = 0) override;
    virtual void StopSystemSound(int soundId = 0) override;
    virtual void OnQuitYes() override;

    // Slot 24 - 31: Interface de Login e Display
    virtual bool LoadLoginUI() override;
    virtual void UnloadLoginUI() override;
    virtual void SetTargetCharScale(float scale, float armScale = 1.0f, float legScale = 1.0f) override;
    virtual void SetPseudoFullscreen(bool bEnable) override;
    virtual void UpdateDisplayMode() override;
    virtual const char* GetDebugStatus() override;
    virtual void ClearEntityLists() override;
    virtual bool SendAuthTicket() override;

    // Slot 32 - 39: Sessão, Coding Path e Versão
    virtual void OnDisconnect() override;
    virtual void OnCodingPathFinish() override;
    virtual bool SendAuxAuthAck() override;
    virtual void OnActionComplete() override;
    virtual void UpdateCameraMode() override;
    virtual void OnEnvironmentUpdate() override;
    virtual const char* GetAccountID() override;
    virtual const char* GetGameVersion() override;

    // Slot 40 - 47: Versão e Tokens de Segurança
    virtual int GetBuildNumber() override;
    virtual const char* GetPatchVersion() override;
    virtual const char* GetSecurityToken(int tokenType = 0) override;
    virtual bool ValidateSecurityToken(const char* token) override;
    virtual void RefreshSecurityToken() override;
    virtual int GetSecurityTokenStatus() override;
    virtual void ClearSecurityToken() override;
    virtual void SetSecurityToken(const char* token) override;

    // Slot 48 - 55: Segurança, HUD e Mensagens
    virtual bool HasValidSecurityToken() override;
    virtual void OnSecurityTokenExpired() override;
    virtual void LogSecurityEvent(int eventId) override;
    virtual void OnPlayerStanceChanged() override;
    virtual void QuitGame(int exitCode = 0) override;
    virtual void CancelQuitGame() override;
    virtual bool IsQuittingGame() override;
    virtual void PostSystemMessage(const char* szMsg, int msgType = 0) override;

    // Slot 56 - 63: Sistema de Teclas de Atalho e SSD
    virtual void ClearSystemMessages() override;
    virtual void UpdateHUDState() override;
    virtual void SetAccountID(const char* szAccount) override;
    virtual void OnNetworkLatencyUpdate(int pingMs) override;
    virtual void SetSSDMode(bool bSSD) override;
    virtual bool IsSSDMode() override;
    virtual bool SendPlayPacket() override;
    virtual bool RegisterHotKey(uint32_t keyId, uint32_t modifiers) override;

    // Slot 64 - 71: Pacotes e Rastreamento de Missões
    virtual bool UnregisterHotKey(uint32_t keyId) override;
    virtual void ProcessHotKey(uint32_t keyId) override;
    virtual void OnFocusChanged(bool bFocused) override;
    virtual bool RecvPacket(uint16_t opcode, const uint8_t* pData, uint32_t size) override;
    virtual void FlushPackets() override;
    virtual void SetQuestIndicatorTitle(const char* szTitle, float fps = 60.0f) override;
    virtual void UpdateQuestTracker() override;
    virtual bool SendGameEnterRequest() override;

    // Slot 72 - 79: Cenário do Mundo e Cinemáticas
    virtual void OnWorldLoaded() override;
    virtual void OnWorldUnloaded() override;
    virtual void UpdateTerrainStreaming() override;
    virtual void UpdateEntityStreaming() override;
    virtual void TestShugoNPC(const char* name) override;
    virtual void TriggerCinematic(int seqId) override;
    virtual void StopCinematic() override;
    virtual bool IsInCinematic() override;

    // Slot 80 - 87: Interações com Shugos e Níveis Listen
    virtual void SetCinematicSpeed(float speed) override;
    virtual void OnCinematicEnd() override;
    virtual bool SendWorldEnterAck() override;
    virtual bool SendPlayerReady() override;
    virtual void ProcessShugoDialog(int npcId) override;
    virtual void ProcessShugoTrade(int npcId) override;
    virtual bool LoadLevelListen(const char* szLevel) override;
    virtual void ProcessShugoQuest(int npcId) override;

    // Slot 88 - 95: Voo, Sons e Equipamentos
    virtual void OnPlayerFlyStart() override;
    virtual void OnPlayerFlyEnd() override;
    virtual void ShowEndingUI(const char* szEnding = "UI_Ending.xml") override;
    virtual void HideEndingUI() override;
    virtual void OnWeatherChangeImmediate(int weatherId) override;
    virtual bool LoadEventSoundTable(const char* szPath) override;
    virtual void GetPlayerWeapons(void* pSlot1, void* pSlot2, void* pTorso) override;
    virtual void PlayGossipSound(const char* szNpcVoice) override;

    // Slot 96 - 103: Mundo, Spawn e Progressão
    virtual void ShowFPSCounter(bool bShow) override;
    virtual bool LoadWorldLevel(const char* szLevel, const char* szWorldXml) override;
    virtual void OnNpcSpawn(uint32_t npcId) override;
    virtual void OnNpcDespawn(uint32_t npcId) override;
    virtual void OnNpcAction(uint32_t npcId, int action) override;
    virtual void OnNpcSay(uint32_t npcId, const char* szText) override;
    virtual void OnPlayerLevelUp(int newLevel) override;
    virtual void OnPlayerDeath() override;

    // Slot 104 - 111: HUDs de Grupo/Legião e Gráficos
    virtual void OnPlayerResurrect() override;
    virtual void UpdatePartyHUD() override;
    virtual void UpdateAllianceHUD() override;
    virtual void UpdateLegionHUD() override;
    virtual void SpawnMobTest(const char* mobName, int count) override;
    virtual bool GetPseudoFullscreen() override;
    virtual void TogglePseudoFullscreen() override;
    virtual void ConfigureMRTDOF(bool bAuto, float amount) override;

    // Slot 112 - 119: Configurações, Teclas e NPCs
    virtual void OnGraphicSettingsChanged() override;
    virtual void OnSoundSettingsChanged() override;
    virtual bool LoadShortcutKeys(const char* szXml = "ShortcutKeys.xml") override;
    virtual void OnShugoGreeting(int npcId) override;
    virtual void OnShugoFarewell(int npcId) override;
    virtual void UpdateMinimap() override;
    virtual void OnShugoTradeSuccess(int npcId) override;
    virtual void OnShugoTradeCancel(int npcId) override;

    // Slot 120 - 127: Ofertas, Áudio e Rede Interna
    virtual void OnShugoSpecialOffer(int npcId) override;
    virtual void OnShugoInventoryFull(int npcId) override;
    virtual void UpdateAmbientSounds() override;
    virtual void OnShugoVoice(const char* szVoice) override;
    virtual void SetDuckingSound(bool bEnable) override;
    virtual bool GetDuckingSound() override;
    virtual const char* GetInternalNetworkRange() override;
    virtual bool IsInternalNetworkAddress(const char* szIp) override;

    // Slot 128 - 130: Background e Teclas de Jogo
    virtual void ProcessBackgroundTasks() override;
    virtual bool RegisterGameHotKey(uint32_t hotkeyId, uint32_t key, uint32_t mod) override;
    virtual bool UnregisterGameHotKey(uint32_t hotkeyId) override;

    // IConsoleSink implementation (offset 8)
    virtual void OnConsoleCommand(const char* szCommand) override;

    // IInputEventListener implementation (offset 16)
    virtual bool OnInputEvent(void* pEvent) override;

    // Liberação de instância
    void Release();

private:
    bool m_bEditor;
    bool m_bDedicated;
    bool m_bSSDMode;
    bool m_bPseudoFullscreen;
    bool m_bDuckingSound;
    bool m_bQuitting;
    int m_footPointCount;
    std::string m_gameName;
    std::string m_accountID;
    std::string m_gameVersion;
    std::string m_patchVersion;
    std::string m_securityToken;

    // Buffer de tamanho de paridade com o objeto oficial (0xcf80 = 53.120 bytes)
    uint8_t m_engineStatePadding[52000];
};

using CGame = CXGame;
