#include "UICommon.h"
#include "../core/I18n.h"
#include <cmath>
#include <algorithm>

#pragma comment(lib, "gdiplus.lib")

namespace BrService {

static ULONG_PTR s_gdiplusToken = 0;

// Aion 2 Visual Palette
const Gdiplus::Color UICommon::ColGlassBack(220, 10, 14, 20);     // Sleek dark glass
const Gdiplus::Color UICommon::ColGlassHeader(245, 16, 22, 32);   // Slightly denser header
const Gdiplus::Color UICommon::ColGoldAccent(255, 215, 170, 50);   // Aion 2 refined gold
const Gdiplus::Color UICommon::ColGoldDim(130, 200, 160, 50);      // Translucent gold border
const Gdiplus::Color UICommon::ColNeonGreen(255, 45, 230, 45);     // Neon green for ping (exact match)
const Gdiplus::Color UICommon::ColTextWhite(255, 245, 245, 248);   // Pure crisp text
const Gdiplus::Color UICommon::ColTextMuted(255, 150, 155, 165);   // Secondary label text
const Gdiplus::Color UICommon::ColBorderSubtle(90, 180, 190, 210); // Glass rim shine
const Gdiplus::Color UICommon::ColBarDamage(255, 210, 60, 65);     // Crimson/amber damage bar

void UICommon::InitializeGdiplus() {
    if (s_gdiplusToken == 0) {
        Gdiplus::GdiplusStartupInput gsi;
        Gdiplus::GdiplusStartup(&s_gdiplusToken, &gsi, nullptr);
    }
}

void UICommon::ShutdownGdiplus() {
    if (s_gdiplusToken != 0) {
        Gdiplus::GdiplusShutdown(s_gdiplusToken);
        s_gdiplusToken = 0;
    }
}

void UICommon::DrawRoundRectangle(Gdiplus::Graphics& g, Gdiplus::Pen* pen, float x, float y, float w, float h, float radius) {
    if (radius <= 0.0f) {
        g.DrawRectangle(pen, x, y, w, h);
        return;
    }
    float d = radius * 2.0f;
    Gdiplus::GraphicsPath path;
    path.AddArc(x, y, d, d, 180, 90);
    path.AddArc(x + w - d, y, d, d, 270, 90);
    path.AddArc(x + w - d, y + h - d, d, d, 0, 90);
    path.AddArc(x, y + h - d, d, d, 90, 90);
    path.CloseFigure();
    g.DrawPath(pen, &path);
}

void UICommon::FillRoundRectangle(Gdiplus::Graphics& g, Gdiplus::Brush* brush, float x, float y, float w, float h, float radius) {
    if (radius <= 0.0f) {
        g.FillRectangle(brush, x, y, w, h);
        return;
    }
    float d = radius * 2.0f;
    Gdiplus::GraphicsPath path;
    path.AddArc(x, y, d, d, 180, 90);
    path.AddArc(x + w - d, y, d, d, 270, 90);
    path.AddArc(x + w - d, y + h - d, d, d, 0, 90);
    path.AddArc(x, y + h - d, d, d, 90, 90);
    path.CloseFigure();
    g.FillPath(brush, &path);
}

void UICommon::DrawFibonacciCurve(Gdiplus::Graphics& g, float x, float y, float w, float h, const std::vector<float>& points) {
    if (points.size() < 2) return;

    float maxVal = 1.0f;
    for (float v : points) if (v > maxVal) maxVal = v;

    std::vector<Gdiplus::PointF> ptArray;
    ptArray.reserve(points.size());

    float stepX = w / (points.size() - 1);
    for (size_t i = 0; i < points.size(); ++i) {
        float normY = points[i] / maxVal;
        float py = y + h - (normY * (h - 8.0f)) - 4.0f;
        ptArray.push_back(Gdiplus::PointF(x + i * stepX, py));
    }

    // Gradient fill under the curve
    Gdiplus::GraphicsPath areaPath;
    areaPath.AddLines(ptArray.data(), (INT)ptArray.size());
    areaPath.AddLine(x + w, y + h, x, y + h);
    areaPath.CloseFigure();

    Gdiplus::LinearGradientBrush areaBrush(
        Gdiplus::PointF(x, y), Gdiplus::PointF(x, y + h),
        Gdiplus::Color(65, 215, 170, 50),
        Gdiplus::Color(5, 10, 14, 20)
    );
    g.FillPath(&areaBrush, &areaPath);

    // Glowing Fibonacci line
    Gdiplus::Pen curvePen(ColGoldAccent, 1.8f);
    g.DrawCurve(&curvePen, ptArray.data(), (INT)ptArray.size(), 0.5f);
}

void UICommon::DrawRadarChart4Axis(Gdiplus::Graphics& g, float cx, float cy, float radius,
                                   float crit, float block, float dodge, float resist) {
    float values[4] = {
        std::clamp(crit / 100.0f, 0.12f, 1.0f),    // Top: Crítico
        std::clamp(block / 100.0f, 0.12f, 1.0f),   // Right: Bloqueio
        std::clamp(dodge / 100.0f, 0.12f, 1.0f),   // Bottom: Esquiva
        std::clamp(resist / 100.0f, 0.12f, 1.0f)   // Left: Resistência
    };

    const wchar_t* labels[4] = {
        I18n::RadarCrit(),
        I18n::RadarBlock(),
        I18n::RadarDodge(),
        I18n::RadarResist()
    };

    // Draw concentric diamond rings (3 levels: 33%, 66%, 100%)
    Gdiplus::Pen webPen(Gdiplus::Color(45, 180, 190, 210), 1.0f);
    for (int ring = 1; ring <= 3; ++ring) {
        float r = radius * (float)ring / 3.0f;
        Gdiplus::PointF ringPts[4] = {
            Gdiplus::PointF(cx, cy - r), // Top
            Gdiplus::PointF(cx + r, cy), // Right
            Gdiplus::PointF(cx, cy + r), // Bottom
            Gdiplus::PointF(cx - r, cy)  // Left
        };
        g.DrawPolygon(&webPen, ringPts, 4);
    }

    // Draw 4 cardinal axis lines and localized labels
    Gdiplus::Font font(L"Segoe UI", 7.5f, Gdiplus::FontStyleBold);
    Gdiplus::SolidBrush labelBrush(ColTextMuted);
    Gdiplus::StringFormat fmt;
    fmt.SetAlignment(Gdiplus::StringAlignmentCenter);
    fmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);

