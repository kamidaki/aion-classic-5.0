#pragma once

#ifndef _CCALCUNIT_H_
#define _CCALCUNIT_H_

class CCalcUnit
{
public:
    CCalcUnit();
    virtual ~CCalcUnit();

    // 23 virtual slots matching binary VTable at 0x1801e4bb8
    virtual float EvalFormula(int formulaId, float baseVal, float modVal);
    virtual float CalculateDistance(float x1, float y1, float z1, float x2, float y2, float z2);
    virtual float CalculateDistance2D(float x1, float y1, float x2, float y2);
    virtual float RadianToDegree(float rad);
    virtual float DegreeToRadian(float deg);
    virtual float NormalizeAngle(float angle);
    virtual void  Slot6();
    virtual void  Slot7();
    virtual void  Slot8();
    virtual void  Slot9();
    virtual void  Slot10();
    virtual void  Slot11();
    virtual void  Slot12();
    virtual void  Slot13();
    virtual void  Slot14();
    virtual void  Slot15();
    virtual void  Slot16();
    virtual void  Slot17();
    virtual void  Slot18();
    virtual void  Slot19();
    virtual void  Slot20();
    virtual void  Slot21();
};

#endif // _CCALCUNIT_H_
