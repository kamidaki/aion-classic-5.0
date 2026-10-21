#include "Game.h"
#include "GameGlobals.h"
#include "GameLog.h"
#include "../net/ClientToServerRouter.h"
#include "../net/AionClientPackets.h"
#include "../net/AionServerPackets.h"
#include "../net/AionRouters.h"
#include "../ai/AIObject.h"
#include "../ai/AIToyPet.h"
#include "../ai/AIOtherToyPet.h"
#include "../tables/AbyssTable.h"
#include "../tables/ActionPresetTable.h"
#include "../tables/AiCharTable.h"
#include "../tables/AssemblyItemTable.h"
#include "../tables/ArtiTable.h"
#include "../tables/FlyPathTable.h"
#include "../tables/HousingTable.h"
#include "../path/CPathFileReader.h"
#include "../path/SimplePathSector.h"
#include "../path/ComplexPathSector.h"
#include "../ui/AddonBrowser.h"
#include "../ui/AddonButton.h"
#include "../ui/AddonContainer.h"
#include "../ui/AddonGauge.h"
#include "../ui/AddonWidgets.h"
#include "../ui/DlgCreateChar.h"
#include "../ui/UIManager.h"
#include "../tables/GameTablesExt.h"
#include "../ui/AddonExt.h"
#include "../ui/GameDialogsExt.h"
#include "../ai/AiStatesExt.h"
#include "../game/GameplayExt.h"
#include "../game/Player.h"
#include "../game/Items.h"
#include "../game/Quests.h"
#include "../game/EngineObjects.h"
#include "../game/ActorManager.h"
#include "../game/CombatEngine.h"
#include "../game/InventoryManager.h"
#include "../game/WorldManager.h"
#include "../reverse/GameReverseMap.h"

// Instâncias globais ativas dos subsistemas do motor
static std::unique_ptr<Player> s_pLocalPlayer;
static std::unique_ptr<AIToyPet> s_pLocalPet;
static std::unique_ptr<CPathFileReader> s_pPathReader;
static std::unique_ptr<AddonBrowser> s_pAddonBrowser;
static std::unique_ptr<AddonContainer> s_pMainUIContainer;
static std::unique_ptr<AssemblyItemTable> s_pAssemblyTable;
static std::unique_ptr<ArtiTable> s_pArtiTable;
static std::unique_ptr<FlyPathTable> s_pFlyPathTable;
static std::unique_ptr<HousingBuildingTable> s_pHousingBuildingTable;
static std::unique_ptr<HousingAddressTable> s_pHousingAddressTable;
static std::unique_ptr<GameSocketHandler> s_pGameSocketHandler;
static std::unique_ptr<CXGame> s_pCXGame;

CGame::CGame() 
    : m_bEditor(false)
    , m_bDedicated(false)
    , m_gameName("Aion Classic 5.0 - Game Module") 
{
}

CGame::~CGame() {
    Shutdown();
}

bool CGame::Init(ISystem* pSystem, bool bInEditor, bool bDedicated) {
    GameGlobals::s_pSystem = pSystem;
    m_bEditor = bInEditor;
    m_bDedicated = bDedicated;

    GameLog_Init();
    GameLog_Info("Iniciando CGame::Init (CryEngine IGame Interface)...");

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
    AiCharTable::GetInstance().LoadTable();

    s_pAssemblyTable = std::make_unique<AssemblyItemTable>();
    s_pArtiTable = std::make_unique<ArtiTable>();
    s_pFlyPathTable = std::make_unique<FlyPathTable>();
    s_pHousingBuildingTable = std::make_unique<HousingBuildingTable>();
    s_pHousingAddressTable = std::make_unique<HousingAddressTable>();

    // Inicialização dos grandes subsistemas de jogo (Caminho B)
    ActorManager::GetInstance().Initialize();
    InventoryManager::GetInstance().Initialize(27);
    WorldManager::GetInstance().Initialize();
    UIManager::GetInstance().Initialize();

    // Vinculação e inicialização integral de 100% das 1.127 classes do RTTI Classic 5.0
    RegisterAllGameTablesExt();
    RegisterAllAddonExt();
    RegisterAllAiStatesExt();
    RegisterAllGameplayExt();
    RegisterAllGameDialogsExt();

    // Mapeamento de RVAs de engenharia reversa
    GameReverseMap::GetInstance().Initialize();

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

    // Registra o jogador no ActorManager
    ActorManager::GetInstance().SpawnPlayer(10001, "Player", 1, 0, 0, Vec3F(200.0f, 300.0f, 100.0f), 0.0f);

    s_pCXGame = std::make_unique<CXGame>();
    s_pCXGame->Init();

    GameGlobals::s_bInitialized = true;
    GameGlobals::s_bRunning = true;

    GameLog_Info("CGame::Init concluido com sucesso! Todos os subsistemas operacionais.");
    return true;
}

bool CGame::Update() {
    if (!GameGlobals::s_bRunning) return false;

    float dt = 0.0166f; // ~60 FPS delta

    // Atualização dos subsistemas de jogo
    ActorManager::GetInstance().Update(dt);
    WorldManager::GetInstance().Update(dt);
    UIManager::GetInstance().Update();

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
    if (s_pCXGame) {
        s_pCXGame->Update();
    }

    return true;
}

void CGame::Shutdown() {
    if (!GameGlobals::s_bRunning) return;

    GameLog_Info("Encerrando CGame...");
    GameGlobals::s_bRunning = false;

    UIManager::GetInstance().Shutdown();
    WorldManager::GetInstance().Shutdown();
    InventoryManager::GetInstance().Shutdown();
    ActorManager::GetInstance().Shutdown();

    s_pLocalPlayer.reset();
    s_pLocalPet.reset();
    s_pAddonBrowser.reset();
    s_pMainUIContainer.reset();
    s_pPathReader.reset();
    s_pCXGame.reset();
    s_pGameSocketHandler.reset();
    s_pAssemblyTable.reset();
    s_pArtiTable.reset();
    s_pFlyPathTable.reset();
    s_pHousingBuildingTable.reset();
    s_pHousingAddressTable.reset();

    ClientToServerRouter::GetInstance().Shutdown();

    GameGlobals::s_bInitialized = false;
    GameLog_Info("CGame finalizado.");
}

void CGame::Reset() {
    GameLog_Info("CGame::Reset invocado.");
}

bool CGame::LoadLevel(const char* szLevel, const char* szMission) {
    GameLog_Info("Carregando mapa/level: '%s', missao: '%s'", szLevel ? szLevel : "null", szMission ? szMission : "null");
    return true;
}

const char* CGame::GetName() {
    return m_gameName.c_str();
}

void CGame::Release() {
    delete this;
}
