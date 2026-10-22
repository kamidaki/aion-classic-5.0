#pragma once

#ifndef _AIONSYSTEMCORE_H_
#define _AIONSYSTEMCORE_H_

#include <windows.h>
#include <cstdint>
#include <cstdio>

// Forward declarations
struct IGame;
struct INetwork;
struct IRenderer;
struct IInput;
struct ITimer;
struct ICryPak;
struct IConsole;
struct IScriptSystem;
struct I3DEngine;
struct ICryCharManager;
struct ISoundSystem;
struct IMusicSystem;
class  IPhysicalWorld;
struct IMovieSystem;
struct IAISystem;
struct IMemoryManager;
struct IEntitySystem;
struct ICryFont;
struct ILog;
struct IStreamEngine;
class  CLUADbg;
struct IValidator;
struct IFrameProfileSystem;
struct SGameInitParams;
struct SSystemInitParams;
class  GameOptions;
class  GameFixedFrame;
class  CharacterLODManager;
class  LITELauncherManager;
class  SdoaLogin;
class  CryFileMonitor;

#pragma pack(push, 8)

// SSystemInitParams for Aion Classic 5.0 (size >= 0x840, pSystem at +0x838)
struct SSystemInitParams
{
    void* hInstance;                // +0x00
    void* hWnd;                     // +0x08
    char  szSystemCmdLine[2048];    // +0x10 .. +0x810
    void* pUserCallback;            // +0x810
    void* pLog;                     // +0x818
    void* pValidator;               // +0x820
    const char* sLogFileName;       // +0x828
    bool  bEditor;                  // +0x830
    bool  bPreview;                 // +0x831
    bool  bTestMode;                // +0x832
    bool  bDedicatedServer;         // +0x833
    uint32_t pad0;                  // +0x834
    void* pSystem;                  // +0x838: Pointer to pre-existing ISystem if any
};

struct SGameInitParams
{
    const char* sGameDLL;           // +0x00
    IGame*      pGame;              // +0x08
    bool        bDedicatedServer;   // +0x10
};

// Official 151 virtual slots matching CrySystem.dll primary VTable at 0x1801e8558
struct ISystem
{
    // Slot 0: CreateGame
    virtual bool CreateGame(const SGameInitParams& params) = 0;
    // Slot 1: IsLoadingScreenEnabled
    virtual bool IsLoadingScreenEnabled() = 0;
    // Slot 2: IsPreloadDone
    virtual bool IsPreloadDone() = 0;
    // Slot 3: SetLoadingProgress
    virtual void SetLoadingProgress(float progress) = 0;
    // Slot 4: Release
    virtual void Release() = 0;
    // Slot 5: ShutDown
    virtual void ShutDown(bool bRelaunch) = 0;
    // Slot 6: WasInDevMode
    virtual bool WasInDevMode() = 0;
    // Slot 7: Relaunch
    virtual void Relaunch(bool bRelaunch) = 0;
    // Slot 8: UpdateLoadingScreen
    virtual void UpdateLoadingScreen() = 0;
    // Slot 9: RenderBegin
    virtual void RenderBegin() = 0;
    // Slot 10: Render
    virtual void Render() = 0;
    // Slot 11: RenderEnd
    virtual void RenderEnd() = 0;
    // Slot 12: RenderStatistics
    virtual void RenderStatistics() = 0;
    // Slot 13: DumpMemoryUsageStatistics
    virtual void DumpMemoryUsageStatistics() = 0;
    // Slot 14: Quit
    virtual void Quit() = 0;
    // Slot 15: IsQuitting
    virtual bool IsQuitting() = 0;
    // Slot 16: Error
    virtual void Error(const char* sFormat, ...) = 0;
    // Slot 17: Warning
    virtual void Warning(int module, int severity, int flags, const char* file, const char* format, ...) = 0;
    // Slot 18: CheckLogVerbosity
    virtual bool CheckLogVerbosity(int verbosity) = 0;
    // Slot 19: IsDedicated
    virtual bool IsDedicated() = 0;
    // Slot 20: Update
    virtual bool Update(int updateFlags, int nPauseMode) = 0;
    // Slot 21: UpdateScriptSink
    virtual void UpdateScriptSink() = 0;
    // Slot 22: SetForceNonDevMode
    virtual void SetForceNonDevMode(const bool bValue) = 0;
    // Slot 23: GetForceNonDevMode
    virtual bool GetForceNonDevMode() const = 0;
    // Slot 24: IsDevMode
    virtual bool IsDevMode() const = 0;
    // Slot 25: SetViewCamera
    virtual void SetViewCamera(void* pCamera) = 0;
    // Slot 26: GetViewCamera
    virtual void* GetViewCamera() = 0;
    // Slot 27: CreateEntityScriptBinding
    virtual void CreateEntityScriptBinding(void* pEntity) = 0;
    // Slot 28: IgnoreUpdates
    virtual void IgnoreUpdates(bool bIgnore) = 0;

