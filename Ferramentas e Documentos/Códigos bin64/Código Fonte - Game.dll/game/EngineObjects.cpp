#include "EngineObjects.h"
#include "../core/GameLog.h"

// CXGame
CXGame::CXGame() {}
CXGame::~CXGame() {}
bool CXGame::Init() { GameLog_Info("CXGame::Init"); return true; }
void CXGame::Reset() { GameLog_Info("CXGame::Reset"); }
void CXGame::Update() {}

// CXEntityProcessingCmd
CXEntityProcessingCmd::CXEntityProcessingCmd() : m_actionFlags(0) {}
CXEntityProcessingCmd::~CXEntityProcessingCmd() {}
void CXEntityProcessingCmd::Reset() { m_actionFlags = 0; }
void CXEntityProcessingCmd::AddAction(int action) { m_actionFlags |= (1 << action); }

// CXArea
CXArea::CXArea(uint32_t areaId, const Vec3F& minPos, const Vec3F& maxPos)
    : m_areaId(areaId), m_min(minPos), m_max(maxPos) {}
CXArea::~CXArea() {}
bool CXArea::IsInside(const Vec3F& p) const {
    return (p.x >= m_min.x && p.x <= m_max.x &&
            p.y >= m_min.y && p.y <= m_max.y &&
            p.z >= m_min.z && p.z <= m_max.z);
}

// CXAreaMgr
CXAreaMgr::CXAreaMgr() {}
CXAreaMgr::~CXAreaMgr() { m_areas.clear(); }
void CXAreaMgr::AddArea(std::shared_ptr<CXArea> area) { m_areas.push_back(area); }
CXArea* CXAreaMgr::GetAreaAt(const Vec3F& pos) const {
    for (const auto& a : m_areas) {
        if (a && a->IsInside(pos)) return a.get();
    }
    return nullptr;
}

// CCryFile
CCryFile::CCryFile() : m_file(nullptr) {}
CCryFile::~CCryFile() { Close(); }
bool CCryFile::Open(const char* szFilename, const char* szMode) {
    fopen_s(&m_file, szFilename, szMode);
    return m_file != nullptr;
}
void CCryFile::Close() {
    if (m_file) {
        fclose(m_file);
        m_file = nullptr;
    }
}
size_t CCryFile::Read(void* lpBuf, size_t nSize) {
    if (!m_file || !lpBuf) return 0;
    return fread(lpBuf, 1, nSize, m_file);
}

// CFilePrefetchLinker
CFilePrefetchLinker::CFilePrefetchLinker() {}
CFilePrefetchLinker::~CFilePrefetchLinker() {}
void CFilePrefetchLinker::Prefetch(const std::string& filename) {
    GameLog_Info("CFilePrefetchLinker: Pré-carregando %s", filename.c_str());
}

// CControlledSceneLoader
CControlledSceneLoader::CControlledSceneLoader() {}
CControlledSceneLoader::~CControlledSceneLoader() {}
bool CControlledSceneLoader::LoadScene(const std::string& sceneName) {
    GameLog_Info("CControlledSceneLoader: Carregando cena '%s'", sceneName.c_str());
    return true;
}

// CFxContainerGameObject
CFxContainerGameObject::CFxContainerGameObject() {}
CFxContainerGameObject::~CFxContainerGameObject() {}

// CMileStoneObject
CMileStoneObject::CMileStoneObject(uint32_t id, const Vec3F& pos) : m_id(id), m_position(pos) {}
CMileStoneObject::~CMileStoneObject() {}

// CMileStoneNoDistObject
CMileStoneNoDistObject::CMileStoneNoDistObject(uint32_t id, const Vec3F& pos) : CMileStoneObject(id, pos) {}
CMileStoneNoDistObject::~CMileStoneNoDistObject() {}

// CMovieUser
CMovieUser::CMovieUser() {}
CMovieUser::~CMovieUser() {}
void CMovieUser::PlayMovie(const std::string& moviePath) {
    GameLog_Info("CMovieUser: Reproduzindo filme: %s", moviePath.c_str());
}
void CMovieUser::StopMovie() {
    GameLog_Info("CMovieUser: Filme parado.");
}

// CScriptObjectBoids
CScriptObjectBoids::CScriptObjectBoids() {}
CScriptObjectBoids::~CScriptObjectBoids() {}

// CTagPoint
CTagPoint::CTagPoint(const std::string& name, const Vec3F& pos) : m_name(name), m_pos(pos) {}
CTagPoint::~CTagPoint() {}

// CUIVideoPanel
CUIVideoPanel::CUIVideoPanel() {}
CUIVideoPanel::~CUIVideoPanel() {}

// Units & Flocks
BirdUnit::BirdUnit() {} BirdUnit::~BirdUnit() {}
BirdsFlock::BirdsFlock() {} BirdsFlock::~BirdsFlock() {}
BoidUnit::BoidUnit() {} BoidUnit::~BoidUnit() {}
BugUnit::BugUnit() {} BugUnit::~BugUnit() {}
BugsFlock::BugsFlock() {} BugsFlock::~BugsFlock() {}

// Channel
Channel::Channel(uint32_t channelId, const std::string& channelName)
    : m_channelId(channelId), m_channelName(channelName) {}
Channel::~Channel() {}

// ChannelChattingClient
ChannelChattingClient::ChannelChattingClient() {}
ChannelChattingClient::~ChannelChattingClient() {}
void ChannelChattingClient::SendChannelMessage(uint32_t channelId, const std::string& message) {
    GameLog_Info("ChannelChattingClient: Mensagem enviada para Canal=%u: %s", channelId, message.c_str());
}

// BannedStringWrapper
BannedStringWrapper::BannedStringWrapper() {
    m_bannedWords = { "gm_hack", "speedhack", "cheat" };
}
BannedStringWrapper::~BannedStringWrapper() {
    m_bannedWords.clear();
}
bool BannedStringWrapper::IsBanned(const std::string& text) const {
    for (const auto& w : m_bannedWords) {
        if (text.find(w) != std::string::npos) return true;
    }
    return false;
}
std::string BannedStringWrapper::FilterText(const std::string& text) const {
    std::string result = text;
    for (const auto& w : m_bannedWords) {
        size_t pos = 0;
        while ((pos = result.find(w, pos)) != std::string::npos) {
            result.replace(pos, w.length(), std::string(w.length(), '*'));
            pos += w.length();
        }
    }
    return result;
}
