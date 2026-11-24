#include "stdafx.h"
#include "AionAnimationBinds.h"
#include "CryModelState.h"
#include <typeinfo>

CryCharFxJointTrail::CryCharFxJointTrail() : CryCharFxTrail(nullptr, CryCharFxTrailParams()) {}
CryCharFxJointTrail::~CryCharFxJointTrail() {}

CryCharFxTrailLong::CryCharFxTrailLong() : CryCharFxTrail(nullptr, CryCharFxTrailParams()) {}
CryCharFxTrailLong::~CryCharFxTrailLong() {}

CBindParticleBoneManager::CBindParticleBoneManager() {}
CBindParticleBoneManager::~CBindParticleBoneManager() {}
void CBindParticleBoneManager::Update(float fDelta) { (void)fDelta; }

CBindParticleManager::CBindParticleManager() {}
CBindParticleManager::~CBindParticleManager() {}
void CBindParticleManager::Update(float fDelta) { (void)fDelta; }

CCalcUnit::CCalcUnit() {}
CCalcUnit::~CCalcUnit() {}
void CCalcUnit::Process() {}

CCalcUnitEx::CCalcUnitEx() {}
CCalcUnitEx::~CCalcUnitEx() {}
void CCalcUnitEx::Process() {}

CControllerTCB_Float::CControllerTCB_Float() {}
CControllerTCB_Float::~CControllerTCB_Float() {}

CSAFChunkFileReader::CSAFChunkFileReader() {}
CSAFChunkFileReader::~CSAFChunkFileReader() {}

CryBoneContainer::CryBoneContainer() {}
CryBoneContainer::~CryBoneContainer() {}

CryModelAsyncLoader::CryModelAsyncLoader(CControllerManager* p) : CryModelLoader(p) {}
CryModelAsyncLoader::~CryModelAsyncLoader() {}

CryModelWholeAsyncLoader::CryModelWholeAsyncLoader(CControllerManager* p) : CryModelLoader(p) {}
CryModelWholeAsyncLoader::~CryModelWholeAsyncLoader() {}

VerletSolver::VerletSolver() {}
VerletSolver::~VerletSolver() {}

// Exported RTTI root anchor prevents dead-code elimination under /O2
__declspec(dllexport) const std::type_info* g_AnimRTTIAnchors[] = {
    &typeid(BSplineVec3d),
    &typeid(CBindParticleBoneManager),
    &typeid(CBindParticleManager),
    &typeid(CCalcUnit),
    &typeid(CCalcUnitEx),
    &typeid(CControllerTCB_Float),
    &typeid(CSAFChunkFileReader),
    &typeid(CryBoneContainer),
    &typeid(CryCharFxJointTrail),
    &typeid(CryCharFxTrailLong),
    &typeid(CryModelAsyncLoader),
    &typeid(CryModelWholeAsyncLoader),
    &typeid(IBindParticleBoneManager),
    &typeid(VerletSolver),
    &typeid(_reference_target_MT)
};
