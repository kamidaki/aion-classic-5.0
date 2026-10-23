#include "SdoaLogin.h"
#include <cstring>

SdoaLogin::SdoaLogin()
    : m_nServerPort(2106),
      m_nSessionKeyLen(0),
      m_bAuthenticated(false),
      m_nLastError(0),
      m_nLoginStatus(0),
      m_pCallback(nullptr)
{
    m_szServerIP[0] = '\0';
    m_szAccountName[0] = '\0';
    m_szToken[0] = '\0';
    memset(m_sessionKey, 0, sizeof(m_sessionKey));
}

SdoaLogin::~SdoaLogin()
{
}

bool SdoaLogin::Init(const char* serverIp, int port)
{
    if (serverIp)
    {
        strncpy_s(m_szServerIP, sizeof(m_szServerIP), serverIp, _TRUNCATE);
    }
    m_nServerPort = port;
    return true;
}

void SdoaLogin::Shutdown()
{
    Reset();
}

bool SdoaLogin::Authenticate(const char* account, const char* token)
{
    if (!account || !account[0])
        return false;

    strncpy_s(m_szAccountName, sizeof(m_szAccountName), account, _TRUNCATE);
    if (token)
    {
        strncpy_s(m_szToken, sizeof(m_szToken), token, _TRUNCATE);
    }
    m_bAuthenticated = true;
    m_nLoginStatus = 1;
    return true;
}

void SdoaLogin::SetSessionKey(const void* key, int keyLen)
{
    if (key && keyLen > 0 && keyLen <= static_cast<int>(sizeof(m_sessionKey)))
    {
        memcpy(m_sessionKey, key, keyLen);
        m_nSessionKeyLen = keyLen;
    }
}

const void* SdoaLogin::GetSessionKey() const
{
    return m_sessionKey;
}

void SdoaLogin::SetAccountName(const char* acc)
{
    if (acc)
    {
        strncpy_s(m_szAccountName, sizeof(m_szAccountName), acc, _TRUNCATE);
    }
}

const char* SdoaLogin::GetAccountName() const
{
    return m_szAccountName;
}

bool SdoaLogin::IsAuthenticated() const
{
    return m_bAuthenticated;
}

const char* SdoaLogin::GetServerIP() const
{
    return m_szServerIP;
}

int SdoaLogin::GetServerPort() const
{
    return m_nServerPort;
}

void SdoaLogin::Disconnect()
{
    m_bAuthenticated = false;
    m_nLoginStatus = 0;
}

void SdoaLogin::Poll()
{
}

int SdoaLogin::GetLastError() const
{
    return m_nLastError;
}

void SdoaLogin::Reset()
{
    m_bAuthenticated = false;
    m_nLoginStatus = 0;
    m_nLastError = 0;
    m_szAccountName[0] = '\0';
    m_szToken[0] = '\0';
    m_nSessionKeyLen = 0;
}

void SdoaLogin::SetLoginCallback(void* pCallback)
{
    m_pCallback = pCallback;
}

int SdoaLogin::GetLoginStatus() const
{
    return m_nLoginStatus;
}
