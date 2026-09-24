#include "ComboRenderer.h"
#include "ComboUI.h"
#include "../core/ServiceGlobals.h"
#include <cmath>
#include <algorithm>
#include <locale>
#include <sstream>
#include <cstdio>

using namespace Gdiplus;

static std::wstring Utf8ToWide(const std::string& s) {
    if (s.empty()) return std::wstring();
    int len = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), nullptr, 0);
    if (len <= 0) return std::wstring();
    std::wstring w(len, 0);
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), &w[0], len);
    return w;
}

uintptr_t ComboRenderer::GetPlayerEntity() {
    if (!BrService::g_isInWorld.load() || BrService::g_isLoadingScreen.load() || !BrService::g_isGameActive.load()) return 0;
    HMODULE hGame = GetModuleHandleA("Game.dll");
    if (!hGame) return 0;
#ifdef _WIN64
    const uintptr_t BASE_OFFSET_PLAYER = 0xECDDC8;
#else
    const uintptr_t BASE_OFFSET_PLAYER = 0x1149DF8;
#endif
    uintptr_t addr = reinterpret_cast<uintptr_t>(hGame) + BASE_OFFSET_PLAYER;
    static const uintptr_t offsets[] = { 0x70, 0x10, 0x20 };
    for (int i = 0; i < 3; ++i) {
        addr = SafeRead<uintptr_t>(addr);
        if (!addr) return 0;
        addr += offsets[i];
    }
    return SafeRead<uintptr_t>(addr);
}

uintptr_t ComboRenderer::GetTargetEntity() {
    if (!BrService::g_isInWorld.load() || BrService::g_isLoadingScreen.load() || !BrService::g_isGameActive.load()) return 0;
    HMODULE hGame = GetModuleHandleA("Game.dll");
    if (!hGame) return 0;
#ifdef _WIN64
    const uintptr_t BASE_OFFSET_TARGET = 0xECE610;
#else
    const uintptr_t BASE_OFFSET_TARGET = 0x114A678;
#endif
    uintptr_t addr = reinterpret_cast<uintptr_t>(hGame) + BASE_OFFSET_TARGET;
    return SafeRead<uintptr_t>(addr);
}

uint32_t ComboRenderer::GetPlayerHP() {
    uintptr_t pEnt = GetPlayerEntity();
    if (!pEnt) return 0;
    const uintptr_t OFFSET_ENTITY_DATA = 0x378;
#ifdef _WIN64
    const uintptr_t OFFSET_HP = 0x147C;
#else
    const uintptr_t OFFSET_HP = 0x15bc;
#endif
    uintptr_t pData = SafeRead<uintptr_t>(pEnt + OFFSET_ENTITY_DATA);
    if (!pData) return 0;
    return SafeRead<uint32_t>(pData + OFFSET_HP);
}

uint32_t ComboRenderer::GetTargetObjId() {
    uintptr_t tEnt = GetTargetEntity();
    if (!tEnt) return 0;
    const uintptr_t OFFSET_ENTITY_DATA = 0x378;
    uintptr_t tData = SafeRead<uintptr_t>(tEnt + OFFSET_ENTITY_DATA);
    if (!tData) return 0;
    return SafeRead<uint32_t>(tData + 0x24);
}

bool ComboRenderer::IsUIHidden() {
    // 0. Hidden when loading, cutscene, or not in world
    if (!BrService::g_isInWorld.load() || BrService::g_isLoadingScreen.load() || !BrService::g_isGameActive.load()) {
        return true;
    }
    // 1. Feature disabled or hidden via in-game settings
    if (!BrService::g_featComboUi.load() || !BrService::g_comboVisible.load()) {
        return true;
    }
    // 2. Window minimized or game window lost focus
    HWND hGame = g_gameHwnd;
    if (!hGame || !IsWindow(hGame) || IsIconic(hGame)) {
        return true;
    }
    HWND fg = GetForegroundWindow();
    if (fg && !IsForegroundInGameProcess(hGame, fg)) {
        return true;
    }
    // 3. Fallback to LostSocket check if available
    typedef BOOL(WINAPI *LS_IsUIHiddenFunc)();
    static LS_IsUIHiddenFunc fn_IsUIHidden = nullptr;
    static bool initialized = false;
    if (!initialized) {
        HMODULE hSocket = GetModuleHandleA("LostSocket.dll");
        if (hSocket) {
            fn_IsUIHidden = reinterpret_cast<LS_IsUIHiddenFunc>(GetProcAddress(hSocket, "LS_IsUIHidden"));
        }
        initialized = true;
    }
    if (fn_IsUIHidden) {
        return fn_IsUIHidden() == TRUE;
    }
    return false;
}

Image* ComboRenderer::GetBanner(const std::string& key) {
    if (key.empty()) return nullptr;
    auto it = sprBanners.find(key);
    if (it != sprBanners.end()) return it->second;
    return nullptr;
}

std::string ComboRenderer::GetNotificationBannerKey(NotificationType type, const std::string& text) {
    switch (type) {
        case NotificationType::AbnormalStun:      return "state_atordoamento";
        case NotificationType::AbnormalParalyzed: return "state_paralisia";
        case NotificationType::AbnormalSilenced:  return "state_silenciamento";
        case NotificationType::AbnormalBlink:     return "state_preso";
        case NotificationType::AbnormalPoison:    return "state_envenenamento";
        case NotificationType::AbnormalBleed:     return "state_sangramento";
        case NotificationType::AbnormalFear:      return "state_medo";
        case NotificationType::AbnormalSleep:     return "state_adormecimento";
        case NotificationType::AbnormalBlind:     return "state_cegueira";
        case NotificationType::AbnormalDisease:   return "state_doenca";
        case NotificationType::AbnormalCurse:     return "state_maldicao";
        case NotificationType::AbnormalConfuse:   return "state_confusao";
        default: break;
    }
    if (text.find("Recorde") != std::string::npos || text.find("recorde") != std::string::npos ||
        text.find("Record") != std::string::npos || text.find("record") != std::string::npos) {
        return "notify_recorde";
    }
    if (text.find("Participa") != std::string::npos || text.find("participa") != std::string::npos ||
        text.find("Point") != std::string::npos || text.find("point") != std::string::npos) {
        return "notify_participacao";
    }
    return "";
}

std::string ComboRenderer::GetComboEndBannerKey(const std::string& title) {
    if (title.empty()) return "combo_break";
    std::string lower;
    for (char c : title) lower += static_cast<char>(tolower(static_cast<unsigned char>(c)));

    if (lower.find("matador") != std::string::npos) return "combo_matador";
    if (lower.find("solador") != std::string::npos) return "combo_solador";
    if (lower.find("implac") != std::string::npos) return "combo_implacavel";
    if (lower.find("monstruoso") != std::string::npos) return "combo_monstruoso";
    if (lower.find("brutal") != std::string::npos) return "combo_brutal";
    if (lower == "rei" || lower.find("rei") != std::string::npos) return "combo_rei";
    if (lower.find("dominador") != std::string::npos) return "combo_dominador";
    if (lower.find("lend") != std::string::npos) return "combo_lendario";
    if (lower.find("insano") != std::string::npos) return "combo_insano";
    if (lower.find("aniquilador") != std::string::npos) return "combo_aniquilador";
    if (lower.find("esgotado") != std::string::npos) return "combo_esgotado";
    if (lower.find("final") != std::string::npos) return "combo_final";
    if (lower.find("cc") != std::string::npos) return "combo_cc_break";
    if (lower.find("death") != std::string::npos) return "combo_death";
    if (lower.find("reset") != std::string::npos) return "combo_reset";

    return "combo_break";
}

bool ComboRenderer::DrawBannerImage(Graphics& g, Image* banner, float cx, float cy, float alpha, float popScale) {
    if (!banner || alpha <= 0.0f) return false;
    float imgW = static_cast<float>(banner->GetWidth());
    float imgH = static_cast<float>(banner->GetHeight());
    if (imgW <= 0.0f || imgH <= 0.0f) return false;

    float drawW = 270.0f * popScale;
    float drawH = (imgH / imgW) * drawW;

    BYTE a = static_cast<BYTE>(ClampInt(static_cast<int>(alpha * 255.0f + 0.5f), 0, 255));
    ColorMatrix cm = {
        1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 0.0f, static_cast<float>(a) / 255.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 0.0f, 1.0f
    };
    ImageAttributes attr;
    attr.SetColorMatrix(&cm, ColorMatrixFlagsDefault, ColorAdjustTypeBitmap);

    RectF destRect(cx - drawW * 0.5f, cy - drawH * 0.5f, drawW, drawH);
    g.DrawImage(banner, destRect, 0.0f, 0.0f, imgW, imgH, UnitPixel, &attr);
    return true;
}

