#pragma once

#ifndef _AIONSYSTEMCORE_H_
#define _AIONSYSTEMCORE_H_

#include <windows.h>
#include <cstdint>
#include <cstdio>
#include "CryCommon/ISystem.h"

// Forward declarations
class  GameOptions;
class  GameFixedFrame;
class  CharacterLODManager;
class  LITELauncherManager;
class  SdoaLogin;
class  CryFileMonitor;

#pragma pack(push, 8)

// ============================================================================
// CSystem concrete implementation with exact binary size 0x3708 (14,088 bytes)
// Matching CrySystem.dll primary VTable and member footprint
// ============================================================================
class CSystem : public ISystem
{
public:
    CSystem();
    virtual ~CSystem() override;

    // Slot 0 to 15
    virtual bool CreateGame(const SGameInitParams& params) override;
    virtual bool IsLoadingScreenEnabled() override;
    virtual bool IsPreloadDone() override;
    virtual void SetLoadingProgress(float progress) override;
    virtual void Release() override;
    virtual void ShutDown(bool bRelaunch = false) override;
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

    // Slot 16 to 19
    virtual float Slot16() override;
    virtual bool  Slot17() override;
    virtual void  Slot18() override;
    virtual bool  Slot19() override;

    // Slot 20 to 28
    virtual void Error(const char* sFormat, ...) override;
    virtual void SetForceNonDevMode(const bool bValue) override;
    virtual void Warning(int module, int severity, int flags, const char* file, const char* format, ...) override;
    virtual bool GetForceNonDevMode() const override;
    virtual bool CheckLogVerbosity(int verbosity) override;
    virtual bool IsDedicated() override;
    virtual bool Update(int updateFlags = 0, int nPauseMode = 0) override;
    virtual void UpdateScriptSink() override;
    virtual bool IsDevMode() const override;

    // Slot 29 to 35
    virtual void* Slot29() override;
    virtual class CCamera& GetViewCamera() override;
    virtual void  Slot31() override;
    virtual void  Slot32() override;
    virtual void  CreateEntityScriptBinding(void* pEntity) override;
    virtual void  IgnoreUpdates(bool bIgnore) override;
    virtual bool  Slot35() override;

    // Slot 36 to 60 (Core Subsystems)
    virtual IGame*               GetIGame() override;
    virtual INetwork*            GetINetwork() override;
    virtual void                 Slot38() override;
    virtual void                 Slot39() override;
    virtual IRenderer*           GetIRenderer() override;
    virtual IInput*              GetIInput() override;
    virtual ITimer*              GetITimer() override;
    virtual ICryPak*             GetIPak() override;
    virtual IConsole*            GetIConsole() override;
    virtual IScriptSystem*       GetIScriptSystem() override;
    virtual I3DEngine*           GetI3DEngine() override;
    virtual ICryCharManager*     GetIAnimationSystem() override;
    virtual ISoundSystem*        GetISoundSystem() override;
    virtual IMusicSystem*        GetIMusicSystem() override;
    virtual IPhysicalWorld*      GetIPhysicalWorld() override;
    virtual IMovieSystem*        GetIMovieSystem() override;
    virtual IAISystem*           GetAISystem() override;
    virtual IMemoryManager*      GetIMemoryManager() override;
    virtual IEntitySystem*       GetIEntitySystem() override;
    virtual ICryFont*            GetICryFont() override;
    virtual ILog*                GetILog() override;
    virtual IStreamEngine*       GetStreamEngine() override;
    virtual CLUADbg*             GetLuaDebugger() override;
    virtual IValidator*          GetIValidator() override;
    virtual IFrameProfileSystem* GetIProfileSystem() override;

