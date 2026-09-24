#include "ServiceLog.h"
#include <cstdarg>
#include <mutex>
#include <cstdio>
#include <cstring>

namespace BrService {

static std::mutex s_logMutex;

static void WriteToFile(const char* msg) {
    static char s_logPath[MAX_PATH] = {0};
    if (s_logPath[0] == '\0') {
        HMODULE hMod = nullptr;
        GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | 
                           GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           (LPCSTR)&WriteToFile, &hMod);
        if (hMod) {
            GetModuleFileNameA(hMod, s_logPath, MAX_PATH);
            char* lastSlash = strrchr(s_logPath, '\\');
            if (lastSlash) {
                strcpy_s(lastSlash + 1, MAX_PATH - (lastSlash + 1 - s_logPath), "brservice.log");
            }
        }
        if (s_logPath[0] == '\0') {
            strcpy_s(s_logPath, "brservice.log");
        }
    }
    FILE* f = nullptr;
    if (fopen_s(&f, s_logPath, "a") == 0 && f) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(f, "[%04d-%02d-%02d %02d:%02d:%02d.%03d] %s",
            st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, msg);
        fclose(f);
    }
}

void LogInfo(const char* fmt, ...) {
    std::lock_guard<std::mutex> lock(s_logMutex);
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    char out[1200];
    snprintf(out, sizeof(out), "[BrService][INFO] %s\n", buf);
    OutputDebugStringA(out);
    WriteToFile(out);
}

void LogError(const char* fmt, ...) {
    std::lock_guard<std::mutex> lock(s_logMutex);
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    char out[1200];
    snprintf(out, sizeof(out), "[BrService][ERROR] %s\n", buf);
    OutputDebugStringA(out);
    WriteToFile(out);
}

} // namespace BrService
