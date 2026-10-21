#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include "../ai/AIObject.h" // Vec3F

#include "../core/Game.h"

// Processamento de comando de entidade (.?AVCXEntityProcessingCmd@@)
class CXEntityProcessingCmd {
public:
    CXEntityProcessingCmd();
    ~CXEntityProcessingCmd();

    void Reset();
    void AddAction(int action);

private:
    uint32_t m_actionFlags;
};

// Área de trigger e áudio no mapa (.?AVCXArea@@)
class CXArea {
public:
    CXArea(uint32_t areaId, const Vec3F& minPos, const Vec3F& maxPos);
    virtual ~CXArea();

    bool IsInside(const Vec3F& pos) const;

private:
    uint32_t m_areaId;
    Vec3F m_min;
    Vec3F m_max;
};

// Gerenciador de áreas (.?AVCXAreaMgr@@)
class CXAreaMgr {
public:
    CXAreaMgr();
    ~CXAreaMgr();

    void AddArea(std::shared_ptr<CXArea> area);
    CXArea* GetAreaAt(const Vec3F& pos) const;

private:
    std::vector<std::shared_ptr<CXArea>> m_areas;
};


// Pré-carregamento assíncrono (.?AVCFilePrefetchLinker@@)
class CFilePrefetchLinker {
public:
    CFilePrefetchLinker();
    ~CFilePrefetchLinker();

    void Prefetch(const std::string& filename);
};

// Carregador de cena controlada (.?AVCControlledSceneLoader@@)
class CControlledSceneLoader {
public:
    CControlledSceneLoader();
    ~CControlledSceneLoader();

    bool LoadScene(const std::string& sceneName);
};

// Contêiner de efeitos FX (.?AVCFxContainerGameObject@@)
class CFxContainerGameObject {
public:
    CFxContainerGameObject();
    virtual ~CFxContainerGameObject();
};

// Marcos e objetivos de navegação (.?AVCMileStoneObject@@)
class CMileStoneObject {
public:
    CMileStoneObject(uint32_t id, const Vec3F& pos);
    virtual ~CMileStoneObject();

    uint32_t m_id;
    Vec3F m_position;
};

// Marco sem cálculo de distância (.?AVCMileStoneNoDistObject@@)
class CMileStoneNoDistObject : public CMileStoneObject {
public:
    CMileStoneNoDistObject(uint32_t id, const Vec3F& pos);
    virtual ~CMileStoneNoDistObject();
};

// Tocador de cinemáticas/filmes (.?AVCMovieUser@@)
class CMovieUser {
public:
    CMovieUser();
    virtual ~CMovieUser();

    void PlayMovie(const std::string& moviePath);
    void StopMovie();
};

// Script de boids / vida selvagem (.?AVCScriptObjectBoids@@)
class CScriptObjectBoids {
public:
    CScriptObjectBoids();
    ~CScriptObjectBoids();
};

// Ponto de marcação / TagPoint (.?AVCTagPoint@@)
class CTagPoint {
public:
    CTagPoint(const std::string& name, const Vec3F& pos);
    ~CTagPoint();

    std::string m_name;
    Vec3F m_pos;
};

// Painel de vídeo na UI (.?AVCUIVideoPanel@@)
class CUIVideoPanel {
public:
    CUIVideoPanel();
    virtual ~CUIVideoPanel();
};

// Entidades de boids / pássaros / insetos
class BirdUnit { public: BirdUnit(); virtual ~BirdUnit(); };
class BirdsFlock { public: BirdsFlock(); virtual ~BirdsFlock(); };
class BoidUnit { public: BoidUnit(); virtual ~BoidUnit(); };
class BugUnit { public: BugUnit(); virtual ~BugUnit(); };
class BugsFlock { public: BugsFlock(); virtual ~BugsFlock(); };

// Canais de chat e moderação
class Channel {
public:
    Channel(uint32_t channelId, const std::string& channelName);
    virtual ~Channel();

    uint32_t m_channelId;
    std::string m_channelName;
};

class ChannelChattingClient {
public:
    ChannelChattingClient();
    virtual ~ChannelChattingClient();

    void SendChannelMessage(uint32_t channelId, const std::string& message);
};
