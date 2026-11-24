#pragma once

#ifndef _IGAMEFIXEDFRAME_H_
#define _IGAMEFIXEDFRAME_H_

struct IGameFixedFrame
{
    virtual int   GetTargetFPS() = 0;
    virtual void  SetTargetFPS(int fps) = 0;
    virtual void  EnableFixedFrame(bool bEnable) = 0;
    virtual void  SetFrameTimeDelta(float delta) = 0;
    virtual float GetFrameTimeDelta() = 0;
    virtual void  SetThrottleMode(int mode) = 0;
    virtual int   GetThrottleMode() = 0;
    virtual void  UpdateFrameTiming(float curTime) = 0;
    virtual void  SetMaxBackgroundFPS(int fps) = 0;
    virtual void  BeginFrameWait() = 0;
    virtual ~IGameFixedFrame() {}
};

#endif // _IGAMEFIXEDFRAME_H_
