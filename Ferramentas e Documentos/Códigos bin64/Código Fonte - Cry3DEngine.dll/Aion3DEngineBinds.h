#ifndef __aion_3dengine_binds_h__
#define __aion_3dengine_binds_h__

#pragma once

#include <vector>
#include <string>
#include <typeinfo>

// Forward declarations
struct ISystem;
class C3DEngine;

// Decal and Shared
class CDecalRenderMatInfo {
public:
    CDecalRenderMatInfo();
    virtual ~CDecalRenderMatInfo();
};

class CDecalSharedObject {
public:
    CDecalSharedObject();
    virtual ~CDecalSharedObject();
};

// Cgf Info and CalcUnit
class CCgfInfoManager {
public:
    CCgfInfoManager();
    virtual ~CCgfInfoManager();
};

class CCalcUnit {
public:
    CCalcUnit();
    virtual ~CCalcUnit();
};

// Entity Context Class Manager
class IEntityContextClassManager {
public:
    virtual ~IEntityContextClassManager() {}
};

class CEntityContextClassManager : public IEntityContextClassManager {
public:
    CEntityContextClassManager();
    virtual ~CEntityContextClassManager();
};

// Fixed Frame Shader
class IFixedFrameShaderMan {
public:
    virtual ~IFixedFrameShaderMan() {}
};

class CFixedFrameShaderMan : public IFixedFrameShaderMan {
public:
    CFixedFrameShaderMan();
    virtual ~CFixedFrameShaderMan();
};

// Effect Sequencer
class CEffectSeqEffect {
public:
    CEffectSeqEffect();
    virtual ~CEffectSeqEffect();
};

class CEffectSeqSequencer {
public:
    CEffectSeqSequencer();
    virtual ~CEffectSeqSequencer();
};

class CEffectSeqManager {
public:
    CEffectSeqManager();
    virtual ~CEffectSeqManager();
};

// FX System Classes
class CFxShader {
public:
    CFxShader();
    virtual ~CFxShader();
};

class CFxcEffectLoader {
public:
    CFxcEffectLoader();
    virtual ~CFxcEffectLoader();
};

class CFxcOverrideEffect {
public:
    CFxcOverrideEffect();
    virtual ~CFxcOverrideEffect();
};

class CGameFx {
public:
    CGameFx();
    virtual ~CGameFx();
};

class CFxMotionTrail {
public:
    CFxMotionTrail();
    virtual ~CFxMotionTrail();
};

class CFxFullscreenEmitter {
public:
    CFxFullscreenEmitter();
    virtual ~CFxFullscreenEmitter();
};

class CFxFullscreenEffect {
public:
    CFxFullscreenEffect();
    virtual ~CFxFullscreenEffect();
};

class CFxArtifactEffect {
public:
    CFxArtifactEffect();
    virtual ~CFxArtifactEffect();
};

class CFxArtifactEmitter {
public:
    CFxArtifactEmitter();
    virtual ~CFxArtifactEmitter();
};

class CFxArtifactSystemManager {
public:
    CFxArtifactSystemManager();
    virtual ~CFxArtifactSystemManager();
};

class CFxContainerEffect {
public:
    CFxContainerEffect();
    virtual ~CFxContainerEffect();
};

class CFxContainerEmitter {
public:
    CFxContainerEmitter();
    virtual ~CFxContainerEmitter();
};

class CFxContainerGameObject {
public:
    CFxContainerGameObject();
    virtual ~CFxContainerGameObject();
};

class CSkyboxEffect {
public:
    CSkyboxEffect();
    virtual ~CSkyboxEffect();
};

class CSkydomeEffect {
public:
    CSkydomeEffect();
    virtual ~CSkydomeEffect();
};

// Height Color Cluster System
class IHeightColor_Cluster_BrushType {
public:
    virtual ~IHeightColor_Cluster_BrushType() {}
};

class IHeightColor_Cluster_TerrainType {
public:
    virtual ~IHeightColor_Cluster_TerrainType() {}
};

class CHeightColor_ClusterType {
public:
    CHeightColor_ClusterType();
    virtual ~CHeightColor_ClusterType();
};

class CHeightColor_Cluster_BrushP2C4D2 : public IHeightColor_Cluster_BrushType {
public:
    CHeightColor_Cluster_BrushP2C4D2();
    virtual ~CHeightColor_Cluster_BrushP2C4D2();
};

class CHeightColor_Cluster_BrushP2C4D8 : public IHeightColor_Cluster_BrushType {
public:
    CHeightColor_Cluster_BrushP2C4D8();
    virtual ~CHeightColor_Cluster_BrushP2C4D8();
};

