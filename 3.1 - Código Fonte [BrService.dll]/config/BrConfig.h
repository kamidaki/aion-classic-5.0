#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>

namespace BrService {

class BrConfig {
public:
    static void Load();
    static void Save();
    static std::wstring GetIniPath();
};

} // namespace BrService