    // Slot 29 (0x0E8): GetIGame -> reads [this + 0x3618]
    virtual IGame* GetIGame() = 0;
    // Slot 30: GetINetwork
    virtual INetwork* GetINetwork() = 0;
    // Slot 31: GetIRenderer
    virtual IRenderer* GetIRenderer() = 0;
    // Slot 32: GetIInput
    virtual IInput* GetIInput() = 0;
    // Slot 33: GetITimer
    virtual ITimer* GetITimer() = 0;
    // Slot 34: GetIPak
    virtual ICryPak* GetIPak() = 0;
    // Slot 35: GetIConsole
    virtual IConsole* GetIConsole() = 0;
    // Slot 36: GetIScriptSystem
    virtual IScriptSystem* GetIScriptSystem() = 0;
    // Slot 37: GetI3DEngine
    virtual I3DEngine* GetI3DEngine() = 0;
    // Slot 38: GetIAnimationSystem
    virtual ICryCharManager* GetIAnimationSystem() = 0;
    // Slot 39: GetISoundSystem
    virtual ISoundSystem* GetISoundSystem() = 0;
    // Slot 40: GetIMusicSystem
    virtual IMusicSystem* GetIMusicSystem() = 0;
    // Slot 41: GetIPhysicalWorld
    virtual IPhysicalWorld* GetIPhysicalWorld() = 0;
    // Slot 42: GetIMovieSystem
    virtual IMovieSystem* GetIMovieSystem() = 0;
    // Slot 43: GetAISystem
    virtual IAISystem* GetAISystem() = 0;
    // Slot 44: GetIMemoryManager
    virtual IMemoryManager* GetIMemoryManager() = 0;
    // Slot 45: GetIEntitySystem
    virtual IEntitySystem* GetIEntitySystem() = 0;
    // Slot 46: GetICryFont
    virtual ICryFont* GetICryFont() = 0;
    // Slot 47: GetILog
    virtual ILog* GetILog() = 0;
    // Slot 48: GetStreamEngine
    virtual IStreamEngine* GetStreamEngine() = 0;
    // Slot 49: GetLuaDebugger
    virtual CLUADbg* GetLuaDebugger() = 0;
    // Slot 50: GetIValidator
    virtual IValidator* GetIValidator() = 0;
    // Slot 51: GetIProfileSystem
    virtual IFrameProfileSystem* GetIProfileSystem() = 0;
    // Slot 52: GetUserName
    virtual const char* GetUserName() = 0;
    // Slot 53: GetCPUFlags
    virtual int GetCPUFlags() = 0;
    // Slot 54: GetSecondsPerCycle
    virtual double GetSecondsPerCycle() = 0;
    // Slot 55: GetGCFrequency
    virtual float GetGCFrequency() = 0;
    // Slot 56: SetGCFrequency
    virtual void SetGCFrequency(float fRate) = 0;
    // Slot 57: DebugStats
    virtual void DebugStats(bool checkpoint, bool leaks) = 0;
    // Slot 58: DumpWinHeaps
    virtual void DumpWinHeaps() = 0;
    // Slot 59: DumpMMStats
    virtual int DumpMMStats(bool log) = 0;
    // Slot 60: GetFileVersion
    virtual void* GetFileVersion() = 0;
    // Slot 61: GetProductVersion
    virtual void* GetProductVersion() = 0;
    // Slot 62: CreateXMLDocument
    virtual void* CreateXMLDocument() = 0;
    // Slot 63: CreateXmlNode
    virtual void* CreateXmlNode(const char* sNodeName) = 0;
    // Slot 64: LoadXmlFile
    virtual void* LoadXmlFile(const char* sFilename) = 0;
    // Slot 65: LoadXmlFromString
    virtual void* LoadXmlFromString(const char* sXmlString) = 0;
    // Slot 66: SetIProcess
    virtual void SetIProcess(void* pProcess) = 0;
    // Slot 67: GetIProcess
    virtual void* GetIProcess() = 0;
    // Slot 68: CreateRenderer
    virtual IRenderer* CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) = 0;
    // Slot 69: IsTestMode
    virtual bool IsTestMode() const = 0;
    // Slot 70: ShowDebugger
    virtual void ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) = 0;
    // Slot 71: SetFrameProfiler
    virtual void SetFrameProfiler(bool on, bool display, char* prefix) = 0;

    // Slot 72 (0x240): OnEnvironmentUpdate -> calls m_pGame->OnEnvironmentUpdate()
    virtual void OnEnvironmentUpdate() = 0;

    // Slots 73..148: Auxiliary methods, subsystems, options
    virtual void Slot73() = 0;
    virtual void Slot74() = 0;
    virtual void Slot75() = 0;
    virtual void Slot76() = 0;
    virtual void Slot77() = 0;
    virtual void Slot78() = 0;
    virtual void Slot79() = 0;
    virtual void Slot80() = 0;
    virtual void Slot81() = 0;
    virtual void Slot82() = 0;
    virtual void Slot83() = 0;
    virtual void Slot84() = 0;
    virtual void Slot85() = 0;
    virtual void Slot86() = 0;
    virtual void Slot87() = 0;
    virtual void Slot88() = 0;
    virtual void Slot89() = 0;
    virtual void Slot90() = 0;
    virtual void Slot91() = 0;
    virtual void Slot92() = 0;
    virtual void Slot93() = 0;
    virtual void Slot94() = 0;
    virtual void Slot95() = 0;
    virtual void Slot96() = 0;
    virtual void Slot97() = 0;
    virtual void Slot98() = 0;
    virtual void Slot99() = 0;
    virtual void Slot100() = 0;
    virtual void Slot101() = 0;
    virtual void Slot102() = 0;
    virtual void Slot103() = 0;
    virtual void Slot104() = 0;
    virtual void Slot105() = 0;
    virtual void Slot106() = 0;
    virtual void Slot107() = 0;
    virtual void Slot108() = 0;
    virtual void Slot109() = 0;
    virtual void Slot110() = 0;
    virtual void Slot111() = 0;
    virtual void Slot112() = 0;
    virtual void Slot113() = 0;
    virtual void Slot114() = 0;
    virtual void Slot115() = 0;
    virtual void Slot116() = 0;
    virtual void Slot117() = 0;
    virtual void Slot118() = 0;
    virtual void Slot119() = 0;
    virtual void Slot120() = 0;
    virtual void Slot121() = 0;
    virtual void Slot122() = 0;
    virtual void Slot123() = 0;
    virtual void Slot124() = 0;
    virtual void Slot125() = 0;
    virtual void Slot126() = 0;
    virtual void Slot127() = 0;
    virtual void Slot128() = 0;
    virtual void Slot129() = 0;
    virtual void Slot130() = 0;
    virtual void Slot131() = 0;
    virtual void Slot132() = 0;
    virtual void Slot133() = 0;
    virtual void Slot134() = 0;
    virtual void Slot135() = 0;
    virtual void Slot136() = 0;
    virtual void Slot137() = 0;
    virtual void Slot138() = 0;
    virtual void Slot139() = 0;
    virtual void Slot140() = 0;
    virtual void Slot141() = 0;
    virtual void Slot142() = 0;
    virtual void Slot143() = 0;
    virtual void Slot144() = 0;
    virtual void Slot145() = 0;
    virtual void Slot146() = 0;
    virtual void Slot147() = 0;
    virtual void Slot148() = 0;

    // Slot 149 (0x4A8): Init
    virtual bool Init(const SSystemInitParams& params) = 0;

    // Slot 150 (0x4B0): Virtual Destructor
    virtual ~ISystem() {}
};

