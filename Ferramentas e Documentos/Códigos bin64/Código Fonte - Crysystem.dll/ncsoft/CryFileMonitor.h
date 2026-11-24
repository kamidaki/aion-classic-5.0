#pragma once

#ifndef _CRYFILEMONITOR_H_
#define _CRYFILEMONITOR_H_

#include <windows.h>
#include <string>
#include <vector>

class FileSystemWatcher
{
public:
    FileSystemWatcher();
    virtual ~FileSystemWatcher();

    // 3 virtual slots matching binary VTable at 0x180200d58
    virtual bool StartWatching(const char* dirPath);
    virtual void StopWatching();
    virtual void OnFileChanged(const char* fileName);

protected:
    HANDLE m_hDir;
    char   m_szPath[MAX_PATH];
    bool   m_bWatching;
};

class CryFileMonitor : public FileSystemWatcher
{
public:
    CryFileMonitor();
    virtual ~CryFileMonitor();

    virtual void OnFileChanged(const char* fileName) override;

    void CheckModifiedFiles();
    void RegisterMonitoredExtension(const char* ext);

private:
    std::vector<std::string> m_extensions;
};

#endif // _CRYFILEMONITOR_H_
