#include "Game.h"
#include "GameGlobals.h"
#include "GameLog.h"
#include "../net/ClientToServerRouter.h"
#include "../net/AionClientPackets.h"
#include "../net/AionServerPackets.h"
#include "../net/AionRouters.h"
#include "../ai/AIObject.h"
#include "../ai/AIToyPet.h"
#include "../tables/AbyssTable.h"
#include "../tables/ActionPresetTable.h"
#include "../tables/AssemblyItemTable.h"
#include "../tables/ArtiTable.h"
#include "../tables/FlyPathTable.h"
#include "../path/CPathFileReader.h"
#include "../path/SimplePathSector.h"
#include "../path/ComplexPathSector.h"
#include "../ui/AddonBrowser.h"
#include "../ui/AddonButton.h"
#include "../ui/AddonContainer.h"
#include "../ui/AddonGauge.h"
#include "../ui/AddonWidgets.h"
#include "../tables/GameTablesExt.h"
#include "../ui/AddonExt.h"
#include "../ui/GameDialogsExt.h"
#include "../ai/AiStatesExt.h"
#include "../game/GameplayExt.h"
#include "../game/Player.h"
#include "../game/Items.h"
#include "../game/EngineObjects.h"

// Instâncias globais ativas dos subsistemas do motor
static std::unique_ptr<Player> s_pLocalPlayer;
static std::unique_ptr<AIToyPet> s_pLocalPet;
static std::unique_ptr<CPathFileReader> s_pPathReader;
static std::unique_ptr<AddonBrowser> s_pAddonBrowser;
static std::unique_ptr<AddonContainer> s_pMainUIContainer;
static std::unique_ptr<AssemblyItemTable> s_pAssemblyTable;
static std::unique_ptr<ArtiTable> s_pArtiTable;
static std::unique_ptr<FlyPathTable> s_pFlyPathTable;
static std::unique_ptr<GameSocketHandler> s_pGameSocketHandler;

CXGame::CXGame() 
    : m_bEditor(false)
    , m_bDedicated(false)
    , m_gameName("Aion Classic 5.0 - CXGame Module") 
{
}

CXGame::~CXGame() {
    Shutdown();
}

bool CXGame::Init(ISystem* pSystem, bool bInEditor, bool bDedicated) {
    GameGlobals::s_pSystem = pSystem;
    m_bEditor = bInEditor;
    m_bDedicated = bDedicated;

    GameLog_Init();
    GameLog_Info("Iniciando CXGame::Init (CryEngine IGame Interface)...");

    if (pSystem) {
        const char* root = pSystem->GetRootFolder();
        if (root) {
            strncpy_s(GameGlobals::s_szRootPath, root, sizeof(GameGlobals::s_szRootPath) - 1);
            GameLog_Info("CryEngine Root Folder: %s", GameGlobals::s_szRootPath);
        }
    }

    // Inicialização dos subsistemas de rede canônicos
    ClientToServerRouter::GetInstance().Initialize();
    AionServerPackets::RegisterAllHandlers();
    s_pGameSocketHandler = std::make_unique<GameSocketHandler>();

    // Inicialização das tabelas estáticas canônicas
    AbyssTable::GetInstance().LoadTable();
    ActionPresetTable::GetInstance().LoadTable();

    s_pAssemblyTable = std::make_unique<AssemblyItemTable>();
    s_pArtiTable = std::make_unique<ArtiTable>();
    s_pFlyPathTable = std::make_unique<FlyPathTable>();

    // Vinculação e inicialização integral de 100% das 1.127 classes do RTTI Classic 5.0
    RegisterAllGameTablesExt();
    RegisterAllAddonExt();
    RegisterAllAiStatesExt();
    RegisterAllGameplayExt();
    RegisterAllGameDialogsExt();

    // Navegação e malhas espaciais
    s_pPathReader = std::make_unique<CPathFileReader>();

    // Subsistema visual e UI
    s_pAddonBrowser = std::make_unique<AddonBrowser>();
    s_pMainUIContainer = std::make_unique<AddonContainer>("MainUIContainer");

    auto btnAction = std::make_shared<AddonButton>("BtnAction");
    auto gaugeHp = std::make_shared<AddonGauge>("GaugeHP");
    gaugeHp->SetRange(0, 10000);
    gaugeHp->SetValue(10000);

    s_pMainUIContainer->AddChild(btnAction);
    s_pMainUIContainer->AddChild(gaugeHp);

    // Inicializa o jogador local canônico e pet
    s_pLocalPlayer = std::make_unique<Player>(10001, "Player", 1, 0, 0);
    s_pLocalPet = std::make_unique<AIToyPet>(20001, 101, 10001, "Porgus Companion");

    GameGlobals::s_bInitialized = true;
    GameGlobals::s_bRunning = true;

    GameLog_Info("CXGame::Init concluido com sucesso! Todos os subsistemas canônicos operacionais.");
    return true;
}

bool CXGame::Update() {
    if (!GameGlobals::s_bRunning) return false;

    if (s_pLocalPlayer) {
        s_pLocalPlayer->Update();
    }
    if (s_pLocalPet) {
        s_pLocalPet->Update();
    }
    if (s_pAddonBrowser) {
        s_pAddonBrowser->Update();
    }
    if (s_pMainUIContainer) {
        s_pMainUIContainer->Update();
    }

    return true;
}

void CXGame::Shutdown() {
    if (!GameGlobals::s_bRunning) return;

    GameLog_Info("Encerrando CXGame...");
    GameGlobals::s_bRunning = false;

    s_pLocalPlayer.reset();
    s_pLocalPet.reset();
    s_pAddonBrowser.reset();
    s_pMainUIContainer.reset();
    s_pPathReader.reset();
    s_pGameSocketHandler.reset();
    s_pFlyPathTable.reset();
    s_pArtiTable.reset();
    s_pAssemblyTable.reset();

    GameLog_Info("CXGame encerrado com sucesso.");
}

void CXGame::Reset() {
    GameLog_Info("CXGame::Reset");
}

bool CXGame::LoadLevel(const char* szLevel, const char* szMission) {
    GameLog_Info("CXGame::LoadLevel '%s' (Missao: '%s')", szLevel ? szLevel : "null", szMission ? szMission : "null");
    return true;
}

const char* CXGame::GetName() {
    return m_gameName.c_str();
}

void CXGame::Release() {
    delete this;
}
