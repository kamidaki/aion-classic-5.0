#include "CCalcUnit.h"
#include <cmath>

CCalcUnit::CCalcUnit()
{
}

CCalcUnit::~CCalcUnit()
{
}

float CCalcUnit::EvalFormula(int formulaId, float baseVal, float modVal)
{
    switch (formulaId)
    {
    case 1: // Additive
        return baseVal + modVal;
    case 2: // Multiplicative percentage
        return baseVal * (1.0f + modVal * 0.01f);
    case 3: // Combat damage mitigation
        if (modVal > 0.0f)
            return baseVal * (1000.0f / (1000.0f + modVal));
        return baseVal;
    default:
        return baseVal;
    }
}

float CCalcUnit::CalculateDistance(float x1, float y1, float z1, float x2, float y2, float z2)
{
    float dx = x2 - x1;
    float dy = y2 - y1;
    float dz = z2 - z1;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

float CCalcUnit::CalculateDistance2D(float x1, float y1, float x2, float y2)
{
    float dx = x2 - x1;
    float dy = y2 - y1;
    return std::sqrt(dx * dx + dy * dy);
}

float CCalcUnit::RadianToDegree(float rad)
{
    return rad * (180.0f / 3.14159265358979323846f);
}

float CCalcUnit::DegreeToRadian(float deg)
{
    return deg * (3.14159265358979323846f / 180.0f);
}

float CCalcUnit::NormalizeAngle(float angle)
{
    while (angle < 0.0f) angle += 360.0f;
    while (angle >= 360.0f) angle -= 360.0f;
    return angle;
}

void CCalcUnit::Slot6() {}
void CCalcUnit::Slot7() {}
void CCalcUnit::Slot8() {}
void CCalcUnit::Slot9() {}
void CCalcUnit::Slot10() {}
void CCalcUnit::Slot11() {}
void CCalcUnit::Slot12() {}
void CCalcUnit::Slot13() {}
void CCalcUnit::Slot14() {}
void CCalcUnit::Slot15() {}
void CCalcUnit::Slot16() {}
void CCalcUnit::Slot17() {}
void CCalcUnit::Slot18() {}
void CCalcUnit::Slot19() {}
void CCalcUnit::Slot20() {}
void CCalcUnit::Slot21() {}