class CHeightColor_Cluster_BrushP2C8D14 : public IHeightColor_Cluster_BrushType {
public:
    CHeightColor_Cluster_BrushP2C8D14();
    virtual ~CHeightColor_Cluster_BrushP2C8D14();
};

class CHeightColor_Cluster_BrushP2C8D6 : public IHeightColor_Cluster_BrushType {
public:
    CHeightColor_Cluster_BrushP2C8D6();
    virtual ~CHeightColor_Cluster_BrushP2C8D6();
};

class CHeightColor_Cluster_BrushP2D14C16 : public IHeightColor_Cluster_BrushType {
public:
    CHeightColor_Cluster_BrushP2D14C16();
    virtual ~CHeightColor_Cluster_BrushP2D14C16();
};

class CHeightColor_Cluster_BrushP2D6C16 : public IHeightColor_Cluster_BrushType {
public:
    CHeightColor_Cluster_BrushP2D6C16();
    virtual ~CHeightColor_Cluster_BrushP2D6C16();
};

class CHeightColor_Cluster_Terrain4 : public IHeightColor_Cluster_TerrainType {
public:
    CHeightColor_Cluster_Terrain4();
    virtual ~CHeightColor_Cluster_Terrain4();
};

class CHeightColor_Cluster_Terrain8 : public IHeightColor_Cluster_TerrainType {
public:
    CHeightColor_Cluster_Terrain8();
    virtual ~CHeightColor_Cluster_Terrain8();
};

class CHeightColorClusterGen {
public:
    CHeightColorClusterGen();
    virtual ~CHeightColorClusterGen();
};

class CHeightColorClusterLoaderMT {
public:
    CHeightColorClusterLoaderMT();
    virtual ~CHeightColorClusterLoaderMT();
};

class CHeightColorGen {
public:
    CHeightColorGen();
    virtual ~CHeightColorGen();
};

class CHeightColorTypeManager {
public:
    CHeightColorTypeManager();
    virtual ~CHeightColorTypeManager();
};

// Serialization & Loaders
class CLMVCSerializationManager {
public:
    CLMVCSerializationManager();
    virtual ~CLMVCSerializationManager();
};

class CLightMapUVLoaderMT {
public:
    CLightMapUVLoaderMT();
    virtual ~CLightMapUVLoaderMT();
};

class CMaterialFXLoader {
public:
    CMaterialFXLoader();
    virtual ~CMaterialFXLoader();
};

class CPartEffectLoader {
public:
    CPartEffectLoader();
    virtual ~CPartEffectLoader();
};

class CPathFileReader {
public:
    CPathFileReader();
    virtual ~CPathFileReader();
};

class CSimpleMemBlock {
public:
    CSimpleMemBlock();
    virtual ~CSimpleMemBlock();
};

class CStatObjInstance {
public:
    CStatObjInstance();
    virtual ~CStatObjInstance();
};

class CTerrainSecTexLow {
public:
    CTerrainSecTexLow();
    virtual ~CTerrainSecTexLow();
};

class CpathFileMapping {
public:
    CpathFileMapping();
    virtual ~CpathFileMapping();
};

class ICryStreamReader {
public:
    virtual ~ICryStreamReader() {}
};

class CryMemStreamReader : public ICryStreamReader {
public:
    CryMemStreamReader();
    virtual ~CryMemStreamReader();
};

// Sound System
class CSoundManager {
public:
    CSoundManager();
    virtual ~CSoundManager();
};

class CSound_MusicDB {
public:
    CSound_MusicDB();
    virtual ~CSound_MusicDB();
};

// Shape Zones
class ShapeZones {
public:
    ShapeZones();
    virtual ~ShapeZones();
};

class ShapeBoidPath : public ShapeZones {
public:
    ShapeBoidPath();
    virtual ~ShapeBoidPath();
};

class ShapeZones_Artifact : public ShapeZones {
public:
    ShapeZones_Artifact();
    virtual ~ShapeZones_Artifact();
};

class ShapeZones_CheckArea : public ShapeZones {
public:
    ShapeZones_CheckArea();
    virtual ~ShapeZones_CheckArea();
};

class ShapeZones_Music : public ShapeZones {
public:
    ShapeZones_Music();
    virtual ~ShapeZones_Music();
};

// OcTree classes
class COcTreeNode {
public:
    COcTreeNode();
    virtual ~COcTreeNode();
};

class COcTreeNodeVisArea : public COcTreeNode {
public:
    COcTreeNodeVisArea();
    virtual ~COcTreeNodeVisArea();
};

class COcTreeObjectVisArea {
public:
    COcTreeObjectVisArea();
    virtual ~COcTreeObjectVisArea();
};

#endif // __aion_3dengine_binds_h__