    float angles[4] = { -1.5707963f, 0.0f, 1.5707963f, 3.1415926f };
    for (int i = 0; i < 4; ++i) {
        float a = angles[i];
        float lx = cx + radius * cosf(a);
        float ly = cy + radius * sinf(a);
        g.DrawLine(&webPen, cx, cy, lx, ly);

        float textR = radius + 13.0f;
        Gdiplus::RectF rect(cx + textR * cosf(a) - 28, cy + textR * sinf(a) - 8, 56, 16);
        g.DrawString(labels[i], -1, &font, rect, &fmt, &labelBrush);
    }

    // 4-Point Polygon for current player/target combat metrics
    Gdiplus::PointF valPts[4] = {
        Gdiplus::PointF(cx, cy - radius * values[0]),
        Gdiplus::PointF(cx + radius * values[1], cy),
        Gdiplus::PointF(cx, cy + radius * values[2]),
        Gdiplus::PointF(cx - radius * values[3], cy)
    };

    Gdiplus::SolidBrush polyBrush(Gdiplus::Color(80, 215, 170, 50));
    g.FillPolygon(&polyBrush, valPts, 4);

    Gdiplus::Pen polyPen(ColGoldAccent, 1.8f);
    g.DrawPolygon(&polyPen, valPts, 4);

    // Subtle corner markers
    Gdiplus::SolidBrush dotBrush(ColTextWhite);
    for (int i = 0; i < 4; ++i) {
        g.FillEllipse(&dotBrush, valPts[i].X - 2.0f, valPts[i].Y - 2.0f, 4.0f, 4.0f);
    }
}

void UICommon::DrawRadarChart(Gdiplus::Graphics& g, float cx, float cy, float radius,
                              float burst, float sustain, float crit, float accuracy, float efficiency) {
    // Forward to 4-axis (Crítico, Bloqueio, Esquiva, Resistência)
    DrawRadarChart4Axis(g, cx, cy, radius, crit, burst, sustain, efficiency);
}

