#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <io.h>
#include "AionSystemCore.h"
#include "ncsoft/GameOptions.h"
#include "ncsoft/GameFixedFrame.h"
#include "ncsoft/CharacterLODManager.h"
#include "ncsoft/LITELauncherManager.h"
#include "ncsoft/SdoaLogin.h"
#include "ncsoft/CryFileMonitor.h"

#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cstdarg>
#include <cstdint>
#include <string>
#include <map>
#include <vector>
#include <algorithm>

typedef void* (*PFN_CREATE_GAME_INSTANCE)(ISystem* pSys);

// Global NCSoft subsystem instances
static GameOptions*         g_pGameOptions = nullptr;
static GameFixedFrame*      g_pGameFixedFrame = nullptr;
static CharacterLODManager* g_pCharacterLODManager = nullptr;
static LITELauncherManager* g_pLITELauncherManager = nullptr;
static SdoaLogin*           g_pSdoaLogin = nullptr;
static CryFileMonitor*      g_pCryFileMonitor = nullptr;

// ============================================================================
// Concrete Subsystem Interfaces & Types
// ============================================================================

class CTimeValue
{
public:
    int64_t m_lValue;
    CTimeValue() : m_lValue(0) {}
    CTimeValue(int64_t v) : m_lValue(v) {}
    float GetSeconds() const { return static_cast<float>(m_lValue) / 1000.0f; }
};

struct ILog
{
    enum ELogType { eMessage = 0, eWarning, eError, eAlways, eWarningAlways, eErrorAlways, eInput };
    virtual void Release() = 0;
    virtual void SetFileName(const char *command = nullptr) = 0;
    virtual const char* GetFileName() = 0;
    virtual void Log(const char *szCommand, ...) = 0;
    virtual void LogWarning(const char *szCommand, ...) = 0;
    virtual void LogError(const char *szCommand, ...) = 0;
    virtual void LogPlus(const char *command, ...) = 0;
    virtual void LogToFile(const char *command, ...) = 0;
    virtual void LogToFilePlus(const char *command, ...) = 0;
    virtual void LogToConsole(const char *command, ...) = 0;
    virtual void LogToConsolePlus(const char *command, ...) = 0;
    virtual void UpdateLoadingScreen(const char *command, ...) = 0;
    virtual void UpdateLoadingScreenPlus(const char *command, ...) = 0;
    virtual void EnableVerbosity(bool bEnable) = 0;
    virtual void SetVerbosity(int verbosity) = 0;
    virtual int  GetVerbosityLevel() = 0;
    virtual ~ILog() {}
};

struct ITimer
{
    virtual void Reset() = 0;
    virtual void Update() = 0;
    virtual const float GetCurrTime() const = 0;
    virtual const CTimeValue GetCurrTimePrecise() const = 0;
    virtual const float GetAsyncCurTime() = 0;
    virtual const float GetFrameTime() const = 0;
    virtual void Enable(bool bEnable) = 0;
    virtual float GetFrameRate() = 0;
    virtual float gfGetTime() = 0;
    virtual float MeasureTime(const char* comment) = 0;
    virtual ~ITimer() {}
};

#define CVAR_INT    1
#define CVAR_FLOAT  2
#define CVAR_STRING 3

struct ICVar
{
    virtual void Release() = 0;
    virtual int GetIVal() = 0;
    virtual float GetFVal() = 0;
    virtual char *GetString() = 0;
    virtual void Set(const char* s) = 0;
    virtual void ForceSet(const char* s) = 0;
    virtual void Set(float f) = 0;
    virtual void Set(int i) = 0;
    virtual void Refresh() = 0;
    virtual void ClearFlags(int flags) = 0;
    virtual int  GetFlags() = 0;
    virtual int  SetFlags(int flags) = 0;
    virtual int  GetType() = 0;
    virtual const char* GetName() = 0;
    virtual const char* GetHelp() = 0;
};

struct ICVarDumpSink { virtual void OnElementFound(ICVar *pCVar) = 0; };
struct IKeyBindDumpSink { virtual void OnKeyBindFound(const char *sBind, const char *sCommand) = 0; };
struct IOutputPrintSink { virtual void Print(const char *inszText) = 0; };
struct IConsoleVarSink { virtual bool OnBeforeVarChange(ICVar *pVar, const char *sNewValue) = 0; };

struct IConsole
{
    virtual void Release() = 0;
    virtual ICVar *CreateVariable(const char *sName, const char *sValue, int nFlags, const char *help = "") = 0;
    virtual ICVar *CreateVariable(const char *sName, int iValue, int nFlags, const char *help = "") = 0;
    virtual ICVar *CreateVariable(const char *sName, float fValue, int nFlags, const char *help = "") = 0;
    virtual void UnregisterVariable(const char *sVarName, bool bDelete = false) = 0;
    virtual void SetScrollMax(int value) = 0;
    virtual void AddOutputPrintSink(IOutputPrintSink *inpSink) = 0;
    virtual void RemoveOutputPrintSink(IOutputPrintSink *inpSink) = 0;
    virtual void ShowConsole(bool show) = 0;
    virtual int Register(const char *name, void *src, float defaultvalue, int flags, int type, const char *help = "") = 0;
    virtual float Register(const char *name, float *src, float defaultvalue, int flags = 0, const char *help = "") = 0;
    virtual int Register(const char *name, int *src, float defaultvalue, int flags = 0, const char *help = "") = 0;
    virtual void DumpCVars(ICVarDumpSink *pCallback, unsigned int nFlagsFilter = 0) = 0;
    virtual void CreateKeyBind(const char *sCmd, const char *sRes, bool bExecute = false) = 0;
    virtual void SetImage(void *pImage, bool bDeleteCurrent = false) = 0;
    virtual void *GetImage() = 0;
    virtual void StaticBackground(bool bStatic) = 0;
    virtual void SetLoadingImage(const char *szFilename) = 0;
    virtual bool GetLineNo(const DWORD indwLineNo, char *outszBuffer, const DWORD indwBufferSize) const = 0;
    virtual int GetLineCount() const = 0;
    virtual ICVar* GetCVar(const char *name, const bool bCaseSensitive = true) = 0;
    virtual void* GetFont() = 0;
    virtual void Help(const char *command = nullptr) = 0;
    virtual char* GetVariable(const char *szVarName, const char *szFileName, const char *def_val) = 0;
    virtual float GetVariable(const char *szVarName, const char *szFileName, float def_val) = 0;
    virtual void PrintLine(const char *s) = 0;
    virtual void PrintLinePlus(const char *s) = 0;
    virtual bool GetStatus() = 0;
    virtual void Clear() = 0;
    virtual void Update() = 0;
    virtual void Draw() = 0;
    virtual void AddCommand(const char *sName, const char *sScriptFunc, const DWORD indwFlags = 0, const char *help = "") = 0;
    virtual void ExecuteString(const char *command, bool bNeedSlash = false, bool bIgnoreDevMode = false) = 0;
    virtual void Exit(const char *command, ...) = 0;
    virtual bool IsOpened() = 0;
    virtual int   GetNumVars() = 0;
    virtual void  GetSortedVars(const char **pszArray, size_t numItems) = 0;
    virtual const char* AutoComplete(const char* substr) = 0;
    virtual const char* AutoCompletePrev(const char* substr) = 0;
    virtual char* ProcessCompletion(const char *szInputBuffer) = 0;
    virtual void  ResetAutoCompletion() = 0;
    virtual void  DumpCommandsVars(char *prefix) = 0;
    virtual void  GetMemoryUsage(void* pSizer) = 0;
    virtual void  ResetProgressBar(int nProgressRange) = 0;
    virtual void  TickProgressBar() = 0;
    virtual void  DumpKeyBinds(IKeyBindDumpSink *pCallback) = 0;
    virtual const char* FindKeyBind(const char *sCmd) = 0;
    virtual void  AddConsoleVarSink(IConsoleVarSink *pSink) = 0;
    virtual void  RemoveConsoleVarSink(IConsoleVarSink *pSink) = 0;
    virtual const char* GetHistoryElement(const bool bUpOrDown) = 0;
    virtual void  AddCommandToHistory(const char *szCommand) = 0;
};

