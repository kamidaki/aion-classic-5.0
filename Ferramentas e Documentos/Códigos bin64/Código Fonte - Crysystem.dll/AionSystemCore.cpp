#include "AionSystemCore.h"
#include "ncsoft/GameOptions.h"
#include "ncsoft/GameFixedFrame.h"
#include "ncsoft/CharacterLODManager.h"
#include "ncsoft/LITELauncherManager.h"
#include "ncsoft/SdoaLogin.h"
#include "ncsoft/CryFileMonitor.h"
#include <cstring>
#include <cstdio>

typedef void* (*PFN_CREATE_GAME_INSTANCE)(ISystem* pSys);

// Global subsystem instances
static GameOptions*         g_pGameOptions = nullptr;
static GameFixedFrame*      g_pGameFixedFrame = nullptr;
static CharacterLODManager* g_pCharacterLODManager = nullptr;
static LITELauncherManager* g_pLITELauncherManager = nullptr;
static SdoaLogin*           g_pSdoaLogin = nullptr;
static CryFileMonitor*      g_pCryFileMonitor = nullptr;

CSystem::CSystem()
    : m_pGame(nullptr),
      m_dwLoadingState(0),
      m_pad3624(0),
      m_fLoadingProgress(0.0f),
      m_pad362C(0),
      m_perfFreq(0),
      m_authStatus(1),
      m_nGameVersion(5026),
      m_nBuildNumber(7307)
{
    memset(m_cryCommonPadding, 0, sizeof(m_cryCommonPadding));
    memset(m_padBeforeUser, 0, sizeof(m_padBeforeUser));
    memset(m_szUserName, 0, sizeof(m_szUserName));
    memset(m_padBeforePerf, 0, sizeof(m_padBeforePerf));
    memset(m_padBeforeAuth, 0, sizeof(m_padBeforeAuth));
    memset(m_padBeforeVer, 0, sizeof(m_padBeforeVer));

    strncpy_s(m_szUserName, sizeof(m_szUserName), "AionClassicUser", _TRUNCATE);

    LARGE_INTEGER freq;
    if (QueryPerformanceFrequency(&freq))
    {
        m_perfFreq = freq.QuadPart;
    }

    if (!g_pGameOptions) g_pGameOptions = new GameOptions();
    if (!g_pGameFixedFrame) g_pGameFixedFrame = new GameFixedFrame();
    if (!g_pCharacterLODManager) g_pCharacterLODManager = new CharacterLODManager();
    if (!g_pLITELauncherManager) g_pLITELauncherManager = new LITELauncherManager();
    if (!g_pSdoaLogin) g_pSdoaLogin = new SdoaLogin();
    if (!g_pCryFileMonitor) g_pCryFileMonitor = new CryFileMonitor();
}

CSystem::~CSystem()
{
    ShutDown(false);
}