void ComboRenderer::LoadSprites() {
    wchar_t dllPath[MAX_PATH] = {};
    HMODULE hMod = BrService::g_hModule;
    if (!hMod) hMod = GetModuleHandleW(L"BrService.dll");
    GetModuleFileNameW(hMod, dllPath, MAX_PATH);
    std::wstring dir(dllPath);
    auto slash = dir.find_last_of(L"\\/"); 
    if (slash != std::wstring::npos) dir = dir.substr(0, slash + 1);
    else dir += L'\\';

    // Strictly resolve sprites directory in the exact same directory as the DLL (e.g. bin64\sprites\effects\)
    // NEVER look in the root or parent directory (../)
    std::wstring effectsBase = dir + L"sprites\\effects\\";

    auto loadGif = [&](const std::wstring& path, Image*& outImg, GUID& outDim, UINT& outCount, float& outMs) {
        outImg = Image::FromFile(path.c_str());
        if (outImg && outImg->GetLastStatus() != Ok) { delete outImg; outImg = nullptr; return; }
        if (!outImg) return;
        UINT dimCount = outImg->GetFrameDimensionsCount();
        if (dimCount > 0) {
            std::vector<GUID> dims(dimCount);
            outImg->GetFrameDimensionsList(dims.data(), dimCount);
            outDim = dims[0];
            outCount = outImg->GetFrameCount(&outDim);
        }
        UINT propSize = outImg->GetPropertyItemSize(PropertyTagFrameDelay);
        if (propSize > 0) {
            std::vector<BYTE> buf(propSize);
            PropertyItem* pi = reinterpret_cast<PropertyItem*>(buf.data());
            if (outImg->GetPropertyItem(PropertyTagFrameDelay, propSize, pi) == Ok) {
                UINT* delays = reinterpret_cast<UINT*>(pi->value);
                outMs = delays[0] * 10.0f;
                if (outMs < 20.0f) outMs = 50.0f;
            }
        }
    };

    std::wstring hitPath = effectsBase + L"hit1.gif";
    loadGif(hitPath, sprHitGif, sprHitDimension, sprHitFrameCount, sprHitGifMs);

    {
        std::wstring effectsDir = effectsBase;
        std::wstring searchPattern = effectsDir + L"flash-effect_*.gif";
        std::vector<std::wstring> flashFiles;
        WIN32_FIND_DATAW findData;
        HANDLE hFind = FindFirstFileW(searchPattern.c_str(), &findData);
        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                    flashFiles.push_back(effectsDir + findData.cFileName);
                }
            } while (FindNextFileW(hFind, &findData));
            FindClose(hFind);
        }
        std::sort(flashFiles.begin(), flashFiles.end());

        flashCycleGifs.clear();
        for (auto& fpath : flashFiles) {
            FlashGifAsset asset;
            loadGif(fpath, asset.img, asset.dimension, asset.frameCount, asset.frameMs);
            if (asset.img) flashCycleGifs.push_back(asset);
        }
        flashCycleNextIndex = 0;
        flashCycleActiveSlot = -1;
        flashCycleActive = false;
    }

    std::wstring w2Path = effectsBase + L"200w_2.gif";
    loadGif(w2Path, spr200w2, w2Dimension, w2FrameCount, w2FrameMs);

    std::wstring top200wPath = effectsBase + L"200w.gif";
    loadGif(top200wPath, spr200wTop, spr200wTopDimension, spr200wTopFrameCount, spr200wTopFrameMs);

    std::wstring finishPath = effectsBase + L"flash-effect_4.gif";
    loadGif(finishPath, sprFinishGif, finishDimension, finishFrameCount, finishFrameMs);

    std::wstring comboBreakerPath = effectsBase + L"combo-breaker.png";
    sprComboBreakerPng = Image::FromFile(comboBreakerPath.c_str());
    if (sprComboBreakerPng && sprComboBreakerPng->GetLastStatus() != Ok) {
        delete sprComboBreakerPng;
        sprComboBreakerPng = nullptr;
    }

    const std::pair<const char*, const wchar_t*> bannerFiles[] = {
        { "state_atordoamento",   L"state_atordoamento.png" },
        { "state_paralisia",     L"state_paralisia.png" },
        { "state_silenciamento", L"state_silenciamento.png" },
        { "state_preso",         L"state_preso.png" },
        { "state_envenenamento", L"state_envenenamento.png" },
        { "state_sangramento",   L"state_sangramento.png" },
        { "state_medo",          L"state_medo.png" },
        { "state_adormecimento", L"state_adormecimento.png" },
        { "state_cegueira",      L"state_cegueira.png" },
        { "state_cego",          L"state_cego.png" },
        { "state_doenca",        L"state_doenca.png" },
        { "state_maldicao",      L"state_maldicao.png" },
        { "state_confusao",      L"state_confusao.png" },
        { "combo_breaker",       L"combo_breaker.png" },
        { "combo_start",         L"combo_start.png" },
        { "combo_update",        L"combo_update.png" },
        { "combo_break",         L"combo_break.png" },
        { "combo_final",         L"combo_final.png" },
        { "combo_cc_break",      L"combo_cc_break.png" },
        { "combo_death",         L"combo_death.png" },
        { "combo_reset",         L"combo_reset.png" },
        { "combo_esgotado",      L"combo_esgotado.png" },
        { "combo_matador",       L"combo_matador.png" },
        { "combo_solador",       L"combo_solador.png" },
        { "combo_implacavel",    L"combo_implacavel.png" },
        { "combo_monstruoso",    L"combo_monstruoso.png" },
        { "combo_brutal",        L"combo_brutal.png" },
        { "combo_rei",           L"combo_rei.png" },
        { "combo_dominador",     L"combo_dominador.png" },
        { "combo_lendario",      L"combo_lendario.png" },
        { "combo_insano",        L"combo_insano.png" },
        { "combo_aniquilador",   L"combo_aniquilador.png" },
        { "notify_recorde",      L"notify_recorde.png" },
        { "notify_participacao", L"notify_participacao.png" },
    };

    for (const auto& item : bannerFiles) {
        std::wstring bPath = effectsBase + item.second;
        Image* bImg = Image::FromFile(bPath.c_str());
        if (bImg && bImg->GetLastStatus() == Ok) {
            sprBanners[item.first] = bImg;
        } else {
            delete bImg;
        }
    }
}

void ComboRenderer::FreeSprites() {
    delete sprHitGif;          sprHitGif          = nullptr;
    delete spr200w2;           spr200w2           = nullptr;
    delete spr200wTop;         spr200wTop         = nullptr;
    delete sprFinishGif;       sprFinishGif       = nullptr;
    delete sprComboBreakerPng; sprComboBreakerPng = nullptr;

    for (auto& asset : flashCycleGifs) {
        delete asset.img;
    }
    flashCycleGifs.clear();

    for (auto& pair : sprBanners) {
        delete pair.second;
    }
    sprBanners.clear();
}

bool ComboRenderer::DrawHitFlash(Graphics& g, float cx, float cy, float dt) {
    if (!sprHitGif || sprHitFrameCount == 0) return false;
    sprHitElapsed += dt * 1000.0f;
    float totalMs = sprHitFrameCount * sprHitGifMs;
    if (sprHitElapsed >= totalMs) return false;
    UINT frame = static_cast<UINT>(sprHitElapsed / sprHitGifMs);
    if (frame >= sprHitFrameCount) frame = sprHitFrameCount - 1;
    sprHitGif->SelectActiveFrame(&sprHitDimension, frame);
    float sz = 180.0f;
    g.DrawImage(sprHitGif, cx - sz / 2, cy - sz / 2, sz, sz);
    return true;
}

bool ComboRenderer::DrawLightning(Graphics& g, float cx, float cy, float dt) {
    bool any = false;

    if (flashCycleActive && flashCycleActiveSlot >= 0 &&
        flashCycleActiveSlot < static_cast<int>(flashCycleGifs.size())) {
        FlashGifAsset& asset = flashCycleGifs[flashCycleActiveSlot];
        if (asset.img && asset.frameCount > 0) {
            flashCycleElapsed += dt * 1000.0f;
            float totalMs = asset.frameCount * asset.frameMs;
            if (flashCycleElapsed >= totalMs) {
                flashCycleActive = false;
            } else {
                UINT f = static_cast<UINT>(flashCycleElapsed / asset.frameMs);
                if (f >= asset.frameCount) f = asset.frameCount - 1;
                asset.img->SelectActiveFrame(&asset.dimension, f);
                float sz = 260.0f;
                g.DrawImage(asset.img, cx - sz / 2, cy - sz / 2, sz, sz);
                any = true;
            }
        } else {
            flashCycleActive = false;
        }
    }

    if (w2Active && spr200w2 && w2FrameCount > 0) {
        w2Elapsed += dt * 1000.0f;
        float totalMs = w2FrameCount * w2FrameMs;
        if (w2Elapsed >= totalMs) { w2Active = false; }
        else {
            UINT f = static_cast<UINT>(w2Elapsed / w2FrameMs);
            if (f >= w2FrameCount) f = w2FrameCount - 1;
            spr200w2->SelectActiveFrame(&w2Dimension, f);
            float sz = 220.0f; g.DrawImage(spr200w2, cx - sz/2, cy - sz/2, sz, sz);
            any = true;
        }
    }
    return any;
}

