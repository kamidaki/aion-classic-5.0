#include "GameFixedFrame.h"

GameFixedFrame::GameFixedFrame()
    : m_nTargetFPS(60),
      m_bFixedFrameEnabled(true),
      m_nThrottleMode(0),
      m_nMaxBackgroundFPS(30),
      m_fFrameTimeDelta(1.0f / 60.0f)
{
    QueryPerformanceFrequency(&m_llFrequency);
    QueryPerformanceCounter(&m_llLastTick);
}

GameFixedFrame::~GameFixedFrame()
{
}

int GameFixedFrame::GetTargetFPS()
{
    return m_nTargetFPS;
}

void GameFixedFrame::SetTargetFPS(int fps)
{
    if (fps < 15) fps = 15;
    if (fps > 300) fps = 300;
    m_nTargetFPS = fps;
    m_fFrameTimeDelta = 1.0f / static_cast<float>(fps);
}

void GameFixedFrame::EnableFixedFrame(bool bEnable)
{
    m_bFixedFrameEnabled = bEnable;
}

void GameFixedFrame::SetFrameTimeDelta(float delta)
{
    if (delta > 0.0001f && delta < 1.0f)
    {
        m_fFrameTimeDelta = delta;
        m_nTargetFPS = static_cast<int>(1.0f / delta);
    }
}

float GameFixedFrame::GetFrameTimeDelta()
{
    return m_fFrameTimeDelta;
}

void GameFixedFrame::SetThrottleMode(int mode)
{
    if (mode >= 0 && mode <= 2)
    {
        m_nThrottleMode = mode;
    }
}

int GameFixedFrame::GetThrottleMode()
{
    return m_nThrottleMode;
}

void GameFixedFrame::UpdateFrameTiming(float curTime)
{
    (void)curTime;
    QueryPerformanceCounter(&m_llLastTick);
}

void GameFixedFrame::SetMaxBackgroundFPS(int fps)
{
    if (fps < 5) fps = 5;
    if (fps > 120) fps = 120;
    m_nMaxBackgroundFPS = fps;
}

void GameFixedFrame::BeginFrameWait()
{
    if (!m_bFixedFrameEnabled || m_nTargetFPS <= 0)
        return;

    LARGE_INTEGER curTick;
    QueryPerformanceCounter(&curTick);

    double elapsed = static_cast<double>(curTick.QuadPart - m_llLastTick.QuadPart) / static_cast<double>(m_llFrequency.QuadPart);
    double targetDuration = 1.0 / static_cast<double>(m_nTargetFPS);

    if (elapsed < targetDuration)
    {
        double waitSec = targetDuration - elapsed;
        DWORD waitMs = static_cast<DWORD>(waitSec * 1000.0);
        if (waitMs > 1)
        {
            Sleep(waitMs - 1);
        }
        do
        {
            QueryPerformanceCounter(&curTick);
            elapsed = static_cast<double>(curTick.QuadPart - m_llLastTick.QuadPart) / static_cast<double>(m_llFrequency.QuadPart);
        } while (elapsed < targetDuration);
    }

    m_llLastTick = curTick;
}
