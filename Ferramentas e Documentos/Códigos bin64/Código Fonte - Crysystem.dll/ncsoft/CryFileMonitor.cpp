#include "CryFileMonitor.h"
#include <cstdio>

FileSystemWatcher::FileSystemWatcher()
    : m_hDir(INVALID_HANDLE_VALUE),
      m_bWatching(false)
{
    m_szPath[0] = '\0';
}

FileSystemWatcher::~FileSystemWatcher()
{
    StopWatching();
}

bool FileSystemWatcher::StartWatching(const char* dirPath)
{
    if (!dirPath || !dirPath[0])
        return false;

    strncpy_s(m_szPath, sizeof(m_szPath), dirPath, _TRUNCATE);
    m_bWatching = true;
    return true;
}

void FileSystemWatcher::StopWatching()
{
    if (m_hDir != INVALID_HANDLE_VALUE)
    {
        CloseHandle(m_hDir);
        m_hDir = INVALID_HANDLE_VALUE;
    }
    m_bWatching = false;
}

void FileSystemWatcher::OnFileChanged(const char* fileName)
{
    (void)fileName;
}

CryFileMonitor::CryFileMonitor()
{
    m_extensions.push_back(".pak");
    m_extensions.push_back(".xml");
    m_extensions.push_back(".cfg");
}

CryFileMonitor::~CryFileMonitor()
{
}

void CryFileMonitor::OnFileChanged(const char* fileName)
{
    if (!fileName) return;

    // Check if matching monitored extension
    std::string s(fileName);
    for (const auto& ext : m_extensions)
    {
        if (s.length() >= ext.length() &&
            s.compare(s.length() - ext.length(), ext.length(), ext) == 0)
        {
            char buf[512];
            snprintf(buf, sizeof(buf), "[CryFileMonitor] Monitored file modified: %s\n", fileName);
            OutputDebugStringA(buf);
            break;
        }
    }
}

void CryFileMonitor::CheckModifiedFiles()
{
}

void CryFileMonitor::RegisterMonitoredExtension(const char* ext)
{
    if (ext && ext[0])
    {
        m_extensions.push_back(ext);
    }
}