bool ComboRenderer::DrawFinishGif(Graphics& g, float cx, float cy, float dt) {
    if (!finishGifActive || !sprFinishGif || finishFrameCount == 0) return false;
    finishElapsed += dt * 1000.0f;
    float totalMs = finishFrameCount * finishFrameMs;
    if (finishElapsed >= totalMs) {
        finishGifActive = false;
        return false;
    }
    UINT frame = static_cast<UINT>(finishElapsed / finishFrameMs);
    if (frame >= finishFrameCount) frame = finishFrameCount - 1;
    sprFinishGif->SelectActiveFrame(&finishDimension, frame);
    float sz = 200.0f;
    g.DrawImage(sprFinishGif, cx - sz / 2, cy - sz / 2, sz, sz);
    return true;
}

float ComboRenderer::ComputeFadeEnvelope(DWORD age, DWORD durationMs, DWORD fadeMs) {
    if (age >= durationMs) return 0.0f;
    if (age < fadeMs) return static_cast<float>(age) / static_cast<float>(fadeMs);
    DWORD remain = durationMs - age;
    if (remain < fadeMs) return static_cast<float>(remain) / static_cast<float>(fadeMs);
    return 1.0f;
}

bool ComboRenderer::DrawComboBreakerShock(Graphics& g, float anchorX, float anchorY, float refSize, DWORD now, DWORD startTime) {
    if (!sprComboBreakerPng) return false;
    DWORD age = now - startTime;
    float alpha01 = ComputeFadeEnvelope(age, kRemoveShockDurationMs, kRemoveShockFadeMs);
    if (alpha01 <= 0.0f) return false;

    float imgW = static_cast<float>(sprComboBreakerPng->GetWidth());
    float imgH = static_cast<float>(sprComboBreakerPng->GetHeight());
    if (imgW <= 0.0f || imgH <= 0.0f) return false;

    float targetW = refSize * 2.2f;
    float scale = targetW / imgW;
    float drawW = imgW * scale;
    float drawH = imgH * scale;

    float popScale = 0.92f + 0.08f * alpha01;

    float offsetX = refSize * 1.35f;
    float offsetY = -refSize * 0.5f;
    float cx = anchorX + offsetX + drawW * 0.5f * popScale;
    float cy = anchorY + offsetY;

    GraphicsState savedState = g.Save();

    Matrix m;
    m.Translate(cx, cy);
    m.Rotate(-14.0f);
    m.Scale(popScale, popScale);
    g.SetTransform(&m);

    BYTE a = static_cast<BYTE>(ClampInt(static_cast<int>(alpha01 * 255.0f + 0.5f), 0, 255));
    ColorMatrix cm = {
        1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 0.0f, static_cast<float>(a) / 255.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 0.0f, 1.0f
    };
    ImageAttributes attr;
    attr.SetColorMatrix(&cm, ColorMatrixFlagsDefault, ColorAdjustTypeBitmap);

    RectF destRect(-drawW * 0.5f, -drawH * 0.5f, drawW, drawH);
    g.DrawImage(sprComboBreakerPng, destRect, 0.0f, 0.0f, imgW, imgH, UnitPixel, &attr);

    g.SetTransform(&Matrix());
    g.Restore(savedState);
    return true;
}

BYTE ComboRenderer::ClampByte(int v) const {
    if (v < 0) return 0;
    if (v > 255) return 255;
    return static_cast<BYTE>(v);
}

Color ComboRenderer::MixColor(Color a, Color b, float t, int alpha) const {
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    return Color(ClampByte(alpha),
                 ClampByte(static_cast<int>(a.GetR() + (b.GetR() - a.GetR()) * t)),
                 ClampByte(static_cast<int>(a.GetG() + (b.GetG() - a.GetG()) * t)),
                 ClampByte(static_cast<int>(a.GetB() + (b.GetB() - a.GetB()) * t)));
}

float ComboRenderer::BarPartRand01() {
    barPartSeed = barPartSeed * 1664525u + 1013904223u;
    return static_cast<float>((barPartSeed >> 8) & 0x00FFFFFF) / 16777215.0f;
}

float ComboRenderer::BarPartRand(float lo, float hi) {
    return lo + (hi - lo) * BarPartRand01();
}

void ComboRenderer::ClearBarParticles() {
    for (auto& p : barParticles) p.active = false;
    barPartAccum = 0.0f;
}

void ComboRenderer::SpawnBarParticle(float barX, float barW, float barY, float barH, float fillRatio) {
    size_t slot = barParticles.size();
    for (size_t i = 0; i < barParticles.size(); ++i) {
        size_t idx = (barPartCursor + i) % barParticles.size();
        if (!barParticles[idx].active) { slot = idx; break; }
    }
    if (slot == barParticles.size()) {
        slot = barPartCursor;
    }
    barPartCursor = (slot + 1) % barParticles.size();

    float fillW = (std::max)(6.0f, (barW - 2.0f) * ClampFloat(fillRatio, 0.0f, 1.0f));
    float x01 = BarPartRand01();
    float baseJitter = sinf(BarPartRand(0.0f, 6.283185f)) * BarPartRand(0.0f, 2.2f);

    BarRisingParticle& p = barParticles[slot];
    p.active = true;
    p.spark = BarPartRand01() < 0.14f;
    p.x = barX + 1.0f + x01 * fillW + baseJitter;
    p.y = barY + barH * BarPartRand(0.30f, 1.08f);
    p.heat = BarPartRand(0.58f, 1.0f);
    p.wobblePhase = BarPartRand(0.0f, 6.283185f);
    p.wobbleSpeed = BarPartRand(7.0f, 16.0f);
    p.wobbleAmp = BarPartRand(5.0f, 17.0f);
    p.spin = BarPartRand(-0.9f, 0.9f);
    p.spinSpeed = BarPartRand(-2.4f, 2.4f);

    if (p.spark) {
        p.vx = BarPartRand(-14.0f, 14.0f);
        p.vy = BarPartRand(-165.0f, -92.0f);
        p.maxLife = BarPartRand(0.24f, 0.52f);
        p.width0 = BarPartRand(1.2f, 2.8f);
        p.height0 = BarPartRand(5.0f, 11.0f);
        p.stretch = BarPartRand(1.4f, 2.7f);
    } else {
        p.vx = BarPartRand(-9.0f, 9.0f);
        p.vy = BarPartRand(-116.0f, -58.0f);
        p.maxLife = BarPartRand(0.36f, 0.86f);
        p.width0 = BarPartRand(4.0f, 11.5f);
        p.height0 = BarPartRand(15.0f, 34.0f);
        p.stretch = BarPartRand(0.85f, 1.65f);
    }
    p.life = p.maxLife;
}

