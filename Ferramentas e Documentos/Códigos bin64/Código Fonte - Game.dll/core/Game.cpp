#include "Game.h"
#include "GameGlobals.h"
#include "GameLog.h"
#include "../net/ClientToServerRouter.h"
#include "../net/AionClientPackets.h"
#include "../net/AionServerPackets.h"
#include "../net/AionRouters.h"
#include "../ai/AIObject.h"
#include "../ai/AIToyPet.h"
#include "../tables/AbyssTable.h"
#include "../tables/ActionPresetTable.h"
#include "../tables/AssemblyItemTable.h"
#include "../tables/ArtiTable.h"
#include "../tables/FlyPathTable.h"
#include "../path/CPathFileReader.h"
#include "../path/SimplePathSector.h"
#include "../path/ComplexPathSector.h"
#include "../ui/AddonBrowser.h"
#include "../ui/AddonButton.h"
#include "../ui/AddonContainer.h"
#include "../ui/AddonGauge.h"
#include "../ui/AddonWidgets.h"
#include "../tables/GameTablesExt.h"
#include "../ui/AddonExt.h"
#include "../ui/GameDialogsExt.h"
#include "../ai/AiStatesExt.h"
#include "../game/GameplayExt.h"
#include "../game/Player.h"
#include "../game/Items.h"
#include "../game/EngineObjects.h"
#include "../framework/CryEngineInterfaces.h"
#include "../framework/ATLInterfaces.h"
#include "../framework/StdTemplates.h"
#include "../ui/AionCEF.h"
#include "../ui/AionUIWidgets.h"
#include "../net/AionNetSystem.h"
#include <cstring>

// Instâncias globais ativas dos subsistemas do motor
static std::unique_ptr<Player> s_pLocalPlayer;
static std::unique_ptr<AIToyPet> s_pLocalPet;
static std::unique_ptr<CPathFileReader> s_pPathReader;
static std::unique_ptr<AddonBrowser> s_pAddonBrowser;
static std::unique_ptr<AddonContainer> s_pMainUIContainer;
static std::unique_ptr<AssemblyItemTable> s_pAssemblyTable;
static std::unique_ptr<ArtiTable> s_pArtiTable;
static std::unique_ptr<FlyPathTable> s_pFlyPathTable;
static std::unique_ptr<GameSocketHandler> s_pGameSocketHandler;

CXGame::CXGame() 
    : m_bEditor(false)
    , m_bDedicated(false)
    , m_bSSDMode(false)
    , m_bPseudoFullscreen(false)
    , m_bDuckingSound(false)
    , m_bQuitting(false)
    , m_footPointCount(0)
    , m_gameName("Aion Classic 5.0 - CXGame Module")
    , m_accountID("ClassicUser")
    , m_gameVersion("5.0.0.1")
    , m_patchVersion("5.0.0")
    , m_securityToken("VALID_SECURITY_TOKEN_CLASSIC")
{
    std::memset(m_engineStatePadding, 0, sizeof(m_engineStatePadding));
}

CXGame::~CXGame() {
    Shutdown();
}

