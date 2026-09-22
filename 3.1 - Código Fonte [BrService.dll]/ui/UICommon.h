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
    static std::wstring Utf8ToWide(const std::string& utf8Str);

    // Legacy Palette (for PingHud and combat meters)
    static const Gdiplus::Color ColGlassBack;
    static const Gdiplus::Color ColGlassHeader;
    static const Gdiplus::Color ColGoldAccent;
    static const Gdiplus::Color ColGoldDim;
    static const Gdiplus::Color ColNeonGreen;
    static const Gdiplus::Color ColTextWhite;
    static const Gdiplus::Color ColTextMuted;
    static const Gdiplus::Color ColBorderSubtle;
    static const Gdiplus::Color ColBarDamage;

    // Model 3 Light Theme Palette
    static const Gdiplus::Color ColModel3Bg;
    static const Gdiplus::Color ColModel3Card;
    static const Gdiplus::Color ColModel3Border;
    static const Gdiplus::Color ColModel3BorderDark;
    static const Gdiplus::Color ColModel3TextDark;
    static const Gdiplus::Color ColModel3TextMuted;
    static const Gdiplus::Color ColModel3TextLight;
    static const Gdiplus::Color ColModel3Blue;
    static const Gdiplus::Color ColModel3BlueLight;
    static const Gdiplus::Color ColModel3BlueBorder;
    static const Gdiplus::Color ColModel3BlueHover;
    static const Gdiplus::Color ColModel3HpRed;

    // Theme palette variants (for Advanced tab theme selector)
    static const Gdiplus::Color ColThemeDarkBg;       // Dark/Black theme background
    static const Gdiplus::Color ColThemeDarkCard;     // Dark/Black theme card
    static const Gdiplus::Color ColThemeDarkBorder;   // Dark/Black theme border
    static const Gdiplus::Color ColThemeDarkText;     // Dark/Black theme text (white)
    static const Gdiplus::Color ColThemeGrayBg;
    static const Gdiplus::Color ColThemeGrayCard;
    static const Gdiplus::Color ColThemeNavyBg;
    static const Gdiplus::Color ColThemeNavyCard;

    static void DrawDpsSplineChart(Gdiplus::Graphics& g, float x, float y, float w, float h,
                                   const std::vector<float>& points, uint32_t durationSec);
    static void DrawModernSwitch(Gdiplus::Graphics& g, float x, float y, bool active,
                                 const wchar_t* activeText, const wchar_t* inactiveText);
    static void DrawBarChart(Gdiplus::Graphics& g, float x, float y, float w, float h,
                             const std::vector<float>& bars, Gdiplus::Color barColor);
};

} // namespace BrService
