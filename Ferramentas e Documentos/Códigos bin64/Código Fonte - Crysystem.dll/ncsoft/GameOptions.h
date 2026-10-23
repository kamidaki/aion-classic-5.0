#pragma once

#ifndef _GAMEOPTIONS_H_
#define _GAMEOPTIONS_H_

#include "IGameOptions.h"
#include <map>
#include <string>

class GameOptions : public IGameOptions
{
public:
    GameOptions();
    virtual ~GameOptions();

    // Core IGameOptions virtual slots
    virtual bool Init() override;
    virtual void Shutdown() override;
    virtual void SetPreset(int presetLevel) override;
    virtual int  GetPreset() const override;
    virtual void ApplyOptions() override;
    virtual void SaveOptions() override;
    virtual void LoadOptions() override;
    virtual void ResetToDefaults() override;

    virtual void SetGraphicOption(const char* name, int value) override;
    virtual int  GetGraphicOption(const char* name) const override;
    virtual void SetGraphicOptionFloat(const char* name, float value) override;
    virtual float GetGraphicOptionFloat(const char* name) const override;

    virtual void SetResolution(int width, int height, int bpp, int refresh) override;
    virtual void GetResolution(int& width, int& height, int& bpp, int& refresh) const override;
    virtual void SetFullscreen(bool bFullscreen) override;
    virtual bool IsFullscreen() const override;

    virtual void SetNCPingEnabled(bool bEnable) override;
    virtual bool IsNCPingEnabled() const override;

    virtual void SetMRTEnabled(bool bEnable) override;
    virtual bool IsMRTEnabled() const override;

    // Additional virtual slots matching 78 total slots in GameOptions VTable
    virtual void Slot20();
    virtual void Slot21();
    virtual void Slot22();
    virtual void Slot23();
    virtual void Slot24();
    virtual void Slot25();
    virtual void Slot26();
    virtual void Slot27();
    virtual void Slot28();
    virtual void Slot29();
    virtual void Slot30();
    virtual void Slot31();
    virtual void Slot32();
    virtual void Slot33();
    virtual void Slot34();
    virtual void Slot35();
    virtual void Slot36();
    virtual void Slot37();
    virtual void Slot38();
    virtual void Slot39();
    virtual void Slot40();
    virtual void Slot41();
    virtual void Slot42();
    virtual void Slot43();
    virtual void Slot44();
    virtual void Slot45();
    virtual void Slot46();
    virtual void Slot47();
    virtual void Slot48();
    virtual void Slot49();
    virtual void Slot50();
    virtual void Slot51();
    virtual void Slot52();
    virtual void Slot53();
    virtual void Slot54();
    virtual void Slot55();
    virtual void Slot56();
    virtual void Slot57();
    virtual void Slot58();
    virtual void Slot59();
    virtual void Slot60();
    virtual void Slot61();
    virtual void Slot62();
    virtual void Slot63();
    virtual void Slot64();
    virtual void Slot65();
    virtual void Slot66();
    virtual void Slot67();
    virtual void Slot68();
    virtual void Slot69();
    virtual void Slot70();
    virtual void Slot71();
    virtual void Slot72();
    virtual void Slot73();
    virtual void Slot74();
    virtual void Slot75();
    virtual void Slot76();
    virtual void Slot77();

private:
    int   m_nPreset;
    int   m_nWidth;
    int   m_nHeight;
    int   m_nBPP;
    int   m_nRefresh;
    bool  m_bFullscreen;
    bool  m_bNCPing;
    bool  m_bMRT;
    std::map<std::string, int>   m_intOptions;
    std::map<std::string, float> m_floatOptions;
};

#endif // _GAMEOPTIONS_H_