// CSystem concrete implementation with exact binary size 0x3708 (14,088 bytes)
class CSystem : public ISystem
{
public:
    CSystem();
    virtual ~CSystem() override;

    // Implementation of all 151 slots
    virtual bool CreateGame(const SGameInitParams& params) override;
    virtual bool IsLoadingScreenEnabled() override;
    virtual bool IsPreloadDone() override;
    virtual void SetLoadingProgress(float progress) override;
    virtual void Release() override;
    virtual void ShutDown(bool bRelaunch) override;
    virtual bool WasInDevMode() override;
    virtual void Relaunch(bool bRelaunch) override;
    virtual void UpdateLoadingScreen() override;
    virtual void RenderBegin() override;
    virtual void Render() override;
    virtual void RenderEnd() override;
    virtual void RenderStatistics() override;
    virtual void DumpMemoryUsageStatistics() override;
    virtual void Quit() override;
    virtual bool IsQuitting() override;
    virtual void Error(const char* sFormat, ...) override;
    virtual void Warning(int module, int severity, int flags, const char* file, const char* format, ...) override;
    virtual bool CheckLogVerbosity(int verbosity) override;
    virtual bool IsDedicated() override;
    virtual bool Update(int updateFlags, int nPauseMode) override;
    virtual void UpdateScriptSink() override;
    virtual void SetForceNonDevMode(const bool bValue) override;
    virtual bool GetForceNonDevMode() const override;
    virtual bool IsDevMode() const override;
    virtual void SetViewCamera(void* pCamera) override;
    virtual void* GetViewCamera() override;
    virtual void CreateEntityScriptBinding(void* pEntity) override;
    virtual void IgnoreUpdates(bool bIgnore) override;

