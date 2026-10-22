#include "CryCommon/crysound.h"
#include "FmodExBridge.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

static FMOD_SYSTEM* g_pFMODSystem = nullptr;
static FMOD_CHANNEL* g_pChannels[256] = { nullptr };
static CS_OPENCALLBACK g_userOpen = nullptr;
static CS_CLOSECALLBACK g_userClose = nullptr;
static CS_READCALLBACK g_userRead = nullptr;
static CS_SEEKCALLBACK g_userSeek = nullptr;
static CS_TELLCALLBACK g_userTell = nullptr;

static inline FMOD_CHANNEL* GetChannelFromIndex(int channel)
{
    if (channel >= 0 && channel < 256)
        return g_pChannels[channel];
    return nullptr;
}

static inline void RegisterChannel(FMOD_CHANNEL* pChannel)
{
    if (!pChannel) return;
    int idx = -1;
    if (FMOD_Channel_GetIndex(pChannel, &idx) == FMOD_OK && idx >= 0 && idx < 256)
    {
        g_pChannels[idx] = pChannel;
    }
}

// Convert CRYSOUND mode flags to FMOD Ex mode flags
static FMOD_MODE ConvertCSModeToFMOD(unsigned int cs_mode)
{
    FMOD_MODE fmod_mode = FMOD_DEFAULT;

    if (cs_mode & CS_LOOP_NORMAL)
        fmod_mode |= FMOD_LOOP_NORMAL;
    else if (cs_mode & CS_LOOP_OFF)
        fmod_mode |= FMOD_LOOP_OFF;

    if (cs_mode & CS_2D)
        fmod_mode |= FMOD_2D;
    if (cs_mode & CS_HW3D)
        fmod_mode |= FMOD_3D;

    if (cs_mode & CS_LOADMEMORY)
        fmod_mode |= FMOD_OPENMEMORY;
    if (cs_mode & CS_LOADRAW)
        fmod_mode |= FMOD_OPENRAW;
    if (cs_mode & CS_NONBLOCKING)
        fmod_mode |= FMOD_NONBLOCKING;

    return fmod_mode;
}