struct ICryPak
{
    virtual bool Init(const char *szBasePath) = 0;
    virtual void Release() = 0;
    virtual bool OpenPack(const char *pName, unsigned nFlags = 0) = 0;
    virtual bool OpenPack(const char* pBindingRoot, const char *pName, unsigned nFlags = 0) = 0;
    virtual bool ClosePack(const char* pName, unsigned nFlags = 0) = 0;
    virtual bool OpenPacks(const char *pWildcard, unsigned nFlags = 0) = 0;
    virtual bool OpenPacks(const char* pBindingRoot, const char *pWildcard, unsigned nFlags = 0) = 0;
    virtual bool ClosePacks(const char* pWildcard, unsigned nFlags = 0) = 0;
    virtual void AddMod(const char* szMod) = 0;
    virtual void RemoveMod(const char* szMod) = 0;
    virtual void* GetPakInfo() = 0;
    virtual void FreePakInfo(void* pInfo) = 0;
    virtual FILE *FOpen(const char *pName, const char *mode, unsigned nFlags = 0) = 0;
    virtual FILE *FOpen(const char *pName, const char *mode, char *szFileGamePath, int nLen) = 0;
    virtual size_t FRead(void *data, size_t length, size_t elems, FILE *handle) = 0;
    virtual size_t FWrite(void *data, size_t length, size_t elems, FILE *handle) = 0;
    virtual int FSeek(FILE *handle, long seek, int mode) = 0;
    virtual long FTell(FILE *handle) = 0;
    virtual int FClose(FILE *handle) = 0;
    virtual int FEof(FILE *handle) = 0;
    virtual int FScanf(FILE *handle, const char *format, ...) = 0;
    virtual char *FGetS(char *str, int n, FILE *handle) = 0;
    virtual int Getc(FILE *handle) = 0;
    virtual int Ungetc(int c, FILE *handle) = 0;
    virtual intptr_t FindFirst(const char *pDir, struct _finddata_t *fd) = 0;
    virtual int FindNext(intptr_t handle, struct _finddata_t *fd) = 0;
    virtual int FindClose(intptr_t handle) = 0;
    virtual FILETIME GetFileTime(const char *pName) = 0;
    virtual bool IsCpuFileAccessAllowed() = 0;
    virtual void SetDirectFileAccessMode(bool bEnable) = 0;
    virtual bool GetDirectFileAccessMode() = 0;
    virtual void RecordFileOpen(bool bEnable) = 0;
    virtual void EnumerateRecordedFiles(void *fnCallback, void *pUserData) = 0;
    virtual void OnMissingFile(const char *szPath) = 0;
    virtual ~ICryPak() {}
};

struct IStreamEngine
{
    virtual void* StartRead(const char* szSource, const char* szFile, void* pCallback = nullptr, void* pParams = nullptr) = 0;
    virtual unsigned GetFileSize(const char* szFile, unsigned nCryPakFlags = 0) = 0;
    virtual void Update(unsigned nFlags = 0) = 0;
    virtual unsigned Wait(unsigned nMilliseconds, unsigned nFlags = 0) = 0;
    virtual void GetMemoryStatistics(void *pSizer) = 0;
    virtual void SuspendCallbackTimeQuota() = 0;
    virtual void ResumeCallbackTimeQuota() = 0;
    virtual DWORD GetStreamCompressionMask() const = 0;
    virtual ~IStreamEngine() {}
};

enum EValidatorSeverity { VALIDATOR_ERROR = 0, VALIDATOR_WARNING, VALIDATOR_COMMENT };
enum EValidatorModule { VALIDATOR_MODULE_UNKNOWN = 0 };
struct SValidatorRecord { EValidatorSeverity severity; const char *file; const char *text; EValidatorModule module; int flags; };
struct IValidator
{
    virtual void Report(SValidatorRecord &record) = 0;
    virtual ~IValidator() {}
};

struct IFrameProfileSystem
{
    virtual void Reset() = 0;
    virtual void AddFrameProfiler(void *pProfiler) = 0;
    virtual void StartFrame() = 0;
    virtual void EndFrame() = 0;
    virtual int  GetProfilerCount() const = 0;
    virtual void* GetProfiler(int index) const = 0;
    virtual void Enable(bool bCollect, bool bDisplay) = 0;
    virtual void SetSubsystemFilter(bool bFilterSubsystem, int subsystem) = 0;
    virtual bool IsEnabled() const = 0;
    virtual bool IsProfiling() const = 0;
    virtual void SetDisplayQuantity(int quantity) = 0;
    virtual void StartCustomSection(void *pSection) = 0;
    virtual void EndCustomSection(void *pSection) = 0;
    virtual void AddPeaksListener(void *pPeakCallback) = 0;
    virtual void RemovePeaksListener(void *pPeakCallback) = 0;
    virtual ~IFrameProfileSystem() {}
};

// ============================================================================
// CAionLog: Complete ILog implementation
// ============================================================================
class CAionLog : public ILog
{
public:
    CAionLog() : m_verbosity(5), m_sFileName("Log.txt"), m_pFile(nullptr)
    {
        fopen_s(&m_pFile, m_sFileName.c_str(), "a+");
    }

    virtual ~CAionLog() override
    {
        if (m_pFile)
        {
            fclose(m_pFile);
            m_pFile = nullptr;
        }
    }

    virtual void Release() override { delete this; }

    virtual void SetFileName(const char *command = nullptr) override
    {
        if (command && command[0])
        {
            if (m_pFile) { fclose(m_pFile); m_pFile = nullptr; }
            m_sFileName = command;
            fopen_s(&m_pFile, m_sFileName.c_str(), "a+");
        }
    }

    virtual const char* GetFileName() override { return m_sFileName.c_str(); }

    virtual void Log(const char *szCommand, ...) override
    {
        if (!szCommand) return;
        char buffer[4096];
        va_list args;
        va_start(args, szCommand);
        vsnprintf(buffer, sizeof(buffer), szCommand, args);
        va_end(args);

        OutputDebugStringA(buffer);
        OutputDebugStringA("\n");

        if (m_pFile)
        {
            fprintf(m_pFile, "%s\n", buffer);
            fflush(m_pFile);
        }
    }

    virtual void LogWarning(const char *szCommand, ...) override
    {
        if (!szCommand) return;
        char buffer[4096];
        va_list args;
        va_start(args, szCommand);
        vsnprintf(buffer, sizeof(buffer), szCommand, args);
        va_end(args);

        OutputDebugStringA("[WARNING] ");
        OutputDebugStringA(buffer);
        OutputDebugStringA("\n");

        if (m_pFile)
        {
            fprintf(m_pFile, "[WARNING] %s\n", buffer);
            fflush(m_pFile);
        }
    }

    virtual void LogError(const char *szCommand, ...) override
    {
        if (!szCommand) return;
        char buffer[4096];
        va_list args;
        va_start(args, szCommand);
        vsnprintf(buffer, sizeof(buffer), szCommand, args);
        va_end(args);

        OutputDebugStringA("[ERROR] ");
        OutputDebugStringA(buffer);
        OutputDebugStringA("\n");

        if (m_pFile)
        {
            fprintf(m_pFile, "[ERROR] %s\n", buffer);
            fflush(m_pFile);
        }
    }

    virtual void LogPlus(const char *command, ...) override
    {
        if (!command) return;
        char buffer[4096];
        va_list args;
        va_start(args, command);
        vsnprintf(buffer, sizeof(buffer), command, args);
        va_end(args);

        OutputDebugStringA(buffer);
        if (m_pFile)
        {
            fprintf(m_pFile, "%s", buffer);
            fflush(m_pFile);
        }
    }

    virtual void LogToFile(const char *command, ...) override
    {
        if (!command || !m_pFile) return;
        char buffer[4096];
        va_list args;
        va_start(args, command);
        vsnprintf(buffer, sizeof(buffer), command, args);
        va_end(args);

        fprintf(m_pFile, "%s\n", buffer);
        fflush(m_pFile);
    }

    virtual void LogToFilePlus(const char *command, ...) override
    {
        if (!command || !m_pFile) return;
        char buffer[4096];
        va_list args;
        va_start(args, command);
        vsnprintf(buffer, sizeof(buffer), command, args);
        va_end(args);

        fprintf(m_pFile, "%s", buffer);
        fflush(m_pFile);
    }