    virtual IGame* GetIGame() override;
    virtual INetwork* GetINetwork() override;
    virtual IRenderer* GetIRenderer() override;
    virtual IInput* GetIInput() override;
    virtual ITimer* GetITimer() override;
    virtual ICryPak* GetIPak() override;
    virtual IConsole* GetIConsole() override;
    virtual IScriptSystem* GetIScriptSystem() override;
    virtual I3DEngine* GetI3DEngine() override;
    virtual ICryCharManager* GetIAnimationSystem() override;
    virtual ISoundSystem* GetISoundSystem() override;
    virtual IMusicSystem* GetIMusicSystem() override;
    virtual IPhysicalWorld* GetIPhysicalWorld() override;
    virtual IMovieSystem* GetIMovieSystem() override;
    virtual IAISystem* GetAISystem() override;
    virtual IMemoryManager* GetIMemoryManager() override;
    virtual IEntitySystem* GetIEntitySystem() override;
    virtual ICryFont* GetICryFont() override;
    virtual ILog* GetILog() override;
    virtual IStreamEngine* GetStreamEngine() override;
    virtual CLUADbg* GetLuaDebugger() override;
    virtual IValidator* GetIValidator() override;
    virtual IFrameProfileSystem* GetIProfileSystem() override;
    virtual const char* GetUserName() override;
    virtual int GetCPUFlags() override;
    virtual double GetSecondsPerCycle() override;
    virtual float GetGCFrequency() override;
    virtual void SetGCFrequency(float fRate) override;
    virtual void DebugStats(bool checkpoint, bool leaks) override;
    virtual void DumpWinHeaps() override;
    virtual int DumpMMStats(bool log) override;
    virtual void* GetFileVersion() override;
    virtual void* GetProductVersion() override;
    virtual void* CreateXMLDocument() override;
    virtual void* CreateXmlNode(const char* sNodeName) override;
    virtual void* LoadXmlFile(const char* sFilename) override;
    virtual void* LoadXmlFromString(const char* sXmlString) override;
    virtual void SetIProcess(void* pProcess) override;
    virtual void* GetIProcess() override;
    virtual IRenderer* CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) override;
    virtual bool IsTestMode() const override;
    virtual void ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) override;
    virtual void SetFrameProfiler(bool on, bool display, char* prefix) override;

    virtual void OnEnvironmentUpdate() override;

    virtual void Slot73() override;
    virtual void Slot74() override;
    virtual void Slot75() override;
    virtual void Slot76() override;
    virtual void Slot77() override;
    virtual void Slot78() override;
    virtual void Slot79() override;
    virtual void Slot80() override;
    virtual void Slot81() override;
    virtual void Slot82() override;
    virtual void Slot83() override;
    virtual void Slot84() override;
    virtual void Slot85() override;
    virtual void Slot86() override;
    virtual void Slot87() override;
    virtual void Slot88() override;
    virtual void Slot89() override;
    virtual void Slot90() override;
    virtual void Slot91() override;
    virtual void Slot92() override;
    virtual void Slot93() override;
    virtual void Slot94() override;
    virtual void Slot95() override;
    virtual void Slot96() override;
    virtual void Slot97() override;
    virtual void Slot98() override;
    virtual void Slot99() override;
    virtual void Slot100() override;
    virtual void Slot101() override;
    virtual void Slot102() override;
    virtual void Slot103() override;
    virtual void Slot104() override;
    virtual void Slot105() override;
    virtual void Slot106() override;
    virtual void Slot107() override;
    virtual void Slot108() override;
    virtual void Slot109() override;
    virtual void Slot110() override;
    virtual void Slot111() override;
    virtual void Slot112() override;
    virtual void Slot113() override;
    virtual void Slot114() override;
    virtual void Slot115() override;
    virtual void Slot116() override;
    virtual void Slot117() override;
    virtual void Slot118() override;
    virtual void Slot119() override;
    virtual void Slot120() override;
    virtual void Slot121() override;
    virtual void Slot122() override;
    virtual void Slot123() override;
    virtual void Slot124() override;
    virtual void Slot125() override;
    virtual void Slot126() override;
    virtual void Slot127() override;
    virtual void Slot128() override;
    virtual void Slot129() override;
    virtual void Slot130() override;
    virtual void Slot131() override;
    virtual void Slot132() override;
    virtual void Slot133() override;
    virtual void Slot134() override;
    virtual void Slot135() override;
    virtual void Slot136() override;
    virtual void Slot137() override;
    virtual void Slot138() override;
    virtual void Slot139() override;
    virtual void Slot140() override;
    virtual void Slot141() override;
    virtual void Slot142() override;
    virtual void Slot143() override;
    virtual void Slot144() override;
    virtual void Slot145() override;
    virtual void Slot146() override;
    virtual void Slot147() override;
    virtual void Slot148() override;

    virtual bool Init(const SSystemInitParams& params) override;

    // Subsystems accessors
    GameOptions*         GetGameOptions();
    GameFixedFrame*      GetGameFixedFrame();
    CharacterLODManager* GetCharacterLODManager();
    LITELauncherManager* GetLITELauncherManager();
    SdoaLogin*           GetSdoaLogin();
    CryFileMonitor*      GetCryFileMonitor();

