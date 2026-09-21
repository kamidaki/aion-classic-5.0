#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>
#include <string>
#include <vector>
#include <cstdint>

namespace BrService {

class UICommon {
public:
    static void InitializeGdiplus();
    static void ShutdownGdiplus();

    static void DrawRoundRectangle(Gdiplus::Graphics& g, Gdiplus::Pen* pen, float x, float y, float w, float h, float radius);
    static void FillRoundRectangle(Gdiplus::Graphics& g, Gdiplus::Brush* brush, float x, float y, float w, float h, float radius);

    static void DrawFibonacciCurve(Gdiplus::Graphics& g, float x, float y, float w, float h, const std::vector<float>& points);
    static void DrawRadarChart4Axis(Gdiplus::Graphics& g, float cx, float cy, float radius,
                                   float crit, float block, float dodge, float resist);
    static void DrawRadarChart(Gdiplus::Graphics& g, float cx, float cy, float radius,
                               float burst, float sustain, float crit, float accuracy, float efficiency);
    static void DrawTargetEmblemDisk(Gdiplus::Graphics& g, float cx, float cy, float radius,
                                     const std::string& rating, const std::string& race, bool isNpc = true);
    static void DrawSkillIconBadge(Gdiplus::Graphics& g, float x, float y, float size, uint32_t skillId, const std::string& skillName);

    static std::wstring FormatNumber(uint64_t val);
    static std::wstring FormatTime(uint32_t totalSecs);

    // Color constants (Aion 2 Palette)
    static const Gdiplus::Color ColGlassBack;
    static const Gdiplus::Color ColGlassHeader;
    static const Gdiplus::Color ColGoldAccent;
    static const Gdiplus::Color ColGoldDim;
    static const Gdiplus::Color ColNeonGreen;
    static const Gdiplus::Color ColTextWhite;
    static const Gdiplus::Color ColTextMuted;
    static const Gdiplus::Color ColBorderSubtle;
    static const Gdiplus::Color ColBarDamage;
};

} // namespace BrService