void ComboRenderer::DrawBarRisingParticles(Graphics& g, float barX, float barW, float barY, float barH,
                                           float fillRatio, float dt, Color baseColor, Color hotColor) {
    if (fillRatio <= 0.01f) { ClearBarParticles(); return; }
    dt = ClampFloat(dt, 0.0f, 0.050f);

    float fillW = (std::max)(6.0f, (barW - 2.0f) * ClampFloat(fillRatio, 0.0f, 1.0f));
    float densityScale = ClampFloat(barW / 240.0f, 0.65f, 1.35f);
    barPartAccum += dt * (128.0f + 92.0f * fillRatio) * densityScale;
    int spawnCount = 0;
    while (barPartAccum >= 1.0f && spawnCount < 18) {
        SpawnBarParticle(barX, barW, barY, barH, fillRatio);
        barPartAccum -= 1.0f;
        ++spawnCount;
    }
    if (barPartAccum > 18.0f) barPartAccum = 1.0f;

    Color coreColor(255, 255, 248, 214);
    Color amberColor(255, 255, 175, 62);
    Color smokeColor(255, 48, 43, 39);

    RectF glowRect(barX, barY - barH * 1.25f, fillW, barH * 2.25f);
    LinearGradientBrush baseGlow(glowRect,
        Color(ClampInt(static_cast<int>(85.0f * fillRatio), 20, 105), hotColor.GetR(), hotColor.GetG(), hotColor.GetB()),
        Color(0, baseColor.GetR(), baseColor.GetG(), baseColor.GetB()),
        LinearGradientModeVertical);
    g.FillRectangle(&baseGlow, glowRect);

    for (auto& p : barParticles) {
        if (!p.active) continue;
        p.life -= dt;
        if (p.life <= 0.0f) { p.active = false; continue; }

        p.wobblePhase += p.wobbleSpeed * dt;
        p.spin += p.spinSpeed * dt;
        float t = 1.0f - (p.life / (std::max)(0.001f, p.maxLife));
        float turbulence = sinf(p.wobblePhase) * p.wobbleAmp;
        p.vx += sinf(p.wobblePhase * 0.47f + p.spin) * dt * 18.0f;
        p.x += (p.vx + turbulence) * dt;
        p.y += p.vy * dt;

        float fade = sinf(ClampFloat(t, 0.0f, 1.0f) * 3.1415926f);
        fade *= (1.0f - 0.34f * t) * (0.72f + 0.28f * p.heat);
        if (fade <= 0.01f) continue;

        if (p.spark) {
            int aSpark = ClampInt(static_cast<int>(fade * 230.0f), 0, 230);
            float len = p.height0 * p.stretch * (1.0f + t * 0.9f);
            Color sparkColor = MixColor(amberColor, coreColor, 0.65f + 0.25f * p.heat, aSpark);
            Pen sparkPen(sparkColor, (std::max)(1.0f, p.width0));
            g.DrawLine(&sparkPen, PointF(p.x, p.y), PointF(p.x - p.vx * 0.018f, p.y + len));
            continue;
        }

        float narrow = 1.0f - 0.72f * t;
        float w = (std::max)(0.8f, p.width0 * narrow * (1.0f + 0.20f * sinf(p.spin)));
        float h = p.height0 * (1.0f + p.stretch * t);
        float x = p.x + sinf(p.spin) * w * 0.22f;
        float y = p.y - h * 0.18f * t;

        int aGlow = ClampInt(static_cast<int>(fade * 92.0f), 0, 92);
        int aOuter = ClampInt(static_cast<int>(fade * 188.0f), 0, 188);
        int aMid = ClampInt(static_cast<int>(fade * 220.0f), 0, 220);
        int aCore = ClampInt(static_cast<int>(fade * 245.0f * (1.0f - t * 0.72f)), 0, 245);

        if (t > 0.58f && aGlow > 0) {
            Color smoke = MixColor(baseColor, smokeColor, ClampFloat((t - 0.58f) * 2.4f, 0.0f, 1.0f), aGlow / 2);
            SolidBrush smokeBrush(smoke);
            g.FillEllipse(&smokeBrush, RectF(x - w * 0.95f, y - h * 0.55f, w * 1.9f, h * 0.92f));
        }

        if (aGlow > 0) {
            Color glow = MixColor(baseColor, hotColor, 0.35f + 0.45f * p.heat, aGlow);
            SolidBrush glowBrush(glow);
            g.FillEllipse(&glowBrush, RectF(x - w * 0.95f, y - h * 0.58f, w * 1.9f, h * 1.16f));
        }

        if (aOuter > 0) {
            Color outer = MixColor(baseColor, hotColor, ClampFloat(0.20f + t * 0.85f, 0.0f, 1.0f), aOuter);
            SolidBrush outerBrush(outer);
            g.FillEllipse(&outerBrush, RectF(x - w * 0.52f, y - h * 0.54f, w, h));
        }

        if (aMid > 0 && t < 0.82f) {
            Color mid = MixColor(hotColor, amberColor, ClampFloat(0.45f + p.heat * 0.45f, 0.0f, 1.0f), aMid);
            SolidBrush midBrush(mid);
            g.FillEllipse(&midBrush, RectF(x - w * 0.34f, y - h * 0.40f, w * 0.68f, h * 0.70f));
        }

        if (aCore > 0 && t < 0.54f) {
            Color core = MixColor(amberColor, coreColor, ClampFloat(0.35f + p.heat * 0.60f, 0.0f, 1.0f), aCore);
            SolidBrush coreBrush(core);
            g.FillEllipse(&coreBrush, RectF(x - w * 0.18f, y - h * 0.25f, w * 0.36f, h * 0.42f));
        }
    }
}

void ComboRenderer::EnsureBuffer(int width, int height) {
    if (memDC && bufW == width && bufH == height) return;
    ReleaseBuffer();
    memDC = CreateCompatibleDC(screenDC);
    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    void* pvBits = nullptr;
    memBitmap = CreateDIBSection(screenDC, &bmi, DIB_RGB_COLORS, &pvBits, NULL, 0);
    oldBitmap = reinterpret_cast<HBITMAP>(SelectObject(memDC, memBitmap));
    bufW = width;
    bufH = height;
}

void ComboRenderer::ReleaseBuffer() {
    if (memDC) {
        if (oldBitmap) SelectObject(memDC, oldBitmap);
        if (memBitmap) DeleteObject(memBitmap);
        DeleteDC(memDC);
    }
    memDC = nullptr;
    memBitmap = nullptr;
    oldBitmap = nullptr;
    bufW = bufH = 0;
}

LRESULT CALLBACK ComboRenderer::WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == WM_DESTROY) {
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

Color ComboRenderer::GetComboTierColor(int hits) {
    if (hits >= 300) return Color(255, 40, 40, 40);
    if (hits >= 280) return Color(255, 120, 20, 20);
    if (hits >= 260) return Color(255, 220, 30, 30);
    if (hits >= 240) return Color(255, 255, 70, 70);
    if (hits >= 220) return Color(255, 255, 40, 130);
    if (hits >= 200) return Color(255, 255, 105, 180);
    if (hits >= 180) return Color(255, 218, 50, 200);
    if (hits >= 160) return Color(255, 180, 40, 220);
    if (hits >= 140) return Color(255, 148, 0, 211);
    if (hits >= 120) return Color(255, 110, 50, 225);
    if (hits >= 100) return Color(255, 65, 105, 225);
    if (hits >= 80)  return Color(255, 30, 144, 255);
    if (hits >= 60)  return Color(255, 0, 191, 255);
    if (hits >= 40)  return Color(255, 0, 220, 170);
    if (hits >= 20)  return Color(255, 255, 180, 0);
    int r = (std::min)(255, 200 + hits * 2);
    int g = (std::max)(50, 255 - hits * 5);
    int b = (std::max)(50, 255 - hits * 5);
    return Color(255, r, g, b);
}

Color ComboRenderer::ShiftColor(Color base, int delta, int alpha) const {
    return Color(ClampByte(alpha),
                 ClampByte(static_cast<int>(base.GetR()) + delta),
                 ClampByte(static_cast<int>(base.GetG()) + delta),
                 ClampByte(static_cast<int>(base.GetB()) + delta));
}

void ComboRenderer::RenderLoop() {
    GdiplusStartupInput gdiplusStartupInput;
    GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    fontFamilyImpact = new FontFamily(L"Impact");
    LoadSprites();

    HINSTANCE hInstance = GetModuleHandle(NULL);
    WNDCLASSEXA wc = { sizeof(WNDCLASSEXA) };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "AionComboUI";
    RegisterClassExA(&wc);

    HWND gameHwnd = FindWindowA("AIONClient", nullptr);
    if (!gameHwnd) gameHwnd = FindWindowA("AIONClientWndClass1.0", nullptr);
    if (!gameHwnd) gameHwnd = FindWindowA("Lost Academy", nullptr);
    if (!gameHwnd) gameHwnd = FindWindowA("LostAcademyWndClass1.0", nullptr);

    RECT rect;
    if (gameHwnd) {
        ComputeOverlayRect(gameHwnd, rect);
    } else {
        rect.left = 0; rect.top = 0; rect.right = COMBO_W; rect.bottom = COMBO_H;
    }
    int rectW = (std::max)(1, static_cast<int>(rect.right - rect.left));
    int rectH = (std::max)(1, static_cast<int>(rect.bottom - rect.top));

    hwnd = CreateWindowExA(
        WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        "AionComboUI", "ComboUI",
        WS_POPUP,
        rect.left, rect.top, rectW, rectH,
        nullptr, NULL, hInstance, NULL);

    SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER);
    ShowWindow(hwnd, SW_HIDE); // Start hidden to preserve DWM hardware flip

    screenDC = GetDC(NULL);
    EnsureBuffer(rectW, rectH);

    ULONGLONG lastFrameTick = GetTickCount64();
    bool transparentFrameApplied = true;

    while (running) {
        MSG msg;
        while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }

        if (!gameHwnd || !IsWindow(gameHwnd)) {
            gameHwnd = FindWindowA("AIONClientWndClass1.0", nullptr);
            if (!gameHwnd) gameHwnd = FindWindowA("AIONClient", nullptr);

            if (gameHwnd) {
                g_gameHwnd = gameHwnd;
                g_overlayHwnd = hwnd;
            }
        }

        bool shouldDraw = false;
        RECT drawRect = { 0 };
        HWND fg = GetForegroundWindow();

        if (gameHwnd && IsWindowVisible(gameHwnd) && !IsIconic(gameHwnd)) {
            bool foregroundIsClient = (fg == hwnd) || IsForegroundInGameProcess(gameHwnd, fg);
            if (foregroundIsClient) {
                shouldDraw = true;
            }
            ComputeOverlayRect(gameHwnd, drawRect);
        }
        if (IsUIHidden()) {
            shouldDraw = false;
        }
        int drawW = (std::max)(1, static_cast<int>(drawRect.right - drawRect.left));
        int drawH = (std::max)(1, static_cast<int>(drawRect.bottom - drawRect.top));

        bool active = false;
        {
            std::lock_guard<std::mutex> lock(stateMutex);
            active = (currentHits > 0 || isBreaking || isRemoveShock || sprHitActive ||
                      flashCycleActive || w2Active || spr200wTopActive || finishGifActive ||
                      !activeNotifications.empty());
        }

        if (shouldDraw && active) {
            RECT currRect;
            GetWindowRect(hwnd, &currRect);
            bool needsPosUpdate = (currRect.left != drawRect.left || currRect.top != drawRect.top ||
                                   (currRect.right - currRect.left) != drawW ||
                                   (currRect.bottom - currRect.top) != drawH);

            if (needsPosUpdate || !IsWindowVisible(hwnd)) {
                SetWindowPos(hwnd, HWND_TOPMOST, drawRect.left, drawRect.top, drawW, drawH,
                             SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_NOOWNERZORDER | SWP_ASYNCWINDOWPOS);
            }

            ULONGLONG nowTick = GetTickCount64();
            float dt = static_cast<float>(nowTick - lastFrameTick) / 1000.0f;
            if (dt > 0.05f) dt = 0.05f;
            lastFrameTick = nowTick;

            UpdateOverlay(drawW, drawH, drawRect.left, drawRect.top, dt);
            transparentFrameApplied = false;

            if (wakeEvent) WaitForSingleObject(wakeEvent, 16);
            else std::this_thread::sleep_for(std::chrono::milliseconds(16));
        } else {
            lastFrameTick = GetTickCount64();
            if (IsWindowVisible(hwnd)) {
                ShowWindowAsync(hwnd, SW_HIDE);
                transparentFrameApplied = false;
            }
            if (wakeEvent) WaitForSingleObject(wakeEvent, 300);
            else std::this_thread::sleep_for(std::chrono::milliseconds(300));
        }
    }
    ReleaseBuffer();
    if (screenDC) { ReleaseDC(NULL, screenDC); screenDC = nullptr; }
    FreeSprites();
    delete fontFamilyImpact;
    fontFamilyImpact = nullptr;
    DestroyWindow(hwnd);
    UnregisterClassA("AionComboUI", hInstance);
    GdiplusShutdown(gdiplusToken);
}

