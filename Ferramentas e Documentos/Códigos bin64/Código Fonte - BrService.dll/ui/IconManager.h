#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>
#include <string>
#include <unordered_map>
#include <mutex>
#include <cstdint>

namespace BrService {

class IconManager {
public:
    static bool Initialize();
    static void Shutdown();

    // Skill Icon rendering
    static void DrawSkillIcon(Gdiplus::Graphics& g, float x, float y, float size, uint32_t skillId, const std::string& skillName);

    // Class / NPC Icon rendering
    static void DrawClassIcon(Gdiplus::Graphics& g, float x, float y, float size, const std::string& className);

    // Asset path resolution
    static std::wstring GetSkillIconPath(const std::string& skillName, uint32_t skillId);
    static std::wstring GetClassIconPath(const std::string& className);
    static const std::wstring& GetBaseIconDir() { return s_baseIconDir; }
    static const std::wstring& GetGameDataDir() { return s_gameDataDir; }
    static const std::wstring& GetGameTexturesDir() { return s_gameTexturesDir; }

private:
    static void LoadSkillDatabase();
    static Gdiplus::Bitmap* GetOrLoadBitmap(const std::wstring& fullPath);

    static std::wstring s_baseIconDir;
    static std::wstring s_gameDataDir;
    static std::wstring s_gameTexturesDir;
    static std::unordered_map<std::string, std::string> s_skillNameToIconFile;
    static std::unordered_map<uint32_t, std::string> s_skillIdToIconFile;
    static std::unordered_map<std::wstring, Gdiplus::Bitmap*> s_bitmapCache;
    static std::mutex s_cacheMutex;
    static bool s_initialized;
};

} // namespace BrService
