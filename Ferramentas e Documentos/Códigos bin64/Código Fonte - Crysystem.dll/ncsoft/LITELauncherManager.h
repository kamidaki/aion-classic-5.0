#pragma once

#ifndef _LITELAUNCHERMANAGER_H_
#define _LITELAUNCHERMANAGER_H_

class LITELauncherManager
{
public:
    LITELauncherManager();
    virtual ~LITELauncherManager();

    bool Init();
    void Shutdown();
    bool IsLaunchedFromLauncher() const;
    const char* GetLauncherToken() const;
    void SetLauncherToken(const char* token);

private:
    bool m_bLaunchedFromLauncher;
    char m_szToken[256];
};

#endif // _LITELAUNCHERMANAGER_H_