// Slot 0: Init
bool CXGame::Init(ISystem* pSystem, bool bInEditor, bool bDedicated) {
    GameGlobals::s_pSystem = pSystem;
    m_bEditor = bInEditor;
    m_bDedicated = bDedicated;

    GameLog_Init();
    GameLog_Info("Iniciando CXGame::Init (CryEngine IGame Interface)...");

    if (pSystem) {
        const char* root = pSystem->GetRootFolder();
        if (root) {
            strncpy_s(GameGlobals::s_szRootPath, root, sizeof(GameGlobals::s_szRootPath) - 1);
            GameLog_Info("CryEngine Root Folder: %s", GameGlobals::s_szRootPath);
        }
    }

    // Inicialização dos subsistemas de rede canônicos
    ClientToServerRouter::GetInstance().Initialize();
    AionServerPackets::RegisterAllHandlers();
    s_pGameSocketHandler = std::make_unique<GameSocketHandler>();

    // Inicialização das tabelas estáticas canônicas
    AbyssTable::GetInstance().LoadTable();
    ActionPresetTable::GetInstance().LoadTable();

    s_pAssemblyTable = std::make_unique<AssemblyItemTable>();
    s_pArtiTable = std::make_unique<ArtiTable>();
    s_pFlyPathTable = std::make_unique<FlyPathTable>();

    // Registro das 1.977 classes canônicas do RTTI
    RegisterAllGameTablesExt();
    RegisterAllAddonExt();
    RegisterAllAiStatesExt();
    RegisterAllGameplayExt();
    RegisterAllGameDialogsExt();

    // Navegação e malhas espaciais
    s_pPathReader = std::make_unique<CPathFileReader>();

    // Subsistema visual e UI
    s_pAddonBrowser = std::make_unique<AddonBrowser>();
    s_pMainUIContainer = std::make_unique<AddonContainer>("MainUIContainer");

    auto btnAction = std::make_shared<AddonButton>("BtnAction");
    auto gaugeHp = std::make_shared<AddonGauge>("GaugeHP");
    gaugeHp->SetRange(0, 10000);
    gaugeHp->SetValue(10000);

    s_pMainUIContainer->AddChild(btnAction);
    s_pMainUIContainer->AddChild(gaugeHp);

    // Inicializa o jogador local canônico e pet
    s_pLocalPlayer = std::make_unique<Player>(10001, "Player", 1, 0, 0);
    s_pLocalPet = std::make_unique<AIToyPet>(20001, 101, 10001, "Porgus Companion");

    GameGlobals::s_bInitialized = true;
    GameGlobals::s_bRunning = true;

    GameLog_Info("CXGame::Init concluido com sucesso! Todos os subsistemas canônicos operacionais.");
    return true;
}

// Slot 1: InitUISystem
bool CXGame::InitUISystem(void* pParam) {
    (void)pParam;
    GameLog_Info("CXGame::InitUISystem inicializado.");
    return true;
}

// Slot 2: Update
bool CXGame::Update() {
    if (!GameGlobals::s_bRunning) return false;

    if (s_pLocalPlayer) s_pLocalPlayer->Update();
    if (s_pLocalPet) s_pLocalPet->Update();
    if (s_pAddonBrowser) s_pAddonBrowser->Update();
    if (s_pMainUIContainer) s_pMainUIContainer->Update();

    return true;
}

// Slot 3: Shutdown
void CXGame::Shutdown() {
    if (!GameGlobals::s_bRunning) return;

    GameLog_Info("Encerrando CXGame...");
    GameGlobals::s_bRunning = false;

    s_pLocalPlayer.reset();
    s_pLocalPet.reset();
    s_pAddonBrowser.reset();
    s_pMainUIContainer.reset();
    s_pPathReader.reset();
    s_pGameSocketHandler.reset();
    s_pFlyPathTable.reset();
    s_pArtiTable.reset();
    s_pAssemblyTable.reset();

    GameLog_Info("CXGame encerrado com sucesso.");
}

// Slot 4: Reset
void CXGame::Reset() {
    GameLog_Info("CXGame::Reset");
}

// Slot 5: LoadLevel
bool CXGame::LoadLevel(const char* szLevel, const char* szMission) {
    GameLog_Info("CXGame::LoadLevel '%s' (Missao: '%s')", szLevel ? szLevel : "null", szMission ? szMission : "null");
    return true;
}

// Slot 6: GetName
const char* CXGame::GetName() {
    return m_gameName.c_str();
}

// Slot 7: Process
void CXGame::Process() {
}

// Slot 8: IsClient
bool CXGame::IsClient() {
    return !m_bDedicated;
}

// Slot 9: GetFootPoint
bool CXGame::GetFootPoint(int index, void* pOutPoint) {
    (void)index; (void)pOutPoint;
    return false;
}

// Slot 10: SetFootPoint
void CXGame::SetFootPoint(int index, void* pInPoint) {
    (void)index; (void)pInPoint;
}