    virtual void LogToConsole(const char *command, ...) override
    {
        if (!command) return;
        char buffer[4096];
        va_list args;
        va_start(args, command);
        vsnprintf(buffer, sizeof(buffer), command, args);
        va_end(args);

        OutputDebugStringA(buffer);
        OutputDebugStringA("\n");
    }

    virtual void LogToConsolePlus(const char *command, ...) override
    {
        if (!command) return;
        char buffer[4096];
        va_list args;
        va_start(args, command);
        vsnprintf(buffer, sizeof(buffer), command, args);
        va_end(args);

        OutputDebugStringA(buffer);
    }

    virtual void UpdateLoadingScreen(const char *command, ...) override {}
    virtual void UpdateLoadingScreenPlus(const char *command, ...) override {}
    virtual void EnableVerbosity(bool bEnable) override {}
    virtual void SetVerbosity(int verbosity) override { m_verbosity = verbosity; }
    virtual int  GetVerbosityLevel() override { return m_verbosity; }

private:
    int         m_verbosity;
    std::string m_sFileName;
    FILE*       m_pFile;
};

// ============================================================================
// CAionTimer: High precision ITimer implementation
// ============================================================================
class CAionTimer : public ITimer
{
public:
    CAionTimer()
        : m_fCurrTime(0.0f),
          m_fFrameTime(0.016f),
          m_fFrameRate(60.0f),
          m_bEnabled(true),
          m_nTicksPerSec(10000000),
          m_nBaseTicks(0),
          m_nLastTicks(0),
          m_nCurrTicks(0)
    {
        LARGE_INTEGER li;
        if (QueryPerformanceFrequency(&li))
            m_nTicksPerSec = li.QuadPart;
        if (QueryPerformanceCounter(&li))
        {
            m_nBaseTicks = li.QuadPart;
            m_nLastTicks = li.QuadPart;
            m_nCurrTicks = li.QuadPart;
        }
    }

    virtual ~CAionTimer() override {}

    virtual void Reset() override
    {
        LARGE_INTEGER li;
        if (QueryPerformanceCounter(&li))
        {
            m_nBaseTicks = li.QuadPart;
            m_nLastTicks = li.QuadPart;
            m_nCurrTicks = li.QuadPart;
        }
        m_fCurrTime = 0.0f;
        m_fFrameTime = 0.016f;
    }

    virtual void Update() override
    {
        LARGE_INTEGER li;
        if (QueryPerformanceCounter(&li))
        {
            m_nCurrTicks = li.QuadPart;
            int64_t diff = m_nCurrTicks - m_nLastTicks;
            m_nLastTicks = m_nCurrTicks;

            m_fFrameTime = static_cast<float>(static_cast<double>(diff) / static_cast<double>(m_nTicksPerSec));
            if (m_fFrameTime < 0.0001f) m_fFrameTime = 0.0001f;
            if (m_fFrameTime > 0.5f) m_fFrameTime = 0.5f;

            m_fCurrTime = static_cast<float>(static_cast<double>(m_nCurrTicks - m_nBaseTicks) / static_cast<double>(m_nTicksPerSec));
            if (m_fFrameTime > 0.0f)
                m_fFrameRate = 1.0f / m_fFrameTime;
        }
    }

    virtual const float GetCurrTime() const override { return m_fCurrTime; }

    virtual const CTimeValue GetCurrTimePrecise() const override
    {
        int64_t diff = m_nCurrTicks - m_nBaseTicks;
        int64_t ms = (diff * 1000) / m_nTicksPerSec;
        return CTimeValue(ms);
    }

    virtual const float GetAsyncCurTime() override
    {
        LARGE_INTEGER li;
        QueryPerformanceCounter(&li);
        int64_t diff = li.QuadPart - m_nBaseTicks;
        return static_cast<float>(static_cast<double>(diff) / static_cast<double>(m_nTicksPerSec));
    }

    virtual const float GetFrameTime() const override { return m_fFrameTime; }
    virtual void Enable(bool bEnable) override { m_bEnabled = bEnable; }
    virtual float GetFrameRate() override { return m_fFrameRate; }
    virtual float gfGetTime() override { return GetAsyncCurTime(); }
    virtual float MeasureTime(const char* comment) override { (void)comment; return GetFrameTime(); }

private:
    float   m_fCurrTime;
    float   m_fFrameTime;
    float   m_fFrameRate;
    bool    m_bEnabled;
    int64_t m_nTicksPerSec;
    int64_t m_nBaseTicks;
    int64_t m_nLastTicks;
    int64_t m_nCurrTicks;
};

// ============================================================================
// CAionCVar: Concrete ICVar implementation with memory-pointer binding
// ============================================================================
class CAionCVar : public ICVar
{
public:
    CAionCVar(const char* name, int val, int flags, const char* help = "")
        : m_name(name ? name : ""),
          m_help(help ? help : ""),
          m_flags(flags),
          m_type(CVAR_INT),
          m_iVal(val),
          m_fVal(static_cast<float>(val)),
          m_pInt(nullptr),
          m_pFloat(nullptr)
    {
        char buf[32];
        sprintf_s(buf, sizeof(buf), "%d", val);
        m_sVal = buf;
    }

    CAionCVar(const char* name, float val, int flags, const char* help = "")
        : m_name(name ? name : ""),
          m_help(help ? help : ""),
          m_flags(flags),
          m_type(CVAR_FLOAT),
          m_iVal(static_cast<int>(val)),
          m_fVal(val),
          m_pInt(nullptr),
          m_pFloat(nullptr)
    {
        char buf[32];
        sprintf_s(buf, sizeof(buf), "%f", val);
        m_sVal = buf;
    }

    CAionCVar(const char* name, const char* val, int flags, const char* help = "")
        : m_name(name ? name : ""),
          m_help(help ? help : ""),
          m_flags(flags),
          m_type(CVAR_STRING),
          m_iVal(val ? atoi(val) : 0),
          m_fVal(val ? static_cast<float>(atof(val)) : 0.0f),
          m_sVal(val ? val : ""),
          m_pInt(nullptr),
          m_pFloat(nullptr)
    {
    }

    CAionCVar(const char* name, int* pSrc, float defaultval, int flags, const char* help = "")
        : m_name(name ? name : ""),
          m_help(help ? help : ""),
          m_flags(flags),
          m_type(CVAR_INT),
          m_iVal(static_cast<int>(defaultval)),
          m_fVal(defaultval),
          m_pInt(pSrc),
          m_pFloat(nullptr)
    {
        if (m_pInt) *m_pInt = m_iVal;
        char buf[32];
        sprintf_s(buf, sizeof(buf), "%d", m_iVal);
        m_sVal = buf;
    }

    CAionCVar(const char* name, float* pSrc, float defaultval, int flags, const char* help = "")
        : m_name(name ? name : ""),
          m_help(help ? help : ""),
          m_flags(flags),
          m_type(CVAR_FLOAT),
          m_iVal(static_cast<int>(defaultval)),
          m_fVal(defaultval),
          m_pInt(nullptr),
          m_pFloat(pSrc)
    {
        if (m_pFloat) *m_pFloat = m_fVal;
        char buf[32];
        sprintf_s(buf, sizeof(buf), "%f", m_fVal);
        m_sVal = buf;
    }

    ~CAionCVar() {}

    virtual void Release() override
    {
        // In CryEngine architecture, CVars registered in IConsole are owned and managed by IConsole.
        // Releasing an interface reference does not destroy the console registry entry.
    }

    virtual int GetIVal() override
    {
        if (m_pInt) return *m_pInt;
        return m_iVal;
    }

    virtual float GetFVal() override
    {
        if (m_pFloat) return *m_pFloat;
        return m_fVal;
    }

    virtual char* GetString() override
    {
        return const_cast<char*>(m_sVal.c_str());
    }

    virtual void Set(const char* s) override
    {
        if (!s) return;
        m_sVal = s;
        m_iVal = atoi(s);
        m_fVal = static_cast<float>(atof(s));
        if (m_pInt) *m_pInt = m_iVal;
        if (m_pFloat) *m_pFloat = m_fVal;
    }

    virtual void ForceSet(const char* s) override
    {
        Set(s);
    }