bool CSystem::CreateGame(const SGameInitParams& params)
{
    printf("[CrySystem::CreateGame] Started CreateGame...\n");
    fflush(stdout);

    if (params.pGame)
    {
        m_pGame = params.pGame;
        return true;
    }

    const char* dllName = params.sGameDLL ? params.sGameDLL : "Game.dll";
    printf("[CrySystem::CreateGame] Target DLL: %s\n", dllName);
    fflush(stdout);

    wchar_t wszDllName[MAX_PATH];
    MultiByteToWideChar(CP_UTF8, 0, dllName, -1, wszDllName, MAX_PATH);
    HMODULE hGameDll = LoadLibraryW(wszDllName);
    if (!hGameDll)
    {
        MultiByteToWideChar(CP_ACP, 0, dllName, -1, wszDllName, MAX_PATH);
        hGameDll = LoadLibraryW(wszDllName);
    }
    if (!hGameDll)
    {
        hGameDll = LoadLibraryW(L"Game.dll");
        if (!hGameDll)
        {
            hGameDll = LoadLibraryW(L"bin64\\Game.dll");
        }
    }
    if (!hGameDll)
    {
        printf("[CrySystem::CreateGame] LoadLibraryW failed for %s! Error: %lu\n", dllName, GetLastError());
        fflush(stdout);
        Error("Error in CSystem::CreateGame, failed to load %s", dllName);
        return false;
    }
    printf("[CrySystem::CreateGame] Game.dll loaded at %p\n", hGameDll);
    fflush(stdout);

    PFN_CREATE_GAME_INSTANCE pfnCreate = (PFN_CREATE_GAME_INSTANCE)GetProcAddress(hGameDll, "CreateGameInstance");
    if (!pfnCreate)
    {
        // Ordinal 1 fallback
        pfnCreate = (PFN_CREATE_GAME_INSTANCE)GetProcAddress(hGameDll, (LPCSTR)1);
    }

    if (!pfnCreate)
    {
        printf("[CrySystem::CreateGame] CreateGameInstance not found in Game.dll!\n");
        fflush(stdout);
        Error("Error in CSystem::CreateGame, CreateGameInstance entry point not found in %s", dllName);
        return false;
    }
    printf("[CrySystem::CreateGame] Found CreateGameInstance at %p\n", pfnCreate);
    fflush(stdout);

    m_pGame = reinterpret_cast<IGame*>(pfnCreate(this));
    if (!m_pGame)
    {
        printf("[CrySystem::CreateGame] CreateGameInstance returned NULL!\n");
        fflush(stdout);
        Error("Error in CSystem::CreateGame, CreateGameInstance returned NULL");
        return false;
    }
    printf("[CrySystem::CreateGame] CXGame instance created at %p\n", m_pGame);
    fflush(stdout);

    // Call Game->Init(ISystem* pSystem, bool bInEditor, bool bDedicated)
    // Primary VTable slot 0 of CXGame
    typedef bool (__fastcall *PFN_GAME_INIT)(void* pThis, ISystem* pSys, bool bEditor, bool bDedicated);
    void** gameVTable = *reinterpret_cast<void***>(m_pGame);
    PFN_GAME_INIT pfnInit = reinterpret_cast<PFN_GAME_INIT>(gameVTable[0]);
    if (pfnInit)
    {
        printf("[CrySystem::CreateGame] Calling CXGame::Init(pSystem=%p, bEditor=false, bDedicated=%d)...\n",
               this, params.bDedicatedServer ? 1 : 0);
        fflush(stdout);
        bool bInitRes = pfnInit(m_pGame, this, false, params.bDedicatedServer);
        printf("[CrySystem::CreateGame] CXGame::Init returned %s\n", bInitRes ? "true" : "false");
        fflush(stdout);
    }

    return true;
}

bool CSystem::IsLoadingScreenEnabled()
{
    return (m_dwLoadingState == 1);
}

bool CSystem::IsPreloadDone()
{
    return (m_dwLoadingState == 2);
}

void CSystem::SetLoadingProgress(float progress)
{
    m_fLoadingProgress = progress;
}

void CSystem::Release()
{
    delete this;
}

void CSystem::ShutDown(bool bRelaunch)
{
    (void)bRelaunch;
    if (m_pGame)
    {
        // Call Game->Shutdown()
        m_pGame = nullptr;
    }
}

bool CSystem::WasInDevMode()
{
    return false;
}

void CSystem::Relaunch(bool bRelaunch)
{
    (void)bRelaunch;
}

void CSystem::UpdateLoadingScreen()
{
}

void CSystem::RenderBegin()
{
}

void CSystem::Render()
{
}

void CSystem::RenderEnd()
{
}

void CSystem::RenderStatistics()
{
}

void CSystem::DumpMemoryUsageStatistics()
{
}

void CSystem::Quit()
{
    PostQuitMessage(0);
}

bool CSystem::IsQuitting()
{
    return false;
}

void CSystem::Error(const char* sFormat, ...)
{
    char buf[1024];
    va_list args;
    va_start(args, sFormat);
    vsnprintf(buf, sizeof(buf), sFormat, args);
    va_end(args);
    OutputDebugStringA("[CrySystem ERROR] ");
    OutputDebugStringA(buf);
    OutputDebugStringA("\n");
}

void CSystem::Warning(int module, int severity, int flags, const char* file, const char* format, ...)
{
    (void)module; (void)severity; (void)flags; (void)file;
    char buf[1024];
    va_list args;
    va_start(args, format);
    vsnprintf(buf, sizeof(buf), format, args);
    va_end(args);
    OutputDebugStringA("[CrySystem WARNING] ");
    OutputDebugStringA(buf);
    OutputDebugStringA("\n");
}

bool CSystem::CheckLogVerbosity(int verbosity)
{
    return (verbosity <= 3);
}

bool CSystem::IsDedicated()
{
    return false;
}

