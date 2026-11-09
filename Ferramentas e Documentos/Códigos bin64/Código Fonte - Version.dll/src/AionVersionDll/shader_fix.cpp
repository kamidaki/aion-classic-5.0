#include <algorithm>
#include <cstring>
#include <string>
#include <shlobj.h>
#include <shlwapi.h>
#pragma comment(lib, "Shlwapi.lib")
#include "detours.h"

typedef HRESULT(WINAPI* PFN_D3DXCompileShader)(LPCSTR, UINT, const void*, void*, LPCSTR, LPCSTR, DWORD, void**, void**, void**);
static PFN_D3DXCompileShader real_D3DXCompileShader = nullptr;

static HRESULT WINAPI zzD3DXCompileShader(LPCSTR pSrcData, UINT SrcDataLen, const void* pDefines, void* pInclude, LPCSTR pFunctionName, LPCSTR pProfile, DWORD Flags, void** ppShader, void** ppErrorMsgs, void** ppConstantTable) {
    static constexpr char target[] = "  fogInt *= ( 1.0f - exp( -t ) ) / t;";
    static constexpr char insertFix[] = " if (t != 0)";
    const char* begin = pSrcData;
    const char* end = pSrcData + SrcDataLen;
    auto it = std::search(begin, end, std::begin(target), std::end(target) - 1);
    if (it != end) {
        size_t pos = it - begin;
        std::string modified(pSrcData, SrcDataLen);
        modified.insert(pos + 1, insertFix);
        UINT modifiedLen = static_cast<UINT>(modified.size());
        return real_D3DXCompileShader(modified.c_str(), modifiedLen, pDefines, pInclude, pFunctionName, pProfile, Flags, ppShader, ppErrorMsgs, ppConstantTable);
    }
    return real_D3DXCompileShader(pSrcData, SrcDataLen, pDefines, pInclude, pFunctionName, pProfile, Flags, ppShader, ppErrorMsgs, ppConstantTable);
}

static std::string getGameRootDir() {
    char gameDir[MAX_PATH];
    GetModuleFileNameA(NULL, gameDir, MAX_PATH);
    PathRemoveFileSpecA(gameDir);
    PathRemoveFileSpecA(gameDir);
    return std::string(gameDir);
}

static void CreateFoldersRecursive(const std::string& path) {
    SHCreateDirectoryExA(NULL, path.c_str(), NULL);
}

static void DeleteFiles(const std::string& folder, const std::string& pattern) {
    WIN32_FIND_DATAA findData;
    HANDLE hFind = FindFirstFileA((folder + "\\" + pattern).c_str(), &findData);
    if (hFind == INVALID_HANDLE_VALUE) {
        return;
    }
    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            std::string filePath = folder + "\\" + findData.cFileName;
            DeleteFileA(filePath.c_str());
        }
    } while (FindNextFileA(hFind, &findData) != 0);
    FindClose(hFind);
}

