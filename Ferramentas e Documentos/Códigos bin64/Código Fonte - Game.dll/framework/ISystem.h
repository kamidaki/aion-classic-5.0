#pragma once

#ifndef _ISYSTEM_FRAMEWORK_H_
#define _ISYSTEM_FRAMEWORK_H_

#include <cstdint>
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

struct SGameInitParams;
struct SSystemInitParams;

// Canonical 151 virtual functions of CryEngine ISystem in Aion Classic 5.0
struct ISystem
{
    virtual bool CreateGame(const SGameInitParams& params) = 0; // 0
    virtual bool IsLoadingScreenEnabled() = 0;                   // 1
    virtual bool IsPreloadDone() = 0;                            // 2
    virtual void SetLoadingProgress(float progress) = 0;         // 3
    virtual void Release() = 0;                                  // 4
    virtual void ShutDown(bool bRelaunch) = 0;                   // 5
    virtual bool WasInDevMode() = 0;                             // 6
    virtual void Relaunch(bool bRelaunch) = 0;                   // 7
    virtual void UpdateLoadingScreen() = 0;                      // 8
    virtual void RenderBegin() = 0;                              // 9
    virtual void Render() = 0;                                   // 10
    virtual void RenderEnd() = 0;                                // 11
    virtual void RenderStatistics() = 0;                         // 12
    virtual void DumpMemoryUsageStatistics() = 0;                // 13
    virtual void Quit() = 0;                                     // 14
    virtual bool IsQuitting() = 0;                               // 15
    virtual void Error(const char* sFormat, ...) = 0;            // 16
    virtual void Warning(int module, int severity, int flags, const char* file, const char* format, ...) = 0; // 17
    virtual bool CheckLogVerbosity(int verbosity) = 0;           // 18
    virtual bool IsDedicated() = 0;                              // 19
    virtual bool Update(int updateFlags = 0, int nPauseMode = 0) = 0; // 20
    virtual void UpdateScriptSink() = 0;                         // 21
    virtual void SetForceNonDevMode(const bool bValue) = 0;      // 22
    virtual bool GetForceNonDevMode() const = 0;                 // 23
    virtual bool IsDevMode() const = 0;                          // 24
    virtual void SetViewCamera(void* pCamera) = 0;               // 25
    virtual void* GetViewCamera() = 0;                           // 26
    virtual void CreateEntityScriptBinding(void* pEntity) = 0;   // 27
    virtual void IgnoreUpdates(bool bIgnore) = 0;                // 28

    // Slot 29: GetIGame
    virtual IGame* GetIGame() = 0;                               // 29
    virtual INetwork* GetINetwork() = 0;                         // 30
    virtual IRenderer* GetIRenderer() = 0;                       // 31
    virtual IInput* GetIInput() = 0;                             // 32
    virtual ITimer* GetITimer() = 0;                             // 33
    virtual ICryPak* GetIPak() = 0;                              // 34
    virtual IConsole* GetIConsole() = 0;                         // 35
    virtual IScriptSystem* GetIScriptSystem() = 0;               // 36
    virtual I3DEngine* GetI3DEngine() = 0;                       // 37
    virtual ICryCharManager* GetIAnimationSystem() = 0;          // 38
    virtual ISoundSystem* GetISoundSystem() = 0;                 // 39
    virtual IMusicSystem* GetIMusicSystem() = 0;                 // 40
    virtual IPhysicalWorld* GetIPhysicalWorld() = 0;             // 41
    virtual IMovieSystem* GetIMovieSystem() = 0;                 // 42
    virtual IAISystem* GetAISystem() = 0;                        // 43
    virtual IMemoryManager* GetIMemoryManager() = 0;             // 44
    virtual IEntitySystem* GetIEntitySystem() = 0;               // 45
    virtual ICryFont* GetICryFont() = 0;                         // 46
    virtual ILog* GetILog() = 0;                                 // 47
    virtual IStreamEngine* GetStreamEngine() = 0;                // 48
    virtual CLUADbg* GetLuaDebugger() = 0;                       // 49
    virtual IValidator* GetIValidator() = 0;                     // 50
    virtual IFrameProfileSystem* GetIProfileSystem() = 0;        // 51
    virtual const char* GetUserName() = 0;                       // 52
    virtual int GetCPUFlags() = 0;                               // 53
    virtual double GetSecondsPerCycle() = 0;                     // 54
    virtual float GetGCFrequency() = 0;                          // 55
    virtual void SetGCFrequency(float fRate) = 0;                // 56
    virtual void DebugStats(bool checkpoint, bool leaks) = 0;    // 57
    virtual void DumpWinHeaps() = 0;                             // 58
    virtual int DumpMMStats(bool log) = 0;                       // 59
    virtual void* GetFileVersion() = 0;                          // 60
    virtual void* GetProductVersion() = 0;                      // 61
    virtual void* CreateXMLDocument() = 0;                       // 62
    virtual void* CreateXmlNode(const char* sNodeName) = 0;      // 63
    virtual void* LoadXmlFile(const char* sFilename) = 0;        // 64
    virtual void* LoadXmlFromString(const char* sXmlString) = 0; // 65
    virtual void SetIProcess(void* pProcess) = 0;                // 66
    virtual void* GetIProcess() = 0;                             // 67
    virtual IRenderer* CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) = 0; // 68
    virtual bool IsTestMode() const = 0;                         // 69
    virtual void ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) = 0; // 70
    virtual void SetFrameProfiler(bool on, bool display, char* prefix) = 0; // 71

    // Slot 72: OnEnvironmentUpdate
    virtual void OnEnvironmentUpdate() = 0;                      // 72

    // Slots 73..148
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

    // Slot 149: Init
    virtual bool Init(const SSystemInitParams& params) = 0;      // 149

    // Slot 150: Destructor
    virtual ~ISystem() {}                                       // 150
};

#endif // _ISYSTEM_FRAMEWORK_H_
