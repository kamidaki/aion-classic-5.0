#include "ServiceLog.h"
#include <cstdarg>
#include <mutex>

namespace BrService {

static std::mutex s_logMutex;

void LogInfo(const char* fmt, ...) {
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    char out[1200];
    snprintf(out, sizeof(out), "[BrService][INFO] %s\n", buf);
    OutputDebugStringA(out);
}

void LogError(const char* fmt, ...) {
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    char out[1200];
    snprintf(out, sizeof(out), "[BrService][ERROR] %s\n", buf);
    OutputDebugStringA(out);
}

} // namespace BrService
