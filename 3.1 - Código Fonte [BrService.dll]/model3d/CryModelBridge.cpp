#include "CryModelBridge.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cmath>
#include <mutex>
#include <algorithm>
#include <thread>
#include <vector>

namespace BrService {

static std::mutex s_modelMutex;
static HANDLE s_hSharedMem = nullptr;
static void*  s_pSharedMemView = nullptr;
static uint32_t s_currentNpcId = 0;
static uint8_t  s_currentEntityType = 1;
static uint8_t  s_currentRace = 0;
static float    s_targetMemoryYaw = 0.0f;
static float    s_pedestalRotYaw = 0.0f;
static ULONGLONG s_lastRotTime = 0;

void CryModelBridge::EnsureSharedMemory() {
    if (!s_pSharedMemView) {
        if (!s_hSharedMem) {
            s_hSharedMem = OpenFileMappingW(FILE_MAP_READ, FALSE, L"Local\\LostAcademy_CryModel_FrameBuffer");
        }
        if (s_hSharedMem) {
            s_pSharedMemView = MapViewOfFile(s_hSharedMem, FILE_MAP_READ, 0, 0, 0);
            if (s_pSharedMemView) {
                LogInfo("CryModelBridge: Conectado ao Frame Buffer compartilhado Local\\LostAcademy_CryModel_FrameBuffer.");
            }
        }
    }
}

bool CryModelBridge::IsFrameBufferConnected() {
    EnsureSharedMemory();
    if (!s_pSharedMemView) return false;
    const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
    // Accepts both 'AION' (0x41494F4E) and 'ACMB' (0x41434D42)
    return ((h->magic == 0x41494F4E || h->magic == 0x41434D42) && h->status == 2);
}

void CryModelBridge::RequestNpcModelOverPipe(uint32_t npcId) {
    std::thread([npcId]() {
        char cmd[64];
        if (npcId == 0) {
            snprintf(cmd, sizeof(cmd), "LOAD_PLAYER\n");
        } else {
            snprintf(cmd, sizeof(cmd), "LOAD %u\n", npcId);
        }

        HANDLE hPipe = CreateFileA("\\\\.\\pipe\\LostAcademy_CryModelBridge",
                                   GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                                   OPEN_EXISTING, 0, nullptr);
        if (hPipe != INVALID_HANDLE_VALUE) {
            DWORD written = 0;
            WriteFile(hPipe, cmd, (DWORD)strlen(cmd), &written, nullptr);
            CloseHandle(hPipe);
        }
    }).detach();
}

bool CryModelBridge::Initialize() {
    std::lock_guard<std::mutex> lock(s_modelMutex);
    EnsureSharedMemory();

    // Diagn\u00f3stico: reportar status do shared memory e do pipe
    if (s_pSharedMemView) {
        const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
        LogInfo("CryModelBridge: Shared memory conectada. magic=0x%08X status=%u w=%u h=%u pitch=%u",
                h->magic, h->status, h->width, h->height, h->pitch);
    } else {
        // Tentar abrir pipe como teste
        HANDLE hPipe = CreateFileA("\\\\.\\pipe\\LostAcademy_CryModelBridge",
                                   GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                                   OPEN_EXISTING, 0, nullptr);
        if (hPipe != INVALID_HANDLE_VALUE) {
            CloseHandle(hPipe);
            LogInfo("CryModelBridge: Pipe encontrado mas shared memory ausente. Broker iniciado mas frame ainda nao disponivel.");
        } else {
            LogError("CryModelBridge: Broker NAO encontrado (sem shared memory nem pipe). Modelos 3D usarao silhueta fallback. Inicie o broker LostAcademy_CryModelBridge para renderizacao real.");
        }
    }

    // Nao solicitar player model fallback (requisito: sem fallback para proprio personagem)
    return true;
}

static Gdiplus::Bitmap* s_pMonsterBitmap = nullptr;
static uint32_t s_cachedMonsterModelId = 0;

static Gdiplus::Bitmap* LoadMonsterBitmap(uint32_t modelId) {
    if (s_pMonsterBitmap && s_cachedMonsterModelId == modelId) {
        return s_pMonsterBitmap;
    }
    if (s_pMonsterBitmap) {
        delete s_pMonsterBitmap;
        s_pMonsterBitmap = nullptr;
        s_cachedMonsterModelId = 0;
    }

    wchar_t dllPath[MAX_PATH] = { 0 };
    HMODULE hMod = g_hModule;
    if (!hMod) {
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           (LPCWSTR)&CryModelBridge::Initialize, &hMod);
    }
    GetModuleFileNameW(hMod, dllPath, MAX_PATH);
    wchar_t* lastSlash = wcsrchr(dllPath, L'\\');
    if (lastSlash) *lastSlash = L'\0';