// Slot 11: GetFootPointCount
int CXGame::GetFootPointCount() {
    return m_footPointCount;
}

// Slot 12: GetSubObject
void* CXGame::GetSubObject(int subId) {
    (void)subId;
    return nullptr;
}

// Slot 13: TestRoutine13
void CXGame::TestRoutine13(int a1, void* a2) {
    (void)a1; (void)a2;
}

// Slot 14: SendAboutToPlay
bool CXGame::SendAboutToPlay() {
    return true;
}

// Slot 15: ProcessMovements
void CXGame::ProcessMovements() {
}

// Slot 16: OnLevelPreload
void CXGame::OnLevelPreload() {
}

// Slot 17: LoadMaterialDB
bool CXGame::LoadMaterialDB(const char* szPath) {
    (void)szPath;
    return true;
}

// Slot 18: GetCharactersFromEntitySystem
void* CXGame::GetCharactersFromEntitySystem() {
    return nullptr;
}

// Slot 19: OnWeaponSwitch
void CXGame::OnWeaponSwitch() {
}

// Slot 20: OnPlayerAction
void CXGame::OnPlayerAction(int actionId) {
    (void)actionId;
}

// Slot 21: PlaySystemSound
void CXGame::PlaySystemSound(const char* szSoundName, int id) {
    (void)szSoundName; (void)id;
}

// Slot 22: StopSystemSound
void CXGame::StopSystemSound(int soundId) {
    (void)soundId;
}

// Slot 23: OnQuitYes
void CXGame::OnQuitYes() {
    QuitGame(0);
}

// Slot 24: LoadLoginUI
bool CXGame::LoadLoginUI() {
    return true;
}

// Slot 25: UnloadLoginUI
void CXGame::UnloadLoginUI() {
}

// Slot 26: SetTargetCharScale
void CXGame::SetTargetCharScale(float scale, float armScale, float legScale) {
    (void)scale; (void)armScale; (void)legScale;
}

// Slot 27: SetPseudoFullscreen
void CXGame::SetPseudoFullscreen(bool bEnable) {
    m_bPseudoFullscreen = bEnable;
}

// Slot 28: UpdateDisplayMode
void CXGame::UpdateDisplayMode() {
}

// Slot 29: GetDebugStatus
const char* CXGame::GetDebugStatus() {
    return "Aion Classic 5.0 Running";
}

// Slot 30: ClearEntityLists
void CXGame::ClearEntityLists() {
}

// Slot 31: SendAuthTicket
bool CXGame::SendAuthTicket() {
    return true;
}

// Slot 32: OnDisconnect
void CXGame::OnDisconnect() {
    GameLog_Info("CXGame::OnDisconnect notificado.");
}

// Slot 33: OnCodingPathFinish
void CXGame::OnCodingPathFinish() {
}

// Slot 34: SendAuxAuthAck
bool CXGame::SendAuxAuthAck() {
    return true;
}

// Slot 35: OnActionComplete
void CXGame::OnActionComplete() {
}

// Slot 36: UpdateCameraMode
void CXGame::UpdateCameraMode() {
}

// Slot 37: OnEnvironmentUpdate
void CXGame::OnEnvironmentUpdate() {
}

// Slot 38: GetAccountID
const char* CXGame::GetAccountID() {
    return m_accountID.c_str();
}

// Slot 39: GetGameVersion
const char* CXGame::GetGameVersion() {
    return m_gameVersion.c_str();
}

// Slot 40: GetBuildNumber
int CXGame::GetBuildNumber() {
    return 5001;
}

// Slot 41: GetPatchVersion
const char* CXGame::GetPatchVersion() {
    return m_patchVersion.c_str();
}

// Slot 42: GetSecurityToken
const char* CXGame::GetSecurityToken(int tokenType) {
    (void)tokenType;
    return m_securityToken.c_str();
}

// Slot 43: ValidateSecurityToken
bool CXGame::ValidateSecurityToken(const char* token) {
    return token != nullptr;
}

// Slot 44: RefreshSecurityToken
void CXGame::RefreshSecurityToken() {
}