extern "C" {

DLL_API float F_API CS_GetVersion()
{
    return CS_VERSION;
}

DLL_API signed char F_API CS_Init(int mixrate, int maxsoftwarechannels, unsigned int flags)
{
    if (!g_pFMODSystem)
    {
        if (FMOD_System_Create(&g_pFMODSystem) != FMOD_OK)
            return 0;
    }

    if (mixrate <= 0) mixrate = 44100;
    if (maxsoftwarechannels <= 0) maxsoftwarechannels = 64;

    FMOD_System_SetSoftwareChannels(g_pFMODSystem, maxsoftwarechannels);
    FMOD_System_SetSoftwareFormat(g_pFMODSystem, mixrate, 0, 2, 0, 0);

    FMOD_RESULT res = FMOD_System_Init(g_pFMODSystem, maxsoftwarechannels, FMOD_INIT_NORMAL, nullptr);
    if (res != FMOD_OK)
    {
        FMOD_System_SetOutput(g_pFMODSystem, FMOD_OUTPUTTYPE_NOSOUND);
        res = FMOD_System_Init(g_pFMODSystem, maxsoftwarechannels, FMOD_INIT_NORMAL, nullptr);
    }
    return (res == FMOD_OK) ? 1 : 0;
}

DLL_API void F_API CS_Close()
{
    if (g_pFMODSystem)
    {
        FMOD_System_Close(g_pFMODSystem);
        FMOD_System_Release(g_pFMODSystem);
        g_pFMODSystem = nullptr;
    }
    memset(g_pChannels, 0, sizeof(g_pChannels));
}

DLL_API void F_API CS_Update()
{
    if (g_pFMODSystem)
        FMOD_System_Update(g_pFMODSystem);
}

DLL_API signed char F_API CS_SetBufferSize(int len_ms)
{
    if (g_pFMODSystem && len_ms > 0)
    {
        FMOD_System_SetDSPBufferSize(g_pFMODSystem, (unsigned int)len_ms, 4);
    }
    return 1;
}

DLL_API signed char F_API CS_SetHWND(void *hwnd)
{
    return 1;
}

DLL_API signed char F_API CS_SetMaxHardwareChannels(int max)
{
    if (g_pFMODSystem && max > 0)
        FMOD_System_SetHardwareChannels(g_pFMODSystem, max);
    return 1;
}

DLL_API signed char F_API CS_SetMinHardwareChannels(int min)
{
    return 1;
}

DLL_API signed char F_API CS_SetMemorySystem(void *pool, int poollen, CS_ALLOCCALLBACK useralloc, CS_REALLOCCALLBACK userrealloc, CS_FREECALLBACK userfree)
{
    FMOD_Memory_Initialize(pool, poollen, (void*)useralloc, (void*)userrealloc, (void*)userfree, 0);
    return 1;
}

DLL_API void F_API CS_File_SetCallbacks(CS_OPENCALLBACK useropen, CS_CLOSECALLBACK userclose, CS_READCALLBACK userread, CS_SEEKCALLBACK userseek, CS_TELLCALLBACK usertell)
{
    g_userOpen = useropen;
    g_userClose = userclose;
    g_userRead = userread;
    g_userSeek = userseek;
    g_userTell = usertell;
}

DLL_API int F_API CS_GetNumDrivers()
{
    int num = 0;
    if (g_pFMODSystem)
        FMOD_System_GetNumDrivers(g_pFMODSystem, &num);
    return num;
}

DLL_API signed char * F_API CS_GetDriverName(int id)
{
    static char s_driverName[256];
    s_driverName[0] = 0;
    if (g_pFMODSystem)
    {
        FMOD_GUID guid;
        FMOD_System_GetDriverInfo(g_pFMODSystem, id, s_driverName, sizeof(s_driverName), &guid);
    }
    return (signed char*)s_driverName;
}

DLL_API signed char F_API CS_GetDriverCaps(int id, unsigned int *caps)
{
    if (g_pFMODSystem && caps)
    {
        FMOD_SPEAKERMODE sm;
        int minf = 0, maxf = 0;
        FMOD_System_GetDriverCaps(g_pFMODSystem, id, caps, &minf, &maxf, &sm);
        return 1;
    }
    return 0;
}

DLL_API int F_API CS_GetDriver()
{
    int drv = 0;
    if (g_pFMODSystem)
        FMOD_System_GetDriver(g_pFMODSystem, &drv);
    return drv;
}

DLL_API int F_API CS_GetMaxChannels()
{
    int maxChannels = 64;
    if (g_pFMODSystem)
        FMOD_System_GetSoftwareChannels(g_pFMODSystem, &maxChannels);
    return maxChannels;
}

DLL_API int F_API CS_GetChannelsPlaying()
{
    int count = 0;
    if (g_pFMODSystem)
        FMOD_System_GetChannelsPlaying(g_pFMODSystem, &count);
    return count;
}

DLL_API float F_API CS_GetCPUUsage()
{
    float dsp = 0.0f, stream = 0.0f, geom = 0.0f, update = 0.0f, total = 0.0f;
    if (g_pFMODSystem)
        FMOD_System_GetCPUUsage(g_pFMODSystem, &dsp, &stream, &geom, &update, &total);
    return total;
}

DLL_API void F_API CS_GetMemoryStats(unsigned int *currentalloced, unsigned int *maxalloced)
{
    int curr = 0, maxa = 0;
    FMOD_Memory_GetStats(&curr, &maxa, 0);
    if (currentalloced) *currentalloced = (unsigned int)curr;
    if (maxalloced) *maxalloced = (unsigned int)maxa;
}

DLL_API int F_API CS_GetMixer()
{
    return 0;
}

DLL_API int F_API CS_GetOutputRate()
{
    int rate = 44100;
    if (g_pFMODSystem)
    {
        int channels = 0;
        FMOD_System_SetSoftwareFormat(g_pFMODSystem, rate, 0, 2, 0, 0);
    }
    return rate;
}

DLL_API void F_API CS_SetSpeakerMode(unsigned int speakermode)
{
    if (g_pFMODSystem)
        FMOD_System_SetSpeakerMode(g_pFMODSystem, (FMOD_SPEAKERMODE)speakermode);
}

DLL_API void F_API CS_SetPanSeperation(float pansep)
{
}

DLL_API void F_API CS_SetSFXMasterVolume(int volume)
{
}

DLL_API signed char F_API CS_Reverb_SetProperties(CS_REVERB_PROPERTIES *prop)
{
    if (g_pFMODSystem && prop)
    {
        FMOD_REVERB_PROPERTIES fprop;
        memset(&fprop, 0, sizeof(fprop));
        fprop.Environment = prop->Environment;
        fprop.EnvSize = prop->EnvSize;
        fprop.EnvDiffusion = prop->EnvDiffusion;
        fprop.Room = prop->Room;
        fprop.RoomHF = prop->RoomHF;
        fprop.DecayTime = prop->DecayTime;
        fprop.DecayHFRatio = prop->DecayHFRatio;
        fprop.Reflections = prop->Reflections;
        fprop.ReflectionsDelay = prop->ReflectionsDelay;
        fprop.Reverb = prop->Reverb;
        fprop.ReverbDelay = prop->ReverbDelay;
        fprop.RoomRolloffFactor = prop->RoomRolloffFactor;
        fprop.AirAbsorptionHF = prop->AirAbsorptionHF;
        fprop.Flags = prop->Flags;
        FMOD_System_SetReverbAmbientProperties(g_pFMODSystem, &fprop);
        return 1;
    }
    return 0;
}

DLL_API CS_SAMPLE * F_API CS_Sample_Load(int index, const char *name_or_data, unsigned int mode, int memlength)
{
    if (!g_pFMODSystem || !name_or_data) return nullptr;

    FMOD_MODE fmod_mode = ConvertCSModeToFMOD(mode);
    FMOD_CREATESOUNDEXINFO exinfo;
    memset(&exinfo, 0, sizeof(exinfo));
    exinfo.cbsize = sizeof(exinfo);
    if (mode & CS_LOADMEMORY)
        exinfo.length = memlength;

    FMOD_SOUND* pSound = nullptr;
    if (FMOD_System_CreateSound(g_pFMODSystem, name_or_data, fmod_mode, &exinfo, &pSound) == FMOD_OK)
    {
        return (CS_SAMPLE*)pSound;
    }
    return nullptr;
}

DLL_API void F_API CS_Sample_Free(CS_SAMPLE *sptr)
{
    if (sptr)
        FMOD_Sound_Release((FMOD_SOUND*)sptr);
}

DLL_API unsigned int F_API CS_Sample_GetLength(CS_SAMPLE *sptr)
{
    if (!sptr) return 0;
    unsigned int len = 0;
    FMOD_Sound_GetLength((FMOD_SOUND*)sptr, &len, FMOD_TIMEUNIT_PCM);
    return len;
}

DLL_API signed char F_API CS_Sample_SetLoopPoints(CS_SAMPLE *sptr, int loopstart, int loopend)
{
    if (!sptr) return 0;
    return (FMOD_Sound_SetLoopPoints((FMOD_SOUND*)sptr, loopstart, FMOD_TIMEUNIT_PCM, loopend, FMOD_TIMEUNIT_PCM) == FMOD_OK) ? 1 : 0;
}

DLL_API signed char F_API CS_Sample_SetMinMaxDistance(CS_SAMPLE *sptr, float min, float max)
{
    if (!sptr) return 0;
    return (FMOD_Sound_Set3DMinMaxDistance((FMOD_SOUND*)sptr, min, max) == FMOD_OK) ? 1 : 0;
}

DLL_API signed char F_API CS_Sample_SetMode(CS_SAMPLE *sptr, unsigned int mode)
{
    if (!sptr) return 0;
    return (FMOD_Sound_SetMode((FMOD_SOUND*)sptr, ConvertCSModeToFMOD(mode)) == FMOD_OK) ? 1 : 0;
}

DLL_API signed char F_API CS_Sample_SetDefaults(CS_SAMPLE *sptr, int deffreq, int defvol, int defpan, int defpri)
{
    if (!sptr) return 0;
    float vol = (defvol >= 0) ? (defvol / 255.0f) : -1.0f;
    float pan = (defpan >= 0) ? ((defpan - 128) / 128.0f) : -1.0f;
    float freq = (deffreq > 0) ? (float)deffreq : -1.0f;
    return (FMOD_Sound_SetDefaults((FMOD_SOUND*)sptr, freq, vol, pan, defpri) == FMOD_OK) ? 1 : 0;
}

DLL_API signed char F_API CS_Sample_GetDefaults(CS_SAMPLE *sptr, int *deffreq, int *defvol, int *defpan, int *defpri)
{
    if (!sptr) return 0;
    float freq = 0.0f, vol = 0.0f, pan = 0.0f;
    int pri = 0;
    if (FMOD_Sound_GetDefaults((FMOD_SOUND*)sptr, &freq, &vol, &pan, &pri) == FMOD_OK)
    {
        if (deffreq) *deffreq = (int)freq;
        if (defvol) *defvol = (int)(vol * 255.0f);
        if (defpan) *defpan = (int)(pan * 128.0f + 128.0f);
        if (defpri) *defpri = pri;
        return 1;
    }
    return 0;
}

DLL_API int F_API CS_PlaySoundEx(int channel, CS_SAMPLE *sptr, CS_DSPUNIT *dsp, signed char startpaused)
{
    if (!g_pFMODSystem || !sptr) return -1;
    FMOD_CHANNEL* pChannel = nullptr;
    if (FMOD_System_PlaySound(g_pFMODSystem, FMOD_CHANNEL_FREE, (FMOD_SOUND*)sptr, startpaused != 0, &pChannel) == FMOD_OK && pChannel)
    {
        RegisterChannel(pChannel);
        int idx = -1;
        FMOD_Channel_GetIndex(pChannel, &idx);
        return idx;
    }
    return -1;
}

DLL_API signed char F_API CS_StopSound(int channel)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
        return (FMOD_Channel_Stop(pCh) == FMOD_OK) ? 1 : 0;
    return 0;
}

