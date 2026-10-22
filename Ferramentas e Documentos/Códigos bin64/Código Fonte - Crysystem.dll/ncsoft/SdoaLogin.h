#pragma once

#ifndef _SDOALOGIN_H_
#define _SDOALOGIN_H_

class SdoaLogin
{
public:
    SdoaLogin();
    virtual ~SdoaLogin();

    // 17 virtual slots matching binary VTable at 0x1801e7e78
    virtual bool Init(const char* serverIp, int port);
    virtual void Shutdown();
    virtual bool Authenticate(const char* account, const char* token);
    virtual void SetSessionKey(const void* key, int keyLen);
    virtual const void* GetSessionKey() const;
    virtual void SetAccountName(const char* acc);
    virtual const char* GetAccountName() const;
    virtual bool IsAuthenticated() const;
    virtual const char* GetServerIP() const;
    virtual int  GetServerPort() const;
    virtual void Disconnect();
    virtual void Poll();
    virtual int  GetLastError() const;
    virtual void Reset();
    virtual void SetLoginCallback(void* pCallback);
    virtual int  GetLoginStatus() const;

private:
    char m_szServerIP[64];
    int  m_nServerPort;
    char m_szAccountName[64];
    char m_szToken[256];
    char m_sessionKey[128];
    int  m_nSessionKeyLen;
    bool m_bAuthenticated;
    int  m_nLastError;
    int  m_nLoginStatus;
    void* m_pCallback;
};

#endif // _SDOALOGIN_H_