    virtual void Set(float f) override
    {
        m_fVal = f;
        m_iVal = static_cast<int>(f);
        char buf[32];
        sprintf_s(buf, sizeof(buf), "%f", f);
        m_sVal = buf;
        if (m_pInt) *m_pInt = m_iVal;
        if (m_pFloat) *m_pFloat = m_fVal;
    }

    virtual void Set(int i) override
    {
        m_iVal = i;
        m_fVal = static_cast<float>(i);
        char buf[32];
        sprintf_s(buf, sizeof(buf), "%d", i);
        m_sVal = buf;
        if (m_pInt) *m_pInt = m_iVal;
        if (m_pFloat) *m_pFloat = m_fVal;
    }

    virtual void Refresh() override {}
    virtual void ClearFlags(int flags) override { m_flags &= ~flags; }
    virtual int  GetFlags() override { return m_flags; }
    virtual int  SetFlags(int flags) override { m_flags = flags; return m_flags; }
    virtual int  GetType() override { return m_type; }
    virtual const char* GetName() override { return m_name.c_str(); }
    virtual const char* GetHelp() override { return m_help.c_str(); }

private:
    std::string m_name;
    std::string m_help;
    int         m_flags;
    int         m_type;
    int         m_iVal;
    float       m_fVal;
    std::string m_sVal;
    int*        m_pInt;
    float*      m_pFloat;
};

// ============================================================================
// CAionConsole: Complete IConsole implementation
// ============================================================================
class CAionConsole : public IConsole
{
public:
    CAionConsole() {}
    ~CAionConsole()
    {
        for (auto& pair : m_vars)
        {
            delete pair.second;
        }
        m_vars.clear();
    }

    virtual void Release() override { delete this; }

    virtual ICVar* CreateVariable(const char *sName, const char *sValue, int nFlags, const char *help = "") override
    {
        if (!sName) return nullptr;
        auto it = m_vars.find(sName);
        if (it != m_vars.end())
        {
            it->second->Set(sValue);
            return it->second;
        }
        CAionCVar* pVar = new CAionCVar(sName, sValue, nFlags, help);
        m_vars[sName] = pVar;
        return pVar;
    }

    virtual ICVar* CreateVariable(const char *sName, int iValue, int nFlags, const char *help = "") override
    {
        if (!sName) return nullptr;
        auto it = m_vars.find(sName);
        if (it != m_vars.end())
        {
            it->second->Set(iValue);
            return it->second;
        }
        CAionCVar* pVar = new CAionCVar(sName, iValue, nFlags, help);
        m_vars[sName] = pVar;
        return pVar;
    }

    virtual ICVar* CreateVariable(const char *sName, float fValue, int nFlags, const char *help = "") override
    {
        if (!sName) return nullptr;
        auto it = m_vars.find(sName);
        if (it != m_vars.end())
        {
            it->second->Set(fValue);
            return it->second;
        }
        CAionCVar* pVar = new CAionCVar(sName, fValue, nFlags, help);
        m_vars[sName] = pVar;
        return pVar;
    }

    virtual void UnregisterVariable(const char *sVarName, bool bDelete = false) override
    {
        if (!sVarName) return;
        auto it = m_vars.find(sVarName);
        if (it != m_vars.end())
        {
            if (bDelete) delete it->second;
            m_vars.erase(it);
        }
    }

    virtual void SetScrollMax(int value) override {}
    virtual void AddOutputPrintSink(IOutputPrintSink *inpSink) override {}
    virtual void RemoveOutputPrintSink(IOutputPrintSink *inpSink) override {}
    virtual void ShowConsole(bool show) override {}

    virtual int Register(const char *name, void *src, float defaultvalue, int flags, int type, const char *help = "") override
    {
        if (!name || !src) return 0;
        if (type == CVAR_INT)
        {
            Register(name, (int*)src, defaultvalue, flags, help);
            return static_cast<int>(defaultvalue);
        }
        else if (type == CVAR_FLOAT)
        {
            Register(name, (float*)src, defaultvalue, flags, help);
            return static_cast<int>(defaultvalue);
        }
        return 0;
    }

    virtual float Register(const char *name, float *src, float defaultvalue, int flags = 0, const char *help = "") override
    {
        if (!name || !src) return defaultvalue;
        auto it = m_vars.find(name);
        if (it != m_vars.end())
        {
            it->second->Set(defaultvalue);
            return defaultvalue;
        }
        CAionCVar* pVar = new CAionCVar(name, src, defaultvalue, flags, help);
        m_vars[name] = pVar;
        return defaultvalue;
    }

    virtual int Register(const char *name, int *src, float defaultvalue, int flags = 0, const char *help = "") override
    {
        if (!name || !src) return static_cast<int>(defaultvalue);
        auto it = m_vars.find(name);
        if (it != m_vars.end())
        {
            it->second->Set(static_cast<int>(defaultvalue));
            return static_cast<int>(defaultvalue);
        }
        CAionCVar* pVar = new CAionCVar(name, src, defaultvalue, flags, help);
        m_vars[name] = pVar;
        return static_cast<int>(defaultvalue);
    }

    virtual void DumpCVars(ICVarDumpSink *pCallback, unsigned int nFlagsFilter = 0) override
    {
        if (!pCallback) return;
        for (auto& pair : m_vars)
        {
            pCallback->OnElementFound(pair.second);
        }
    }

    virtual void CreateKeyBind(const char *sCmd, const char *sRes, bool bExecute = false) override {}
    virtual void SetImage(void *pImage, bool bDeleteCurrent = false) override {}
    virtual void *GetImage() override { return nullptr; }
    virtual void StaticBackground(bool bStatic) override {}
    virtual void SetLoadingImage(const char *szFilename) override {}
    virtual bool GetLineNo(const DWORD indwLineNo, char *outszBuffer, const DWORD indwBufferSize) const override { return false; }
    virtual int GetLineCount() const override { return 0; }

    virtual ICVar* GetCVar(const char *name, const bool bCaseSensitive = true) override
    {
        if (!name) return nullptr;
        auto it = m_vars.find(name);
        if (it != m_vars.end()) return it->second;
        return nullptr;
    }

    virtual void* GetFont() override { return nullptr; }
    virtual void Help(const char *command = nullptr) override {}

    virtual char* GetVariable(const char *szVarName, const char *szFileName, const char *def_val) override
    {
        ICVar* pVar = GetCVar(szVarName);
        if (pVar) return pVar->GetString();
        return const_cast<char*>(def_val ? def_val : "");
    }

    virtual float GetVariable(const char *szVarName, const char *szFileName, float def_val) override
    {
        ICVar* pVar = GetCVar(szVarName);
        if (pVar) return pVar->GetFVal();
        return def_val;
    }

    virtual void PrintLine(const char *s) override { if (s) OutputDebugStringA(s); }
    virtual void PrintLinePlus(const char *s) override { if (s) OutputDebugStringA(s); }
    virtual bool GetStatus() override { return false; }
    virtual void Clear() override {}
    virtual void Update() override {}
    virtual void Draw() override {}

    virtual void AddCommand(const char *sName, const char *sScriptFunc, const DWORD indwFlags = 0, const char *help = "") override {}
    virtual void ExecuteString(const char *command, bool bNeedSlash = false, bool bIgnoreDevMode = false) override {}
    virtual void Exit(const char *command, ...) override {}
    virtual bool IsOpened() override { return false; }

    virtual int   GetNumVars() override { return static_cast<int>(m_vars.size()); }
    virtual void  GetSortedVars(const char **pszArray, size_t numItems) override {}
    virtual const char* AutoComplete(const char* substr) override { return ""; }
    virtual const char* AutoCompletePrev(const char* substr) override { return ""; }
    virtual char* ProcessCompletion(const char *szInputBuffer) override { return nullptr; }
    virtual void  ResetAutoCompletion() override {}
    virtual void  DumpCommandsVars(char *prefix) override {}
    virtual void  GetMemoryUsage(void* pSizer) override {}
    virtual void  ResetProgressBar(int nProgressRange) override {}
    virtual void  TickProgressBar() override {}
    virtual void  DumpKeyBinds(IKeyBindDumpSink *pCallback) override {}
    virtual const char* FindKeyBind(const char *sCmd) override { return ""; }
    virtual void  AddConsoleVarSink(IConsoleVarSink *pSink) override {}
    virtual void  RemoveConsoleVarSink(IConsoleVarSink *pSink) override {}
    virtual const char* GetHistoryElement(const bool bUpOrDown) override { return ""; }
    virtual void  AddCommandToHistory(const char *szCommand) override {}

private:
    std::map<std::string, ICVar*> m_vars;
};