    std::wstring basePath = dllPath;
    std::vector<std::wstring> candidatePaths;
    if (modelId > 0) {
        candidatePaths.push_back(basePath + L"\\sprites\\icons\\monsters\\" + std::to_wstring(modelId) + L".png");
        candidatePaths.push_back(L"D:\\GameForge\\aionclassic\\bin64\\sprites\\icons\\monsters\\" + std::to_wstring(modelId) + L".png");
    }
    candidatePaths.push_back(basePath + L"\\sprites\\icons\\monsters\\crestlich.png");
    candidatePaths.push_back(L"D:\\GameForge\\aionclassic\\bin64\\sprites\\icons\\monsters\\crestlich.png");
    candidatePaths.push_back(basePath + L"\\sprites\\icons\\monsters\\default.png");
    candidatePaths.push_back(L"D:\\GameForge\\aionclassic\\bin64\\sprites\\icons\\monsters\\default.png");

    for (const auto& path : candidatePaths) {
        DWORD attr = GetFileAttributesW(path.c_str());
        if (attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY)) {
            Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromFile(path.c_str());
            if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
                s_pMonsterBitmap = bmp;
                s_cachedMonsterModelId = modelId;
                return s_pMonsterBitmap;
            }
            if (bmp) delete bmp;
        }
    }
    return nullptr;
}

void CryModelBridge::Shutdown() {
    std::lock_guard<std::mutex> lock(s_modelMutex);
    if (s_pMonsterBitmap) {
        delete s_pMonsterBitmap;
        s_pMonsterBitmap = nullptr;
        s_cachedMonsterModelId = 0;
    }
    if (s_pSharedMemView) {
        UnmapViewOfFile(s_pSharedMemView);
        s_pSharedMemView = nullptr;
    }
    if (s_hSharedMem) {
        CloseHandle(s_hSharedMem);
        s_hSharedMem = nullptr;
    }
}

void CryModelBridge::SetTargetNpc(uint32_t npcId) {
    SetTargetEntity(npcId, 1, 0, 0.0f);
}

void CryModelBridge::SetTargetEntity(uint32_t modelId, uint8_t entityType, uint8_t race, float yaw) {
    std::lock_guard<std::mutex> lock(s_modelMutex);
    bool changed = (s_currentNpcId != modelId);
    s_currentNpcId = modelId;
    s_currentEntityType = entityType;
    s_currentRace = race;
    s_targetMemoryYaw = yaw;

    if (modelId != 0 && changed) {
        RequestNpcModelOverPipe(modelId);
    }
}

void CryModelBridge::LoadFallbackMesh(uint32_t /*npcId*/) {
}

