#pragma once

#ifndef _FMOD_EX_BRIDGE_H_
#define _FMOD_EX_BRIDGE_H_

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

// FMOD types
typedef struct FMOD_SYSTEM FMOD_SYSTEM;
typedef struct FMOD_SOUND FMOD_SOUND;
typedef struct FMOD_CHANNEL FMOD_CHANNEL;
typedef struct FMOD_CHANNELGROUP FMOD_CHANNELGROUP;
typedef struct FMOD_SOUNDGROUP FMOD_SOUNDGROUP;
typedef struct FMOD_DSP FMOD_DSP;
typedef int FMOD_RESULT;
#define FMOD_OK 0

typedef int FMOD_OUTPUTTYPE;
#define FMOD_OUTPUTTYPE_AUTODETECT 0
#define FMOD_OUTPUTTYPE_NOSOUND    1
#define FMOD_OUTPUTTYPE_WAVWRITER  2
#define FMOD_OUTPUTTYPE_DSOUND     4

typedef unsigned int FMOD_INITFLAGS;
#define FMOD_INIT_NORMAL 0x00000000

typedef unsigned int FMOD_MODE;
#define FMOD_DEFAULT          0x00000000
#define FMOD_LOOP_OFF         0x00000001
#define FMOD_LOOP_NORMAL      0x00000002
#define FMOD_HARDWARE         0x00000020
#define FMOD_SOFTWARE         0x00000040
#define FMOD_2D               0x00000008
#define FMOD_3D               0x00000010
#define FMOD_OPENMEMORY       0x00000800
#define FMOD_OPENRAW          0x00001000
#define FMOD_NONBLOCKING      0x00010000
#define FMOD_CREATESTREAM     0x00000080
#define FMOD_CREATESAMPLE     0x00000100
#define FMOD_3D_HEADRELATIVE  0x00040000
#define FMOD_3D_WORLDRELATIVE 0x00080000

typedef unsigned int FMOD_TIMEUNIT;
#define FMOD_TIMEUNIT_MS       0x00000001
#define FMOD_TIMEUNIT_PCM      0x00000002
#define FMOD_TIMEUNIT_PCMBYTES 0x00000004

typedef int FMOD_SPEAKERMODE;
#define FMOD_SPEAKERMODE_RAW     0
#define FMOD_SPEAKERMODE_MONO    1
#define FMOD_SPEAKERMODE_STEREO  2
#define FMOD_SPEAKERMODE_QUAD    3
#define FMOD_SPEAKERMODE_SURROUND 4
#define FMOD_SPEAKERMODE_5POINT1 5
#define FMOD_SPEAKERMODE_7POINT1 6
#define FMOD_SPEAKERMODE_PROLOGIC 7

#define FMOD_CHANNEL_FREE    -1
#define FMOD_CHANNEL_REUSE   -2

typedef struct FMOD_VECTOR
{
    float x;
    float y;
    float z;
} FMOD_VECTOR;

typedef struct FMOD_GUID
{
    unsigned int   Data1;
    unsigned short Data2;
    unsigned short Data3;
    unsigned char  Data4[8];
} FMOD_GUID;

typedef struct FMOD_REVERB_PROPERTIES
{
    int          Instance;
    int          Environment;
    float        EnvSize;
    float        EnvDiffusion;
    int          Room;
    int          RoomHF;
    int          RoomLF;
    float        DecayTime;
    float        DecayHFRatio;
    float        DecayLFRatio;
    int          Reflections;
    float        ReflectionsDelay;
    float        ReflectionsPan[3];
    int          Reverb;
    float        ReverbDelay;
    float        ReverbPan[3];
    float        EchoTime;
    float        EchoDepth;
    float        ModulationTime;
    float        ModulationDepth;
    float        AirAbsorptionHF;
    float        HFReference;
    float        LFReference;
    float        RoomRolloffFactor;
    float        Diffusion;
    float        Density;
    unsigned int Flags;
} FMOD_REVERB_PROPERTIES;

