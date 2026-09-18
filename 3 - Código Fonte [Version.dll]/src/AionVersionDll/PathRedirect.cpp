#include "PathRedirect.h"
#include "detours.h"
#include <vector>
#include <algorithm>

static decltype(GetFileAttributesW)* real_GetFileAttributesW = GetFileAttributesW;
static decltype(GetFileAttributesA)* real_GetFileAttributesA = GetFileAttributesA;
static decltype(GetFileAttributesExW)* real_GetFileAttributesExW = GetFileAttributesExW;
static decltype(GetFileAttributesExA)* real_GetFileAttributesExA = GetFileAttributesExA;
static decltype(CreateFileW)* real_CreateFileW = CreateFileW;
static decltype(CreateFileA)* real_CreateFileA = CreateFileA;
static decltype(FindFirstFileW)* real_FindFirstFileW = FindFirstFileW;
static decltype(FindFirstFileA)* real_FindFirstFileA = FindFirstFileA;
static decltype(SetCurrentDirectoryA)* real_SetCurrentDirectoryA = SetCurrentDirectoryA;
static decltype(SetCurrentDirectoryW)* real_SetCurrentDirectoryW = SetCurrentDirectoryW;

static std::wstring GetCurrentBinFolderW() {
    static std::wstring s_binFolder;
    if (s_binFolder.empty()) {
        wchar_t buf[MAX_PATH] = {0};
        GetModuleFileNameW(nullptr, buf, MAX_PATH);
        wchar_t* p = wcsrchr(buf, L'\\');
        if (p) {
            *p = L'\0';
            wchar_t* p2 = wcsrchr(buf, L'\\');
            if (p2) {
                s_binFolder = p2 + 1;
            }
        }
        if (s_binFolder.empty()) s_binFolder = L"bin64";
    }
    return s_binFolder;
}

static std::string GetCurrentBinFolderA() {
    static std::string s_binFolder;
    if (s_binFolder.empty()) {
        char buf[MAX_PATH] = {0};
        GetModuleFileNameA(nullptr, buf, MAX_PATH);
        char* p = strrchr(buf, '\\');
        if (p) {
            *p = '\0';
            char* p2 = strrchr(buf, '\\');
            if (p2) {
                s_binFolder = p2 + 1;
            }
        }
        if (s_binFolder.empty()) s_binFolder = "bin64";
    }
    return s_binFolder;
}

std::wstring GetGameRootW() {
    static std::wstring s_gameRoot;
    if (s_gameRoot.empty()) {
        wchar_t buf[MAX_PATH] = {0};
        GetModuleFileNameW(nullptr, buf, MAX_PATH);
        wchar_t* p = wcsrchr(buf, L'\\');
        if (p) {
            *p = L'\0'; // strip executable name
            wchar_t* pRoot = wcsrchr(buf, L'\\');
            if (pRoot) {
                *pRoot = L'\0'; // strip bin directory to get game root
            }
        }
        s_gameRoot = buf;
    }
    return s_gameRoot;
}

std::string GetGameRootA() {
    static std::string s_gameRoot;
    if (s_gameRoot.empty()) {
        char buf[MAX_PATH] = {0};
        GetModuleFileNameA(nullptr, buf, MAX_PATH);
        char* p = strrchr(buf, '\\');
        if (p) {
            *p = '\0'; // strip executable name
            char* pRoot = strrchr(buf, '\\');
            if (pRoot) {
                *pRoot = '\0'; // strip bin directory to get game root
            }
        }
        s_gameRoot = buf;
    }
    return s_gameRoot;
}

std::wstring RedirectPathW(const std::wstring& path) {
    if (path.empty()) return path;
    const std::wstring& curBin = GetCurrentBinFolderW();
    if (_wcsicmp(curBin.c_str(), L"bin64") == 0) {
        return path;
    }

    std::wstring replacement = L"\\" + curBin;
    std::wstring result = path;
    size_t pos = 0;
    while (true) {
        pos = result.find(L"\\bin64", pos);
        if (pos == std::wstring::npos) {
            pos = result.find(L"/bin64", pos);
        }
        if (pos == std::wstring::npos) {
            break;
        }
        size_t nextCharPos = pos + 6;
        if (nextCharPos == result.size() || result[nextCharPos] == L'\\' || result[nextCharPos] == L'/') {
            result.replace(pos, 6, replacement);
        }
        pos += replacement.length();
    }
    return result;
}