// ============================================================================
// CAionPak: Concrete ICryPak file management implementation
// ============================================================================
class CAionPak : public ICryPak
{
public:
    CAionPak() {}
    virtual ~CAionPak() override {}

    virtual bool Init(const char *szBasePath) override { return true; }
    virtual void Release() override { delete this; }

    virtual bool OpenPack(const char *pName, unsigned nFlags = 0) override { return true; }
    virtual bool OpenPack(const char* pBindingRoot, const char *pName, unsigned nFlags = 0) override { return true; }
    virtual bool ClosePack(const char* pName, unsigned nFlags = 0) override { return true; }
    virtual bool OpenPacks(const char *pWildcard, unsigned nFlags = 0) override { return true; }
    virtual bool OpenPacks(const char* pBindingRoot, const char *pWildcard, unsigned nFlags = 0) override { return true; }
    virtual bool ClosePacks(const char* pWildcard, unsigned nFlags = 0) override { return true; }
    virtual void AddMod(const char* szMod) override {}
    virtual void RemoveMod(const char* szMod) override {}

    virtual void* GetPakInfo() override { return nullptr; }
    virtual void  FreePakInfo(void* pInfo) override {}

    virtual FILE *FOpen(const char *pName, const char *mode, unsigned nFlags = 0) override
    {
        if (!pName || !mode) return nullptr;
        FILE* fp = nullptr;
        fopen_s(&fp, pName, mode);
        return fp;
    }

    virtual FILE *FOpen(const char *pName, const char *mode, char *szFileGamePath, int nLen) override
    {
        return FOpen(pName, mode, 0);
    }

    virtual size_t FRead(void *data, size_t length, size_t elems, FILE *handle) override
    {
        if (!data || !handle) return 0;
        return fread(data, length, elems, handle);
    }

    virtual size_t FWrite(void *data, size_t length, size_t elems, FILE *handle) override
    {
        if (!data || !handle) return 0;
        return fwrite(data, length, elems, handle);
    }

    virtual int FSeek(FILE *handle, long seek, int mode) override
    {
        if (!handle) return -1;
        return fseek(handle, seek, mode);
    }

    virtual long FTell(FILE *handle) override
    {
        if (!handle) return -1;
        return ftell(handle);
    }

    virtual int FClose(FILE *handle) override
    {
        if (!handle) return -1;
        return fclose(handle);
    }

    virtual int FEof(FILE *handle) override
    {
        if (!handle) return 1;
        return feof(handle);
    }

    virtual int FScanf(FILE *handle, const char *format, ...) override
    {
        return 0;
    }

    virtual char *FGetS(char *str, int n, FILE *handle) override
    {
        if (!str || !handle) return nullptr;
        return fgets(str, n, handle);
    }

    virtual int Getc(FILE *handle) override
    {
        if (!handle) return EOF;
        return fgetc(handle);
    }

    virtual int Ungetc(int c, FILE *handle) override
    {
        if (!handle) return EOF;
        return ungetc(c, handle);
    }

    virtual intptr_t FindFirst(const char *pDir, struct _finddata_t *fd) override
    {
        if (!pDir || !fd) return -1;
        return _findfirst(pDir, fd);
    }

    virtual int FindNext(intptr_t handle, struct _finddata_t *fd) override
    {
        if (handle == -1 || !fd) return -1;
        return _findnext(handle, fd);
    }

    virtual int FindClose(intptr_t handle) override
    {
        if (handle == -1) return -1;
        return _findclose(handle);
    }

    virtual FILETIME GetFileTime(const char *pName) override
    {
        FILETIME ft = { 0, 0 };
        return ft;
    }

    virtual bool IsCpuFileAccessAllowed() override { return true; }
    virtual void SetDirectFileAccessMode(bool bEnable) override {}
    virtual bool GetDirectFileAccessMode() override { return true; }
    virtual void RecordFileOpen(bool bEnable) override {}
    virtual void EnumerateRecordedFiles(void *fnCallback, void *pUserData) override {}
    virtual void OnMissingFile(const char *szPath) override {}
};

// ============================================================================
// CAionStreamEngine: IStreamEngine implementation
// ============================================================================
class CAionStreamEngine : public IStreamEngine
{
public:
    CAionStreamEngine() {}
    virtual ~CAionStreamEngine() override {}

    virtual void* StartRead(const char* szSource, const char* szFile, void* pCallback = nullptr, void* pParams = nullptr) override
    {
        return nullptr;
    }

    virtual unsigned GetFileSize(const char* szFile, unsigned nCryPakFlags = 0) override
    {
        if (!szFile) return 0;
        WIN32_FILE_ATTRIBUTE_DATA fad;
        if (GetFileAttributesExA(szFile, GetFileExInfoStandard, &fad))
            return fad.nFileSizeLow;
        return 0;
    }

    virtual void Update(unsigned nFlags = 0) override {}
    virtual unsigned Wait(unsigned nMilliseconds, unsigned nFlags = 0) override { return 0; }
    virtual void GetMemoryStatistics(void *pSizer) override {}
    virtual void SuspendCallbackTimeQuota() override {}
    virtual void ResumeCallbackTimeQuota() override {}
    virtual DWORD GetStreamCompressionMask() const override { return 0; }
};

// ============================================================================
// CAionValidator: IValidator implementation
// ============================================================================
class CAionValidator : public IValidator
{
public:
    CAionValidator(ILog* pLog) : m_pLog(pLog) {}
    virtual ~CAionValidator() override {}

    virtual void Report(SValidatorRecord &record) override
    {
        if (m_pLog && record.text)
        {
            if (record.severity == VALIDATOR_ERROR)
                m_pLog->LogError("[%s] %s (%s)", "VALIDATOR", record.text, record.file ? record.file : "");
            else
                m_pLog->LogWarning("[%s] %s (%s)", "VALIDATOR", record.text, record.file ? record.file : "");
        }
    }

private:
    ILog* m_pLog;
};

// ============================================================================
// CAionProfileSystem: IFrameProfileSystem implementation
// ============================================================================
class CAionProfileSystem : public IFrameProfileSystem
{
public:
    CAionProfileSystem() {}
    virtual ~CAionProfileSystem() override {}

    virtual void Reset() override {}
    virtual void AddFrameProfiler(void *pProfiler) override {}
    virtual void StartFrame() override {}
    virtual void EndFrame() override {}
    virtual int  GetProfilerCount() const override { return 0; }
    virtual void* GetProfiler(int index) const override { return nullptr; }
    virtual void Enable(bool bCollect, bool bDisplay) override {}
    virtual void SetSubsystemFilter(bool bFilterSubsystem, int subsystem) override {}
    virtual bool IsEnabled() const override { return false; }
    virtual bool IsProfiling() const override { return false; }
    virtual void SetDisplayQuantity(int quantity) override {}
    virtual void StartCustomSection(void *pSection) override {}
    virtual void EndCustomSection(void *pSection) override {}
    virtual void AddPeaksListener(void *pPeakCallback) override {}
    virtual void RemovePeaksListener(void *pPeakCallback) override {}
};

// ============================================================================
// CSystem: Core Implementation
// ============================================================================

