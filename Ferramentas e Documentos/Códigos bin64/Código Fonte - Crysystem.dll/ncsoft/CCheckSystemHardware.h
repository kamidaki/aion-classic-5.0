#pragma once

#ifndef _CCHECKSYSTEMHARDWARE_H_
#define _CCHECKSYSTEMHARDWARE_H_

class CCheckSystemHardware
{
public:
    CCheckSystemHardware();
    virtual ~CCheckSystemHardware();

    // 7 virtual slots matching binary VTable at 0x180201f18
    virtual bool CheckSystemSpecs();
    virtual int  GetCPUCoreCount() const;
    virtual int  GetTotalPhysicalMemoryMB() const;
    virtual int  GetGPUVRAMMB() const;
    virtual bool Is64BitOS() const;
    virtual int  GetRecommendedPreset() const;

private:
    int  m_nCores;
    int  m_nTotalRAM_MB;
    int  m_nGPUVRAM_MB;
    bool m_bIs64Bit;
    int  m_nRecommendedPreset;
};

#endif // _CCHECKSYSTEMHARDWARE_H_
