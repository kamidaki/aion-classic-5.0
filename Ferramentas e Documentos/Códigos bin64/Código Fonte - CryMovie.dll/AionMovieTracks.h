#ifndef __aion_movietracks_h__
#define __aion_movietracks_h__

#pragma once

#include "IMovieSystem.h"
#include "AnimTrack.h"

namespace NFX {
    class CFxContainerGameObject {
    public:
        CFxContainerGameObject();
        virtual ~CFxContainerGameObject();
        virtual void Update(float fDelta);
    };
}

class CAnimSequenceStringTable {
public:
    CAnimSequenceStringTable();
    virtual ~CAnimSequenceStringTable();
    virtual const char* GetString(int nIndex);
};

// Custom Aion Classic 5.0 Cinematic Tracks
struct IAionEventKey : public IKey {
    IAionEventKey() {}
};

class CAionTrackBase : public TAnimTrack<IAionEventKey> {
public:
    virtual void SerializeKey(IAionEventKey &key, XmlNodeRef &keyNode, bool bLoading) override {
        (void)key;
        (void)keyNode;
        (void)bLoading;
    }
};

class CCarrierPathInfoTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)100; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CDofTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)101; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CEffectTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)102; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CFxCameraEffectTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)103; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CFxScreenTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)104; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CFxTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)105; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CGameNarrationTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)106; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CGameSpeechTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)107; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CGameViewTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)108; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CHeadRotateTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)109; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CImageTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)110; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CLightTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)111; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CScreenFxTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)112; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CScreenTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)113; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CTodControlTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)114; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

class CVisibleTrack : public CAionTrackBase {
public:
    virtual EAnimTrackType GetType() override { return (EAnimTrackType)115; }
    virtual EAnimValue GetValueType() override { return AVALUE_EVENT; }
    virtual void GetKeyInfo(int key, const char* &desc, float &duration) override;
};

#endif // __aion_movietracks_h__