void ComboRenderer::UpdateOverlay(int width, int height, int screenX, int screenY, float dt) {
    if (width <= 0 || height <= 0) return;
    EnsureBuffer(width, height);

    {
        Graphics graphics(memDC);
        graphics.SetSmoothingMode(SmoothingModeAntiAlias);
        graphics.SetTextRenderingHint(TextRenderingHintAntiAlias);
        graphics.Clear(Color(0, 0, 0, 0));

        graphics.ScaleTransform(static_cast<REAL>(width) / static_cast<REAL>(COMBO_W),
                                static_cast<REAL>(height) / static_cast<REAL>(COMBO_H));
        DrawCombo(graphics, COMBO_W, COMBO_H, dt);
    }

    POINT ptDst = { screenX, screenY };
    SIZE sizeDst = { width, height };
    POINT ptSrc = { 0, 0 };
    float op = GetComboOverlayOpacity();
    BYTE alpha = static_cast<BYTE>(op * 255.0f);
    BLENDFUNCTION blend = { AC_SRC_OVER, 0, alpha, AC_SRC_ALPHA };

    UpdateLayeredWindow(hwnd, screenDC, &ptDst, &sizeDst, memDC, &ptSrc, 0, &blend, ULW_ALPHA);
}

void ComboRenderer::DrawNotifications(Graphics& graphics, DWORD now, float centerX, float centerY) {
    std::lock_guard<std::mutex> lock(stateMutex);
    if (activeNotifications.empty()) return;

    float baseY = centerY - 150.0f;
    float spacingY = 55.0f;
    int activeCount = 0;

    for (auto it = activeNotifications.begin(); it != activeNotifications.end(); ) {
        DWORD age = now - it->tick;
        if (age > 4000) {
            it = activeNotifications.erase(it);
            continue;
        }

        float fade = 1.0f;
        float yOffset = 0.0f;

        if (age < 500) {
            fade = age / 500.0f;
            yOffset = 30.0f * (1.0f - fade);
        } else if (age > 3000) {
            fade = 1.0f - ((age - 3000) / 1000.0f);
            yOffset = -20.0f * (1.0f - fade);
        }

        if (fade > 0.0f) {
            float currentY = baseY - (activeCount * spacingY) + yOffset;
            int alpha = static_cast<int>(255.0f * fade);

            std::wstring wText = Utf8ToWide(it->text);
            
            Color valueStart, valueMid, valueEnd;
            float fontSize = 24.0f;
            int particleCount = 0;
            float particleDuration = 0.0f;

            if (it->type == NotificationType::Normal) {
                valueStart = Color(alpha, 255, 215, 0);
                valueMid   = Color(alpha, 255, 140, 0);
                valueEnd   = Color(alpha, 255, 69, 0);
                particleCount = 5; particleDuration = 800.0f;
            } else if (it->type == NotificationType::AbnormalPoison) {
                valueStart = Color(alpha, 50, 205, 50);
                valueMid   = Color(alpha, 34, 139, 34);
                valueEnd   = Color(alpha, 0, 100, 0);
                fontSize = 28.0f; particleCount = 18; particleDuration = 2000.0f;
            } else if (it->type == NotificationType::AbnormalFear) {
                valueStart = Color(alpha, 147, 112, 219);
                valueMid   = Color(alpha, 138, 43, 226);
                valueEnd   = Color(alpha, 75, 0, 130);
                fontSize = 28.0f; particleCount = 20; particleDuration = 2500.0f;
            } else if (it->type == NotificationType::AbnormalBleed) {
                valueStart = Color(alpha, 220, 20, 60);
                valueMid   = Color(alpha, 178, 34, 34);
                valueEnd   = Color(alpha, 139, 0, 0);
                fontSize = 28.0f; particleCount = 25; particleDuration = 2200.0f;
            } else if (it->type == NotificationType::AbnormalStun) {
                valueStart = Color(alpha, 255, 255, 0);
                valueMid   = Color(alpha, 218, 165, 32);
                valueEnd   = Color(alpha, 184, 134, 11);
                fontSize = 30.0f; particleCount = 15; particleDuration = 1200.0f;
            } else if (it->type == NotificationType::AbnormalParalyzed) {
                valueStart = Color(alpha, 0, 255, 255);
                valueMid   = Color(alpha, 0, 191, 255);
                valueEnd   = Color(alpha, 0, 0, 139);
                fontSize = 28.0f; particleCount = 12; particleDuration = 1800.0f;
            } else if (it->type == NotificationType::AbnormalSilenced) {
                valueStart = Color(alpha, 211, 211, 211);
                valueMid   = Color(alpha, 169, 169, 169);
                valueEnd   = Color(alpha, 105, 105, 105);
                fontSize = 26.0f; particleCount = 10; particleDuration = 1500.0f;
            } else if (it->type == NotificationType::AbnormalBlink) {
                valueStart = Color(alpha, 255, 20, 147);
                valueMid   = Color(alpha, 199, 21, 133);
                valueEnd   = Color(alpha, 139, 0, 139);
                fontSize = 28.0f; particleCount = 15; particleDuration = 2000.0f;
            } else if (it->type == NotificationType::AbnormalSleep) {
                valueStart = Color(alpha, 100, 149, 237);
                valueMid   = Color(alpha, 65, 105, 225);
                valueEnd   = Color(alpha, 25, 25, 112);
                fontSize = 28.0f; particleCount = 12; particleDuration = 2200.0f;
            } else if (it->type == NotificationType::AbnormalBlind) {
                valueStart = Color(alpha, 169, 169, 169);
                valueMid   = Color(alpha, 105, 105, 105);
                valueEnd   = Color(alpha, 0, 0, 0);
                fontSize = 28.0f; particleCount = 20; particleDuration = 1800.0f;
            } else if (it->type == NotificationType::AbnormalDisease) {
                valueStart = Color(alpha, 189, 183, 107);
                valueMid   = Color(alpha, 128, 128, 0);
                valueEnd   = Color(alpha, 85, 107, 47);
                fontSize = 28.0f; particleCount = 18; particleDuration = 2000.0f;
            } else if (it->type == NotificationType::AbnormalCurse) {
                valueStart = Color(alpha, 139, 0, 0);
                valueMid   = Color(alpha, 47, 79, 79);
                valueEnd   = Color(alpha, 0, 0, 0);
                fontSize = 28.0f; particleCount = 22; particleDuration = 2500.0f;
            } else if (it->type == NotificationType::AbnormalConfuse) {
                valueStart = Color(alpha, 255, 165, 0);
                valueMid   = Color(alpha, 255, 20, 147);
                valueEnd   = Color(alpha, 148, 0, 211);
                fontSize = 28.0f; particleCount = 20; particleDuration = 2000.0f;
            }

            std::string bannerKey = GetNotificationBannerKey(it->type, it->text);
            Image* bannerImg = GetBanner(bannerKey);
            if (bannerImg) {
                DrawBannerImage(graphics, bannerImg, centerX, currentY, fade, 1.0f);
            } else {
                DrawOutlinedSegmentText(
                    graphics,
                    L"", 
                    wText,
                    centerX,
                    currentY,
                    fontSize + 6.0f,
                    fontSize,
                    FontStyleBoldItalic,
                    alpha,
                    Color(alpha, 255, 255, 255), 
                    valueStart,
                    valueMid,
                    valueEnd,
                    3.0f
                );
            }
            
            if (age < particleDuration) {
                float partAlpha = 1.0f - (age / particleDuration);
                int pA = static_cast<int>(255 * partAlpha);
                if (pA > 0) {
                    SolidBrush partBrush(Color(pA, valueMid.GetR(), valueMid.GetG(), valueMid.GetB()));
                    for (int p = 0; p < particleCount; p++) {
                        unsigned int seed = it->tick + p * 12345;
                        float randX = static_cast<float>(seed % 200) - 100.0f;
                        float randY = static_cast<float>((seed / 2) % 60) - 30.0f;
                        float speed = 10.0f + (seed % 40);
                        
                        float px = centerX + randX;
                        float py = currentY + randY;
                        
                        if (it->type == NotificationType::AbnormalPoison || it->type == NotificationType::AbnormalBleed) {
                            py += (age / 1000.0f) * speed;
                            px += sinf(age / 300.0f + p) * 5.0f;
                        } else if (it->type == NotificationType::AbnormalFear) {
                            px += sinf(age / 200.0f + p) * 20.0f;
                            py += cosf(age / 200.0f + p) * 20.0f;
                        } else if (it->type == NotificationType::AbnormalStun) {
                            float angle = static_cast<float>(p) * 0.4f;
                            px += cosf(angle) * (age / 1000.0f) * 60.0f;
                            py += sinf(angle) * (age / 1000.0f) * 60.0f;
                        } else if (it->type == NotificationType::AbnormalParalyzed) {
                            px += (seed % 2 == 0 ? 1 : -1) * sinf(age / 50.0f) * 4.0f;
                            py += (seed % 3 == 0 ? 1 : -1) * cosf(age / 50.0f) * 4.0f;
                        } else if (it->type == NotificationType::AbnormalBlink) {
                            px -= (age / 1000.0f) * speed * 2.0f;
                            py += sinf(px / 20.0f) * 10.0f;
                        } else if (it->type == NotificationType::AbnormalSleep) {
                            px += sinf(age / 300.0f + p) * 15.0f;
                            py -= (age / 1000.0f) * speed * 0.8f;
                        } else if (it->type == NotificationType::AbnormalBlind) {
                            px += (seed % 2 == 0 ? 1 : -1) * (age / 1000.0f) * speed * 1.5f;
                            py -= (age / 1000.0f) * speed * 0.3f;
                        } else if (it->type == NotificationType::AbnormalDisease) {
                            py += sinf(age / 150.0f + p) * 10.0f;
                            px += cosf(age / 150.0f + p) * 10.0f;
                        } else if (it->type == NotificationType::AbnormalCurse) {
                            py += (age / 1000.0f) * speed * 0.5f;
                            px += sinf(age / 400.0f + p) * 25.0f;
                        } else if (it->type == NotificationType::AbnormalConfuse) {
                            float spiral = age / 200.0f + p;
                            px += cosf(spiral) * (age / 50.0f);
                            py += sinf(spiral) * (age / 50.0f);
                        } else {
                            py -= (age / 1000.0f) * speed * 0.5f;
                        }
                        
                        float pSize = 3.0f + (seed % 5);
                        graphics.FillEllipse(&partBrush, px, py, pSize, pSize);
                    }
                }
            }
        }
        
        activeCount++;
        ++it;
    }
}

