#include "UICommon.h"
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

void UICommon::DrawRadarChart(Gdiplus::Graphics& g, float cx, float cy, float radius,
                             float burst, float sustain, float crit, float accuracy, float efficiency) {
    float values[5] = {
        std::clamp(burst / 100.0f, 0.1f, 1.0f),
        std::clamp(sustain / 100.0f, 0.1f, 1.0f),
        std::clamp(crit / 100.0f, 0.1f, 1.0f),
        std::clamp(accuracy / 100.0f, 0.1f, 1.0f),
        std::clamp(efficiency / 100.0f, 0.1f, 1.0f)
    };
    const wchar_t* labels[5] = { L"BURST", L"SUSTAIN", L"CRIT", L"PREC", L"EFIC" };

    // Draw concentric web rings
    Gdiplus::Pen webPen(Gdiplus::Color(45, 180, 190, 210), 1.0f);
    for (int ring = 1; ring <= 3; ++ring) {
        float r = radius * (float)ring / 3.0f;
        Gdiplus::PointF ringPts[5];
        for (int i = 0; i < 5; ++i) {
            float a = -1.5707963f + i * (6.2831853f / 5.0f);
            ringPts[i] = Gdiplus::PointF(cx + r * cosf(a), cy + r * sinf(a));
        }
        g.DrawPolygon(&webPen, ringPts, 5);
    }

    // Draw axis lines and labels
    Gdiplus::Font font(L"Segoe UI", 7.5f, Gdiplus::FontStyleBold);
    Gdiplus::SolidBrush labelBrush(ColTextMuted);
    Gdiplus::StringFormat fmt;
    fmt.SetAlignment(Gdiplus::StringAlignmentCenter);
    fmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);

    for (int i = 0; i < 5; ++i) {
        float a = -1.5707963f + i * (6.2831853f / 5.0f);
        float lx = cx + radius * cosf(a);
        float ly = cy + radius * sinf(a);
        g.DrawLine(&webPen, cx, cy, lx, ly);

        float textR = radius + 12.0f;
        Gdiplus::RectF rect(cx + textR * cosf(a) - 24, cy + textR * sinf(a) - 8, 48, 16);
        g.DrawString(labels[i], -1, &font, rect, &fmt, &labelBrush);
    }

    // Polygon for current metrics
    Gdiplus::PointF valPts[5];
    for (int i = 0; i < 5; ++i) {
        float a = -1.5707963f + i * (6.2831853f / 5.0f);
        float r = radius * values[i];
        valPts[i] = Gdiplus::PointF(cx + r * cosf(a), cy + r * sinf(a));
    }

    Gdiplus::SolidBrush polyBrush(Gdiplus::Color(80, 215, 170, 50));
    g.FillPolygon(&polyBrush, valPts, 5);

    Gdiplus::Pen polyPen(ColGoldAccent, 1.8f);
    g.DrawPolygon(&polyPen, valPts, 5);
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
