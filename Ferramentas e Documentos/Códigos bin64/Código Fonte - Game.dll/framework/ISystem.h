#pragma once

#ifndef _ISYSTEM_AION_CLASSIC_H_
#define _ISYSTEM_AION_CLASSIC_H_

#include <cstdint>
#include <cstdio>
#include <cstdarg>
#include <windows.h>

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
struct ICVar;
class  CCamera;
struct SFileVersion;

#if defined(__has_include)
#if __has_include("CryVersion.h")
#include "CryVersion.h"
#endif
#if __has_include("IXml.h")
#include "IXml.h"
#endif
#if __has_include("IXMLDOM.h")
#include "IXMLDOM.h"
#endif
#endif

namespace XDOM {
    struct IXMLDOMDocument;
}

enum ESystemConfigSpec
{
    CONFIG_LOW_SPEC = 0,
    CONFIG_MEDIUM_SPEC = 1,
    CONFIG_HIGH_SPEC = 2,
    CONFIG_VERYHIGH_SPEC = 3
};

#ifndef __ixml_h__
struct IXmlNode;
class XmlNodeRef
{
public:
    IXmlNode* p;
    XmlNodeRef() : p(nullptr) {}
    XmlNodeRef(IXmlNode* _p) : p(_p) {}
    operator bool() const { return p != nullptr; }
    IXmlNode* operator->() const { return p; }
};
#endif

#pragma pack(push, 8)

struct SGameInitParams
{
    const char* sGameDLL;
    IGame*      pGame;
    bool        bDedicatedServer;
};

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