void UICommon::DrawTargetEmblemDisk(Gdiplus::Graphics& g, float cx, float cy, float radius,
                                   const std::string& rating, const std::string& race, bool isNpc) {
    // 1. Determine palette based on NPC Rating or Player Race
    Gdiplus::Color ringOuterCol = Gdiplus::Color(255, 140, 150, 165); // Normal NPC / Slate
    Gdiplus::Color ringInnerCol = Gdiplus::Color(255, 70, 80, 95);
    Gdiplus::Color bgCenterCol  = Gdiplus::Color(240, 25, 30, 40);

    if (isNpc) {
        if (rating == "LEGENDARY") {
            ringOuterCol = Gdiplus::Color(255, 235, 60, 75);  // Crimson Dragon
            ringInnerCol = Gdiplus::Color(255, 255, 195, 50);  // Gold Core
            bgCenterCol  = Gdiplus::Color(255, 45, 12, 18);
        } else if (rating == "HERO") {
            ringOuterCol = Gdiplus::Color(255, 255, 195, 50);  // Gold Sunburst
            ringInnerCol = Gdiplus::Color(255, 220, 140, 30);
            bgCenterCol  = Gdiplus::Color(255, 40, 30, 15);
        } else if (rating == "ELITE") {
            ringOuterCol = Gdiplus::Color(255, 80, 175, 255);  // Silver Blue
            ringInnerCol = Gdiplus::Color(255, 140, 210, 255);
            bgCenterCol  = Gdiplus::Color(255, 20, 35, 55);
        }
    } else {
        if (race == "ELYOS") {
            ringOuterCol = Gdiplus::Color(255, 255, 225, 110); // Seraphic Gold
            ringInnerCol = Gdiplus::Color(255, 220, 185, 75);
            bgCenterCol  = Gdiplus::Color(255, 38, 34, 20);
        } else if (race == "ASMODIANS") {
            ringOuterCol = Gdiplus::Color(255, 190, 75, 225);  // Shadow Violet
            ringInnerCol = Gdiplus::Color(255, 130, 45, 170);
            bgCenterCol  = Gdiplus::Color(255, 32, 16, 40);
        }
    }

    // 2. Outer Ornate Border Disc
    float d = radius * 2.0f;
    Gdiplus::SolidBrush bgBrush(bgCenterCol);
    g.FillEllipse(&bgBrush, cx - radius, cy - radius, d, d);

    // 3. Dual Concentric Rims with metallic shading
    Gdiplus::Pen rimPen(ringOuterCol, 1.8f);
    g.DrawEllipse(&rimPen, cx - radius, cy - radius, d, d);

    Gdiplus::Pen innerPen(ringInnerCol, 1.0f);
    g.DrawEllipse(&innerPen, cx - radius + 2.0f, cy - radius + 2.0f, d - 4.0f, d - 4.0f);

    // 4. Subtle cardinal ornamental notches on disk perimeter
    Gdiplus::Pen notchPen(ringOuterCol, 1.4f);
    g.DrawLine(&notchPen, cx, cy - radius - 1.0f, cx, cy - radius + 3.0f);
    g.DrawLine(&notchPen, cx + radius - 3.0f, cy, cx + radius + 1.0f, cy);
    g.DrawLine(&notchPen, cx, cy + radius - 3.0f, cx, cy + radius + 1.0f);
    g.DrawLine(&notchPen, cx - radius - 1.0f, cy, cx - radius + 3.0f, cy);

    // 5. Stylized Central Emblem Rune
    Gdiplus::SolidBrush runeBrush(ringOuterCol);
    if (rating == "LEGENDARY" || rating == "HERO") {
        // Star / Diamond Rune
        Gdiplus::PointF pts[4] = {
            Gdiplus::PointF(cx, cy - radius * 0.55f),
            Gdiplus::PointF(cx + radius * 0.55f, cy),
            Gdiplus::PointF(cx, cy + radius * 0.55f),
            Gdiplus::PointF(cx - radius * 0.55f, cy)
        };
        g.FillPolygon(&runeBrush, pts, 4);
    } else {
        // Circular Rune Core
        g.FillEllipse(&runeBrush, cx - 2.5f, cy - 2.5f, 5.0f, 5.0f);
    }
}

void UICommon::DrawSkillIconBadge(Gdiplus::Graphics& g, float x, float y, float size, uint32_t skillId, const std::string& skillName) {
    // Dark glass tile
    Gdiplus::SolidBrush tileBg(Gdiplus::Color(220, 24, 28, 36));
    FillRoundRectangle(g, &tileBg, x, y, size, size, 3.0f);

    // Dynamic border color based on skillId or damage type
    uint32_t hash = skillId ^ 0x5F3759DF;
    BYTE r = 120 + (BYTE)(hash % 120);
    BYTE gCol = 140 + (BYTE)((hash >> 8) % 100);
    BYTE b = 180 + (BYTE)((hash >> 16) % 75);

    Gdiplus::Pen borderPen(Gdiplus::Color(220, r, gCol, b), 1.0f);
    DrawRoundRectangle(g, &borderPen, x, y, size, size, 3.0f);

    // Inner skill initial letter or rune glyph
    wchar_t initial = L'⚔';
    if (!skillName.empty()) {
        initial = (wchar_t)towupper((wchar_t)skillName[0]);
    }
    wchar_t initStr[2] = { initial, L'\0' };

    Gdiplus::Font font(L"Segoe UI", size * 0.45f, Gdiplus::FontStyleBold);
    Gdiplus::SolidBrush textBrush(Gdiplus::Color(240, r, gCol, b));
    Gdiplus::StringFormat fmt;
    fmt.SetAlignment(Gdiplus::StringAlignmentCenter);
    fmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);

    Gdiplus::RectF rect(x, y, size, size);
    g.DrawString(initStr, 1, &font, rect, &fmt, &textBrush);
}

std::wstring UICommon::FormatNumber(uint64_t val) {
    wchar_t temp[64];
    swprintf_s(temp, L"%llu", val);
    int len = (int)wcslen(temp);
    std::wstring out;
    for (int i = 0; i < len; i++) {
        if (i > 0 && (len - i) % 3 == 0) {
            out.push_back(L',');
        }
        out.push_back(temp[i]);
    }
    return out;
}

std::wstring UICommon::FormatTime(uint32_t totalSecs) {
    uint32_t mins = totalSecs / 60;
    uint32_t secs = totalSecs % 60;
    wchar_t buf[32];
    swprintf_s(buf, L"%02u:%02u", mins, secs);
    return std::wstring(buf);
}

} // namespace BrService