void ComboRenderer::DrawOutlinedSegmentText(Graphics& graphics,
                                             const std::wstring& label,
                                             const std::wstring& value,
                                             float centerX,
                                             float y,
                                             float height,
                                             float fontPx,
                                             INT fontStyle,
                                             int alpha,
                                             Color labelColor,
                                             Color valueStart,
                                             Color valueMid,
                                             Color valueEnd,
                                             float outlineWidth) {
    if (!fontFamilyImpact || value.empty()) return;

    Font font(fontFamilyImpact, fontPx, fontStyle, UnitPixel);
    StringFormat nearFormat;
    nearFormat.SetAlignment(StringAlignmentNear);
    nearFormat.SetLineAlignment(StringAlignmentCenter);

    RectF labelMeasure;
    RectF valueMeasure;
    graphics.MeasureString(label.c_str(), -1, &font, PointF(0.0f, 0.0f), &labelMeasure);
    graphics.MeasureString(value.c_str(), -1, &font, PointF(0.0f, 0.0f), &valueMeasure);

    float labelW = (std::max)(1.0f, labelMeasure.Width);
    float valueW = (std::max)(1.0f, valueMeasure.Width);
    float totalW = labelW + valueW;
    float left = centerX - (totalW * 0.5f);

    RectF labelRect(left, y, labelW + 4.0f, height);
    RectF valueRect(left + labelW, y, valueW + 8.0f, height);

    GraphicsPath labelPath;
    labelPath.AddString(label.c_str(), -1, fontFamilyImpact, fontStyle, fontPx, labelRect, &nearFormat);
    GraphicsPath valuePath;
    valuePath.AddString(value.c_str(), -1, fontFamilyImpact, fontStyle, fontPx, valueRect, &nearFormat);

    Pen outline(Color(alpha, 0, 0, 0), outlineWidth);
    graphics.DrawPath(&outline, &labelPath);
    graphics.DrawPath(&outline, &valuePath);

    SolidBrush labelBrush(Color(alpha, labelColor.GetR(), labelColor.GetG(), labelColor.GetB()));
    graphics.FillPath(&labelBrush, &labelPath);

    LinearGradientBrush valueBrush(
        PointF(valueRect.X, valueRect.Y),
        PointF(valueRect.X + valueRect.Width, valueRect.Y + valueRect.Height),
        valueStart,
        valueEnd
    );
    Color colors[] = { valueStart, valueMid, valueEnd };
    REAL positions[] = { 0.0f, 0.48f, 1.0f };
    valueBrush.SetInterpolationColors(colors, positions, 3);
    graphics.FillPath(&valueBrush, &valuePath);
}