DLL_API signed char F_API CS_SetVolume(int channel, int vol)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
    {
        float v = (float)vol / 255.0f;
        return (FMOD_Channel_SetVolume(pCh, v) == FMOD_OK) ? 1 : 0;
    }
    return 0;
}

DLL_API signed char F_API CS_SetPan(int channel, int pan)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
    {
        float p = ((float)pan - 128.0f) / 128.0f;
        return (FMOD_Channel_SetPan(pCh, p) == FMOD_OK) ? 1 : 0;
    }
    return 0;
}

DLL_API signed char F_API CS_SetFrequency(int channel, int freq)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
        return (FMOD_Channel_SetFrequency(pCh, (float)freq) == FMOD_OK) ? 1 : 0;
    return 0;
}

DLL_API signed char F_API CS_SetPaused(int channel, signed char paused)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
        return (FMOD_Channel_SetPaused(pCh, paused != 0) == FMOD_OK) ? 1 : 0;
    return 0;
}

DLL_API signed char F_API CS_IsPlaying(int channel)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
    {
        int playing = 0;
        if (FMOD_Channel_IsPlaying(pCh, &playing) == FMOD_OK)
            return (signed char)playing;
    }
    return 0;
}

DLL_API signed char F_API CS_SetPriority(int channel, int priority)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
        return (FMOD_Channel_SetPriority(pCh, priority) == FMOD_OK) ? 1 : 0;
    return 0;
}

