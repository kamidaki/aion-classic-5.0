#pragma once

#ifndef _IGAMEOPTIONS_H_
#define _IGAMEOPTIONS_H_

struct IGameOptions
{
    virtual bool Init() = 0;
    virtual void Shutdown() = 0;
    virtual void SetPreset(int presetLevel) = 0;
    virtual int  GetPreset() const = 0;
    virtual void ApplyOptions() = 0;
    virtual void SaveOptions() = 0;
    virtual void LoadOptions() = 0;
    virtual void ResetToDefaults() = 0;

    virtual void SetGraphicOption(const char* name, int value) = 0;
    virtual int  GetGraphicOption(const char* name) const = 0;
    virtual void SetGraphicOptionFloat(const char* name, float value) = 0;
    virtual float GetGraphicOptionFloat(const char* name) const = 0;

    virtual void SetResolution(int width, int height, int bpp, int refresh) = 0;
    virtual void GetResolution(int& width, int& height, int& bpp, int& refresh) const = 0;
    virtual void SetFullscreen(bool bFullscreen) = 0;
    virtual bool IsFullscreen() const = 0;

    virtual void SetNCPingEnabled(bool bEnable) = 0;
    virtual bool IsNCPingEnabled() const = 0;

    virtual void SetMRTEnabled(bool bEnable) = 0;
    virtual bool IsMRTEnabled() const = 0;

    virtual ~IGameOptions() {}
};

#endif // _IGAMEOPTIONS_H_
