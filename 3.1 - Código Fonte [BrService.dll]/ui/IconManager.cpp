#include "IconManager.h"
#include "UICommon.h"
#include "../core/ServiceLog.h"
#include "../core/ServiceGlobals.h"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <regex>
#include <vector>

namespace BrService {

std::wstring IconManager::s_baseIconDir;
std::wstring IconManager::s_gameDataDir;
std::wstring IconManager::s_gameTexturesDir;
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

// Decodificador nativo de arquivos DDS (DirectDraw Surface) para Gdiplus::Bitmap
static Gdiplus::Bitmap* LoadDDSBitmap(const std::wstring& fullPath) {
    HANDLE hFile = CreateFileW(fullPath.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, 0, nullptr);
    if (hFile == INVALID_HANDLE_VALUE) return nullptr;

    DWORD fileSize = GetFileSize(hFile, nullptr);
    if (fileSize < 128) {
        CloseHandle(hFile);
        return nullptr;
    }

    std::vector<BYTE> buf(fileSize);
    DWORD bytesRead = 0;
    if (!ReadFile(hFile, buf.data(), fileSize, &bytesRead, nullptr) || bytesRead < 128) {
        CloseHandle(hFile);
        return nullptr;
    }
    CloseHandle(hFile);

    if (*(DWORD*)buf.data() != 0x20534444) return nullptr; // "DDS "

    DWORD h = *(DWORD*)(buf.data() + 12);
    DWORD w = *(DWORD*)(buf.data() + 16);
    if (w == 0 || h == 0 || w > 4096 || h > 4096) return nullptr;

    DWORD fourCC = *(DWORD*)(buf.data() + 84);
    DWORD rgbBits = *(DWORD*)(buf.data() + 88);
    BYTE* pSrc = buf.data() + 128;

    // Formato nativo Aion: 32-bit BGRA8888 descomprimido
    if (fourCC == 0 && rgbBits == 32) {
        Gdiplus::Bitmap* bmp = new Gdiplus::Bitmap((INT)w, (INT)h, PixelFormat32bppARGB);
        Gdiplus::BitmapData bmpData;
        Gdiplus::Rect rc(0, 0, (INT)w, (INT)h);
        if (bmp->LockBits(&rc, Gdiplus::ImageLockModeWrite, PixelFormat32bppARGB, &bmpData) == Gdiplus::Ok) {
            for (DWORD y = 0; y < h; ++y) {
                if (pSrc + (y + 1) * w * 4 <= buf.data() + bytesRead) {
                    memcpy((BYTE*)bmpData.Scan0 + y * bmpData.Stride, pSrc + y * w * 4, w * 4);
                }
            }
            bmp->UnlockBits(&bmpData);
            return bmp;
        }
        delete bmp;
    }
    return nullptr;
}

static std::wstring CheckFileWithExtensions(const std::wstring& baseDir, const std::wstring& stem) {
    if (stem.empty()) return L"";
    std::wstring p1 = baseDir + L"\\" + stem;
    if (FileExists(p1)) return p1;

    size_t dot = stem.rfind(L'.');
    if (dot != std::wstring::npos) {
        std::wstring raw = stem.substr(0, dot);
        std::wstring ext = stem.substr(dot);
        if (_wcsicmp(ext.c_str(), L".png") == 0) {
            std::wstring pDds = baseDir + L"\\" + raw + L".dds";
            if (FileExists(pDds)) return pDds;
        } else if (_wcsicmp(ext.c_str(), L".dds") == 0) {
            std::wstring pPng = baseDir + L"\\" + raw + L".png";
            if (FileExists(pPng)) return pPng;
        }
    } else {
        std::wstring pPng = baseDir + L"\\" + stem + L".png";
        if (FileExists(pPng)) return pPng;
        std::wstring pDds = baseDir + L"\\" + stem + L".dds";
        if (FileExists(pDds)) return pDds;
    }
    return L"";
}

static std::wstring TryCandidateNames(const std::wstring& baseDir, const std::string& filename) {
    if (filename.empty() || baseDir.empty()) return L"";
    std::wstring wName(filename.begin(), filename.end());

    // 1. Verificação direta (png e dds)
    std::wstring found = CheckFileWithExtensions(baseDir, wName);
    if (!found.empty()) return found;

    // 2. Prefixo cbt_ (skills de combate)
    if (filename.rfind("cbt_", 0) != 0) {
        std::wstring p2 = CheckFileWithExtensions(baseDir, L"cbt_" + wName);
        if (!p2.empty()) return p2;
    } else {
        std::wstring pNoCbt = CheckFileWithExtensions(baseDir, std::wstring(wName.begin() + 4, wName.end()));
        if (!pNoCbt.empty()) return pNoCbt;
    }

    // 3. Remoção de sufixo _proc
    std::string base = filename;
    size_t procPos = base.find("_proc");
    if (procPos != std::string::npos) {
        base.erase(procPos, 5);
        std::wstring pProc = CheckFileWithExtensions(baseDir, std::wstring(base.begin(), base.end()));
        if (!pProc.empty()) return pProc;
    }

    // 4. Fallback de nível de graduação para grade 1 (_g1)
    size_t gPos = base.rfind("_g");
    if (gPos != std::string::npos) {
        size_t dotPos = base.rfind('.');
        std::string ext = (dotPos != std::string::npos) ? base.substr(dotPos) : ".png";
        std::string baseG1 = base.substr(0, gPos) + "_g1" + ext;
        if (baseG1 != base) {
            std::wstring pG1 = CheckFileWithExtensions(baseDir, std::wstring(baseG1.begin(), baseG1.end()));
            if (!pG1.empty()) return pG1;
        }
    }

    return L"";
}

static std::wstring ResolveExistingIcon(const std::string& filename) {
    if (filename.empty()) return L"";

    // Busca relativa em ordem de prioridade (zero paths absolutos)
    const std::wstring* dirs[] = {
        &IconManager::GetBaseIconDir(),
        &IconManager::GetGameDataDir(),
        &IconManager::GetGameTexturesDir()
    };

    // Subpastas relativas
    std::vector<std::wstring> searchLocations = {
        IconManager::GetBaseIconDir() + L"\\skills",
        IconManager::GetGameDataDir() + L"\\items",
        IconManager::GetGameDataDir() + L"\\skills",
        IconManager::GetGameTexturesDir() + L"\\UI",
        IconManager::GetBaseIconDir()
    };

    for (const auto& loc : searchLocations) {
        std::wstring res = TryCandidateNames(loc, filename);
        if (!res.empty()) return res;
    }

    return L"";
}

bool IconManager::Initialize() {
    std::lock_guard<std::mutex> lock(s_cacheMutex);
    if (s_initialized) return true;

    // Resolução 100% relativa da DLL (portabilidade universal)
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
    // dllPath é a pasta da DLL (<GameRoot>\bin64)
    std::wstring binDir = dllPath;

    // gameRootDir é a raiz do jogo (<GameRoot>), uma pasta acima de bin64
    std::wstring gameRootDir = dllPath;
    wchar_t* upSlash = wcsrchr(dllPath, L'\\');
    if (upSlash) {
        gameRootDir = std::wstring(dllPath, upSlash);
    }

    s_baseIconDir = binDir + L"\\sprites\\icons";
    s_gameDataDir = gameRootDir + L"\\data";
    s_gameTexturesDir = gameRootDir + L"\\Textures";

    // Verifica se skills.json existe na pasta de sprites da DLL ou na pasta raiz
    std::wstring testJson = s_baseIconDir + L"\\skills.json";
    if (!FileExists(testJson)) {
        std::wstring altJson = binDir + L"\\skills.json";
        if (FileExists(altJson)) {
            s_baseIconDir = binDir;
        }
    }

    LoadSkillDatabase();

    // Contagem diagnóstica de ícones na pasta de skills
    int iconCount = 0;
    std::wstring searchPath = s_baseIconDir + L"\\skills\\*.*";
    WIN32_FIND_DATAW fd = {};
    HANDLE hFind = FindFirstFileW(searchPath.c_str(), &fd);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                iconCount++;
            }
        } while (FindNextFileW(hFind, &fd));
        FindClose(hFind);
    }
    LogInfo("IconManager: %d icones de skills detectados em %ls\\skills\\ (caminho relativo).", iconCount, s_baseIconDir.c_str());

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
        LogInfo("skills.json nao encontrado em %ls. Busca automatica sera efetuada por nome de arquivo.", jsonPath.c_str());
        return;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();

    size_t pos = 0;
    size_t count = 0;

    while ((pos = content.find('{', pos)) != std::string::npos) {
        size_t endObj = content.find('}', pos);
        if (endObj == std::string::npos) break;

        std::string obj = content.substr(pos, endObj - pos + 1);

        uint32_t skillId = 0;
        std::string nameStr;
        std::string iconStr;

        // "id": 123
        size_t idPos = obj.find("\"id\":");
        if (idPos != std::string::npos) {
            skillId = (uint32_t)strtoul(obj.c_str() + idPos + 5, nullptr, 10);
        }

        // "name": "..."
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

        // "icon": "..."
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

    // Auto attack
    if (skillId == 0 || skillName == "Auto Attack" || skillName == "Ataque Normal" ||
        skillName.find("Auto Attack") != std::string::npos || skillName.find("Magic Attack") != std::string::npos) {
        std::wstring autoAtk = ResolveExistingIcon("icon_action_operation.png");
        if (!autoAtk.empty()) return autoAtk;
    }

    std::string iconFilename;

    // 1. Busca por skillId
    if (skillId > 0) {
        auto itId = s_skillIdToIconFile.find(skillId);
        if (itId != s_skillIdToIconFile.end()) {
            iconFilename = itId->second;
        }
    }

    // 2. Busca por nome normalizado
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

    // 3. Fallback de nome direto de arquivo
    if (iconFilename.empty() && !skillName.empty()) {
        iconFilename = ToLowerAscii(skillName);
    }

    if (!iconFilename.empty()) {
        std::wstring resolved = ResolveExistingIcon(iconFilename);
        if (!resolved.empty()) return resolved;
    }

    // Fallback padrão
    std::wstring fallback = ResolveExistingIcon("icon_action_operation.png");
    if (!fallback.empty()) return fallback;

    return L"";
}