// Slot 45: GetSecurityTokenStatus
int CXGame::GetSecurityTokenStatus() {
    return 1; // Valid
}

// Slot 46: ClearSecurityToken
void CXGame::ClearSecurityToken() {
    m_securityToken.clear();
}

// Slot 47: SetSecurityToken
void CXGame::SetSecurityToken(const char* token) {
    if (token) m_securityToken = token;
}

// Slot 48: HasValidSecurityToken
bool CXGame::HasValidSecurityToken() {
    return !m_securityToken.empty();
}

// Slot 49: OnSecurityTokenExpired
void CXGame::OnSecurityTokenExpired() {
}

// Slot 50: LogSecurityEvent
void CXGame::LogSecurityEvent(int eventId) {
    (void)eventId;
}

// Slot 51: OnPlayerStanceChanged
void CXGame::OnPlayerStanceChanged() {
}

// Slot 52: QuitGame
void CXGame::QuitGame(int exitCode) {
    (void)exitCode;
    m_bQuitting = true;
    Shutdown();
}

// Slot 53: CancelQuitGame
void CXGame::CancelQuitGame() {
    m_bQuitting = false;
}

// Slot 54: IsQuittingGame
bool CXGame::IsQuittingGame() {
    return m_bQuitting;
}

// Slot 55: PostSystemMessage
void CXGame::PostSystemMessage(const char* szMsg, int msgType) {
    (void)msgType;
    if (szMsg) GameLog_Info("CXGame SystemMessage: %s", szMsg);
}

// Slot 56: ClearSystemMessages
void CXGame::ClearSystemMessages() {
}

// Slot 57: UpdateHUDState
void CXGame::UpdateHUDState() {
}

// Slot 58: SetAccountID
void CXGame::SetAccountID(const char* szAccount) {
    if (szAccount) m_accountID = szAccount;
}

// Slot 59: OnNetworkLatencyUpdate
void CXGame::OnNetworkLatencyUpdate(int pingMs) {
    (void)pingMs;
}

// Slot 60: SetSSDMode
void CXGame::SetSSDMode(bool bSSD) {
    m_bSSDMode = bSSD;
}

// Slot 61: IsSSDMode
bool CXGame::IsSSDMode() {
    return m_bSSDMode;
}

// Slot 62: SendPlayPacket
bool CXGame::SendPlayPacket() {
    return true;
}

// Slot 63: RegisterHotKey
bool CXGame::RegisterHotKey(uint32_t keyId, uint32_t modifiers) {
    (void)keyId; (void)modifiers;
    return true;
}

// Slot 64: UnregisterHotKey
bool CXGame::UnregisterHotKey(uint32_t keyId) {
    (void)keyId;
    return true;
}

// Slot 65: ProcessHotKey
void CXGame::ProcessHotKey(uint32_t keyId) {
    (void)keyId;
}

// Slot 66: OnFocusChanged
void CXGame::OnFocusChanged(bool bFocused) {
    (void)bFocused;
}

// Slot 67: RecvPacket
bool CXGame::RecvPacket(uint16_t opcode, const uint8_t* pData, uint32_t size) {
    (void)opcode; (void)pData; (void)size;
    return true;
}

// Slot 68: FlushPackets
void CXGame::FlushPackets() {
}

// Slot 69: SetQuestIndicatorTitle
void CXGame::SetQuestIndicatorTitle(const char* szTitle, float fps) {
    (void)szTitle; (void)fps;
}

// Slot 70: UpdateQuestTracker
void CXGame::UpdateQuestTracker() {
}

// Slot 71: SendGameEnterRequest
bool CXGame::SendGameEnterRequest() {
    return true;
}

// Slot 72: OnWorldLoaded
void CXGame::OnWorldLoaded() {
    GameLog_Info("CXGame::OnWorldLoaded disparado.");
}

// Slot 73: OnWorldUnloaded
void CXGame::OnWorldUnloaded() {
    GameLog_Info("CXGame::OnWorldUnloaded disparado.");
}