bool CSystem::Update(int updateFlags, int nPauseMode)
{
    (void)updateFlags; (void)nPauseMode;
    if (g_pGameFixedFrame)
    {
        g_pGameFixedFrame->BeginFrameWait();
    }
    if (m_pGame)
    {
        // Delegate update to CXGame
        typedef bool (__fastcall *PFN_GAME_UPDATE)(void* pThis);
        void** gameVTable = *reinterpret_cast<void***>(m_pGame);
        PFN_GAME_UPDATE pfnUpdate = reinterpret_cast<PFN_GAME_UPDATE>(gameVTable[2]); // Slot 2 = Update
        if (pfnUpdate)
        {
            pfnUpdate(m_pGame);
        }
    }
    return true;
}

void CSystem::UpdateScriptSink()
{
}

void CSystem::SetForceNonDevMode(const bool bValue)
{
    (void)bValue;
}

bool CSystem::GetForceNonDevMode() const
{
    return true;
}

bool CSystem::IsDevMode() const
{
    return false;
}

void CSystem::SetViewCamera(void* pCamera)
{
    (void)pCamera;
}

void* CSystem::GetViewCamera()
{
    return nullptr;
}

void CSystem::CreateEntityScriptBinding(void* pEntity)
{
    (void)pEntity;
}

void CSystem::IgnoreUpdates(bool bIgnore)
{
    (void)bIgnore;
}

// Slot 29: GetIGame
IGame* CSystem::GetIGame()
{
    return m_pGame;
}

INetwork* CSystem::GetINetwork() { return nullptr; }
IRenderer* CSystem::GetIRenderer() { return nullptr; }
IInput* CSystem::GetIInput() { return nullptr; }
ITimer* CSystem::GetITimer() { return nullptr; }
ICryPak* CSystem::GetIPak() { return nullptr; }
IConsole* CSystem::GetIConsole() { return nullptr; }
IScriptSystem* CSystem::GetIScriptSystem() { return nullptr; }
I3DEngine* CSystem::GetI3DEngine() { return nullptr; }
ICryCharManager* CSystem::GetIAnimationSystem() { return nullptr; }
ISoundSystem* CSystem::GetISoundSystem() { return nullptr; }
IMusicSystem* CSystem::GetIMusicSystem() { return nullptr; }
IPhysicalWorld* CSystem::GetIPhysicalWorld() { return nullptr; }
IMovieSystem* CSystem::GetIMovieSystem() { return nullptr; }
IAISystem* CSystem::GetAISystem() { return nullptr; }
IMemoryManager* CSystem::GetIMemoryManager() { return nullptr; }
IEntitySystem* CSystem::GetIEntitySystem() { return nullptr; }
ICryFont* CSystem::GetICryFont() { return nullptr; }
ILog* CSystem::GetILog() { return nullptr; }
IStreamEngine* CSystem::GetStreamEngine() { return nullptr; }
CLUADbg* CSystem::GetLuaDebugger() { return nullptr; }
IValidator* CSystem::GetIValidator() { return nullptr; }
IFrameProfileSystem* CSystem::GetIProfileSystem() { return nullptr; }

const char* CSystem::GetUserName()
{
    return m_szUserName;
}

int CSystem::GetCPUFlags() { return 0x1F; }
double CSystem::GetSecondsPerCycle() { return 1.0 / static_cast<double>(m_perfFreq ? m_perfFreq : 10000000); }
float CSystem::GetGCFrequency() { return 10.0f; }
void CSystem::SetGCFrequency(float fRate) { (void)fRate; }
void CSystem::DebugStats(bool checkpoint, bool leaks) { (void)checkpoint; (void)leaks; }
void CSystem::DumpWinHeaps() {}
int CSystem::DumpMMStats(bool log) { (void)log; return 0; }
void* CSystem::GetFileVersion() { return &m_nGameVersion; }
void* CSystem::GetProductVersion() { return &m_nBuildNumber; }
void* CSystem::CreateXMLDocument() { return nullptr; }
void* CSystem::CreateXmlNode(const char* sNodeName) { (void)sNodeName; return nullptr; }
void* CSystem::LoadXmlFile(const char* sFilename) { (void)sFilename; return nullptr; }
void* CSystem::LoadXmlFromString(const char* sXmlString) { (void)sXmlString; return nullptr; }
void CSystem::SetIProcess(void* pProcess) { (void)pProcess; }
void* CSystem::GetIProcess() { return nullptr; }
IRenderer* CSystem::CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) { (void)fullscreen; (void)hinst; (void)hWndAttach; return nullptr; }
bool CSystem::IsTestMode() const { return false; }
void CSystem::ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) { (void)pszSourceFile; (void)iLine; (void)pszReason; }
void CSystem::SetFrameProfiler(bool on, bool display, char* prefix) { (void)on; (void)display; (void)prefix; }