DLL_API signed char F_API CS_3D_SetAttributes(int channel, float *pos, float *vel)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh && pos)
    {
        FMOD_VECTOR vpos = { pos[0], pos[1], pos[2] };
        FMOD_VECTOR vvel = { vel ? vel[0] : 0.0f, vel ? vel[1] : 0.0f, vel ? vel[2] : 0.0f };
        return (FMOD_Channel_Set3DAttributes(pCh, &vpos, &vvel) == FMOD_OK) ? 1 : 0;
    }
    return 0;
}

DLL_API void F_API CS_3D_Listener_SetAttributes(float *pos, float *vel, float fx, float fy, float fz, float tx, float ty, float tz)
{
    if (g_pFMODSystem && pos)
    {
        FMOD_VECTOR vpos = { pos[0], pos[1], pos[2] };
        FMOD_VECTOR vvel = { vel ? vel[0] : 0.0f, vel ? vel[1] : 0.0f, vel ? vel[2] : 0.0f };
        FMOD_VECTOR forward = { fx, fy, fz };
        FMOD_VECTOR up = { tx, ty, tz };
        FMOD_System_Set3DListenerAttributes(g_pFMODSystem, 0, &vpos, &vvel, &forward, &up);
    }
}

DLL_API unsigned int F_API CS_GetCurrentPosition(int channel)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
    {
        unsigned int pos = 0;
        FMOD_Channel_GetPosition(pCh, &pos, FMOD_TIMEUNIT_PCM);
        return pos;
    }
    return 0;
}