    // Slot 61 to 89
    virtual const char* GetUserName() override;
    virtual int         GetCPUFlags() override;
    virtual double      GetSecondsPerCycle() override;
    virtual float       GetGCFrequency() override;
    virtual void        SetGCFrequency(float fRate) override;
    virtual void        DebugStats(bool checkpoint, bool leaks) override;
    virtual void        DumpWinHeaps() override;
    virtual int         DumpMMStats(bool log) override;
    virtual void*       Slot69() override;
    virtual void*       Slot70() override;
    virtual void*       Slot71() override;
    virtual void*       Slot72() override;
    virtual void*       Slot73() override;
    virtual const struct SFileVersion& GetFileVersion() override;
    virtual void*       Slot75() override;
    virtual void*       Slot76() override;
    virtual void*       Slot77() override;
    virtual const struct SFileVersion& GetProductVersion() override;
    virtual XDOM::IXMLDOMDocument* CreateXMLDocument() override;
    virtual XmlNodeRef  CreateXmlNode(const char* sNodeName) override;
    virtual XmlNodeRef  LoadXmlFile(const char* sFilename) override;
    virtual XmlNodeRef  LoadXmlFromString(const char* sXmlString) override;
    virtual void        SetIProcess(void* pProcess) override;
    virtual void*       GetIProcess() override;
    virtual IRenderer*  CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) override;
    virtual bool        IsTestMode() const override;
    virtual void        ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) override;
    virtual void        SetFrameProfiler(bool on, bool display, char* prefix) override;
    virtual void        OnEnvironmentUpdate() override;

    // Slots 90 to 148
    virtual void Slot90() override;  virtual void Slot91() override;  virtual void Slot92() override;  virtual void Slot93() override;
    virtual void Slot94() override;  virtual void Slot95() override;  virtual void Slot96() override;  virtual void Slot97() override;
    virtual void Slot98() override;  virtual void Slot99() override;  virtual void Slot100() override; virtual void Slot101() override;
    virtual void Slot102() override; virtual void Slot103() override; virtual void Slot104() override; virtual void Slot105() override;
    virtual void Slot106() override; virtual void Slot107() override; virtual void Slot108() override; virtual void Slot109() override;
    virtual void Slot110() override; virtual void Slot111() override; virtual void Slot112() override; virtual void Slot113() override;
    virtual void Slot114() override; virtual void Slot115() override; virtual void Slot116() override; virtual void Slot117() override;
    virtual void Slot118() override; virtual void Slot119() override; virtual void Slot120() override; virtual void Slot121() override;
    virtual void Slot122() override; virtual void Slot123() override; virtual void Slot124() override; virtual void Slot125() override;
    virtual void Slot126() override; virtual void Slot127() override; virtual void Slot128() override; virtual void Slot129() override;
    virtual void Slot130() override; virtual void Slot131() override; virtual void Slot132() override; virtual void Slot133() override;
    virtual void Slot134() override; virtual void Slot135() override; virtual void Slot136() override; virtual void Slot137() override;
    virtual void Slot138() override; virtual void Slot139() override; virtual void Slot140() override; virtual void Slot141() override;
    virtual void Slot142() override; virtual void Slot143() override; virtual void Slot144() override; virtual void Slot145() override;
    virtual void Slot146() override; virtual void Slot147() override; virtual void Slot148() override;

    // Slot 149
    virtual bool Init(const SSystemInitParams& params) override;

    // Subsystems accessors
    GameOptions*         GetGameOptions();
    GameFixedFrame*      GetGameFixedFrame();
    CharacterLODManager* GetCharacterLODManager();
    LITELauncherManager* GetLITELauncherManager();
    SdoaLogin*           GetSdoaLogin();
    CryFileMonitor*      GetCryFileMonitor();

private:
    // Subsystem pointers and DLL handles
    ILog*                m_pLog;
    IConsole*            m_pConsole;
    ITimer*              m_pTimer;
    ICryPak*             m_pIPak;
    IStreamEngine*       m_pStreamEngine;
    IInput*              m_pInput;
    IScriptSystem*       m_pScriptSystem;
    IEntitySystem*       m_pEntitySystem;
    ICryFont*            m_pCryFont;
    ISoundSystem*        m_pSound;
    IMusicSystem*        m_pMusic;
    IPhysicalWorld*      m_pPhysicalWorld;
    IMovieSystem*        m_pMovieSystem;
    IAISystem*           m_pAISystem;
    ICryCharManager*     m_pAnimationSystem;
    I3DEngine*           m_p3DEngine;
    IRenderer*           m_pRenderer;
    INetwork*            m_pNetwork;
    IValidator*          m_pValidator;
    IFrameProfileSystem* m_pProfileSystem;
    HMODULE              m_hInputDll;
    HMODULE              m_hScriptDll;
    HMODULE              m_hFontDll;
    HMODULE              m_hEntityDll;
    HMODULE              m_hSoundDll;
    HMODULE              m_hPhysicsDll;
    HMODULE              m_hMovieDll;
    HMODULE              m_hAnimationDll;
    HMODULE              m_h3DEngineDll;

    // Memory layout structured to exactly 0x3708 bytes matching official Aion binary
    uint8_t              m_cryCommonPadding[0x3618 - 0x08 - (29 * sizeof(void*))];

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