std::string RedirectPathA(const std::string& path) {
    if (path.empty()) return path;
    const std::string& curBin = GetCurrentBinFolderA();
    if (_stricmp(curBin.c_str(), "bin64") == 0) {
        return path;
    }

    std::string replacement = "\\" + curBin;
    std::string result = path;
    size_t pos = 0;
    while (true) {
        pos = result.find("\\bin64", pos);
        if (pos == std::string::npos) {
            pos = result.find("/bin64", pos);
        }
        if (pos == std::string::npos) {
            break;
        }
        size_t nextCharPos = pos + 6;
        if (nextCharPos == result.size() || result[nextCharPos] == '\\' || result[nextCharPos] == '/') {
            result.replace(pos, 6, replacement);
        }
        pos += replacement.length();
    }
    return result;
}

static inline bool NeedsRedirectW(LPCWSTR s) {
    if (!s) return false;
    for (const wchar_t* p = s; *p; p++) {
        if ((p[0] == L'b' || p[0] == L'B') &&
            (p[1] == L'i' || p[1] == L'I') &&
            (p[2] == L'n' || p[2] == L'N') &&
            p[3] == L'6' && p[4] == L'4') {
            return true;
        }
    }
    return false;
}

static inline bool NeedsRedirectA(LPCSTR s) {
    if (!s) return false;
    for (const char* p = s; *p; p++) {
        if ((p[0] == 'b' || p[0] == 'B') &&
            (p[1] == 'i' || p[1] == 'I') &&
            (p[2] == 'n' || p[2] == 'N') &&
            p[3] == '6' && p[4] == '4') {
            return true;
        }
    }
    return false;
}