static void SetupShaderCache() {
    std::string cacheDir = getGameRootDir() + "\\Shaders\\Cache";
    // the game client deletes all cached shader files on startup if it crashed or closed improperly.
    // we name the marker file so that it also gets deleted on such recompilation events.
    // this way there remains no stale marker file if the game client recompiled shaders without the fix installed
    std::string markerFile = cacheDir + "\\CGPShaders\\#shader_fix_marker.cgps";
    CreateFoldersRecursive(cacheDir + "\\CGPShaders");
    CreateFoldersRecursive(cacheDir + "\\CGVShaders");
    bool markerFileMissing = GetFileAttributesA(markerFile.c_str()) == INVALID_FILE_ATTRIBUTES;
    if (markerFileMissing) {
        // delete all cached shader files to force recompilation with the fix
        DeleteFiles(cacheDir + "\\CGPShaders", "*.cgps");
        DeleteFiles(cacheDir + "\\CGVShaders", "*.cgvp");
        HANDLE hFile = CreateFileA(markerFile.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (hFile != INVALID_HANDLE_VALUE) {
            CloseHandle(hFile);
        }
    }
}

#include <mutex>
#include <d3d9.h>
#pragma comment(lib, "d3d9.lib")

#pragma pack(push, 1)
struct AionSharedFrameHeader {
    uint32_t magic;       // 0x41494F4E ("AION")
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    uint32_t format;      // 1 = 32-bit BGRA
    uint32_t frameSeq;
    uint64_t timestamp;
    uint32_t dataSize;
};
#pragma pack(pop)

static HANDLE s_hMapFile = NULL;
static void* s_pSharedView = NULL;
static IDirect3DSurface9* s_pOffscreenSurface = nullptr;
static UINT s_offscreenWidth = 0;
static UINT s_offscreenHeight = 0;
static D3DFORMAT s_offscreenFormat = D3DFMT_UNKNOWN;
static DWORD s_lastCaptureTick = 0;
static uint32_t s_frameSeq = 0;

typedef HRESULT (WINAPI* PFN_Present)(
    IDirect3DDevice9* pThis,
    const RECT* pSourceRect,
    const RECT* pDestRect,
    HWND hDestWindowOverride,
    const RGNDATA* pDirtyRegion
);
static PFN_Present real_Present = nullptr;

extern "C" bool WINAPI IsWebPortClient();

static HRESULT WINAPI zzPresent(
    IDirect3DDevice9* pThis,
    const RECT* pSourceRect,
    const RECT* pDestRect,
    HWND hDestWindowOverride,
    const RGNDATA* pDirtyRegion
) {
    DWORD now = GetTickCount();
    DWORD minInterval = IsWebPortClient() ? 8 : 33; // 8ms = ~120 FPS target for web port
    if (pThis && (now - s_lastCaptureTick >= minInterval)) {
        s_lastCaptureTick = now;

        IDirect3DSurface9* pBackBuffer = nullptr;
        if (SUCCEEDED(pThis->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &pBackBuffer)) && pBackBuffer) {
            D3DSURFACE_DESC desc;
            if (SUCCEEDED(pBackBuffer->GetDesc(&desc))) {
                if (!s_pOffscreenSurface || s_offscreenWidth != desc.Width || s_offscreenHeight != desc.Height || s_offscreenFormat != desc.Format) {
                    if (s_pOffscreenSurface) {
                        s_pOffscreenSurface->Release();
                        s_pOffscreenSurface = nullptr;
                    }
                    if (SUCCEEDED(pThis->CreateOffscreenPlainSurface(desc.Width, desc.Height, desc.Format, D3DPOOL_SYSTEMMEM, &s_pOffscreenSurface, NULL))) {
                        s_offscreenWidth = desc.Width;
                        s_offscreenHeight = desc.Height;
                        s_offscreenFormat = desc.Format;

                        uint32_t bufSize = sizeof(AionSharedFrameHeader) + (desc.Width * desc.Height * 4);
                        if (s_pSharedView) {
                            UnmapViewOfFile(s_pSharedView);
                            s_pSharedView = NULL;
                        }
                        if (s_hMapFile) {
                            CloseHandle(s_hMapFile);
                            s_hMapFile = NULL;
                        }
                        s_hMapFile = CreateFileMappingA(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, bufSize, "Local\\AionFrameBuffer");
                        if (s_hMapFile) {
                            s_pSharedView = MapViewOfFile(s_hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, bufSize);
                        }
                    }
                }

                if (s_pOffscreenSurface && s_pSharedView) {
                    if (SUCCEEDED(pThis->GetRenderTargetData(pBackBuffer, s_pOffscreenSurface))) {
                        D3DLOCKED_RECT lr;
                        if (SUCCEEDED(s_pOffscreenSurface->LockRect(&lr, NULL, D3DLOCK_READONLY))) {
                            AionSharedFrameHeader* pHdr = (AionSharedFrameHeader*)s_pSharedView;
                            uint8_t* pDest = (uint8_t*)s_pSharedView + sizeof(AionSharedFrameHeader);

                            uint32_t rowBytes = desc.Width * 4;
                            for (UINT y = 0; y < desc.Height; y++) {
                                memcpy(pDest + (y * rowBytes), (const uint8_t*)lr.pBits + (y * lr.Pitch), rowBytes);
                            }

                            s_pOffscreenSurface->UnlockRect();

                            pHdr->magic = 0x41494F4E; // "AION"
                            pHdr->width = desc.Width;
                            pHdr->height = desc.Height;
                            pHdr->stride = rowBytes;
                            pHdr->format = 1;
                            pHdr->frameSeq = ++s_frameSeq;
                            pHdr->timestamp = (uint64_t)now;
                            pHdr->dataSize = desc.Width * desc.Height * 4;
                        }
                    }
                }
            }
            pBackBuffer->Release();
        }
    }

    return real_Present(pThis, pSourceRect, pDestRect, hDestWindowOverride, pDirtyRegion);
}

typedef HRESULT (WINAPI* PFN_CreateDevice)(
    IDirect3D9* pThis,
    UINT Adapter,
    D3DDEVTYPE DeviceType,
    HWND hFocusWindow,
    DWORD BehaviorFlags,
    D3DPRESENT_PARAMETERS* pPresentationParameters,
    IDirect3DDevice9** ppReturnedDeviceInterface
);
static PFN_CreateDevice real_CreateDevice = nullptr;

static HRESULT WINAPI zzCreateDevice(
    IDirect3D9* pThis,
    UINT Adapter,
    D3DDEVTYPE DeviceType,
    HWND hFocusWindow,
    DWORD BehaviorFlags,
    D3DPRESENT_PARAMETERS* pPresentationParameters,
    IDirect3DDevice9** ppReturnedDeviceInterface
) {
    if (IsWebPortClient() && pPresentationParameters) {
        pPresentationParameters->Windowed = TRUE;
        pPresentationParameters->FullScreen_RefreshRateInHz = 0;
    }
    HRESULT hr = real_CreateDevice(pThis, Adapter, DeviceType, hFocusWindow, BehaviorFlags, pPresentationParameters, ppReturnedDeviceInterface);
    if (SUCCEEDED(hr) && ppReturnedDeviceInterface && *ppReturnedDeviceInterface) {
        IDirect3DDevice9* pDev = *ppReturnedDeviceInterface;
        static bool s_presentHooked = false;
        if (!s_presentHooked) {
            void** devVtbl = *(void***)pDev;
            real_Present = (PFN_Present)devVtbl[17];
            DetourTransactionBegin();
            DetourUpdateThread(GetCurrentThread());
            DetourAttach(&(PVOID&)real_Present, zzPresent);
            DetourTransactionCommit();
            s_presentHooked = true;
        }
    }
    return hr;
}