typedef struct FMOD_CREATESOUNDEXINFO
{
    int                            cbsize;
    unsigned int                   length;
    unsigned int                   fileoffset;
    int                            numchannels;
    int                            defaultfrequency;
    int                            format;
    unsigned int                   decodebuffersize;
    int                            initialsubsound;
    int                            numsubsounds;
    int                           *inclusionlist;
    int                            inclusionlistnum;
    void                          *pcmreadcallback;
    void                          *pcmsetposcallback;
    void                          *nonblockcallback;
    const char                    *dlsname;
    const char                    *encryptionkey;
    int                            maxpolyphony;
    void                          *userdata;
    int                            suggestedsoundtype;
    void                          *useropen;
    void                          *userclose;
    void                          *userread;
    void                          *userseek;
    void                          *userasyncread;
    void                          *userasynccancel;
    int                            speakermap;
    void                          *initialsoundgroup;
    unsigned int                   initialseekposition;
    int                            initialseekpostype;
    int                            ignoresetfilesystem;
} FMOD_CREATESOUNDEXINFO;

// FMOD Ex C API Imports from fmodex64.dll
FMOD_RESULT __stdcall FMOD_System_Create(FMOD_SYSTEM **system);
FMOD_RESULT __stdcall FMOD_System_Init(FMOD_SYSTEM *system, int maxchannels, FMOD_INITFLAGS flags, void *extradriverdata);
FMOD_RESULT __stdcall FMOD_System_Close(FMOD_SYSTEM *system);
FMOD_RESULT __stdcall FMOD_System_Release(FMOD_SYSTEM *system);
FMOD_RESULT __stdcall FMOD_System_Update(FMOD_SYSTEM *system);
FMOD_RESULT __stdcall FMOD_System_GetVersion(FMOD_SYSTEM *system, unsigned int *version);
FMOD_RESULT __stdcall FMOD_System_SetOutput(FMOD_SYSTEM *system, int output);
FMOD_RESULT __stdcall FMOD_System_GetOutput(FMOD_SYSTEM *system, int *output);
FMOD_RESULT __stdcall FMOD_System_GetNumDrivers(FMOD_SYSTEM *system, int *numdrivers);
FMOD_RESULT __stdcall FMOD_System_GetDriverInfo(FMOD_SYSTEM *system, int id, char *name, int namelen, FMOD_GUID *guid);
FMOD_RESULT __stdcall FMOD_System_GetDriverCaps(FMOD_SYSTEM *system, int id, unsigned int *caps, int *minfrequency, int *maxfrequency, FMOD_SPEAKERMODE *controlpanelspeakermode);
FMOD_RESULT __stdcall FMOD_System_SetDriver(FMOD_SYSTEM *system, int driver);
FMOD_RESULT __stdcall FMOD_System_GetDriver(FMOD_SYSTEM *system, int *driver);
FMOD_RESULT __stdcall FMOD_System_SetHardwareChannels(FMOD_SYSTEM *system, int numhardwarechannels);
FMOD_RESULT __stdcall FMOD_System_SetSoftwareChannels(FMOD_SYSTEM *system, int numsoftwarechannels);
FMOD_RESULT __stdcall FMOD_System_GetSoftwareChannels(FMOD_SYSTEM *system, int *numsoftwarechannels);
FMOD_RESULT __stdcall FMOD_System_SetSoftwareFormat(FMOD_SYSTEM *system, int samplerate, int format, int numoutputchannels, int maxinputchannels, int resamplemethod);
FMOD_RESULT __stdcall FMOD_System_SetDSPBufferSize(FMOD_SYSTEM *system, unsigned int bufferlength, int numbuffers);
FMOD_RESULT __stdcall FMOD_System_SetSpeakerMode(FMOD_SYSTEM *system, FMOD_SPEAKERMODE speakermode);
FMOD_RESULT __stdcall FMOD_System_CreateSound(FMOD_SYSTEM *system, const char *name_or_data, FMOD_MODE mode, FMOD_CREATESOUNDEXINFO *exinfo, FMOD_SOUND **sound);
FMOD_RESULT __stdcall FMOD_System_CreateStream(FMOD_SYSTEM *system, const char *name_or_data, FMOD_MODE mode, FMOD_CREATESOUNDEXINFO *exinfo, FMOD_SOUND **sound);
FMOD_RESULT __stdcall FMOD_System_PlaySound(FMOD_SYSTEM *system, int channelid, FMOD_SOUND *sound, int paused, FMOD_CHANNEL **channel);
FMOD_RESULT __stdcall FMOD_System_Set3DListenerAttributes(FMOD_SYSTEM *system, int listener, const FMOD_VECTOR *pos, const FMOD_VECTOR *vel, const FMOD_VECTOR *forward, const FMOD_VECTOR *up);
FMOD_RESULT __stdcall FMOD_System_SetReverbAmbientProperties(FMOD_SYSTEM *system, FMOD_REVERB_PROPERTIES *prop);
FMOD_RESULT __stdcall FMOD_System_GetChannelsPlaying(FMOD_SYSTEM *system, int *channels);
FMOD_RESULT __stdcall FMOD_System_GetCPUUsage(FMOD_SYSTEM *system, float *dsp, float *stream, float *geometry, float *update, float *total);
FMOD_RESULT __stdcall FMOD_System_SetFileSystem(FMOD_SYSTEM *system, void *useropen, void *userclose, void *userread, void *userseek, void *userasyncread, void *userasynccancel, int blockalign);