CSystem::CSystem()
    : m_pLog(nullptr),
      m_pConsole(nullptr),
      m_pTimer(nullptr),
      m_pIPak(nullptr),
      m_pStreamEngine(nullptr),
      m_pInput(nullptr),
      m_pScriptSystem(nullptr),
      m_pEntitySystem(nullptr),
      m_pCryFont(nullptr),
      m_pSound(nullptr),
      m_pMusic(nullptr),
      m_pPhysicalWorld(nullptr),
      m_pMovieSystem(nullptr),
      m_pAISystem(nullptr),
      m_pAnimationSystem(nullptr),
      m_p3DEngine(nullptr),
      m_pRenderer(nullptr),
      m_pNetwork(nullptr),
      m_pValidator(nullptr),
      m_pProfileSystem(nullptr),
      m_hInputDll(nullptr),
      m_hScriptDll(nullptr),
      m_hFontDll(nullptr),
      m_hEntityDll(nullptr),
      m_hSoundDll(nullptr),
      m_hPhysicsDll(nullptr),
      m_hMovieDll(nullptr),
      m_hAnimationDll(nullptr),
      m_h3DEngineDll(nullptr),
      m_pGame(nullptr),
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

    // Instantiate core internal subsystems immediately
    m_pLog = new CAionLog();
    m_pTimer = new CAionTimer();
    m_pConsole = new CAionConsole();
    m_pIPak = new CAionPak();
    m_pStreamEngine = new CAionStreamEngine();
    m_pValidator = new CAionValidator(m_pLog);
    m_pProfileSystem = new CAionProfileSystem();

    // NCSoft extensions
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

    delete m_pProfileSystem; m_pProfileSystem = nullptr;
    delete m_pValidator;     m_pValidator = nullptr;
    delete m_pStreamEngine;  m_pStreamEngine = nullptr;
    delete m_pIPak;          m_pIPak = nullptr;
    delete m_pConsole;       m_pConsole = nullptr;
    delete m_pTimer;         m_pTimer = nullptr;
    delete m_pLog;           m_pLog = nullptr;
}

static HMODULE TryLoadModule(const char* name)
{
    HMODULE h = GetModuleHandleA(name);
    if (h) return h;
    h = LoadLibraryA(name);
    if (h) return h;
    char path[MAX_PATH];
    sprintf_s(path, sizeof(path), "bin64\\%s", name);
    h = LoadLibraryA(path);
    if (h) return h;

    wchar_t sysModPath[MAX_PATH] = { 0 };
    HMODULE hThis = NULL;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       (LPCWSTR)&TryLoadModule, &hThis);
    if (hThis && GetModuleFileNameW(hThis, sysModPath, MAX_PATH))
    {
        wchar_t* pSlash = wcsrchr(sysModPath, L'\\');
        if (pSlash)
        {
            *(pSlash + 1) = L'\0';
            wchar_t wName[MAX_PATH];
            MultiByteToWideChar(CP_UTF8, 0, name, -1, wName, MAX_PATH);
            wcscat_s(sysModPath, MAX_PATH, wName);
            h = LoadLibraryExW(sysModPath, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
        }
    }
    return h;
}

