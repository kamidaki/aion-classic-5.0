#include "IconManager.h"
#include "UICommon.h"
#include "../core/ServiceLog.h"
#include "../core/ServiceGlobals.h"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <regex>

namespace BrService {

std::wstring IconManager::s_baseIconDir;
std::unordered_map<std::string, std::string> IconManager::s_skillNameToIconFile;
std::unordered_map<uint32_t, std::string> IconManager::s_skillIdToIconFile;
std::unordered_map<std::wstring, Gdiplus::Bitmap*> IconManager::s_bitmapCache;
std::mutex IconManager::s_cacheMutex;
bool IconManager::s_initialized = false;

static std::string ToLowerAscii(const std::string& str) {
    std::string s = str;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return (unsigned char)::tolower(c);
    });
    return s;
}

static std::string NormalizeSkillName(const std::string& raw) {
    std::string s = raw;
    static const std::regex rankRegex(R"(\s+(?:[IVXLCDM]+|\d+)\s*$)");
    s = std::regex_replace(s, rankRegex, "");

    // Strip [DoT] or other bracket prefixes
    if (s.rfind("[DoT] ", 0) == 0) {
        s = s.substr(6);
    }
    // Strip (Effect) suffix
    size_t eff = s.find(" (Effect)");
    if (eff != std::string::npos) {
        s.erase(eff, 9);
    }
    // Strip colons or extra hyphens
    s.erase(std::remove(s.begin(), s.end(), ':'), s.end());
    return ToLowerAscii(s);
}

static bool FileExists(const std::wstring& path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return (attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY));
}

static std::wstring ResolveExistingIcon(const std::wstring& baseDir, const std::string& filename) {
    if (filename.empty()) return L"";
    std::wstring wName(filename.begin(), filename.end());

    // 1. Direct check
    std::wstring p1 = baseDir + L"\\" + wName;
    if (FileExists(p1)) return p1;

    // 2. Try with cbt_ prefix (combat skills)
    if (filename.rfind("cbt_", 0) != 0) {
        std::wstring p2 = baseDir + L"\\cbt_" + wName;
        if (FileExists(p2)) return p2;
    } else {
        // Try without cbt_
        std::wstring pNoCbt = baseDir + L"\\" + std::wstring(filename.begin() + 4, filename.end());
        if (FileExists(pNoCbt)) return pNoCbt;
    }

    // 3. Try removing _proc
    std::string base = filename;
    size_t procPos = base.find("_proc");
    if (procPos != std::string::npos) {
        base.erase(procPos, 5);
        std::wstring pProc = ResolveExistingIcon(baseDir, base);
        if (!pProc.empty()) return pProc;
    }

    // 4. Try fallback to grade 1 (_g1)
    size_t gPos = base.rfind("_g");
    if (gPos != std::string::npos && gPos + 3 <= base.length()) {
        std::string baseG1 = base.substr(0, gPos) + "_g1.png";
        if (baseG1 != base) {
            std::wstring pG1 = ResolveExistingIcon(baseDir, baseG1);
            if (!pG1.empty()) return pG1;
        }
    }

    return L"";
}

bool IconManager::Initialize() {
    std::lock_guard<std::mutex> lock(s_cacheMutex);
    if (s_initialized) return true;

    wchar_t dllPath[MAX_PATH] = { 0 };
    HMODULE hMod = g_hModule;
    if (!hMod) {
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           (LPCWSTR)&Initialize, &hMod);
    }
    GetModuleFileNameW(hMod, dllPath, MAX_PATH);

    wchar_t* lastSlash = wcsrchr(dllPath, L'\\');
    if (lastSlash) {
        *lastSlash = L'\0';
    }

    // Lista de caminhos candidatos para encontrar a pasta de icones
    const wchar_t* candidateDirs[] = {
        L"sprites\\icons",
        L"D:\\GameForge\\aionclassic\\bin64\\sprites\\icons",
        L"D:\\AION CLASSIC 5.0 - EMULADOR\\4 - Patch para o Client 5.0\\bin64\\sprites\\icons",
        L"D:\\Downloads - Google\\Lost Academy - Remake v1\\LostAcademy\\sprites\\icons",
    };

    s_baseIconDir = std::wstring(dllPath) + L"\\sprites\\icons";
    for (const wchar_t* cd : candidateDirs) {
        std::wstring path = (cd[1] == L':') ? std::wstring(cd) : (std::wstring(dllPath) + L"\\" + cd);
        std::wstring testJson = path + L"\\skills.json";
        if (FileExists(testJson)) {
            s_baseIconDir = path;
            break;
        }
    }

    LoadSkillDatabase();

    // Contar arquivos .png na pasta de skills para diagnóstico
    int iconCount = 0;
    std::wstring searchPath = s_baseIconDir + L"\\skills\\*.png";
    WIN32_FIND_DATAW fd = {};
    HANDLE hFind = FindFirstFileW(searchPath.c_str(), &fd);
    if (hFind != INVALID_HANDLE_VALUE) {
        do { iconCount++; } while (FindNextFileW(hFind, &fd));
        FindClose(hFind);
    }
    LogInfo("IconManager: %d icones .png encontrados em %ls\\skills\\.", iconCount, s_baseIconDir.c_str());

    s_initialized = true;
    return true;
}