private:
    // Memory layout structured to exactly 0x3708 bytes matching official Aion binary
    // Offset +0x0008 to +0x3618
    uint8_t              m_cryCommonPadding[0x3618 - 0x08];

    // Offset +0x3618: m_pGame pointer
    IGame*               m_pGame;             // +0x3618
    uint32_t             m_dwLoadingState;    // +0x3620
    uint32_t             m_pad3624;           // +0x3624
    float                m_fLoadingProgress;  // +0x3628
    uint32_t             m_pad362C;           // +0x362C
    uint8_t              m_padBeforeUser[0x3650 - 0x3630];
    char                 m_szUserName[64];    // +0x3650
    uint8_t              m_padBeforePerf[0x36A8 - 0x3690];
    uint64_t             m_perfFreq;          // +0x36A8
    uint8_t              m_padBeforeAuth[0x36CC - 0x36B0];
    uint32_t             m_authStatus;        // +0x36CC
    uint8_t              m_padBeforeVer[0x3700 - 0x36D0];
    uint32_t             m_nGameVersion;      // +0x3700
    uint32_t             m_nBuildNumber;      // +0x3704
};

static_assert(sizeof(CSystem) == 0x3708, "CSystem size must be exactly 0x3708 (14,088 bytes) to match binary parity!");

#pragma pack(pop)

#endif // _AIONSYSTEMCORE_H_
