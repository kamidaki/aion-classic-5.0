#pragma once
#include <string>
#include <vector>
#include <cstdint>

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

// Versão de API gráfica
enum class RenderAPIType {
    Direct3D9 = 0,
    Direct3D11,
    OpenGL
};

// Formato de textura canônica (.dds)
enum class TextureFormat {
    Unknown = 0,
    DXT1,
    DXT3,
    DXT5,
    BC7,
    RGBA8
};

// Descritor de textura carregada (.dds)
struct TextureResource {
    std::string path;
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t mipLevels = 1;
    TextureFormat format = TextureFormat::DXT5;
    bool hasAlpha = false;
};

// Material com canais de textura canônicos do CryEngine
struct CryMaterial {
    std::string name;
    std::string diffuseMap;   // Textura Difusa (.dds)
    std::string normalMap;    // Normal Map / Relevo (_ddn.dds)
    std::string specularMap;  // Specular / Brilho (_spec.dds)
    float glossiness = 10.0f;
    float specularLevel = 1.0f;
    bool isTransparent = false;
};

// Chunk de malha geométrica CryEngine (.cgf / .cga)
enum class CryChunkType : uint32_t {
    ChunkType_Mesh = 0x1000,
    ChunkType_Helper = 0x1001,
    ChunkType_BoneNameList = 0x1002,
    ChunkType_MeshMorphTarget = 0x1003,
    ChunkType_Material = 0x1004
};

// Vértice 3D de malha geométrica
struct CryVertex {
    float x, y, z;
    float nx, ny, nz;
    float u, v;
};

// Malha geométrica carregada (.cgf ou .cga)
struct CryMeshGeometry {
    std::string fileName;
    bool isAnimated = false; // true = .cga, false = .cgf
    std::vector<CryVertex> vertices;
    std::vector<uint32_t> indices;
    std::vector<CryChunkType> chunks;
    uint32_t numBones = 0;
};

// Parâmetros de Pós-Processamento e Shaders
struct PostProcessSettings {
    bool enableBloom = true;
    float bloomThreshold = 0.8f;
    float bloomIntensity = 1.2f;

    bool enableHDR = true;
    float hdrExposure = 1.0f;

    bool enableMotionBlur = true;
    float motionBlurAmount = 0.4f;

    bool enableWaterRefraction = true;
    float waterWaveSpeed = 1.0f;
    float waterReflectionIntensity = 0.75f;
};

// Interface do Renderizador Gráfico da CryEngine (CryRender)
CRY_INTERFACE IRenderer {
    virtual ~IRenderer() = default;

    // Inicialização e gerenciamento de contexto gráfico
    virtual bool InitDevice(RenderAPIType api, void* hWnd, uint32_t width, uint32_t height, bool bFullscreen) = 0;
    virtual void ShutdownDevice() = 0;
    virtual void BeginFrame() = 0;
    virtual void EndFrame() = 0;

    // Getters de estado
    virtual RenderAPIType GetCurrentAPI() const = 0;
    virtual uint32_t GetWidth() const = 0;
    virtual uint32_t GetHeight() const = 0;

    // Carregamento de malhas (.cgf / .cga)
    virtual bool LoadGeometry(const std::string& filePath, CryMeshGeometry& outMesh) = 0;

    // Sistema de materiais e texturas (.dds)
    virtual bool LoadTextureDDS(const std::string& filePath, TextureResource& outTex) = 0;
    virtual bool RegisterMaterial(const CryMaterial& mat) = 0;
    virtual const CryMaterial* GetMaterial(const std::string& name) const = 0;

    // Shaders e Pós-Processamento
    virtual void SetPostProcessSettings(const PostProcessSettings& settings) = 0;
    virtual const PostProcessSettings& GetPostProcessSettings() const = 0;
};
