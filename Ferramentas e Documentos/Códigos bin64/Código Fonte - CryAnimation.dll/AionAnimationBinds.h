#ifndef __aion_animation_binds_h__
#define __aion_animation_binds_h__

#pragma once

#include "CryCharFxTrail.h"
#include "Controller.h"
#include "ChunkFileReader.h"
#include "CryModelLoader.h"
#include "BSplineOpen.h"
#include <smartptr.h>

class CryCharFxJointTrail : public CryCharFxTrail {
public:
    CryCharFxJointTrail();
    virtual ~CryCharFxJointTrail();
};

class CryCharFxTrailLong : public CryCharFxTrail {
public:
    CryCharFxTrailLong();
    virtual ~CryCharFxTrailLong();
};

class IBindParticleBoneManager {
public:
    virtual ~IBindParticleBoneManager() {}
    virtual void Update(float fDelta) = 0;
};

class CBindParticleBoneManager : public IBindParticleBoneManager {
public:
    CBindParticleBoneManager();
    virtual ~CBindParticleBoneManager();
    virtual void Update(float fDelta) override;
};

class CBindParticleManager {
public:
    CBindParticleManager();
    virtual ~CBindParticleManager();
    virtual void Update(float fDelta);
};

class CCalcUnit {
public:
    CCalcUnit();
    virtual ~CCalcUnit();
    virtual void Process();
};

class CCalcUnitEx : public CCalcUnit {
public:
    CCalcUnitEx();
    virtual ~CCalcUnitEx();
    virtual void Process() override;
};

class CControllerTCB_Float : public IController {
public:
    CControllerTCB_Float();
    virtual ~CControllerTCB_Float();
    virtual unsigned GetID() const override { return 0; }
    virtual CryQuat GetOrientation(float t) override { (void)t; return CryQuat(1,0,0,0); }
    virtual Vec3 GetOrientation2(float t) override { (void)t; return Vec3(0,0,0); }
    virtual Vec3 GetPosition(float t) override { (void)t; return Vec3(0,0,0); }
    virtual Vec3 GetScale(float t) override { (void)t; return Vec3(1,1,1); }
    virtual void GetValue(float t, CryQuat& q, Vec3& p) override { (void)t; q = CryQuat(1,0,0,0); p = Vec3(0,0,0); }
    virtual void GetValue2(float t, PQLog& pq) override { (void)t; (void)pq; }
    virtual float GetTimeStart() override { return 0.0f; }
    virtual float GetTimeEnd() override { return 0.0f; }
};

class CSAFChunkFileReader : public CChunkFileReader {
public:
    CSAFChunkFileReader();
    virtual ~CSAFChunkFileReader();
};

class CryBoneContainer {
public:
    CryBoneContainer();
    virtual ~CryBoneContainer();
};

class CryModelAsyncLoader : public CryModelLoader {
public:
    CryModelAsyncLoader(class CControllerManager* p);
    virtual ~CryModelAsyncLoader();
};

class CryModelWholeAsyncLoader : public CryModelLoader {
public:
    CryModelWholeAsyncLoader(class CControllerManager* p);
    virtual ~CryModelWholeAsyncLoader();
};

class VerletSolver {
public:
    VerletSolver();
    virtual ~VerletSolver();
};

#endif // __aion_animation_binds_h__