typedef void* (WINAPI* PFN_Direct3DCreate9)(UINT);
static PFN_Direct3DCreate9 real_Direct3DCreate9 = nullptr;
static PFN_Direct3DCreate9 dxvk_Direct3DCreate9 = nullptr;

typedef HRESULT (WINAPI* PFN_Direct3DCreate9Ex)(UINT, void**);
static PFN_Direct3DCreate9Ex real_Direct3DCreate9Ex = nullptr;

static void HookD3D9CreateDevice(void* pD3D) {
    if (!pD3D) return;
    static bool s_createDeviceHooked = false;
    if (!s_createDeviceHooked) {
        void** vtbl = *(void***)pD3D;
        if (vtbl && vtbl[16]) {
            real_CreateDevice = (PFN_CreateDevice)vtbl[16];
            DetourTransactionBegin();
            DetourUpdateThread(GetCurrentThread());
            DetourAttach(&(PVOID&)real_CreateDevice, zzCreateDevice);
            DetourTransactionCommit();
            s_createDeviceHooked = true;
        }
    }
}

static HRESULT WINAPI zzDirect3DCreate9Ex(UINT SDKVersion, void** ppD3D) {
    if (!real_Direct3DCreate9Ex) return E_FAIL;
    HRESULT hr = real_Direct3DCreate9Ex(SDKVersion, ppD3D);
    if (SUCCEEDED(hr) && ppD3D && *ppD3D) {
        HookD3D9CreateDevice(*ppD3D);
    }
    return hr;
}

static void* WINAPI zzDirect3DCreate9(UINT SDKVersion) {
    static std::once_flag s_d3dInit;
    std::call_once(s_d3dInit, []() {
        wchar_t exeDir[MAX_PATH];
        GetModuleFileNameW(nullptr, exeDir, MAX_PATH);
        PathRemoveFileSpecW(exeDir);
        PathAppendW(exeDir, L"dxvk_d3d9.dll");

        HMODULE hDxvk = LoadLibraryW(exeDir);
        if (!hDxvk) {
            hDxvk = LoadLibraryW(L"dxvk_d3d9.dll");
        }
        if (hDxvk) {
            dxvk_Direct3DCreate9 = (PFN_Direct3DCreate9)GetProcAddress(hDxvk, "Direct3DCreate9");
        }
    });

    if (dxvk_Direct3DCreate9) {
        void* pD3D = dxvk_Direct3DCreate9(SDKVersion);
        if (pD3D) {
            HookD3D9CreateDevice(pD3D);
            return pD3D;
        }
    }
    if (real_Direct3DCreate9Ex) {
        void* pEx = nullptr;
        HRESULT hr = real_Direct3DCreate9Ex(SDKVersion, &pEx);
        if (SUCCEEDED(hr) && pEx) {
            HookD3D9CreateDevice(pEx);
            return pEx;
        }
    }
    if (real_Direct3DCreate9) {
        void* pD3D = real_Direct3DCreate9(SDKVersion);
        if (pD3D) {
            HookD3D9CreateDevice(pD3D);
        }
        return pD3D;
    }
    return nullptr;
}

/// Fixes black flickering when using the High Quality graphics engine with Nvidia drivers from 2016 or later, as well as rendering issues with AMD's Vulkan driver for Windows.
/// Bridges Direct3DCreate9 to DXVK (or Direct3DCreate9Ex) on Windows 10/11 WDDM systems to eliminate 'Could not find any compatible Direct3D acceleration devices' CryEngine crash.
void InstallShaderFix() {
    HMODULE hD3d9 = LoadLibraryW(L"d3d9.dll");
    if (hD3d9) {
        real_Direct3DCreate9 = (PFN_Direct3DCreate9)GetProcAddress(hD3d9, "Direct3DCreate9");
        real_Direct3DCreate9Ex = (PFN_Direct3DCreate9Ex)GetProcAddress(hD3d9, "Direct3DCreate9Ex");
        if (real_Direct3DCreate9) {
            DetourAttach(&(PVOID&)real_Direct3DCreate9, zzDirect3DCreate9);
        }
        if (real_Direct3DCreate9Ex) {
            DetourAttach(&(PVOID&)real_Direct3DCreate9Ex, zzDirect3DCreate9Ex);
        }
    }

    HMODULE hD3dx9 = LoadLibrary(L"d3dx9_38.dll");
    if (hD3dx9) {
        SetupShaderCache();
        real_D3DXCompileShader = (PFN_D3DXCompileShader)GetProcAddress(hD3dx9, "D3DXCompileShader");
        DetourAttach(&(PVOID&)real_D3DXCompileShader, zzD3DXCompileShader);
    }
}