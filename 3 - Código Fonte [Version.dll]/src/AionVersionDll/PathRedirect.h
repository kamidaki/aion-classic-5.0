#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif

#include <windows.h>
#include <string>

std::wstring RedirectPathW(const std::wstring& path);
std::string RedirectPathA(const std::string& path);
std::wstring GetGameRootW();
std::string GetGameRootA();

void InstallPathRedirect();