static std::string NormalizeClassName(const std::string& raw) {
    std::string s = ToLowerAscii(raw);
    if (s.find("gladiador") != std::string::npos || s == "gladiator" || s == "fighter") return "Gladiator";
    if (s.find("templ") != std::string::npos || s == "knight") return "Templar";
    if (s.find("guerreiro") != std::string::npos || s == "warrior") return "Warrior";
    if (s.find("batedor") != std::string::npos || s == "scout") return "Scout";
    if (s.find("assassin") != std::string::npos) return "Assassin";
    if (s.find("arqueiro") != std::string::npos || s == "ranger") return "Ranger";
    if (s.find("mago") != std::string::npos || s == "mage") return "Mage";
    if (s.find("feiticeiro") != std::string::npos || s == "sorcerer" || s == "wizard") return "Sorcerer";
    if (s.find("invocador") != std::string::npos || s.find("spirit") != std::string::npos || s == "elementalist") return "Spiritmaster";
    if (s.find("sacerdote") != std::string::npos || s == "priest") return "Priest";
    if (s.find("clérigo") != std::string::npos || s.find("clerigo") != std::string::npos || s == "cleric") return "Cleric";
    if (s.find("cantor") != std::string::npos || s == "chanter") return "Chanter";
    if (s.find("revenant") != std::string::npos || s.find("thunderer") != std::string::npos || s.find("monk") != std::string::npos) return "Revenant";
    if (s.find("brawler") != std::string::npos || s.find("lutador") != std::string::npos || s.find("striker") != std::string::npos || s.find("battlemaster") != std::string::npos) return "Brawler";
    if (s.find("luminess") != std::string::npos || s.find("lumin") != std::string::npos || s.find("orchestrator") != std::string::npos) return "Luminess";
    if (s.find("phoenix") != std::string::npos || s.find("fenix") != std::string::npos || s.find("engineer") != std::string::npos || s.find("gunner") != std::string::npos) return "Phoenix";
    if (s.find("soul_reaper") != std::string::npos || s.find("ceifador") != std::string::npos || s.find("reaper") != std::string::npos || s.find("runeblade") != std::string::npos) return "Soul_Reaper";
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

    std::wstring pPng = s_baseIconDir + L"\\classes\\" + wClass + L".png";
    if (FileExists(pPng)) return pPng;

    std::wstring pDds = s_baseIconDir + L"\\classes\\" + wClass + L".dds";
    if (FileExists(pDds)) return pDds;

    return pPng;
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

    Gdiplus::Bitmap* bmp = nullptr;
    if (fullPath.length() >= 4 && _wcsicmp(fullPath.c_str() + fullPath.length() - 4, L".dds") == 0) {
        bmp = LoadDDSBitmap(fullPath);
    } else {
        bmp = Gdiplus::Bitmap::FromFile(fullPath.c_str(), FALSE);
    }

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
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.SetPixelOffsetMode(Gdiplus::PixelOffsetModeHighQuality);

        g.DrawImage(bmp, x, y, size, size);

        Gdiplus::Pen rimPen(Gdiplus::Color(160, 20, 25, 32), 1.0f);
        UICommon::DrawRoundRectangle(g, &rimPen, x, y, size, size, 2.0f);
    } else {
        // Fallback estilizado se a imagem não estiver presente
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
