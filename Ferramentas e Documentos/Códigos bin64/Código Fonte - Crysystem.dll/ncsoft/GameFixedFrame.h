#pragma once

#ifndef _GAMEFIXEDFRAME_H_
#define _GAMEFIXEDFRAME_H_

#include "IGameFixedFrame.h"
#include <windows.h>

class GameFixedFrame : public IGameFixedFrame
{
public:
    GameFixedFrame();
    virtual ~GameFixedFrame();

    // 11 virtual slots matching binary VTable at 0x1801e33b8
    virtual int   GetTargetFPS() override;
    virtual void  SetTargetFPS(int fps) override;
    virtual void  EnableFixedFrame(bool bEnable) override;
    virtual void  SetFrameTimeDelta(float delta) override;
    virtual float GetFrameTimeDelta() override;
    virtual void  SetThrottleMode(int mode) override;
    virtual int   GetThrottleMode() override;
    virtual void  UpdateFrameTiming(float curTime) override;
    virtual void  SetMaxBackgroundFPS(int fps) override;
    virtual void  BeginFrameWait() override;

private:
    int   m_nTargetFPS;         // +0x08
    bool  m_bFixedFrameEnabled; // +0x0C
    int   m_nThrottleMode;      // +0x14
    int   m_nMaxBackgroundFPS;  // +0x18
    float m_fFrameTimeDelta;    // +0x24
    LARGE_INTEGER m_llLastTick; // +0x28
    LARGE_INTEGER m_llFrequency;// +0x30
};

#endif // _GAMEFIXEDFRAME_H_
