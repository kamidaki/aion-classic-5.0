#include "CCheckSystemHardware.h"
#include <windows.h>

CCheckSystemHardware::CCheckSystemHardware()
    : m_nCores(4),
      m_nTotalRAM_MB(8192),
      m_nGPUVRAM_MB(4096),
      m_bIs64Bit(true),
      m_nRecommendedPreset(3)
{
    CheckSystemSpecs();
}

CCheckSystemHardware::~CCheckSystemHardware()
{
}

bool CCheckSystemHardware::CheckSystemSpecs()
{
    SYSTEM_INFO sysInfo;
    GetNativeSystemInfo(&sysInfo);
    m_nCores = static_cast<int>(sysInfo.dwNumberOfProcessors);

    MEMORYSTATUSEX memStatus;
    memStatus.dwLength = sizeof(memStatus);
    if (GlobalMemoryStatusEx(&memStatus))
    {
        m_nTotalRAM_MB = static_cast<int>(memStatus.ullTotalPhys / (1024 * 1024));
    }

    m_bIs64Bit = (sysInfo.wProcessorArchitecture == PROCESSOR_ARCHITECTURE_AMD64);

    // Calculate recommended preset based on hardware
    if (m_nCores >= 8 && m_nTotalRAM_MB >= 16384)
    {
        m_nRecommendedPreset = 4; // High / Ultra
    }
    else if (m_nCores >= 4 && m_nTotalRAM_MB >= 8192)
    {
        m_nRecommendedPreset = 3; // Standard High
    }
    else if (m_nCores >= 2 && m_nTotalRAM_MB >= 4096)
    {
        m_nRecommendedPreset = 2; // Medium
    }
    else
    {
        m_nRecommendedPreset = 1; // Low
    }

    return true;
}

int CCheckSystemHardware::GetCPUCoreCount() const
{
    return m_nCores;
}

int CCheckSystemHardware::GetTotalPhysicalMemoryMB() const
{
    return m_nTotalRAM_MB;
}

int CCheckSystemHardware::GetGPUVRAMMB() const
{
    return m_nGPUVRAM_MB;
}

bool CCheckSystemHardware::Is64BitOS() const
{
    return m_bIs64Bit;
}

int CCheckSystemHardware::GetRecommendedPreset() const
{
    return m_nRecommendedPreset;
}