void ComboRenderer::DrawCombo(Graphics& graphics, int w, int h, float dt) {
    uint32_t currentTarget = GetTargetObjId();
    uint32_t currentHp = GetPlayerHP();
    DWORD nowTick = GetTickCount();

    {
        std::lock_guard<std::mutex> lock(stateMutex);
        if (lastKnownPlayerHp == 0) {
            lastKnownPlayerHp = currentHp;
        }

        if (currentTarget != 0 && currentTarget != lastKnownTargetObjId) {
            recentHitDamages.clear();
            lastKnownTargetObjId = currentTarget;
            lastKnownPlayerHp = currentHp;
        }

        if (lastKnownPlayerHp != 0 && currentHp < lastKnownPlayerHp) {
            int dmgReceived = static_cast<int>(lastKnownPlayerHp - currentHp);
            if (dmgReceived > 0 && dmgReceived < 20000 && currentHits > 0) {
                recentHitDamages.push_back({ dmgReceived, nowTick, true });
                while (recentHitDamages.size() > 5) {
                    recentHitDamages.erase(recentHitDamages.begin());
                }
            }
        }
        lastKnownPlayerHp = currentHp;
    }

    int snapHits; std::string snapTitle; DWORD snapLastEvent; DWORD snapTimeout;
    bool snapBreaking; DWORD snapBreakStart; int snapFinalHits; std::string snapFinalTitle;
    bool snapRemoveShock; DWORD snapRemoveShockTime;
    int snapTotalDamage;
    std::vector<DamageLine> snapDamageLines;
    {
        std::lock_guard<std::mutex> lock(stateMutex);
        snapHits = currentHits;
        snapTitle = currentTitle;
        snapLastEvent = lastEventTime;
        snapTimeout = timeoutMs;
        snapBreaking = isBreaking;
        snapBreakStart = breakStartTime;
        snapFinalHits = finalHits;
        snapFinalTitle = finalTitle;
        snapRemoveShock = isRemoveShock;
        snapRemoveShockTime = removeShockTime;
        snapTotalDamage = totalDamage;
        snapDamageLines = recentHitDamages;
    }

    DWORD now = GetTickCount();
    float centerX = w * 0.5f;
    float centerY = h * 0.5f;

    if (snapRemoveShock) {
        DWORD age = now - snapRemoveShockTime;
        if (age >= kRemoveShockDurationMs) {
            std::lock_guard<std::mutex> lock(stateMutex);
            isRemoveShock = false;
            snapRemoveShock = false;
        }
    }

    if (snapBreaking) {
        float elapsed = static_cast<float>(now - snapBreakStart);
        
        if (finishGifActive) {
            DrawFinishGif(graphics, centerX, centerY - 40, dt);
        }
        
        if (elapsed < 1500) {
            float alpha = 1.0f - (elapsed / 1500.0f);
            float t01 = elapsed / 1500.0f;
            float pop = 1.0f + (std::max)(0.0f, (0.15f - t01)) * 1.2f;

            std::string bannerKey = GetComboEndBannerKey(snapFinalTitle);
            Image* bImg = GetBanner(bannerKey);
            if (bImg) {
                DrawBannerImage(graphics, bImg, centerX, centerY - 40.0f * pop, alpha, pop);
            } else {
                StringFormat format;
                format.SetAlignment(StringAlignmentCenter);
                format.SetLineAlignment(StringAlignmentCenter);

                std::wstring wTitle = Utf8ToWide(snapFinalTitle.empty() ? std::string("ᴇꜱɢᴏᴛᴀᴅᴏ") : snapFinalTitle);

                GraphicsPath tPath;
                tPath.AddString(wTitle.c_str(), -1, fontFamilyImpact, FontStyleBold, 44.0f * pop,
                                RectF(centerX - 220, centerY - 60 * pop, 440, 120), &format);

                Color tierColor = GetComboTierColor(snapFinalHits);
                Pen outline(Color(static_cast<int>(255 * alpha), 0, 0, 0), 4.0f);
                graphics.DrawPath(&outline, &tPath);
                SolidBrush fill(Color(static_cast<int>(255 * alpha), tierColor.GetR(), tierColor.GetG(), tierColor.GetB()));
                graphics.FillPath(&fill, &tPath);
            }
        } else {
            std::lock_guard<std::mutex> lock(stateMutex);
            isBreaking = false;
            finishGifActive = false;
        }
        return;
    }

    if (snapHits > 0) {
        float timeRatio = 1.0f - static_cast<float>(now - snapLastEvent) / snapTimeout;
        if (timeRatio < 0) timeRatio = 0;

        Color tierColor = GetComboTierColor(snapHits);

        StringFormat format;
        format.SetAlignment(StringAlignmentCenter);
        format.SetLineAlignment(StringAlignmentCenter);

        const float dpsBandH = 22.0f;
        const float gapDpsToBar = 6.0f;
        const float gapHitToDps = 2.0f;
        const float hitBandH = 70.0f;

        float barW = 200.0f;
        float barH = 15.0f;
        float barX = centerX - barW / 2;
        float barY = centerY + 40;

        float dpsBottom = barY - gapDpsToBar;
        float dpsTop = dpsBottom - dpsBandH;
        float hitBottom = dpsTop - gapHitToDps;
        float titleY = barY + barH + 4.0f;

        float pulseScale = 1.0f;
        if (now - snapLastEvent < 200) {
            pulseScale = 1.0f + (1.0f - static_cast<float>(now - snapLastEvent) / 200.0f) * 0.3f;
        }
        float hitRectH = hitBandH * pulseScale;
        float hitTop = hitBottom - hitRectH;
        float hitCenterX = centerX;
        float hitCenterY = hitTop + hitRectH / 2;

        DrawLightning(graphics, centerX, centerY, dt);

        if (sprHitActive) {
            bool still = DrawHitFlash(graphics, hitCenterX, hitCenterY, dt);
            if (!still) sprHitActive = false;
        }

        float skew = 10.0f;

        PointF bgPts[4] = {
            PointF(barX + skew, barY),
            PointF(barX + barW, barY),
            PointF(barX + barW - skew, barY + barH),
            PointF(barX, barY + barH)
        };

        SolidBrush bgBrush(Color(100, 0, 0, 0));
        graphics.FillPolygon(&bgBrush, bgPts, 4);

        float fillW = barW * timeRatio;
        Color barC1 = ShiftColor(tierColor, 80);
        Color barC2 = ShiftColor(tierColor, -60);
        if (fillW > skew) {
            PointF fillPts[4] = {
                PointF(barX + skew, barY),
                PointF(barX + fillW, barY),
                PointF(barX + fillW - skew, barY + barH),
                PointF(barX, barY + barH)
            };

            LinearGradientBrush gradBrush(
                PointF(barX, barY),
                PointF(barX + barW, barY),
                barC1,
                barC2
            );
            Color colors[] = { barC1, tierColor, barC2 };
            REAL positions[] = { 0.0f, 0.5f, 1.0f };
            gradBrush.SetInterpolationColors(colors, positions, 3);
            graphics.FillPolygon(&gradBrush, fillPts, 4);
        }

        Pen border(Color(200, 255, 255, 255), 2.0f);
        graphics.DrawPolygon(&border, bgPts, 4);

        wchar_t hitBuf[32];
        swprintf_s(hitBuf, L"%dₓ", snapHits);

        GraphicsPath hPath;
        hPath.AddString(hitBuf, -1, fontFamilyImpact, FontStyleBold, 48.0f * pulseScale,
                        RectF(centerX - 200, hitTop, 400, hitRectH), &format);
        Pen outline2(Color(255, 0, 0, 0), 4.0f);
        graphics.DrawPath(&outline2, &hPath);
        auto clampColor = [](int v) -> BYTE {
            if (v < 0) return 0;
            if (v > 255) return 255;
            return static_cast<BYTE>(v);
        };
        Color hitLight(tierColor.GetA(),
                       clampColor(static_cast<int>(tierColor.GetR()) + 70),
                       clampColor(static_cast<int>(tierColor.GetG()) + 70),
                       clampColor(static_cast<int>(tierColor.GetB()) + 70));
        Color hitDark(tierColor.GetA(),
                      clampColor(static_cast<int>(tierColor.GetR()) - 80),
                      clampColor(static_cast<int>(tierColor.GetG()) - 80),
                      clampColor(static_cast<int>(tierColor.GetB()) - 80));
        LinearGradientBrush hitBrush(
            PointF(centerX - 180.0f, hitTop),
            PointF(centerX + 180.0f, hitTop + hitRectH),
            hitLight,
            hitDark
        );
        Color hitColors[] = { hitLight, tierColor, hitDark };
        REAL hitPositions[] = { 0.0f, 0.45f, 1.0f };
        hitBrush.SetInterpolationColors(hitColors, hitPositions, 3);
        graphics.FillPath(&hitBrush, &hPath);

        if (spr200wTopActive && spr200wTop && spr200wTopFrameCount > 0) {
            spr200wTopElapsed += dt * 1000.0f;
            float totalMsTop = spr200wTopFrameCount * spr200wTopFrameMs;
            if (spr200wTopElapsed >= totalMsTop) { spr200wTopActive = false; }
            else {
                UINT tf = static_cast<UINT>(spr200wTopElapsed / spr200wTopFrameMs);
                if (tf >= spr200wTopFrameCount) tf = spr200wTopFrameCount - 1;
                spr200wTop->SelectActiveFrame(&spr200wTopDimension, tf);
                float topSz = hitRectH * 1.4f;
                graphics.DrawImage(spr200wTop, hitCenterX - topSz/2, hitCenterY - topSz/2, topSz, topSz);
            }
        }

        if (snapRemoveShock) {
            DrawComboBreakerShock(graphics, hitCenterX, hitCenterY, hitRectH, now, snapRemoveShockTime);
        }

        if (snapTotalDamage > 0) {
            std::string damageStr = FormatNumberWithDots(snapTotalDamage);
            DrawOutlinedSegmentText(
                graphics,
                Utf8ToWide("ᴛᴏᴛᴀʟ: "),
                Utf8ToWide(damageStr),
                centerX,
                dpsTop,
                dpsBandH,
                20.0f,
                FontStyleBold,
                255,
                Color(255, 255, 255, 255),
                Color(255, 155, 255, 120),
                Color(255, 40, 225, 80),
                Color(255, 0, 135, 35),
                2.5f);
        }

        int lineIndex = 0;
        const DWORD damageLineTtlMs = 1800;
        const float baseLineGap = 2.0f;
        const float extraLineGap = 6.0f;
        const float kLineAlpha[] = { 1.0f, 0.80f, 0.70f, 0.40f, 0.20f };
        float yCursor = titleY;
        for (int i = static_cast<int>(snapDamageLines.size()) - 1; i >= 0 && lineIndex < 5; --i) {
            if (snapDamageLines[i].amount <= 0) continue;
            DWORD age = now - snapDamageLines[i].tick;
            if (age > damageLineTtlMs) continue;

            float fade = 1.0f;
            if (age > 1200) fade = 1.0f - (static_cast<float>(age - 1200) / 600.0f);
            if (fade < 0.0f) fade = 0.0f;

            if (lineIndex < 5) fade *= kLineAlpha[lineIndex];

            float fontPx = (std::max)(12.0f, 22.0f - static_cast<float>(lineIndex * 4));
            float gapBefore = (lineIndex == 0) ? 0.0f : (baseLineGap + extraLineGap);
            float lineTop = yCursor + gapBefore;
            yCursor = lineTop + fontPx;

            std::string hitStr = FormatNumberWithDots(snapDamageLines[i].amount);
            int alpha = static_cast<int>(255.0f * fade);
            if (alpha <= 0) { ++lineIndex; continue; }

            bool isReceived = snapDamageLines[i].received;
            if (isReceived) {
                DrawOutlinedSegmentText(
                    graphics,
                    Utf8ToWide("ꜱᴏꜰʀᴇᴜ: "),
                    Utf8ToWide(hitStr),
                    centerX,
                    lineTop,
                    fontPx + 8.0f,
                    fontPx,
                    FontStyleItalic,
                    alpha,
                    Color(255, 255, 180, 100),
                    Color(alpha, 255, 130, 30),
                    Color(alpha, 235, 60, 0),
                    Color(alpha, 160, 20, 0),
                    3.0f);
            } else {
                DrawOutlinedSegmentText(
                    graphics,
                    Utf8ToWide("ᴄᴀᴜꜱᴏᴜ: "),
                    Utf8ToWide(hitStr),
                    centerX,
                    lineTop,
                    fontPx + 8.0f,
                    fontPx,
                    FontStyleItalic,
                    alpha,
                    Color(255, 200, 255, 180),
                    Color(alpha, 80, 230, 120),
                    Color(alpha, 20, 190, 70),
                    Color(alpha, 0, 110, 30),
                    3.0f);
            }
            ++lineIndex;
        }
        return;
    }

    if (snapRemoveShock) {
        DrawComboBreakerShock(graphics, centerX, centerY, 70.0f, now, snapRemoveShockTime);
    }

    DrawNotifications(graphics, now, centerX, centerY);
}