// Slot 74: UpdateTerrainStreaming
void CXGame::UpdateTerrainStreaming() {
}

// Slot 75: UpdateEntityStreaming
void CXGame::UpdateEntityStreaming() {
}

// Slot 76: TestShugoNPC
void CXGame::TestShugoNPC(const char* name) {
    (void)name;
}

// Slot 77: TriggerCinematic
void CXGame::TriggerCinematic(int seqId) {
    (void)seqId;
}

// Slot 78: StopCinematic
void CXGame::StopCinematic() {
}

// Slot 79: IsInCinematic
bool CXGame::IsInCinematic() {
    return false;
}

// Slot 80: SetCinematicSpeed
void CXGame::SetCinematicSpeed(float speed) {
    (void)speed;
}

// Slot 81: OnCinematicEnd
void CXGame::OnCinematicEnd() {
}

// Slot 82: SendWorldEnterAck
bool CXGame::SendWorldEnterAck() {
    return true;
}

// Slot 83: SendPlayerReady
bool CXGame::SendPlayerReady() {
    return true;
}

// Slot 84: ProcessShugoDialog
void CXGame::ProcessShugoDialog(int npcId) {
    (void)npcId;
}

// Slot 85: ProcessShugoTrade
void CXGame::ProcessShugoTrade(int npcId) {
    (void)npcId;
}

// Slot 86: LoadLevelListen
bool CXGame::LoadLevelListen(const char* szLevel) {
    (void)szLevel;
    return true;
}

// Slot 87: ProcessShugoQuest
void CXGame::ProcessShugoQuest(int npcId) {
    (void)npcId;
}

// Slot 88: OnPlayerFlyStart
void CXGame::OnPlayerFlyStart() {
}

// Slot 89: OnPlayerFlyEnd
void CXGame::OnPlayerFlyEnd() {
}

// Slot 90: ShowEndingUI
void CXGame::ShowEndingUI(const char* szEnding) {
    (void)szEnding;
}

// Slot 91: HideEndingUI
void CXGame::HideEndingUI() {
}

// Slot 92: OnWeatherChangeImmediate
void CXGame::OnWeatherChangeImmediate(int weatherId) {
    (void)weatherId;
}

// Slot 93: LoadEventSoundTable
bool CXGame::LoadEventSoundTable(const char* szPath) {
    (void)szPath;
    return true;
}

// Slot 94: GetPlayerWeapons
void CXGame::GetPlayerWeapons(void* pSlot1, void* pSlot2, void* pTorso) {
    (void)pSlot1; (void)pSlot2; (void)pTorso;
}

// Slot 95: PlayGossipSound
void CXGame::PlayGossipSound(const char* szNpcVoice) {
    (void)szNpcVoice;
}

// Slot 96: ShowFPSCounter
void CXGame::ShowFPSCounter(bool bShow) {
    (void)bShow;
}

// Slot 97: LoadWorldLevel
bool CXGame::LoadWorldLevel(const char* szLevel, const char* szWorldXml) {
    (void)szLevel; (void)szWorldXml;
    return true;
}

// Slot 98: OnNpcSpawn
void CXGame::OnNpcSpawn(uint32_t npcId) {
    (void)npcId;
}

// Slot 99: OnNpcDespawn
void CXGame::OnNpcDespawn(uint32_t npcId) {
    (void)npcId;
}

// Slot 100: OnNpcAction
void CXGame::OnNpcAction(uint32_t npcId, int action) {
    (void)npcId; (void)action;
}

// Slot 101: OnNpcSay
void CXGame::OnNpcSay(uint32_t npcId, const char* szText) {
    (void)npcId; (void)szText;
}

// Slot 102: OnPlayerLevelUp
void CXGame::OnPlayerLevelUp(int newLevel) {
    (void)newLevel;
}

// Slot 103: OnPlayerDeath
void CXGame::OnPlayerDeath() {
}

// Slot 104: OnPlayerResurrect
void CXGame::OnPlayerResurrect() {
}

// Slot 105: UpdatePartyHUD
void CXGame::UpdatePartyHUD() {
}