static void AddCaseVariationsW(const std::wstring& path, std::vector<std::wstring>& candidates) {
    std::wstring p = path;
    size_t pos = p.find(L"/data/");
    if (pos != std::wstring::npos) {
        p.replace(pos, 6, L"/Data/");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find(L"\\data\\");
    if (pos != std::wstring::npos) {
        p.replace(pos, 6, L"\\Data\\");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find(L"/Data/");
    if (pos != std::wstring::npos) {
        p.replace(pos, 6, L"/data/");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find(L"\\Data\\");
    if (pos != std::wstring::npos) {
        p.replace(pos, 6, L"\\data\\");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find(L"/strings/");
    if (pos != std::wstring::npos) {
        p.replace(pos, 9, L"/Strings/");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find(L"\\strings\\");
    if (pos != std::wstring::npos) {
        p.replace(pos, 9, L"\\Strings\\");
        candidates.push_back(p);
    }
}

static void AddCaseVariationsA(const std::string& path, std::vector<std::string>& candidates) {
    std::string p = path;
    size_t pos = p.find("/data/");
    if (pos != std::string::npos) {
        p.replace(pos, 6, "/Data/");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find("\\data\\");
    if (pos != std::string::npos) {
        p.replace(pos, 6, "\\Data\\");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find("/Data/");
    if (pos != std::string::npos) {
        p.replace(pos, 6, "/data/");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find("\\Data\\");
    if (pos != std::string::npos) {
        p.replace(pos, 6, "\\data\\");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find("/strings/");
    if (pos != std::string::npos) {
        p.replace(pos, 9, "/Strings/");
        candidates.push_back(p);
    }
    p = path;
    pos = p.find("\\strings\\");
    if (pos != std::string::npos) {
        p.replace(pos, 9, "\\Strings\\");
        candidates.push_back(p);
    }
}

static DWORD WINAPI zzGetFileAttributesW(LPCWSTR lpFileName) {
    if (NeedsRedirectW(lpFileName)) {
        std::wstring redirected = RedirectPathW(lpFileName);
        return real_GetFileAttributesW(redirected.c_str());
    }
    DWORD res = real_GetFileAttributesW(lpFileName);
    if (res == INVALID_FILE_ATTRIBUTES && lpFileName && lpFileName[0] != L'\\' && lpFileName[0] != L'/' && (wcslen(lpFileName) < 2 || lpFileName[1] != L':')) {
        std::wstring root = GetGameRootW();
        if (!root.empty()) {
            std::vector<std::wstring> cands;
            cands.push_back(root + L"\\" + lpFileName);
            AddCaseVariationsW(cands[0], cands);
            for (const auto& c : cands) {
                DWORD r2 = real_GetFileAttributesW(c.c_str());
                if (r2 != INVALID_FILE_ATTRIBUTES) return r2;
            }
        }
    }
    return res;
}

static DWORD WINAPI zzGetFileAttributesA(LPCSTR lpFileName) {
    if (NeedsRedirectA(lpFileName)) {
        std::string redirected = RedirectPathA(lpFileName);
        return real_GetFileAttributesA(redirected.c_str());
    }
    DWORD res = real_GetFileAttributesA(lpFileName);
    if (res == INVALID_FILE_ATTRIBUTES && lpFileName && lpFileName[0] != '\\' && lpFileName[0] != '/' && (strlen(lpFileName) < 2 || lpFileName[1] != ':')) {
        std::string root = GetGameRootA();
        if (!root.empty()) {
            std::vector<std::string> cands;
            cands.push_back(root + "\\" + lpFileName);
            AddCaseVariationsA(cands[0], cands);
            for (const auto& c : cands) {
                DWORD r2 = real_GetFileAttributesA(c.c_str());
                if (r2 != INVALID_FILE_ATTRIBUTES) return r2;
            }
        }
    }
    return res;
}

static BOOL WINAPI zzGetFileAttributesExW(LPCWSTR lpFileName, GET_FILEEX_INFO_LEVELS fInfoLevelId, LPVOID lpFileInformation) {
    if (NeedsRedirectW(lpFileName)) {
        std::wstring redirected = RedirectPathW(lpFileName);
        return real_GetFileAttributesExW(redirected.c_str(), fInfoLevelId, lpFileInformation);
    }
    BOOL res = real_GetFileAttributesExW(lpFileName, fInfoLevelId, lpFileInformation);
    if (!res && lpFileName && lpFileName[0] != L'\\' && lpFileName[0] != L'/' && (wcslen(lpFileName) < 2 || lpFileName[1] != L':')) {
        std::wstring root = GetGameRootW();
        if (!root.empty()) {
            std::vector<std::wstring> cands;
            cands.push_back(root + L"\\" + lpFileName);
            AddCaseVariationsW(cands[0], cands);
            for (const auto& c : cands) {
                BOOL r2 = real_GetFileAttributesExW(c.c_str(), fInfoLevelId, lpFileInformation);
                if (r2) return r2;
            }
        }
    }
    return res;
}

static BOOL WINAPI zzGetFileAttributesExA(LPCSTR lpFileName, GET_FILEEX_INFO_LEVELS fInfoLevelId, LPVOID lpFileInformation) {
    if (NeedsRedirectA(lpFileName)) {
        std::string redirected = RedirectPathA(lpFileName);
        return real_GetFileAttributesExA(redirected.c_str(), fInfoLevelId, lpFileInformation);
    }
    BOOL res = real_GetFileAttributesExA(lpFileName, fInfoLevelId, lpFileInformation);
    if (!res && lpFileName && lpFileName[0] != '\\' && lpFileName[0] != '/' && (strlen(lpFileName) < 2 || lpFileName[1] != ':')) {
        std::string root = GetGameRootA();
        if (!root.empty()) {
            std::vector<std::string> cands;
            cands.push_back(root + "\\" + lpFileName);
            AddCaseVariationsA(cands[0], cands);
            for (const auto& c : cands) {
                BOOL r2 = real_GetFileAttributesExA(c.c_str(), fInfoLevelId, lpFileInformation);
                if (r2) return r2;
            }
        }
    }
    return res;
}

static HANDLE WINAPI zzCreateFileW(
    LPCWSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
) {
    if (NeedsRedirectW(lpFileName)) {
        std::wstring redirected = RedirectPathW(lpFileName);
        return real_CreateFileW(redirected.c_str(), dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);
    }
    HANDLE h = real_CreateFileW(lpFileName, dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);
    if (h == INVALID_HANDLE_VALUE && lpFileName && lpFileName[0] != L'\\' && lpFileName[0] != L'/' && (wcslen(lpFileName) < 2 || lpFileName[1] != L':')) {
        std::wstring root = GetGameRootW();
        if (!root.empty()) {
            std::vector<std::wstring> cands;
            cands.push_back(root + L"\\" + lpFileName);
            AddCaseVariationsW(cands[0], cands);
            for (const auto& c : cands) {
                HANDLE h2 = real_CreateFileW(c.c_str(), dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);
                if (h2 != INVALID_HANDLE_VALUE) return h2;
            }
        }
    }
    return h;
}

static HANDLE WINAPI zzCreateFileA(
    LPCSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
) {
    if (NeedsRedirectA(lpFileName)) {
        std::string redirected = RedirectPathA(lpFileName);
        return real_CreateFileA(redirected.c_str(), dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);
    }
    HANDLE h = real_CreateFileA(lpFileName, dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);
    if (h == INVALID_HANDLE_VALUE && lpFileName && lpFileName[0] != '\\' && lpFileName[0] != '/' && (strlen(lpFileName) < 2 || lpFileName[1] != ':')) {
        std::string root = GetGameRootA();
        if (!root.empty()) {
            std::vector<std::string> cands;
            cands.push_back(root + "\\" + lpFileName);
            AddCaseVariationsA(cands[0], cands);
            for (const auto& c : cands) {
                HANDLE h2 = real_CreateFileA(c.c_str(), dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);
                if (h2 != INVALID_HANDLE_VALUE) return h2;
            }
        }
    }
    return h;
}

static HANDLE WINAPI zzFindFirstFileW(LPCWSTR lpFileName, LPWIN32_FIND_DATAW lpFindFileData) {
    if (NeedsRedirectW(lpFileName)) {
        std::wstring redirected = RedirectPathW(lpFileName);
        return real_FindFirstFileW(redirected.c_str(), lpFindFileData);
    }
    HANDLE h = real_FindFirstFileW(lpFileName, lpFindFileData);
    if (h == INVALID_HANDLE_VALUE && lpFileName && lpFileName[0] != L'\\' && lpFileName[0] != L'/' && (wcslen(lpFileName) < 2 || lpFileName[1] != L':')) {
        std::wstring root = GetGameRootW();
        if (!root.empty()) {
            std::vector<std::wstring> cands;
            cands.push_back(root + L"\\" + lpFileName);
            AddCaseVariationsW(cands[0], cands);
            for (const auto& c : cands) {
                HANDLE h2 = real_FindFirstFileW(c.c_str(), lpFindFileData);
                if (h2 != INVALID_HANDLE_VALUE) return h2;
            }
        }
    }
    return h;
}

static HANDLE WINAPI zzFindFirstFileA(LPCSTR lpFileName, LPWIN32_FIND_DATAA lpFindFileData) {
    if (NeedsRedirectA(lpFileName)) {
        std::string redirected = RedirectPathA(lpFileName);
        return real_FindFirstFileA(redirected.c_str(), lpFindFileData);
    }
    HANDLE h = real_FindFirstFileA(lpFileName, lpFindFileData);
    if (h == INVALID_HANDLE_VALUE && lpFileName && lpFileName[0] != '\\' && lpFileName[0] != '/' && (strlen(lpFileName) < 2 || lpFileName[1] != ':')) {
        std::string root = GetGameRootA();
        if (!root.empty()) {
            std::vector<std::string> cands;
            cands.push_back(root + "\\" + lpFileName);
            AddCaseVariationsA(cands[0], cands);
            for (const auto& c : cands) {
                HANDLE h2 = real_FindFirstFileA(c.c_str(), lpFindFileData);
                if (h2 != INVALID_HANDLE_VALUE) return h2;
            }
        }
    }
    return h;
}

static BOOL WINAPI zzSetCurrentDirectoryA(LPCSTR lpPathName) {
    if (!lpPathName) return FALSE;
    // If an engine module or launcher attempts to point working directory into bin folder,
    // redirect it to the true game root so relative assets (L10N, Data, Shaders, etc.) resolve cleanly.
    if (strstr(lpPathName, "bin64") != nullptr || strstr(lpPathName, "bin32") != nullptr) {
        std::string root = GetGameRootA();
        if (!root.empty()) {
            return real_SetCurrentDirectoryA(root.c_str());
        }
    }
    return real_SetCurrentDirectoryA(lpPathName);
}

static BOOL WINAPI zzSetCurrentDirectoryW(LPCWSTR lpPathName) {
    if (!lpPathName) return FALSE;
    if (wcsstr(lpPathName, L"bin64") != nullptr || wcsstr(lpPathName, L"bin32") != nullptr) {
        std::wstring root = GetGameRootW();
        if (!root.empty()) {
            return real_SetCurrentDirectoryW(root.c_str());
        }
    }
    return real_SetCurrentDirectoryW(lpPathName);
}

void InstallPathRedirect() {
    // Normalize working directory immediately at startup
    std::string root = GetGameRootA();
    if (!root.empty()) {
        real_SetCurrentDirectoryA(root.c_str());
    }

    DetourAttach(&(PVOID&)real_GetFileAttributesW, zzGetFileAttributesW);
    DetourAttach(&(PVOID&)real_GetFileAttributesA, zzGetFileAttributesA);
    DetourAttach(&(PVOID&)real_GetFileAttributesExW, zzGetFileAttributesExW);
    DetourAttach(&(PVOID&)real_GetFileAttributesExA, zzGetFileAttributesExA);
    DetourAttach(&(PVOID&)real_CreateFileW, zzCreateFileW);
    DetourAttach(&(PVOID&)real_CreateFileA, zzCreateFileA);
    DetourAttach(&(PVOID&)real_FindFirstFileW, zzFindFirstFileW);
    DetourAttach(&(PVOID&)real_FindFirstFileA, zzFindFirstFileA);
    DetourAttach(&(PVOID&)real_SetCurrentDirectoryA, zzSetCurrentDirectoryA);
    DetourAttach(&(PVOID&)real_SetCurrentDirectoryW, zzSetCurrentDirectoryW);
}