void ComboRenderer::ShowNotification(const std::string& text) {
    std::lock_guard<std::mutex> lock(stateMutex);
    activeNotifications.push_back({ text, GetTickCount(), NotificationType::Normal });
    if (!running) Start();
}

void ComboRenderer::ShowAbnormalState(const std::string& text, NotificationType type) {
    std::lock_guard<std::mutex> lock(stateMutex);
    activeNotifications.push_back({ text, GetTickCount(), type });
    if (!running) Start();
}

int ComboRenderer::GetCurrentHits() {
    std::lock_guard<std::mutex> lock(stateMutex);
    return currentHits;
}

void ComboRenderer::OnDamageReceived(int amount) {
    if (amount <= 0) return;
    std::lock_guard<std::mutex> lock(stateMutex);
    DWORD now = GetTickCount();
    recentHitDamages.push_back({ amount, now, true });
    while (recentHitDamages.size() > 5) {
        recentHitDamages.erase(recentHitDamages.begin());
    }
    if (wakeEvent) SetEvent(wakeEvent);
}

int ComboRenderer::GetCurrentDamage() {
    std::lock_guard<std::mutex> lock(stateMutex);
    return totalDamage;
}

void ComboRenderer::Start() {
    if (running) return;
    if (!wakeEvent) wakeEvent = CreateEventA(nullptr, FALSE, FALSE, nullptr);
    g_wakeEvent = wakeEvent;
    running = true;
    renderThread = std::thread(&ComboRenderer::RenderLoop, this);
}

void ComboRenderer::Stop() {
    running = false;
    if (wakeEvent) SetEvent(wakeEvent);
    if (renderThread.joinable()) renderThread.join();
    if (wakeEvent) {
        CloseHandle(wakeEvent);
        wakeEvent = nullptr;
    }
    g_wakeEvent = nullptr;
}

void ComboRenderer::RequestLayoutRefresh() {
    ClearBarParticles();
    if (wakeEvent) SetEvent(wakeEvent);
}

void ComboRenderer::OnEvent(const std::string& event, int hits, const std::string& title, int hitDamage,
                             int totalDamageValue, int serverTimeoutMs) {
    std::lock_guard<std::mutex> lock(stateMutex);
    DWORD now = GetTickCount();

    uint32_t currentTarget = GetTargetObjId();
    if (currentTarget != 0 && currentTarget != lastKnownTargetObjId) {
        recentHitDamages.clear();
        lastKnownTargetObjId = currentTarget;
        lastKnownPlayerHp = GetPlayerHP();
    }

    if (event == "COMBO_START" || event == "COMBO_UPDATE") {
        if (event == "COMBO_START") {
            flashCycleNextIndex = 0;
            flashCycleActiveSlot = -1;
            flashCycleActive = false;
        }

        currentHits = hits;
        currentTitle = title;
        lastHitDamage = (std::max)(0, hitDamage);
        totalDamage = (std::max)(0, totalDamageValue);
        if (event == "COMBO_START") {
            recentHitDamages.clear();
            lastKnownPlayerHp = 0;
        }
        if (hitDamage > 0) {
            recentHitDamages.push_back({ hitDamage, now, false });
            while (recentHitDamages.size() > 5) {
                recentHitDamages.erase(recentHitDamages.begin());
            }
        }
        timeoutMs = (serverTimeoutMs > 0) ? static_cast<DWORD>(serverTimeoutMs) : ComputeComboTimeoutMs(hits);
        isFirstHit = false;
        
        lastEventTime = now;
        isBreaking = false;

        sprHitElapsed = 0.0f;
        sprHitActive = true;

        if (spr200wTop) { spr200wTopActive = true; spr200wTopElapsed = 0.0f; }

        if (hits > 0 && (hits % 4 == 0) && !flashCycleGifs.empty()) {
            flashCycleActiveSlot = static_cast<int>(flashCycleNextIndex % flashCycleGifs.size());
            flashCycleNextIndex++;
            flashCycleActive = true;
            flashCycleElapsed = 0.0f;
        }

        if (hits > 0 && (hits % 17 == 0) && spr200w2) {
            w2Active = true; w2Elapsed = 0.0f;
        }

        if (hits >= 50) {
            if (!poweredModeActive) { poweredModeActive = true; poweredModeStart = now; }
        } else {
            if (poweredModeActive) { poweredModeActive = false; poweredModeStart = now; }
        }

        if (hits >= 100) {
            if (!darkModeActive) { darkModeActive = true; darkModeStart = now; }
        } else {
            if (darkModeActive) { darkModeActive = false; darkModeStart = now; }
        }
    }
    else if (event == "COMBO_BREAK" || event == "COMBO_FINAL" ||
             event == "COMBO_CC_BREAK" || event == "COMBO_DEATH") {
        if (currentHits > 0) {
            isBreaking = true;
            breakStartTime = now;
            finalHits = currentHits;
            finalTitle = currentTitle;

            finishGifActive = true;
            finishElapsed = 0.0f;
        }
        currentHits = 0;
        currentTitle = "";
        isRemoveShock = false;
        totalDamage = 0;
        lastHitDamage = 0;
        recentHitDamages.clear();
        lastKnownPlayerHp = 0;
        flashCycleActive = false;
        flashCycleActiveSlot = -1;
        flashCycleNextIndex = 0;
        w2Active = false;
        spr200wTopActive = false;
        poweredModeActive = false;
        darkModeActive = false;
        isFirstHit = true;
    }
    else if (event == "COMBO_REMOVE_SHOCK") {
        isRemoveShock = true;
        removeShockTime = now;
    }
    else if (event == "COMBO_RESET") {
        currentHits = 0;
        currentTitle = "";
        finalTitle = "";
        isBreaking = false;
        isRemoveShock = false;
        totalDamage = 0;
        lastHitDamage = 0;
        recentHitDamages.clear();
        lastKnownPlayerHp = 0;
        flashCycleActive = false;
        flashCycleActiveSlot = -1;
        flashCycleNextIndex = 0;
        w2Active = false;
        spr200wTopActive = false;
        finishGifActive = false;
        isFirstHit = true;
    }
    if (wakeEvent) SetEvent(wakeEvent);
}