// ============================================================================
// Official 151 virtual functions of CryEngine ISystem in Aion Classic 5.0
// Bit-for-bit verified against CrySystem.dll primary VTable at 0x1801E8558
// ============================================================================
struct ISystem
{
    // Slot 0 (0x000): CreateGame
    virtual bool CreateGame(const SGameInitParams& params) = 0;
    // Slot 1 (0x008): IsLoadingScreenEnabled
    virtual bool IsLoadingScreenEnabled() = 0;
    // Slot 2 (0x010): IsPreloadDone
    virtual bool IsPreloadDone() = 0;
    // Slot 3 (0x018): SetLoadingProgress
    virtual void SetLoadingProgress(float progress) = 0;
    // Slot 4 (0x020): Release
    virtual void Release() = 0;
    // Slot 5 (0x028): ShutDown
    virtual void ShutDown(bool bRelaunch = false) = 0;
    // Slot 6 (0x030): WasInDevMode
    virtual bool WasInDevMode() = 0;
    // Slot 7 (0x038): Relaunch
    virtual void Relaunch(bool bRelaunch) = 0;
    // Slot 8 (0x040): UpdateLoadingScreen
    virtual void UpdateLoadingScreen() = 0;
    // Slot 9 (0x048): RenderBegin
    virtual void RenderBegin() = 0;
    // Slot 10 (0x050): Render
    virtual void Render() = 0;
    // Slot 11 (0x058): RenderEnd
    virtual void RenderEnd() = 0;
    // Slot 12 (0x060): RenderStatistics
    virtual void RenderStatistics() = 0;
    // Slot 13 (0x068): DumpMemoryUsageStatistics
    virtual void DumpMemoryUsageStatistics() = 0;
    // Slot 14 (0x070): Quit
    virtual void Quit() = 0;
    // Slot 15 (0x078): IsQuitting
    virtual bool IsQuitting() = 0;
    // Slot 16 (0x080): Slot16
    virtual float Slot16() = 0;
    // Slot 17 (0x088): Slot17
    virtual bool Slot17() = 0;
    // Slot 18 (0x090): Slot18
    virtual void Slot18() = 0;
    // Slot 19 (0x098): Slot19
    virtual bool Slot19() = 0;
    // Slot 20 (0x0A0): Error
    virtual void Error(const char* sFormat, ...) = 0;
    // Slot 21 (0x0A8): SetForceNonDevMode
    virtual void SetForceNonDevMode(const bool bValue) = 0;
    // Slot 22 (0x0B0): Warning
    virtual void Warning(int module, int severity, int flags, const char* file, const char* format, ...) = 0;
    // Slot 23 (0x0B8): GetForceNonDevMode
    virtual bool GetForceNonDevMode() const = 0;
    // Slot 24 (0x0C0): CheckLogVerbosity
    virtual bool CheckLogVerbosity(int verbosity) = 0;
    // Slot 25 (0x0C8): IsDedicated
    virtual bool IsDedicated() = 0;
    // Slot 26 (0x0D0): Update
    virtual bool Update(int updateFlags = 0, int nPauseMode = 0) = 0;
    // Slot 27 (0x0D8): UpdateScriptSink
    virtual void UpdateScriptSink() = 0;
    // Slot 28 (0x0E0): IsDevMode
    virtual bool IsDevMode() const = 0;
    // Slot 29 (0x0E8): Slot29
    virtual void* Slot29() = 0;
    // Slot 30 (0x0F0): GetViewCamera
    virtual class CCamera& GetViewCamera() = 0;
    // Slot 31 (0x0F8): Slot31
    virtual void Slot31() = 0;
    // Slot 32 (0x100): Slot32
    virtual void Slot32() = 0;
    // Slot 33 (0x108): CreateEntityScriptBinding
    virtual void CreateEntityScriptBinding(void* pEntity) = 0;
    // Slot 34 (0x110): IgnoreUpdates
    virtual void IgnoreUpdates(bool bIgnore) = 0;
    // Slot 35 (0x118): Slot35
    virtual bool Slot35() = 0;
    // Slot 36 (0x120): GetIGame
    virtual IGame* GetIGame() = 0;
    // Slot 37 (0x128): GetINetwork
    virtual INetwork* GetINetwork() = 0;
    // Slot 38 (0x130): Slot38
    virtual void Slot38() = 0;
    // Slot 39 (0x138): Slot39
    virtual void Slot39() = 0;
    // Slot 40 (0x140): GetIRenderer
    virtual IRenderer* GetIRenderer() = 0;
    // Slot 41 (0x148): GetIInput
    virtual IInput* GetIInput() = 0;
    // Slot 42 (0x150): GetITimer
    virtual ITimer* GetITimer() = 0;
    // Slot 43 (0x158): GetIPak
    virtual ICryPak* GetIPak() = 0;
    // Slot 44 (0x160): GetIConsole
    virtual IConsole* GetIConsole() = 0;
    // Slot 45 (0x168): GetIScriptSystem
    virtual IScriptSystem* GetIScriptSystem() = 0;
    // Slot 46 (0x170): GetI3DEngine
    virtual I3DEngine* GetI3DEngine() = 0;
    // Slot 47 (0x178): GetIAnimationSystem
    virtual ICryCharManager* GetIAnimationSystem() = 0;
    // Slot 48 (0x180): GetISoundSystem
    virtual ISoundSystem* GetISoundSystem() = 0;
    // Slot 49 (0x188): GetIMusicSystem
    virtual IMusicSystem* GetIMusicSystem() = 0;
    // Slot 50 (0x190): GetIPhysicalWorld
    virtual IPhysicalWorld* GetIPhysicalWorld() = 0;
    // Slot 51 (0x198): GetIMovieSystem
    virtual IMovieSystem* GetIMovieSystem() = 0;
    // Slot 52 (0x1A0): GetAISystem
    virtual IAISystem* GetAISystem() = 0;
    // Slot 53 (0x1A8): GetIMemoryManager
    virtual IMemoryManager* GetIMemoryManager() = 0;
    // Slot 54 (0x1B0): GetIEntitySystem
    virtual IEntitySystem* GetIEntitySystem() = 0;
    // Slot 55 (0x1B8): GetICryFont
    virtual ICryFont* GetICryFont() = 0;
    // Slot 56 (0x1C0): GetILog
    virtual ILog* GetILog() = 0;
    // Slot 57 (0x1C8): GetStreamEngine
    virtual IStreamEngine* GetStreamEngine() = 0;
    // Slot 58 (0x1D0): GetLuaDebugger
    virtual CLUADbg* GetLuaDebugger() = 0;
    // Slot 59 (0x1D8): GetIValidator
    virtual IValidator* GetIValidator() = 0;
    // Slot 60 (0x1E0): GetIProfileSystem
    virtual IFrameProfileSystem* GetIProfileSystem() = 0;
    // Slot 61 (0x1E8): GetUserName
    virtual const char* GetUserName() = 0;
    // Slot 62 (0x1F0): GetCPUFlags
    virtual int GetCPUFlags() = 0;
    // Slot 63 (0x1F8): GetSecondsPerCycle
    virtual double GetSecondsPerCycle() = 0;
    // Slot 64 (0x200): GetGCFrequency
    virtual float GetGCFrequency() = 0;
    // Slot 65 (0x208): SetGCFrequency
    virtual void SetGCFrequency(float fRate) = 0;
    // Slot 66 (0x210): DebugStats
    virtual void DebugStats(bool checkpoint, bool leaks) = 0;
    // Slot 67 (0x218): DumpWinHeaps
    virtual void DumpWinHeaps() = 0;
    // Slot 68 (0x220): DumpMMStats
    virtual int DumpMMStats(bool log) = 0;
    // Slot 69 (0x228): Slot69
    virtual void* Slot69() = 0;
    // Slot 70 (0x230): Slot70
    virtual void* Slot70() = 0;
    // Slot 71 (0x238): Slot71
    virtual void* Slot71() = 0;
    // Slot 72 (0x240): Slot72
    virtual void* Slot72() = 0;
    // Slot 73 (0x248): Slot73
    virtual void* Slot73() = 0;
    // Slot 74 (0x250): GetFileVersion
    virtual const struct SFileVersion& GetFileVersion() = 0;
    // Slot 75 (0x258): Slot75
    virtual void* Slot75() = 0;
    // Slot 76 (0x260): Slot76
    virtual void* Slot76() = 0;
    // Slot 77 (0x268): Slot77
    virtual void* Slot77() = 0;
    // Slot 78 (0x270): GetProductVersion
    virtual const struct SFileVersion& GetProductVersion() = 0;
    // Slot 79 (0x278): CreateXMLDocument
    virtual XDOM::IXMLDOMDocument* CreateXMLDocument() = 0;
    // Slot 80 (0x280): CreateXmlNode
    virtual XmlNodeRef CreateXmlNode(const char* sNodeName = "") = 0;
    // Slot 81 (0x288): LoadXmlFile
    virtual XmlNodeRef LoadXmlFile(const char* sFilename) = 0;
    // Slot 82 (0x290): LoadXmlFromString
    virtual XmlNodeRef LoadXmlFromString(const char* sXmlString) = 0;
    // Slot 83 (0x298): SetIProcess
    virtual void SetIProcess(void* pProcess) = 0;
    // Slot 84 (0x2A0): GetIProcess
    virtual void* GetIProcess() = 0;
    // Slot 85 (0x2A8): CreateRenderer
    virtual IRenderer* CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) = 0;
    // Slot 86 (0x2B0): IsTestMode
    virtual bool IsTestMode() const = 0;
    // Slot 87 (0x2B8): ShowDebugger
    virtual void ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) = 0;
    // Slot 88 (0x2C0): SetFrameProfiler
    virtual void SetFrameProfiler(bool on, bool display, char* prefix) = 0;
    // Slot 89 (0x2C8): OnEnvironmentUpdate
    virtual void OnEnvironmentUpdate() = 0;

    // Slots 90 to 148: Internal CryEngine / NCSoft extensions (59 slots)
    virtual void Slot90() = 0;  virtual void Slot91() = 0;  virtual void Slot92() = 0;  virtual void Slot93() = 0;
    virtual void Slot94() = 0;  virtual void Slot95() = 0;  virtual void Slot96() = 0;  virtual void Slot97() = 0;
    virtual void Slot98() = 0;  virtual void Slot99() = 0;  virtual void Slot100() = 0; virtual void Slot101() = 0;
    virtual void Slot102() = 0; virtual void Slot103() = 0; virtual void Slot104() = 0; virtual void Slot105() = 0;
    virtual void Slot106() = 0; virtual void Slot107() = 0; virtual void Slot108() = 0; virtual void Slot109() = 0;
    virtual void Slot110() = 0; virtual void Slot111() = 0; virtual void Slot112() = 0; virtual void Slot113() = 0;
    virtual void Slot114() = 0; virtual void Slot115() = 0; virtual void Slot116() = 0; virtual void Slot117() = 0;
    virtual void Slot118() = 0; virtual void Slot119() = 0; virtual void Slot120() = 0; virtual void Slot121() = 0;
    virtual void Slot122() = 0; virtual void Slot123() = 0; virtual void Slot124() = 0; virtual void Slot125() = 0;
    virtual void Slot126() = 0; virtual void Slot127() = 0; virtual void Slot128() = 0; virtual void Slot129() = 0;
    virtual void Slot130() = 0; virtual void Slot131() = 0; virtual void Slot132() = 0; virtual void Slot133() = 0;
    virtual void Slot134() = 0; virtual void Slot135() = 0; virtual void Slot136() = 0; virtual void Slot137() = 0;
    virtual void Slot138() = 0; virtual void Slot139() = 0; virtual void Slot140() = 0; virtual void Slot141() = 0;
    virtual void Slot142() = 0; virtual void Slot143() = 0; virtual void Slot144() = 0; virtual void Slot145() = 0;
    virtual void Slot146() = 0; virtual void Slot147() = 0; virtual void Slot148() = 0;

    // Slot 149 (0x4A8): Init
    virtual bool Init(const SSystemInitParams& params) = 0;

    // Slot 150 (0x4B0): Virtual Destructor
    virtual ~ISystem() {}

    // Non-virtual inline helpers (preserving exact 151-slot canonical VTable)
    inline void StartProfilerSection(class CFrameProfilerSection* pProfileSection) { (void)pProfileSection; }
    inline void EndProfilerSection(class CFrameProfilerSection* pProfileSection) { (void)pProfileSection; }
    inline struct IDataProbe* GetIDataProbe() { return nullptr; }
    inline bool GetSSFileInfo(const char* inszFileName, char* outszInfo, const unsigned long indwBufferSize) { (void)inszFileName; (void)outszInfo; (void)indwBufferSize; return false; }
    inline ESystemConfigSpec GetConfigSpec() { return CONFIG_VERYHIGH_SPEC; }
};

#ifdef __cplusplus
extern ISystem* GetISystem();
#endif

#ifndef MAX_WARNING_LENGTH
#define MAX_WARNING_LENGTH 4096
#endif

inline void CryError(const char *format, ...)
{
    if (!GetISystem()) return;
    va_list args;
    char szBuffer[MAX_WARNING_LENGTH];
    va_start(args, format);
    vsnprintf(szBuffer, sizeof(szBuffer), format, args);
    va_end(args);
    GetISystem()->Error("%s", szBuffer);
}

inline void CryWarning(int module, int severity, const char *format, ...)
{
    if (!GetISystem() || !format) return;
    va_list args;
    char szBuffer[MAX_WARNING_LENGTH];
    va_start(args, format);
    vsnprintf(szBuffer, sizeof(szBuffer), format, args);
    va_end(args);
    GetISystem()->Warning(module, severity, 0, nullptr, "%s", szBuffer);
}

inline void CryLog(const char *format, ...)
{
    (void)format;
}

inline void CryLogAlways(const char *format, ...)
{
    (void)format;
}

inline void CryLogComment(const char *format, ...)
{
    (void)format;
}

#pragma pack(pop)

#endif // _ISYSTEM_AION_CLASSIC_H_