void CryModelBridge::RenderThumbnail(Gdiplus::Graphics& g, float x, float y, float width, float height) {
    uint32_t activeModel = (s_currentNpcId > 0) ? s_currentNpcId : 215492;

    EnsureSharedMemory();

    if (s_pSharedMemView) {
        const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
        if ((h->magic == 0x41494F4E || h->magic == 0x41434D42) && h->status == 2 && h->width > 0 && h->height > 0) {
            BYTE* pPixels = reinterpret_cast<BYTE*>(s_pSharedMemView) + sizeof(BridgeFrameHeader);
            Gdiplus::Bitmap frameBmp((INT)h->width, (INT)h->height, (INT)h->pitch,
                                     PixelFormat32bppARGB, pPixels);

            g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
            g.DrawImage(&frameBmp, x, y, width, height);
            return;
        }
    }

    // Modern Pedestal & Ambient Platform Renderer (Zero cubes, zero boxes)
    ULONGLONG now = GetTickCount64();
    if (s_lastRotTime == 0) s_lastRotTime = now;
    float dt = (float)(now - s_lastRotTime) / 1000.0f;
    s_lastRotTime = now;
    if (dt > 0.1f) dt = 0.033f;

    s_pedestalRotYaw += dt * 0.45f;
    if (s_pedestalRotYaw > 6.2831853f) s_pedestalRotYaw -= 6.2831853f;

    g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);

    float cx = x + width * 0.5f;
    float cy = y + height * 0.82f;
    float pedW = width * 0.82f;
    float pedH = height * 0.24f;

    // 1. Soft Ambient Shadow below pedestal
    Gdiplus::SolidBrush shadowBrush(Gdiplus::Color(35, 10, 20, 35));
    g.FillEllipse(&shadowBrush, cx - pedW * 0.52f, cy + pedH * 0.22f, pedW * 1.04f, pedH * 0.70f);

    // 2. Multi-tier Stone Pedestal
    Gdiplus::SolidBrush stoneBase(Gdiplus::Color(220, 140, 145, 155));
    Gdiplus::SolidBrush stoneTop(Gdiplus::Color(240, 175, 180, 190));
    Gdiplus::SolidBrush grassRim(Gdiplus::Color(210, 85, 145, 80));

    // Lower tier
    g.FillEllipse(&stoneBase, cx - pedW * 0.50f, cy, pedW, pedH);
    // Upper tier
    g.FillEllipse(&stoneTop, cx - pedW * 0.44f, cy - 6.0f, pedW * 0.88f, pedH * 0.88f);
    // Moss / Grass surface
    g.FillEllipse(&grassRim, cx - pedW * 0.38f, cy - 9.0f, pedW * 0.76f, pedH * 0.76f);

    // 3. Faction / Entity Aura Glow Ring
    Gdiplus::Color ringCol = (s_currentRace == 0) ? Gdiplus::Color(160, 59, 130, 246) :   // Elyos Light Blue
                             (s_currentRace == 1) ? Gdiplus::Color(160, 168, 85, 247) :   // Asmodian Violet
                                                    Gdiplus::Color(160, 239, 68, 68);     // Monster Crimson
    Gdiplus::Pen auraPen(ringCol, 2.0f);
    g.DrawEllipse(&auraPen, cx - pedW * 0.34f, cy - 11.0f, pedW * 0.68f, pedH * 0.68f);

    // 4. Try rendering monster model sprite bitmap
    Gdiplus::Bitmap* mBmp = LoadMonsterBitmap(activeModel);
    if (mBmp) {
        float imgH = height * 0.76f;
        float imgW = imgH * ((float)mBmp->GetWidth() / (float)mBmp->GetHeight());
        if (imgW > width * 0.95f) {
            imgW = width * 0.95f;
            imgH = imgW * ((float)mBmp->GetHeight() / (float)mBmp->GetWidth());
        }
        float imgX = cx - imgW * 0.5f;
        float imgY = cy - imgH - 4.0f;
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.DrawImage(mBmp, imgX, imgY, imgW, imgH);
    } else {
        // Character / Creature Standing Silhouette
        float charW = width * 0.40f;
        float charH = height * 0.60f;
        float charX = cx - charW * 0.5f;
        float charY = cy - charH - 10.0f;

        Gdiplus::SolidBrush charGlow(Gdiplus::Color(30, ringCol.GetR(), ringCol.GetG(), ringCol.GetB()));
        g.FillEllipse(&charGlow, charX, charY, charW, charH);

        // Stylized silhouette torso & head
        Gdiplus::SolidBrush silBrush(Gdiplus::Color(180, 70, 80, 95));
        g.FillEllipse(&silBrush, cx - 11.0f, charY + 6.0f, 22.0f, 24.0f);
        Gdiplus::PointF bodyPts[4] = {
            Gdiplus::PointF(cx - 16.0f, charY + 30.0f),
            Gdiplus::PointF(cx + 16.0f, charY + 30.0f),
            Gdiplus::PointF(cx + 26.0f, charY + charH + 4.0f),
            Gdiplus::PointF(cx - 26.0f, charY + charH + 4.0f)
        };
        g.FillPolygon(&silBrush, bodyPts, 4);

        Gdiplus::Pen wingPen(Gdiplus::Color(140, ringCol.GetR(), ringCol.GetG(), ringCol.GetB()), 1.5f);
        g.DrawArc(&wingPen, cx - charW * 0.70f, charY + 12.0f, charW * 0.70f, charH * 0.65f, 160.0f, 150.0f);
        g.DrawArc(&wingPen, cx, charY + 12.0f, charW * 0.70f, charH * 0.65f, 230.0f, 150.0f);
    }
}

} // namespace BrService