bool CSystem::Init(const SSystemInitParams& params)
{
    printf("  [Init] In CSystem::Init...\n"); fflush(stdout);
    if (m_pLog)
    {
        m_pLog->Log("====================================================================");
        m_pLog->Log("[CrySystem] Initializing CryEngine Aion Classic 5.0 Subsystems...");
        m_pLog->Log("====================================================================");
    }

    printf("  [Init] g_pGameOptions->Init...\n"); fflush(stdout);
    if (g_pGameOptions)
        g_pGameOptions->Init();

    printf("  [Init] Loading CryInput...\n"); fflush(stdout);
    // 1. Dynamic Load CryInput.dll
    __try {
        m_hInputDll = TryLoadModule("CryInput.dll");
        if (m_hInputDll)
        {
            typedef IInput* (*PFN_CREATE_INPUT)(ISystem*, void*, void*, bool);
            PFN_CREATE_INPUT pfn = (PFN_CREATE_INPUT)GetProcAddress(m_hInputDll, "CreateInput");
            if (pfn)
            {
                m_pInput = pfn(this, params.hInstance, params.hWnd, false);
                printf("  [Init] CryInput initialized at %p\n", m_pInput); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryInput initialized at %p", m_pInput);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryInput init exception intercepted\n"); fflush(stdout);
    }

    // 2. Dynamic Load CryScriptSystem.dll
    __try {
        m_hScriptDll = TryLoadModule("CryScriptSystem.dll");
        if (m_hScriptDll)
        {
            typedef IScriptSystem* (*PFN_CREATE_SCRIPT)(ISystem*, void*, void*, int);
            PFN_CREATE_SCRIPT pfn = (PFN_CREATE_SCRIPT)GetProcAddress(m_hScriptDll, "CreateScriptSystem");
            if (pfn)
            {
                m_pScriptSystem = pfn(this, nullptr, nullptr, 0);
                printf("  [Init] CryScriptSystem initialized at %p\n", m_pScriptSystem); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryScriptSystem initialized at %p", m_pScriptSystem);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryScriptSystem init exception intercepted\n"); fflush(stdout);
    }

    // 3. Dynamic Load CryFont.dll
    __try {
        m_hFontDll = TryLoadModule("CryFont.dll");
        if (m_hFontDll)
        {
            typedef ICryFont* (*PFN_CREATE_FONT)(ISystem*);
            PFN_CREATE_FONT pfn = (PFN_CREATE_FONT)GetProcAddress(m_hFontDll, "CreateCryFontInterface");
            if (!pfn)
                pfn = (PFN_CREATE_FONT)GetProcAddress(m_hFontDll, "CreateCryFont");
            if (pfn)
            {
                m_pCryFont = pfn(this);
                printf("  [Init] CryFont initialized at %p\n", m_pCryFont); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryFont initialized at %p", m_pCryFont);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryFont init exception intercepted\n"); fflush(stdout);
    }

    // 4. Dynamic Load CryEntitySystem.dll
    __try {
        m_hEntityDll = TryLoadModule("CryEntitySystem.dll");
        if (m_hEntityDll)
        {
            typedef IEntitySystem* (*PFN_CREATE_ENTITY)(ISystem*);
            PFN_CREATE_ENTITY pfn = (PFN_CREATE_ENTITY)GetProcAddress(m_hEntityDll, "CreateEntitySystem");
            if (pfn)
            {
                m_pEntitySystem = pfn(this);
                printf("  [Init] CryEntitySystem initialized at %p\n", m_pEntitySystem); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryEntitySystem initialized at %p", m_pEntitySystem);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryEntitySystem init exception intercepted\n"); fflush(stdout);
    }

    // 5. Dynamic Load CrySoundSystem.dll
    printf("  [Init] Attempting to load CrySoundSystem...\n"); fflush(stdout);
    __try {
        m_hSoundDll = TryLoadModule("CrySoundSystem.dll");
        printf("  [Init] TryLoadModule CrySoundSystem returned %p\n", m_hSoundDll); fflush(stdout);
        if (m_hSoundDll)
        {
            typedef ISoundSystem* (*PFN_CREATE_SOUND)(ISystem*, void*);
            PFN_CREATE_SOUND pfn = (PFN_CREATE_SOUND)GetProcAddress(m_hSoundDll, "CreateSoundSystem");
            printf("  [Init] GetProcAddress CreateSoundSystem returned %p\n", pfn); fflush(stdout);
            if (pfn)
            {
                printf("  [Init] Calling CreateSoundSystem(%p, %p)...\n", this, params.hWnd); fflush(stdout);
                m_pSound = pfn(this, params.hWnd);
                printf("  [Init] CrySoundSystem initialized at %p\n", m_pSound); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CrySoundSystem initialized at %p", m_pSound);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CrySoundSystem init exception intercepted (code: 0x%08lX)\n", GetExceptionCode()); fflush(stdout);
    }

    // 6. Dynamic Load CryPhysics.dll
    __try {
        m_hPhysicsDll = TryLoadModule("CryPhysics.dll");
        if (m_hPhysicsDll)
        {
            typedef IPhysicalWorld* (*PFN_CREATE_PHYSICS)(ISystem*);
            PFN_CREATE_PHYSICS pfn = (PFN_CREATE_PHYSICS)GetProcAddress(m_hPhysicsDll, "CreatePhysicalWorld");
            if (pfn)
            {
                m_pPhysicalWorld = pfn(this);
                printf("  [Init] CryPhysics initialized at %p\n", m_pPhysicalWorld); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryPhysics initialized at %p", m_pPhysicalWorld);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryPhysics init exception intercepted\n"); fflush(stdout);
    }

    // 7. Dynamic Load CryMovie.dll
    __try {
        m_hMovieDll = TryLoadModule("CryMovie.dll");
        if (m_hMovieDll)
        {
            typedef IMovieSystem* (*PFN_CREATE_MOVIE)(ISystem*);
            PFN_CREATE_MOVIE pfn = (PFN_CREATE_MOVIE)GetProcAddress(m_hMovieDll, "CreateMovieSystem");
            if (pfn)
            {
                m_pMovieSystem = pfn(this);
                printf("  [Init] CryMovie initialized at %p\n", m_pMovieSystem); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryMovie initialized at %p", m_pMovieSystem);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryMovie init exception intercepted\n"); fflush(stdout);
    }

    // 8. Dynamic Load CryAnimation.dll
    __try {
        m_hAnimationDll = TryLoadModule("CryAnimation.dll");
        if (m_hAnimationDll)
        {
            typedef ICryCharManager* (*PFN_CREATE_ANIM)(ISystem*, const char*);
            PFN_CREATE_ANIM pfn = (PFN_CREATE_ANIM)GetProcAddress(m_hAnimationDll, "CreateCharManager");
            if (pfn)
            {
                m_pAnimationSystem = pfn(this, "CryAnimation_InterfaceVersion");
                printf("  [Init] CryAnimation initialized at %p\n", m_pAnimationSystem); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem CryAnimation initialized at %p", m_pAnimationSystem);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] CryAnimation init exception intercepted (0x%08lX)\n", GetExceptionCode()); fflush(stdout);
    }

    // 9. Dynamic Load Cry3DEngine.dll
    __try {
        m_h3DEngineDll = TryLoadModule("Cry3DEngine.dll");
        if (m_h3DEngineDll)
        {
            typedef I3DEngine* (*PFN_CREATE_3DENGINE)(ISystem*, const char*);
            PFN_CREATE_3DENGINE pfn = (PFN_CREATE_3DENGINE)GetProcAddress(m_h3DEngineDll, "CreateCry3DEngine");
            if (pfn)
            {
                m_p3DEngine = pfn(this, "Cry3DEngine_InterfaceVersion");
                printf("  [Init] Cry3DEngine initialized at %p\n", m_p3DEngine); fflush(stdout);
                if (m_pLog) m_pLog->Log("[CrySystem] Subsystem Cry3DEngine initialized at %p", m_p3DEngine);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        printf("  [Init] Cry3DEngine init exception intercepted (0x%08lX)\n", GetExceptionCode()); fflush(stdout);
    }

    if (m_pLog)
        m_pLog->Log("[CrySystem] All subsystems initialized successfully.");

    return true;
}

bool CSystem::CreateGame(const SGameInitParams& params)
{
    if (m_pLog)
        m_pLog->Log("[CrySystem::CreateGame] Starting CreateGame...");

    if (params.pGame)
    {
        m_pGame = params.pGame;
        return true;
    }

    const char* dllName = params.sGameDLL ? params.sGameDLL : "Game.dll";
    HMODULE hGameDll = TryLoadModule(dllName);
    if (!hGameDll)
    {
        Error("Error in CSystem::CreateGame, failed to load %s", dllName);
        return false;
    }

    PFN_CREATE_GAME_INSTANCE pfnCreate = (PFN_CREATE_GAME_INSTANCE)GetProcAddress(hGameDll, "CreateGameInstance");
    if (!pfnCreate)
    {
        pfnCreate = (PFN_CREATE_GAME_INSTANCE)GetProcAddress(hGameDll, (LPCSTR)1);
    }

    if (!pfnCreate)
    {
        Error("Error in CSystem::CreateGame, CreateGameInstance entry point not found in %s", dllName);
        return false;
    }

    m_pGame = reinterpret_cast<IGame*>(pfnCreate(this));
    if (!m_pGame)
    {
        Error("Error in CSystem::CreateGame, CreateGameInstance returned NULL");
        return false;
    }

    typedef bool (__fastcall *PFN_GAME_INIT)(void* pThis, ISystem* pSys, bool bEditor, bool bDedicated);
    void** gameVTable = *reinterpret_cast<void***>(m_pGame);
    PFN_GAME_INIT pfnInit = reinterpret_cast<PFN_GAME_INIT>(gameVTable[0]);
    if (pfnInit)
    {
        pfnInit(m_pGame, this, false, params.bDedicatedServer);
    }

    return true;
}

bool CSystem::IsLoadingScreenEnabled() { return (m_dwLoadingState == 1); }
bool CSystem::IsPreloadDone() { return (m_dwLoadingState == 2); }
void CSystem::SetLoadingProgress(float progress) { m_fLoadingProgress = progress; }
void CSystem::Release() { delete this; }

void CSystem::ShutDown(bool bRelaunch)
{
    (void)bRelaunch;
    m_pGame = nullptr;

    if (m_h3DEngineDll)  { FreeLibrary(m_h3DEngineDll);  m_h3DEngineDll = nullptr;  m_p3DEngine = nullptr; }
    if (m_hAnimationDll) { FreeLibrary(m_hAnimationDll); m_hAnimationDll = nullptr; m_pAnimationSystem = nullptr; }
    if (m_hMovieDll)     { FreeLibrary(m_hMovieDll);     m_hMovieDll = nullptr;     m_pMovieSystem = nullptr; }
    if (m_hPhysicsDll)   { FreeLibrary(m_hPhysicsDll);   m_hPhysicsDll = nullptr;   m_pPhysicalWorld = nullptr; }
    if (m_hSoundDll)     { FreeLibrary(m_hSoundDll);     m_hSoundDll = nullptr;     m_pSound = nullptr; }
    if (m_hEntityDll)    { FreeLibrary(m_hEntityDll);    m_hEntityDll = nullptr;    m_pEntitySystem = nullptr; }
    if (m_hFontDll)      { FreeLibrary(m_hFontDll);      m_hFontDll = nullptr;      m_pCryFont = nullptr; }
    if (m_hScriptDll)    { FreeLibrary(m_hScriptDll);    m_hScriptDll = nullptr;    m_pScriptSystem = nullptr; }
    if (m_hInputDll)     { FreeLibrary(m_hInputDll);     m_hInputDll = nullptr;     m_pInput = nullptr; }
}

bool CSystem::WasInDevMode() { return false; }
void CSystem::Relaunch(bool bRelaunch) { (void)bRelaunch; }
void CSystem::UpdateLoadingScreen() {}
void CSystem::RenderBegin() {}
void CSystem::Render() {}
void CSystem::RenderEnd() {}
void CSystem::RenderStatistics() {}
void CSystem::DumpMemoryUsageStatistics() {}
void CSystem::Quit() { PostQuitMessage(0); }
bool CSystem::IsQuitting() { return false; }

void CSystem::Error(const char* sFormat, ...)
{
    char buf[1024];
    va_list args;
    va_start(args, sFormat);
    vsnprintf(buf, sizeof(buf), sFormat, args);
    va_end(args);
    if (m_pLog) m_pLog->LogError("[CrySystem ERROR] %s", buf);
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
    if (m_pLog) m_pLog->LogWarning("[CrySystem WARNING] %s", buf);
    OutputDebugStringA("[CrySystem WARNING] ");
    OutputDebugStringA(buf);
    OutputDebugStringA("\n");
}

bool CSystem::CheckLogVerbosity(int verbosity) { return (verbosity <= 5); }
bool CSystem::IsDedicated() { return false; }

bool CSystem::Update(int updateFlags, int nPauseMode)
{
    (void)updateFlags; (void)nPauseMode;
    if (m_pTimer) m_pTimer->Update();
    if (g_pGameFixedFrame) g_pGameFixedFrame->BeginFrameWait();

    if (m_pGame)
    {
        typedef bool (__fastcall *PFN_GAME_UPDATE)(void* pThis);
        void** gameVTable = *reinterpret_cast<void***>(m_pGame);
        PFN_GAME_UPDATE pfnUpdate = reinterpret_cast<PFN_GAME_UPDATE>(gameVTable[2]);
        if (pfnUpdate) pfnUpdate(m_pGame);
    }
    return true;
}

void CSystem::UpdateScriptSink() {}
void CSystem::SetForceNonDevMode(const bool bValue) { (void)bValue; }
bool CSystem::GetForceNonDevMode() const { return true; }
bool CSystem::IsDevMode() const { return false; }
void CSystem::CreateEntityScriptBinding(void* pEntity) { (void)pEntity; }
void CSystem::IgnoreUpdates(bool bIgnore) { (void)bIgnore; }

// Core Subsystems Virtual Getters
IGame*               CSystem::GetIGame() { return m_pGame; }
INetwork*            CSystem::GetINetwork() { return m_pNetwork; }
IRenderer*           CSystem::GetIRenderer() { return m_pRenderer; }
IInput*              CSystem::GetIInput() { return m_pInput; }
ITimer*              CSystem::GetITimer() { return m_pTimer; }
ICryPak*             CSystem::GetIPak() { return m_pIPak; }
IConsole*            CSystem::GetIConsole() { return m_pConsole; }
IScriptSystem*       CSystem::GetIScriptSystem() { return m_pScriptSystem; }
I3DEngine*           CSystem::GetI3DEngine() { return m_p3DEngine; }
ICryCharManager*     CSystem::GetIAnimationSystem() { return m_pAnimationSystem; }
ISoundSystem*        CSystem::GetISoundSystem() { return m_pSound; }
IMusicSystem*        CSystem::GetIMusicSystem() { return m_pMusic; }
IPhysicalWorld*      CSystem::GetIPhysicalWorld() { return m_pPhysicalWorld; }
IMovieSystem*        CSystem::GetIMovieSystem() { return m_pMovieSystem; }
IAISystem*           CSystem::GetAISystem() { return m_pAISystem; }
IMemoryManager*      CSystem::GetIMemoryManager() { return nullptr; }
IEntitySystem*       CSystem::GetIEntitySystem() { return m_pEntitySystem; }
ICryFont*            CSystem::GetICryFont() { return m_pCryFont; }
ILog*                CSystem::GetILog() { return m_pLog; }
IStreamEngine*       CSystem::GetStreamEngine() { return m_pStreamEngine; }
CLUADbg*             CSystem::GetLuaDebugger() { return nullptr; }
IValidator*          CSystem::GetIValidator() { return m_pValidator; }
IFrameProfileSystem* CSystem::GetIProfileSystem() { return m_pProfileSystem; }

const char* CSystem::GetUserName() { return m_szUserName; }
int CSystem::GetCPUFlags() { return 0x1F; }
double CSystem::GetSecondsPerCycle() { return 1.0 / static_cast<double>(m_perfFreq ? m_perfFreq : 10000000); }
float CSystem::GetGCFrequency() { return 10.0f; }
void CSystem::SetGCFrequency(float fRate) { (void)fRate; }
void CSystem::DebugStats(bool checkpoint, bool leaks) { (void)checkpoint; (void)leaks; }
void CSystem::DumpWinHeaps() {}
int CSystem::DumpMMStats(bool log) { (void)log; return 0; }
static SFileVersion s_fileVersion("5.0.2.6");
const SFileVersion& CSystem::GetFileVersion() { return s_fileVersion; }
const SFileVersion& CSystem::GetProductVersion() { return s_fileVersion; }
XDOM::IXMLDOMDocument* CSystem::CreateXMLDocument() { return nullptr; }
XmlNodeRef CSystem::CreateXmlNode(const char* sNodeName) { (void)sNodeName; return XmlNodeRef(nullptr); }
XmlNodeRef CSystem::LoadXmlFile(const char* sFilename) { (void)sFilename; return XmlNodeRef(nullptr); }
XmlNodeRef CSystem::LoadXmlFromString(const char* sXmlString) { (void)sXmlString; return XmlNodeRef(nullptr); }
void CSystem::SetIProcess(void* pProcess) { (void)pProcess; }
void* CSystem::GetIProcess() { return nullptr; }
IRenderer* CSystem::CreateRenderer(bool fullscreen, void* hinst, void* hWndAttach) { return nullptr; }
bool CSystem::IsTestMode() const { return false; }
void CSystem::ShowDebugger(const char* pszSourceFile, int iLine, const char* pszReason) {}
void CSystem::SetFrameProfiler(bool on, bool display, char* prefix) {}

void CSystem::OnEnvironmentUpdate()
{
    if (m_pGame)
    {
        typedef void (__fastcall *PFN_ENV_UPDATE)(void* pThis);
        void** gameVTable = *reinterpret_cast<void***>(m_pGame);
        PFN_ENV_UPDATE pfnEnv = reinterpret_cast<PFN_ENV_UPDATE>(gameVTable[37]);
        if (pfnEnv) pfnEnv(m_pGame);
    }
}

// ============================================================================
// Official Slot Implementations for Parity with CrySystem.dll Primary VTable
// ============================================================================
float CSystem::Slot16() { return m_fLoadingProgress; }
bool  CSystem::Slot17() { return (m_dwLoadingState == 1); }
void  CSystem::Slot18() {}
bool  CSystem::Slot19() { return (m_dwLoadingState == 2); }

void* CSystem::Slot29() { return m_pGame; }
CCamera& CSystem::GetViewCamera() { return *reinterpret_cast<CCamera*>((uintptr_t)this + 0x2968); }
void  CSystem::Slot31() {}
void  CSystem::Slot32() {}
bool  CSystem::Slot35() { return true; }
void  CSystem::Slot38() {}
void  CSystem::Slot39() {}

void* CSystem::Slot69() { return nullptr; }
void* CSystem::Slot70() { return nullptr; }
void* CSystem::Slot71() { return nullptr; }
void* CSystem::Slot72() { return nullptr; }
void* CSystem::Slot73() { return nullptr; }
void* CSystem::Slot75() { return nullptr; }
void* CSystem::Slot76() { return nullptr; }
void* CSystem::Slot77() { return nullptr; }

void CSystem::Slot90() {}  void CSystem::Slot91() {}  void CSystem::Slot92() {}  void CSystem::Slot93() {}
void CSystem::Slot94() {}  void CSystem::Slot95() {}  void CSystem::Slot96() {}  void CSystem::Slot97() {}
void CSystem::Slot98() {}  void CSystem::Slot99() {}  void CSystem::Slot100() {} void CSystem::Slot101() {}
void CSystem::Slot102() {} void CSystem::Slot103() {} void CSystem::Slot104() {} void CSystem::Slot105() {}
void CSystem::Slot106() {} void CSystem::Slot107() {} void CSystem::Slot108() {} void CSystem::Slot109() {}
void CSystem::Slot110() {} void CSystem::Slot111() {} void CSystem::Slot112() {} void CSystem::Slot113() {}
void CSystem::Slot114() {} void CSystem::Slot115() {} void CSystem::Slot116() {} void CSystem::Slot117() {}
void CSystem::Slot118() {} void CSystem::Slot119() {} void CSystem::Slot120() {} void CSystem::Slot121() {}
void CSystem::Slot122() {} void CSystem::Slot123() {} void CSystem::Slot124() {} void CSystem::Slot125() {}
void CSystem::Slot126() {} void CSystem::Slot127() {} void CSystem::Slot128() {} void CSystem::Slot129() {}
void CSystem::Slot130() {} void CSystem::Slot131() {} void CSystem::Slot132() {} void CSystem::Slot133() {}
void CSystem::Slot134() {} void CSystem::Slot135() {} void CSystem::Slot136() {} void CSystem::Slot137() {}
void CSystem::Slot138() {} void CSystem::Slot139() {} void CSystem::Slot140() {} void CSystem::Slot141() {}
void CSystem::Slot142() {} void CSystem::Slot143() {} void CSystem::Slot144() {} void CSystem::Slot145() {}
void CSystem::Slot146() {} void CSystem::Slot147() {} void CSystem::Slot148() {}

GameOptions*         CSystem::GetGameOptions() { return g_pGameOptions; }
GameFixedFrame*      CSystem::GetGameFixedFrame() { return g_pGameFixedFrame; }
CharacterLODManager* CSystem::GetCharacterLODManager() { return g_pCharacterLODManager; }
LITELauncherManager* CSystem::GetLITELauncherManager() { return g_pLITELauncherManager; }
SdoaLogin*           CSystem::GetSdoaLogin() { return g_pSdoaLogin; }
CryFileMonitor*      CSystem::GetCryFileMonitor() { return g_pCryFileMonitor; }
