#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>
#include <string>
#include <atomic>
#include <mutex>
#include <thread>
#include <chrono>
#include <vector>
#include <array>
#include <unordered_map>
#include "ComboTypes.h"

class ComboRenderer {
private:
    HWND hwnd = nullptr;
    std::thread renderThread;
    std::atomic<bool> running{ false };
    HANDLE wakeEvent = nullptr;

    std::mutex stateMutex;
    int currentHits = 0;
    std::string currentTitle = "";
    DWORD lastEventTime = 0;
    DWORD timeoutMs = (DWORD)COMBO_TIMEOUT_START_MS;
    bool isFirstHit = true;

    bool isBreaking = false;
    DWORD breakStartTime = 0;
    int finalHits = 0;
    std::string finalTitle = "";

    bool isRemoveShock = false;
    DWORD removeShockTime = 0;

    int totalDamage = 0;
    int lastHitDamage = 0;

    struct DamageLine {
        int amount;
        DWORD tick;
        bool received; // true = dano sofrido, false = dano causado
    };
    std::vector<DamageLine> recentHitDamages;

    std::vector<NotificationLine> activeNotifications;

    // Recursos GDI persistentes
    HDC screenDC = nullptr;
    HDC memDC = nullptr;
    HBITMAP memBitmap = nullptr;
    HBITMAP oldBitmap = nullptr;
    int bufW = 0, bufH = 0;

    Gdiplus::FontFamily* fontFamilyImpact = nullptr;

    // Sistema de sprites
    Gdiplus::Image* sprHitGif = nullptr;
    GUID sprHitDimension = {};
    UINT sprHitFrameCount = 0;
    float sprHitElapsed = 0.0f;
    bool sprHitActive = false;
    float sprHitGifMs = 50.0f;

    Gdiplus::Image* spr200wTop = nullptr;
    GUID spr200wTopDimension = {};
    UINT spr200wTopFrameCount = 0;
    float spr200wTopElapsed = 0.0f;
    bool spr200wTopActive = false;
    float spr200wTopFrameMs = 50.0f;

    struct FlashGifAsset {
        Gdiplus::Image* img = nullptr;
        GUID dimension = {};
        UINT frameCount = 0;
        float frameMs = 50.0f;
    };
    std::vector<FlashGifAsset> flashCycleGifs;
    size_t flashCycleNextIndex = 0;
    int flashCycleActiveSlot = -1;
    float flashCycleElapsed = 0.0f;
    bool flashCycleActive = false;

    Gdiplus::Image* spr200w2 = nullptr;
    GUID w2Dimension = {};
    UINT w2FrameCount = 0;
    float w2Elapsed = 0.0f;
    bool w2Active = false;
    float w2FrameMs = 50.0f;

    struct BarRisingParticle {
        bool active = false;
        bool spark = false;
        float x = 0.0f;
        float y = 0.0f;
        float vx = 0.0f;
        float vy = 0.0f;
        float wobblePhase = 0.0f;
        float wobbleSpeed = 0.0f;
        float wobbleAmp = 0.0f;
        float life = 0.0f;
        float maxLife = 0.0f;
        float width0 = 0.0f;
        float height0 = 0.0f;
        float heat = 0.0f;
        float stretch = 0.0f;
        float spin = 0.0f;
        float spinSpeed = 0.0f;
    };
    static constexpr size_t kMaxBarParticles = 224;
    std::array<BarRisingParticle, kMaxBarParticles> barParticles = {};
    uint32_t barPartSeed = 0xC3D2E1F0u;
    size_t barPartCursor = 0;
    float barPartAccum = 0.0f;

    bool poweredModeActive = false;
    DWORD poweredModeStart = 0;
    static constexpr DWORD poweredModeTransitionMs = 500;

    bool darkModeActive = false;
    DWORD darkModeStart = 0;
    static constexpr DWORD darkModeTransitionMs = 500;

    Gdiplus::Image* sprFinishGif = nullptr;
    GUID finishDimension = {};
    UINT finishFrameCount = 0;
    float finishFrameMs = 50.0f;
    float finishElapsed = 0.0f;
    bool finishGifActive = false;

    Gdiplus::Image* sprComboBreakerPng = nullptr;
    std::unordered_map<std::string, Gdiplus::Image*> sprBanners;
    static const DWORD kRemoveShockDurationMs = 1400;
    static const DWORD kRemoveShockFadeMs = 280;

    bool IsUIHidden();

    Gdiplus::Image* GetBanner(const std::string& key);
    std::string GetNotificationBannerKey(NotificationType type, const std::string& text);
    std::string GetComboEndBannerKey(const std::string& title);
    bool DrawBannerImage(Gdiplus::Graphics& g, Gdiplus::Image* banner, float cx, float cy, float alpha, float popScale = 1.0f);

    void LoadSprites();
    void FreeSprites();

    bool DrawHitFlash(Gdiplus::Graphics& g, float cx, float cy, float dt);
    bool DrawLightning(Gdiplus::Graphics& g, float cx, float cy, float dt);
    bool DrawFinishGif(Gdiplus::Graphics& g, float cx, float cy, float dt);
    static float ComputeFadeEnvelope(DWORD age, DWORD durationMs, DWORD fadeMs);
    bool DrawComboBreakerShock(Gdiplus::Graphics& g, float anchorX, float anchorY, float refSize, DWORD now, DWORD startTime);

    BYTE ClampByte(int v) const;
    Gdiplus::Color MixColor(Gdiplus::Color a, Gdiplus::Color b, float t, int alpha) const;
    float BarPartRand01();
    float BarPartRand(float lo, float hi);
    void ClearBarParticles();
    void SpawnBarParticle(float barX, float barW, float barY, float barH, float fillRatio);
    void DrawBarRisingParticles(Gdiplus::Graphics& g, float barX, float barW, float barY, float barH,
                                float fillRatio, float dt, Gdiplus::Color baseColor, Gdiplus::Color hotColor);

    void EnsureBuffer(int width, int height);
    void ReleaseBuffer();
    static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
    Gdiplus::Color GetComboTierColor(int hits);
    Gdiplus::Color ShiftColor(Gdiplus::Color base, int delta, int alpha = 255) const;
    void RenderLoop();
    void UpdateOverlay(int width, int height, int screenX, int screenY, float dt);
    void DrawNotifications(Gdiplus::Graphics& graphics, DWORD now, float centerX, float centerY);
    void DrawOutlinedSegmentText(Gdiplus::Graphics& graphics,
                                 const std::wstring& label,
                                 const std::wstring& value,
                                 float centerX,
                                 float y,
                                 float height,
                                 float fontPx,
                                 INT fontStyle,
                                 int alpha,
                                 Gdiplus::Color labelColor,
                                 Gdiplus::Color valueStart,
                                 Gdiplus::Color valueMid,
                                 Gdiplus::Color valueEnd,
                                 float outlineWidth);
    void DrawCombo(Gdiplus::Graphics& graphics, int w, int h, float dt);

public:
    ComboRenderer() = default;
    ~ComboRenderer() { Stop(); }

    void ShowNotification(const std::string& text);
    void ShowAbnormalState(const std::string& text, NotificationType type);
    int GetCurrentHits();
    void OnDamageReceived(int amount);
    int GetCurrentDamage();
    void Start();
    void Stop();
    void RequestLayoutRefresh();
    void OnEvent(const std::string& event, int hits, const std::string& title, int hitDamage,
                 int totalDamageValue, int serverTimeoutMs);
};
