#pragma once
#include "AiCharState.h"
#include <string>

// RTTI .?AVCCalcUnit@@
class CCalcUnit {
public:
    CCalcUnit();
    virtual ~CCalcUnit();
    virtual const char* GetClassName() const { return "CCalcUnit"; }
};

// RTTI .?AVEventHandleUnit@@
class EventHandleUnit {
public:
    EventHandleUnit();
    virtual ~EventHandleUnit();
    virtual const char* GetClassName() const { return "EventHandleUnit"; }
};

// RTTI .?AVFindHelperFlock@@
class FindHelperFlock {
public:
    FindHelperFlock();
    virtual ~FindHelperFlock();
    virtual const char* GetClassName() const { return "FindHelperFlock"; }
};

// RTTI .?AVFindHelperUnit@@
class FindHelperUnit {
public:
    FindHelperUnit();
    virtual ~FindHelperUnit();
    virtual const char* GetClassName() const { return "FindHelperUnit"; }
};

// RTTI .?AVFishFlock@@
class FishFlock {
public:
    FishFlock();
    virtual ~FishFlock();
    virtual const char* GetClassName() const { return "FishFlock"; }
};

// RTTI .?AVFishUnit@@
class FishUnit {
public:
    FishUnit();
    virtual ~FishUnit();
    virtual const char* GetClassName() const { return "FishUnit"; }
};

// RTTI .?AVFlockObject@@
class FlockObject {
public:
    FlockObject();
    virtual ~FlockObject();
    virtual const char* GetClassName() const { return "FlockObject"; }
};

void RegisterAllAiStatesExt();