FMOD_RESULT __stdcall FMOD_Sound_Release(FMOD_SOUND *sound);
FMOD_RESULT __stdcall FMOD_Sound_GetLength(FMOD_SOUND *sound, unsigned int *length, FMOD_TIMEUNIT lengthtype);
FMOD_RESULT __stdcall FMOD_Sound_SetDefaults(FMOD_SOUND *sound, float defaultfrequency, float defaultvolume, float defaultpan, int defaultpriority);
FMOD_RESULT __stdcall FMOD_Sound_GetDefaults(FMOD_SOUND *sound, float *defaultfrequency, float *defaultvolume, float *defaultpan, int *defaultpriority);
FMOD_RESULT __stdcall FMOD_Sound_SetLoopPoints(FMOD_SOUND *sound, unsigned int loopstart, FMOD_TIMEUNIT loopstarttype, unsigned int loopend, FMOD_TIMEUNIT loopendtype);
FMOD_RESULT __stdcall FMOD_Sound_Set3DMinMaxDistance(FMOD_SOUND *sound, float min, float max);
FMOD_RESULT __stdcall FMOD_Sound_SetMode(FMOD_SOUND *sound, FMOD_MODE mode);

FMOD_RESULT __stdcall FMOD_Channel_Stop(FMOD_CHANNEL *channel);
FMOD_RESULT __stdcall FMOD_Channel_SetPaused(FMOD_CHANNEL *channel, int paused);
FMOD_RESULT __stdcall FMOD_Channel_GetPaused(FMOD_CHANNEL *channel, int *paused);
FMOD_RESULT __stdcall FMOD_Channel_SetVolume(FMOD_CHANNEL *channel, float volume);
FMOD_RESULT __stdcall FMOD_Channel_GetVolume(FMOD_CHANNEL *channel, float *volume);
FMOD_RESULT __stdcall FMOD_Channel_SetFrequency(FMOD_CHANNEL *channel, float frequency);
FMOD_RESULT __stdcall FMOD_Channel_SetPan(FMOD_CHANNEL *channel, float pan);
FMOD_RESULT __stdcall FMOD_Channel_Set3DAttributes(FMOD_CHANNEL *channel, const FMOD_VECTOR *pos, const FMOD_VECTOR *vel);
FMOD_RESULT __stdcall FMOD_Channel_SetPosition(FMOD_CHANNEL *channel, unsigned int position, FMOD_TIMEUNIT postype);
FMOD_RESULT __stdcall FMOD_Channel_GetPosition(FMOD_CHANNEL *channel, unsigned int *position, FMOD_TIMEUNIT postype);
FMOD_RESULT __stdcall FMOD_Channel_IsPlaying(FMOD_CHANNEL *channel, int *isplaying);
FMOD_RESULT __stdcall FMOD_Channel_SetPriority(FMOD_CHANNEL *channel, int priority);
FMOD_RESULT __stdcall FMOD_Channel_GetIndex(FMOD_CHANNEL *channel, int *index);

FMOD_RESULT __stdcall FMOD_Memory_Initialize(void *poolmem, int poollen, void *useralloc, void *userrealloc, void *userfree, unsigned int memtypeflags);
FMOD_RESULT __stdcall FMOD_Memory_GetStats(int *currentalloced, int *maxalloced, int blocking);

#ifdef __cplusplus
}
#endif

#endif // _FMOD_EX_BRIDGE_H_