void IconManager::Shutdown() {
    std::lock_guard<std::mutex> lock(s_cacheMutex);
    for (auto& pair : s_bitmapCache) {
        if (pair.second) {
            delete pair.second;
        }
    }
    s_bitmapCache.clear();
    s_skillNameToIconFile.clear();
    s_skillIdToIconFile.clear();
    s_initialized = false;
}

void IconManager::LoadSkillDatabase() {
    std::wstring jsonPath = s_baseIconDir + L"\\skills.json";
    std::ifstream file(jsonPath);
    if (!file.is_open()) {
        LogInfo("skills.json nao encontrado em %ls. Busca sera efetuada por nome direto de arquivo.", jsonPath.c_str());
        return;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();

    // Fast lightweight JSON parser for array of { "id": N, "name": "...", "icon": "...", "de": "...", "fr": "..." }
    size_t pos = 0;
    size_t count = 0;

    while ((pos = content.find('{', pos)) != std::string::npos) {
        size_t endObj = content.find('}', pos);
        if (endObj == std::string::npos) break;

        std::string obj = content.substr(pos, endObj - pos + 1);

        uint32_t skillId = 0;
        std::string nameStr;
        std::string iconStr;

        // Parse "id": 123
        size_t idPos = obj.find("\"id\":");
        if (idPos != std::string::npos) {
            skillId = (uint32_t)strtoul(obj.c_str() + idPos + 5, nullptr, 10);
        }

        // Parse "name": "..."
        size_t namePos = obj.find("\"name\":");
        if (namePos != std::string::npos) {
            size_t q1 = obj.find('\"', namePos + 7);
            if (q1 != std::string::npos) {
                size_t q2 = obj.find('\"', q1 + 1);
                if (q2 != std::string::npos) {
                    nameStr = obj.substr(q1 + 1, q2 - q1 - 1);
                }
            }
        }

        // Parse "icon": "..."
        size_t iconPos = obj.find("\"icon\":");
        if (iconPos != std::string::npos) {
            size_t q1 = obj.find('\"', iconPos + 7);
            if (q1 != std::string::npos) {
                size_t q2 = obj.find('\"', q1 + 1);
                if (q2 != std::string::npos) {
                    iconStr = obj.substr(q1 + 1, q2 - q1 - 1);
                }
            }
        }

        if (!iconStr.empty()) {
            if (skillId > 0) {
                s_skillIdToIconFile[skillId] = iconStr;
            }
            if (!nameStr.empty()) {
                s_skillNameToIconFile[ToLowerAscii(nameStr)] = iconStr;
                s_skillNameToIconFile[NormalizeSkillName(nameStr)] = iconStr;
            }
            count++;
        }

        pos = endObj + 1;
    }

    LogInfo("skills.json carregado com sucesso. %zu mapeamentos de icones registrados.", count);
}

std::wstring IconManager::GetSkillIconPath(const std::string& skillName, uint32_t skillId) {
    if (!s_initialized) Initialize();

    // Check auto attack first
    if (skillId == 0 || skillName == "Auto Attack" || skillName == "Ataque Normal" ||
        skillName.find("Auto Attack") != std::string::npos || skillName.find("Magic Attack") != std::string::npos) {
        return s_baseIconDir + L"\\skills\\icon_action_operation.png";
    }

    std::string iconFilename;

    // 1. Check skillId mapping
    if (skillId > 0) {
        auto itId = s_skillIdToIconFile.find(skillId);
        if (itId != s_skillIdToIconFile.end()) {
            iconFilename = itId->second;
        }
    }

    // 2. Check normalized skill name mapping
    if (iconFilename.empty() && !skillName.empty()) {
        std::string norm = NormalizeSkillName(skillName);
        auto itName = s_skillNameToIconFile.find(norm);
        if (itName != s_skillNameToIconFile.end()) {
            iconFilename = itName->second;
        } else {
            auto itExact = s_skillNameToIconFile.find(ToLowerAscii(skillName));
            if (itExact != s_skillNameToIconFile.end()) {
                iconFilename = itExact->second;
            }
        }
    }

    // 3. Fallback direct filename check (e.g. if skillName is already an icon key)
    if (iconFilename.empty() && !skillName.empty()) {
        iconFilename = ToLowerAscii(skillName) + ".png";
    }

    if (!iconFilename.empty()) {
        std::wstring resolved = ResolveExistingIcon(s_baseIconDir + L"\\skills", iconFilename);
        if (!resolved.empty()) return resolved;
    }

    // Direct check with skillName without extension
    if (!skillName.empty()) {
        std::wstring resolved = ResolveExistingIcon(s_baseIconDir + L"\\skills", ToLowerAscii(skillName) + ".png");
        if (!resolved.empty()) return resolved;
    }

    // Default fallback to action operation icon if available
    std::wstring fallback = s_baseIconDir + L"\\skills\\icon_action_operation.png";
    if (FileExists(fallback)) return fallback;

    return L"";
}

static std::string NormalizeClassName(const std::string& raw) {
    std::string s = ToLowerAscii(raw);
    if (s.find("gladiador") != std::string::npos || s == "gladiator") return "Gladiator";
    if (s.find("templ") != std::string::npos) return "Templar";
    if (s.find("guerreiro") != std::string::npos || s == "warrior") return "Warrior";
    if (s.find("batedor") != std::string::npos || s == "scout") return "Scout";
    if (s.find("assassin") != std::string::npos) return "Assassin";
    if (s.find("arqueiro") != std::string::npos || s == "ranger") return "Ranger";
    if (s.find("mago") != std::string::npos || s == "mage") return "Mage";
    if (s.find("feiticeiro") != std::string::npos || s == "sorcerer") return "Sorcerer";
    if (s.find("invocador") != std::string::npos || s.find("spirit") != std::string::npos) return "Spiritmaster";
    if (s.find("sacerdote") != std::string::npos || s == "priest") return "Priest";
    if (s.find("clérigo") != std::string::npos || s.find("clerigo") != std::string::npos || s == "cleric") return "Cleric";
    if (s.find("cantor") != std::string::npos || s == "chanter") return "Chanter";
    if (s.find("revenant") != std::string::npos || s.find("thunderer") != std::string::npos || s.find("monk") != std::string::npos) return "Revenant";
    if (s.find("brawler") != std::string::npos || s.find("lutador") != std::string::npos || s.find("striker") != std::string::npos) return "Brawler";
    if (s.find("luminess") != std::string::npos || s.find("lumin") != std::string::npos || s.find("orchestrator") != std::string::npos || s.find("bard") != std::string::npos) return "Luminess";
    if (s.find("phoenix") != std::string::npos || s.find("fenix") != std::string::npos || s.find("engineer") != std::string::npos || s.find("gunner") != std::string::npos) return "Phoenix";
    if (s.find("soul_reaper") != std::string::npos || s.find("ceifador") != std::string::npos || s.find("reaper") != std::string::npos) return "Soul_Reaper";
    if (!raw.empty()) {
        std::string cap = raw;
        cap[0] = (char)::toupper((unsigned char)cap[0]);
        return cap;
    }
    return "Warrior";
}

std::wstring IconManager::GetClassIconPath(const std::string& className) {
    if (!s_initialized) Initialize();
    std::string norm = NormalizeClassName(className);
    std::wstring wClass(norm.begin(), norm.end());
    return s_baseIconDir + L"\\classes\\" + wClass + L".png";
}

Gdiplus::Bitmap* IconManager::GetOrLoadBitmap(const std::wstring& fullPath) {
    if (fullPath.empty()) return nullptr;

    std::lock_guard<std::mutex> lock(s_cacheMutex);
    auto it = s_bitmapCache.find(fullPath);
    if (it != s_bitmapCache.end()) {
        return it->second;
    }

    if (GetFileAttributesW(fullPath.c_str()) == INVALID_FILE_ATTRIBUTES) {
        s_bitmapCache[fullPath] = nullptr;
        return nullptr;
    }

    Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromFile(fullPath.c_str(), FALSE);
    if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
        s_bitmapCache[fullPath] = bmp;
        return bmp;
    }

    if (bmp) delete bmp;
    s_bitmapCache[fullPath] = nullptr;
    return nullptr;
}