// Slot 72: OnEnvironmentUpdate -> calls CXGame::OnEnvironmentUpdate() at VTable slot 37 (+0x128)
void CSystem::OnEnvironmentUpdate()
{
    if (m_pGame)
    {
        typedef void (__fastcall *PFN_ENV_UPDATE)(void* pThis);
        void** gameVTable = *reinterpret_cast<void***>(m_pGame);
        PFN_ENV_UPDATE pfnEnv = reinterpret_cast<PFN_ENV_UPDATE>(gameVTable[37]); // Slot 37 = 0x128
        if (pfnEnv)
        {
            pfnEnv(m_pGame);
        }
    }
}

// Slots 73..148 stubs
void CSystem::Slot73() {}
void CSystem::Slot74() {}
void CSystem::Slot75() {}
void CSystem::Slot76() {}
void CSystem::Slot77() {}
void CSystem::Slot78() {}
void CSystem::Slot79() {}
void CSystem::Slot80() {}
void CSystem::Slot81() {}
void CSystem::Slot82() {}
void CSystem::Slot83() {}
void CSystem::Slot84() {}
void CSystem::Slot85() {}
void CSystem::Slot86() {}
void CSystem::Slot87() {}
void CSystem::Slot88() {}
void CSystem::Slot89() {}
void CSystem::Slot90() {}
void CSystem::Slot91() {}
void CSystem::Slot92() {}
void CSystem::Slot93() {}
void CSystem::Slot94() {}
void CSystem::Slot95() {}
void CSystem::Slot96() {}
void CSystem::Slot97() {}
void CSystem::Slot98() {}
void CSystem::Slot99() {}
void CSystem::Slot100() {}
void CSystem::Slot101() {}
void CSystem::Slot102() {}
void CSystem::Slot103() {}
void CSystem::Slot104() {}
void CSystem::Slot105() {}
void CSystem::Slot106() {}
void CSystem::Slot107() {}
void CSystem::Slot108() {}
void CSystem::Slot109() {}
void CSystem::Slot110() {}
void CSystem::Slot111() {}
void CSystem::Slot112() {}
void CSystem::Slot113() {}
void CSystem::Slot114() {}
void CSystem::Slot115() {}
void CSystem::Slot116() {}
void CSystem::Slot117() {}
void CSystem::Slot118() {}
void CSystem::Slot119() {}
void CSystem::Slot120() {}
void CSystem::Slot121() {}
void CSystem::Slot122() {}
void CSystem::Slot123() {}
void CSystem::Slot124() {}
void CSystem::Slot125() {}
void CSystem::Slot126() {}
void CSystem::Slot127() {}
void CSystem::Slot128() {}
void CSystem::Slot129() {}
void CSystem::Slot130() {}
void CSystem::Slot131() {}
void CSystem::Slot132() {}
void CSystem::Slot133() {}
void CSystem::Slot134() {}
void CSystem::Slot135() {}
void CSystem::Slot136() {}
void CSystem::Slot137() {}
void CSystem::Slot138() {}
void CSystem::Slot139() {}
void CSystem::Slot140() {}
void CSystem::Slot141() {}
void CSystem::Slot142() {}
void CSystem::Slot143() {}
void CSystem::Slot144() {}
void CSystem::Slot145() {}
void CSystem::Slot146() {}
void CSystem::Slot147() {}
void CSystem::Slot148() {}

// Slot 149: Init
bool CSystem::Init(const SSystemInitParams& params)
{
    if (params.pUserCallback)
    {
        // Setup user callback
    }
    if (g_pGameOptions)
    {
        g_pGameOptions->Init();
    }
    OutputDebugStringA("[CrySystem] Aion Classic 5.0 CrySystem Core Initialized Successfully.\n");
    return true;
}

GameOptions*         CSystem::GetGameOptions() { return g_pGameOptions; }
GameFixedFrame*      CSystem::GetGameFixedFrame() { return g_pGameFixedFrame; }
CharacterLODManager* CSystem::GetCharacterLODManager() { return g_pCharacterLODManager; }
LITELauncherManager* CSystem::GetLITELauncherManager() { return g_pLITELauncherManager; }
SdoaLogin*           CSystem::GetSdoaLogin() { return g_pSdoaLogin; }
CryFileMonitor*      CSystem::GetCryFileMonitor() { return g_pCryFileMonitor; }