// Slot 106: UpdateAllianceHUD
void CXGame::UpdateAllianceHUD() {
}

// Slot 107: UpdateLegionHUD
void CXGame::UpdateLegionHUD() {
}

// Slot 108: SpawnMobTest
void CXGame::SpawnMobTest(const char* mobName, int count) {
    (void)mobName; (void)count;
}

// Slot 109: GetPseudoFullscreen
bool CXGame::GetPseudoFullscreen() {
    return m_bPseudoFullscreen;
}

// Slot 110: TogglePseudoFullscreen
void CXGame::TogglePseudoFullscreen() {
    m_bPseudoFullscreen = !m_bPseudoFullscreen;
}

// Slot 111: ConfigureMRTDOF
void CXGame::ConfigureMRTDOF(bool bAuto, float amount) {
    (void)bAuto; (void)amount;
}

// Slot 112: OnGraphicSettingsChanged
void CXGame::OnGraphicSettingsChanged() {
}

// Slot 113: OnSoundSettingsChanged
void CXGame::OnSoundSettingsChanged() {
}

// Slot 114: LoadShortcutKeys
bool CXGame::LoadShortcutKeys(const char* szXml) {
    (void)szXml;
    return true;
}

// Slot 115: OnShugoGreeting
void CXGame::OnShugoGreeting(int npcId) {
    (void)npcId;
}

// Slot 116: OnShugoFarewell
void CXGame::OnShugoFarewell(int npcId) {
    (void)npcId;
}

// Slot 117: UpdateMinimap
void CXGame::UpdateMinimap() {
}

// Slot 118: OnShugoTradeSuccess
void CXGame::OnShugoTradeSuccess(int npcId) {
    (void)npcId;
}

// Slot 119: OnShugoTradeCancel
void CXGame::OnShugoTradeCancel(int npcId) {
    (void)npcId;
}

// Slot 120: OnShugoSpecialOffer
void CXGame::OnShugoSpecialOffer(int npcId) {
    (void)npcId;
}

// Slot 121: OnShugoInventoryFull
void CXGame::OnShugoInventoryFull(int npcId) {
    (void)npcId;
}

// Slot 122: UpdateAmbientSounds
void CXGame::UpdateAmbientSounds() {
}

// Slot 123: OnShugoVoice
void CXGame::OnShugoVoice(const char* szVoice) {
    (void)szVoice;
}

// Slot 124: SetDuckingSound
void CXGame::SetDuckingSound(bool bEnable) {
    m_bDuckingSound = bEnable;
}

// Slot 125: GetDuckingSound
bool CXGame::GetDuckingSound() {
    return m_bDuckingSound;
}

// Slot 126: GetInternalNetworkRange
const char* CXGame::GetInternalNetworkRange() {
    return "172.18.";
}

// Slot 127: IsInternalNetworkAddress
bool CXGame::IsInternalNetworkAddress(const char* szIp) {
    if (!szIp) return false;
    return std::strncmp(szIp, "172.18.", 7) == 0 || std::strncmp(szIp, "127.0.0.1", 9) == 0;
}

// Slot 128: ProcessBackgroundTasks
void CXGame::ProcessBackgroundTasks() {
}

// Slot 129: RegisterGameHotKey
bool CXGame::RegisterGameHotKey(uint32_t hotkeyId, uint32_t key, uint32_t mod) {
    (void)hotkeyId; (void)key; (void)mod;
    return true;
}

// Slot 130: UnregisterGameHotKey
bool CXGame::UnregisterGameHotKey(uint32_t hotkeyId) {
    (void)hotkeyId;
    return true;
}

// IConsoleSink implementation (offset 8)
void CXGame::OnConsoleCommand(const char* szCommand) {
    GameLog_Info("CXGame::OnConsoleCommand '%s'", szCommand ? szCommand : "null");
}

// IInputEventListener implementation (offset 16)
bool CXGame::OnInputEvent(void* pEvent) {
    (void)pEvent;
    return false;
}

// Liberação de instância
void CXGame::Release() {
    delete this;
}