DLL_API signed char F_API CS_SetCurrentPosition(int channel, unsigned int offset)
{
    FMOD_CHANNEL* pCh = GetChannelFromIndex(channel);
    if (pCh)
        return (FMOD_Channel_SetPosition(pCh, offset, FMOD_TIMEUNIT_PCM) == FMOD_OK) ? 1 : 0;
    return 0;
}

DLL_API CS_STREAM * F_API CS_Stream_OpenFile(const char *filename, unsigned int mode, int memlength)
{
    if (!g_pFMODSystem || !filename) return nullptr;

    FMOD_MODE fmod_mode = ConvertCSModeToFMOD(mode) | FMOD_CREATESTREAM;
    FMOD_CREATESOUNDEXINFO exinfo;
    memset(&exinfo, 0, sizeof(exinfo));
    exinfo.cbsize = sizeof(exinfo);
    if (mode & CS_LOADMEMORY)
        exinfo.length = memlength;

    FMOD_SOUND* pSound = nullptr;
    if (FMOD_System_CreateStream(g_pFMODSystem, filename, fmod_mode, &exinfo, &pSound) == FMOD_OK)
    {
        return (CS_STREAM*)pSound;
    }
    return nullptr;
}

DLL_API CS_STREAM * F_API CS_Stream_Open(const char *name_or_data, unsigned int mode, int offset, int length)
{
    return CS_Stream_OpenFile(name_or_data, mode, length);
}

DLL_API CS_STREAM * F_API CS_Stream_Create(CS_STREAMCALLBACK callback, int length, unsigned int mode, int samplerate, int userdata)
{
    return nullptr;
}

DLL_API signed char F_API CS_Stream_Close(CS_STREAM *stream)
{
    if (stream)
        return (FMOD_Sound_Release((FMOD_SOUND*)stream) == FMOD_OK) ? 1 : 0;
    return 0;
}

DLL_API int F_API CS_Stream_Play(int channel, CS_STREAM *stream)
{
    return CS_Stream_PlayEx(channel, stream, nullptr, 0);
}

DLL_API int F_API CS_Stream_PlayEx(int channel, CS_STREAM *stream, CS_DSPUNIT *dsp, signed char startpaused)
{
    if (!g_pFMODSystem || !stream) return -1;
    FMOD_CHANNEL* pChannel = nullptr;
    if (FMOD_System_PlaySound(g_pFMODSystem, FMOD_CHANNEL_FREE, (FMOD_SOUND*)stream, startpaused != 0, &pChannel) == FMOD_OK && pChannel)
    {
        RegisterChannel(pChannel);
        int idx = -1;
        FMOD_Channel_GetIndex(pChannel, &idx);
        return idx;
    }
    return -1;
}

DLL_API signed char F_API CS_Stream_Stop(CS_STREAM *stream)
{
    return 1;
}

DLL_API int F_API CS_Stream_GetLength(CS_STREAM *stream)
{
    if (!stream) return 0;
    unsigned int len = 0;
    FMOD_Sound_GetLength((FMOD_SOUND*)stream, &len, FMOD_TIMEUNIT_PCM);
    return (int)len;
}

DLL_API int F_API CS_Stream_GetLengthMs(CS_STREAM *stream)
{
    if (!stream) return 0;
    unsigned int len = 0;
    FMOD_Sound_GetLength((FMOD_SOUND*)stream, &len, FMOD_TIMEUNIT_MS);
    return (int)len;
}

DLL_API unsigned int F_API CS_Stream_GetPosition(CS_STREAM *stream)
{
    return 0;
}

DLL_API signed char F_API CS_Stream_SetPosition(CS_STREAM *stream, unsigned int position)
{
    return 1;
}

DLL_API int F_API CS_Stream_GetTime(CS_STREAM *stream)
{
    return 0;
}

DLL_API signed char F_API CS_Stream_SetTime(CS_STREAM *stream, int ms)
{
    return 1;
}

DLL_API void F_API CS_DSP_Free(CS_DSPUNIT *unit)
{
}

DLL_API signed char F_API CS_DSP_MixBuffers(void *destbuffer, void *srcbuffer, int len, int freq, int vol, int pan, unsigned int mode)
{
    return 1;
}

DLL_API int F_API CS_FX_Enable(int channel, unsigned int fx)
{
    return 1;
}

DLL_API signed char F_API CS_FX_SetParamEQ(int fxid, float Center, float Bandwidth, float Gain)
{
    return 1;
}

} // extern "C"