void IconManager::DrawSkillIcon(Gdiplus::Graphics& g, float x, float y, float size, uint32_t skillId, const std::string& skillName) {
    std::wstring iconPath = GetSkillIconPath(skillName, skillId);
    Gdiplus::Bitmap* bmp = GetOrLoadBitmap(iconPath);

    if (bmp) {
        // High quality rendering
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.SetPixelOffsetMode(Gdiplus::PixelOffsetModeHighQuality);

        // Draw image smoothly
        g.DrawImage(bmp, x, y, size, size);

        // Subtle dark rim border
        Gdiplus::Pen rimPen(Gdiplus::Color(160, 20, 25, 32), 1.0f);
        UICommon::DrawRoundRectangle(g, &rimPen, x, y, size, size, 2.0f);
    } else {
        // Fallback to stylized rune badge
        UICommon::DrawSkillIconBadge(g, x, y, size, skillId, skillName);
    }
}

void IconManager::DrawClassIcon(Gdiplus::Graphics& g, float x, float y, float size, const std::string& className) {
    std::wstring iconPath = GetClassIconPath(className);
    Gdiplus::Bitmap* bmp = GetOrLoadBitmap(iconPath);

    if (bmp) {
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.DrawImage(bmp, x, y, size, size);
    }
}

} // namespace BrService
