#pragma once
#include <windows.h>
#include <atomic>
#include <cstdint>
#include <string>
#include <vector>
#include <typeinfo>
#include <exception>
#include "CombatMath.h"
#include "SkillGraph.h"
#include "../path/PathSector.h"
#include "../path/SimplePathSector.h"

struct ISystem;
struct IGame;

// RTTI .?AVCEFClientHandler@@ e Delegate
class CEFClientHandler {
public:
    CEFClientHandler();
    virtual ~CEFClientHandler();
    virtual const char* GetClassName() const { return "CEFClientHandler"; }
    class Delegate {
    public:
        Delegate();
        virtual ~Delegate();
        virtual const char* GetClassName() const { return "Delegate"; }
    };
};

// RTTI .?AVUnicodeInput@@ e CUIElementSink
class UnicodeInput {
public:
    UnicodeInput();
    virtual ~UnicodeInput();
    virtual const char* GetClassName() const { return "UnicodeInput"; }
    struct TsfInput {
        class CUIElementSink {
        public:
            CUIElementSink();
            virtual ~CUIElementSink();
            virtual const char* GetClassName() const { return "CUIElementSink"; }
        };
    };
};



// RTTI .?AVAccumulatedEnchantManager@@
class AccumulatedEnchantManager {
public:
    AccumulatedEnchantManager();
    virtual ~AccumulatedEnchantManager();
    virtual const char* GetClassName() const { return "AccumulatedEnchantManager"; }

    bool CanEnchant(int currentEnchant) const { return currentEnchant < 15; } // Classic é travado em +15
    float CalculateEnchantProbability(int itemLevel, int currentEnchant, int stoneLevel, int supplementBonusPercent) const;
    bool AttemptEnchant(int itemLevel, int& inOutEnchant, int stoneLevel, int supplementBonusPercent, float rnd0to1);
    void GetEnchantStatBonus(int itemType, int enchantLevel, int& outPAtk, int& outMBoost, int& outHP, int& outPDef) const;
};

// RTTI .?AVAchvItemData@@
class AchvItemData {
public:
    AchvItemData();
    virtual ~AchvItemData();
    virtual const char* GetClassName() const { return "AchvItemData"; }
};

// RTTI .?AVAionCefApp@@
class AionCefApp {
public:
    AionCefApp();
    virtual ~AionCefApp();
    virtual const char* GetClassName() const { return "AionCefApp"; }
};

namespace AionLookUtil {
    // RTTI .?AVAionLookGridItem@AionLookUtil@@
    class AionLookGridItem {
    public:
        AionLookGridItem();
        virtual ~AionLookGridItem();
        virtual const char* GetClassName() const { return "AionLookGridItem"; }
    };
}

// RTTI .?AVAionLookShop_ApparelPage@@
class AionLookShop_ApparelPage {
public:
    AionLookShop_ApparelPage();
    virtual ~AionLookShop_ApparelPage();
    virtual const char* GetClassName() const { return "AionLookShop_ApparelPage"; }
};

// RTTI .?AVAionLookShop_Base@@
class AionLookShop_Base {
public:
    AionLookShop_Base();
    virtual ~AionLookShop_Base();
    virtual const char* GetClassName() const { return "AionLookShop_Base"; }
};

// RTTI .?AVAionLookShop_CardPage@@
class AionLookShop_CardPage {
public:
    AionLookShop_CardPage();
    virtual ~AionLookShop_CardPage();
    virtual const char* GetClassName() const { return "AionLookShop_CardPage"; }
};

// RTTI .?AVAionLookShop_HairExchangePage@@
class AionLookShop_HairExchangePage {
public:
    AionLookShop_HairExchangePage();
    virtual ~AionLookShop_HairExchangePage();
    virtual const char* GetClassName() const { return "AionLookShop_HairExchangePage"; }
};

// RTTI .?AVAionLookShop_SpecialApparelPage@@
class AionLookShop_SpecialApparelPage {
public:
    AionLookShop_SpecialApparelPage();
    virtual ~AionLookShop_SpecialApparelPage();
    virtual const char* GetClassName() const { return "AionLookShop_SpecialApparelPage"; }
};

// RTTI .?AVBanFromChannelResult@@
class BanFromChannelResult {
public:
    BanFromChannelResult();
    virtual ~BanFromChannelResult();
    virtual const char* GetClassName() const { return "BanFromChannelResult"; }
};

namespace nsDlgBattlePass {
    // RTTI .?AVBattlePassGridItemData@nsDlgBattlePass@@
    class BattlePassGridItemData {
    public:
        BattlePassGridItemData();
        virtual ~BattlePassGridItemData();
        virtual const char* GetClassName() const { return "BattlePassGridItemData"; }
    };
}

namespace nsDlgBattlePass {
    // RTTI .?AVBattlePassMapScrollItemData@nsDlgBattlePass@@
    class BattlePassMapScrollItemData {
    public:
        BattlePassMapScrollItemData();
        virtual ~BattlePassMapScrollItemData();
        virtual const char* GetClassName() const { return "BattlePassMapScrollItemData"; }
    };
}

typedef struct {
    int      level;
    uint32_t freeItemId;
    int      freeCount;
    uint32_t premiumItemId;
    int      premiumCount;
} BattlePassRewardEntry;

typedef struct {
    int         missionId;
    std::string name;
    int         expReward;
    int         targetCount;
    int         currentCount;
    bool        isCompleted;
} BattlePassMissionEntry;

// RTTI .?AVBattlePassPathMap@@
class BattlePassPathMap {
public:
    BattlePassPathMap();
    virtual ~BattlePassPathMap();
    virtual const char* GetClassName() const { return "BattlePassPathMap"; }

    void AddMission(int missionId, const std::string& name, int expReward, int targetCount);
    bool UpdateProgress(int missionId, int delta, int& outGainedExp);
    int GetTotalExp() const { return m_totalExp; }
    int GetLevel() const { return (m_totalExp / 1000) + 1; } // Cada 1000 EXP sobe 1 nível

private:
    std::vector<BattlePassMissionEntry> m_missions;
    int m_totalExp;
};

// RTTI .?AVBattlePassRewardMap@@
class BattlePassRewardMap {
public:
    BattlePassRewardMap();
    virtual ~BattlePassRewardMap();
    virtual const char* GetClassName() const { return "BattlePassRewardMap"; }

    void SetReward(int level, uint32_t freeItemId, int freeCount, uint32_t premItemId, int premCount);
    bool GetReward(int level, uint32_t& outFreeId, int& outFreeCount, uint32_t& outPremId, int& outPremCount) const;
    size_t GetRewardCount() const { return m_rewards.size(); }

private:
    std::vector<BattlePassRewardEntry> m_rewards;
};

namespace ATL {
    // RTTI .?AVCComObjectRootBase@ATL@@
    class CComObjectRootBase {
    public:
        CComObjectRootBase();
        virtual ~CComObjectRootBase();
        virtual const char* GetClassName() const { return "CComObjectRootBase"; }
    };
}

namespace ATL {
    // RTTI .?AVCMessageMap@ATL@@
    class CMessageMap {
    public:
        CMessageMap();
        virtual ~CMessageMap();
        virtual const char* GetClassName() const { return "CMessageMap"; }
    };
}

// RTTI .?AVCannonManager@@
class CannonManager {
public:
    CannonManager();
    virtual ~CannonManager();
    virtual const char* GetClassName() const { return "CannonManager"; }
};

// RTTI .?AVCefApp@@
class CefApp {
public:
    CefApp();
    virtual ~CefApp();
    virtual const char* GetClassName() const { return "CefApp"; }
};

// RTTI .?AVCefBaseRefCounted@@
class CefBaseRefCounted {
public:
    CefBaseRefCounted();
    virtual ~CefBaseRefCounted();
    virtual const char* GetClassName() const { return "CefBaseRefCounted"; }
};

// RTTI .?AVCefClient@@
class CefClient {
public:
    CefClient();
    virtual ~CefClient();
    virtual const char* GetClassName() const { return "CefClient"; }
};

// RTTI .?AVCefCookieVisitor@@
class CefCookieVisitor {
public:
    CefCookieVisitor();
    virtual ~CefCookieVisitor();
    virtual const char* GetClassName() const { return "CefCookieVisitor"; }
};

// RTTI .?AVCefDisplayHandler@@
class CefDisplayHandler {
public:
    CefDisplayHandler();
    virtual ~CefDisplayHandler();
    virtual const char* GetClassName() const { return "CefDisplayHandler"; }
};

// RTTI .?AVCefDownloadHandler@@
class CefDownloadHandler {
public:
    CefDownloadHandler();
    virtual ~CefDownloadHandler();
    virtual const char* GetClassName() const { return "CefDownloadHandler"; }
};

// RTTI .?AVCefLifeSpanHandler@@
class CefLifeSpanHandler {
public:
    CefLifeSpanHandler();
    virtual ~CefLifeSpanHandler();
    virtual const char* GetClassName() const { return "CefLifeSpanHandler"; }
};

// RTTI .?AVCefLoadHandler@@
class CefLoadHandler {
public:
    CefLoadHandler();
    virtual ~CefLoadHandler();
    virtual const char* GetClassName() const { return "CefLoadHandler"; }
};

// RTTI .?AVCefMainArgs@@
class CefMainArgs {
public:
    CefMainArgs();
    virtual ~CefMainArgs();
    virtual const char* GetClassName() const { return "CefMainArgs"; }
};

// RTTI .?AVCefPoint@@
class CefPoint {
public:
    CefPoint();
    virtual ~CefPoint();
    virtual const char* GetClassName() const { return "CefPoint"; }
};

// RTTI .?AVCefRange@@
class CefRange {
public:
    CefRange();
    virtual ~CefRange();
    virtual const char* GetClassName() const { return "CefRange"; }
};

// RTTI .?AVCefRect@@
class CefRect {
public:
    CefRect();
    virtual ~CefRect();
    virtual const char* GetClassName() const { return "CefRect"; }
};

// RTTI .?AVCefRenderHandler@@
class CefRenderHandler {
public:
    CefRenderHandler();
    virtual ~CefRenderHandler();
    virtual const char* GetClassName() const { return "CefRenderHandler"; }
};

// RTTI .?AVCefRequestHandler@@
class CefRequestHandler {
public:
    CefRequestHandler();
    virtual ~CefRequestHandler();
    virtual const char* GetClassName() const { return "CefRequestHandler"; }
};

// RTTI .?AVCefResourceHandler@@
class CefResourceHandler {
public:
    CefResourceHandler();
    virtual ~CefResourceHandler();
    virtual const char* GetClassName() const { return "CefResourceHandler"; }
};

// RTTI .?AVCefResourceRequestHandler@@
class CefResourceRequestHandler {
public:
    CefResourceRequestHandler();
    virtual ~CefResourceRequestHandler();
    virtual const char* GetClassName() const { return "CefResourceRequestHandler"; }
};

// RTTI .?AVCefSchemeHandlerFactory@@
class CefSchemeHandlerFactory {
public:
    CefSchemeHandlerFactory();
    virtual ~CefSchemeHandlerFactory();
    virtual const char* GetClassName() const { return "CefSchemeHandlerFactory"; }
};



// RTTI .?AVChangeChannelOperatorResult@@
class ChangeChannelOperatorResult {
public:
    ChangeChannelOperatorResult();
    virtual ~ChangeChannelOperatorResult();
    virtual const char* GetClassName() const { return "ChangeChannelOperatorResult"; }
};

// RTTI .?AVChannelBannedMemberResult@@
class ChannelBannedMemberResult {
public:
    ChannelBannedMemberResult();
    virtual ~ChannelBannedMemberResult();
    virtual const char* GetClassName() const { return "ChannelBannedMemberResult"; }
};

// RTTI .?AVChannelMemberResult@@
class ChannelMemberResult {
public:
    ChannelMemberResult();
    virtual ~ChannelMemberResult();
    virtual const char* GetClassName() const { return "ChannelMemberResult"; }
};

// RTTI .?AVChannelName@@
class ChannelName {
public:
    ChannelName();
    virtual ~ChannelName();
    virtual const char* GetClassName() const { return "ChannelName"; }
};

// RTTI .?AVChannelOperatorChanged@@
class ChannelOperatorChanged {
public:
    ChannelOperatorChanged();
    virtual ~ChannelOperatorChanged();
    virtual const char* GetClassName() const { return "ChannelOperatorChanged"; }
};

// RTTI .?AVCharTraceAgent@@
class CharTraceAgent {
public:
    CharTraceAgent();
    virtual ~CharTraceAgent();
    virtual const char* GetClassName() const { return "CharTraceAgent"; }
};

// RTTI .?AVCharacterObject@@
class CharacterObject {
public:
    CharacterObject();
    virtual ~CharacterObject();
    virtual const char* GetClassName() const { return "CharacterObject"; }
};

// RTTI .?AVChatName@@
class ChatName {
public:
    ChatName();
    virtual ~ChatName();
    virtual const char* GetClassName() const { return "ChatName"; }
};

// RTTI .?AVCheckPrivacyAgreementClient@@
class CheckPrivacyAgreementClient {
public:
    CheckPrivacyAgreementClient();
    virtual ~CheckPrivacyAgreementClient();
    virtual const char* GetClassName() const { return "CheckPrivacyAgreementClient"; }
};

// RTTI .?AVCligateHandler@@
class CligateHandler {
public:
    CligateHandler();
    virtual ~CligateHandler();
    virtual const char* GetClassName() const { return "CligateHandler"; }
};

// RTTI .?AVConfirmedEnchant@@
class ConfirmedEnchant {
public:
    ConfirmedEnchant();
    virtual ~ConfirmedEnchant();
    virtual const char* GetClassName() const { return "ConfirmedEnchant"; }
};

// RTTI .?AVCpathFileMapping@@
class CpathFileMapping {
public:
    CpathFileMapping();
    virtual ~CpathFileMapping();
    virtual const char* GetClassName() const { return "CpathFileMapping"; }
};



namespace Json {
    // RTTI .?AVDefaultValueAllocator@Json@@
    class DefaultValueAllocator {
    public:
        DefaultValueAllocator();
        virtual ~DefaultValueAllocator();
        virtual const char* GetClassName() const { return "DefaultValueAllocator"; }
    };
}

namespace MixerLib {
    // RTTI .?AVDestLine@MixerLib@@
    class DestLine {
    public:
        DestLine();
        virtual ~DestLine();
        virtual const char* GetClassName() const { return "DestLine"; }
    };
}

// RTTI .?AVDevToolClientHandler@@
class DevToolClientHandler {
public:
    DevToolClientHandler();
    virtual ~DevToolClientHandler();
    virtual const char* GetClassName() const { return "DevToolClientHandler"; }
};

// RTTI .?AVDoorObject@@
class DoorObject {
public:
    DoorObject();
    virtual ~DoorObject();
    virtual const char* GetClassName() const { return "DoorObject"; }
};

// RTTI .?AVEmoticonItem@@
class EmoticonItem {
public:
    EmoticonItem();
    virtual ~EmoticonItem();
    virtual const char* GetClassName() const { return "EmoticonItem"; }
};

// RTTI .?AVEquipItemHandler@@
class EquipItemHandler {
public:
    EquipItemHandler();
    virtual ~EquipItemHandler();
    virtual const char* GetClassName() const { return "EquipItemHandler"; }
};

// RTTI .?AVEquipment@@
class Equipment {
public:
    Equipment();
    virtual ~Equipment();
    virtual const char* GetClassName() const { return "Equipment"; }
};

// RTTI .?AVEquipmentChangeItem@@
class EquipmentChangeItem {
public:
    EquipmentChangeItem();
    virtual ~EquipmentChangeItem();
    virtual const char* GetClassName() const { return "EquipmentChangeItem"; }
};

// RTTI .?AVExtendedObject@@
class ExtendedObject {
public:
    ExtendedObject();
    virtual ~ExtendedObject();
    virtual const char* GetClassName() const { return "ExtendedObject"; }
};

// RTTI .?AVFloaterGroupBase@@
class FloaterGroupBase {
public:
    FloaterGroupBase();
    virtual ~FloaterGroupBase();
    virtual const char* GetClassName() const { return "FloaterGroupBase"; }
};

// RTTI .?AVGEContextHandler@@
class GEContextHandler {
public:
    GEContextHandler();
    virtual ~GEContextHandler();
    virtual const char* GetClassName() const { return "GEContextHandler"; }
};

// RTTI .?AVGEHandlerDecorator@@
class GEHandlerDecorator {
public:
    GEHandlerDecorator();
    virtual ~GEHandlerDecorator();
    virtual const char* GetClassName() const { return "GEHandlerDecorator"; }
};

// RTTI .?AVGSObject@@
class GSObject {
public:
    GSObject();
    virtual ~GSObject();
    virtual const char* GetClassName() const { return "GSObject"; }
};

namespace QuickSlotAutoUseSystem {
    // RTTI .?AVGameEventChangeSlotSkillLevelData@QuickSlotAutoUseSystem@@
    class GameEventChangeSlotSkillLevelData {
    public:
        GameEventChangeSlotSkillLevelData();
        virtual ~GameEventChangeSlotSkillLevelData();
        virtual const char* GetClassName() const { return "GameEventChangeSlotSkillLevelData"; }
    };
}

namespace QuickSlotAutoUseSystem {
    // RTTI .?AVGameEventData@QuickSlotAutoUseSystem@@
    class GameEventData {
    public:
        GameEventData();
        virtual ~GameEventData();
        virtual const char* GetClassName() const { return "GameEventData"; }
    };
}

namespace QuickSlotAutoUseSystem {
    // RTTI .?AVGameEventRemoveSlotItem@QuickSlotAutoUseSystem@@
    class GameEventRemoveSlotItem {
    public:
        GameEventRemoveSlotItem();
        virtual ~GameEventRemoveSlotItem();
        virtual const char* GetClassName() const { return "GameEventRemoveSlotItem"; }
    };
}

// RTTI .?AVGameObject@@
class GameObject {
public:
    GameObject();
    virtual ~GameObject();
    virtual const char* GetClassName() const { return "GameObject"; }
};

// RTTI .?AVGameSystem@@
class GameSystem {
public:
    GameSystem();
    virtual ~GameSystem();
    virtual const char* GetClassName() const { return "GameSystem"; }

    static HMODULE s_hModule;
    static ISystem* s_pSystem;
    static IGame*   s_pGameInstance;
    static std::atomic<bool> s_bInitialized;
    static std::atomic<bool> s_bRunning;
    static char s_szRootPath[MAX_PATH];
};

// RTTI .?AVGameUtils@@
class GameUtils {
public:
    GameUtils();
    virtual ~GameUtils();
    virtual const char* GetClassName() const { return "GameUtils"; }
};

// RTTI .?AVGetAllCookieVisitor@@
class GetAllCookieVisitor {
public:
    GetAllCookieVisitor();
    virtual ~GetAllCookieVisitor();
    virtual const char* GetClassName() const { return "GetAllCookieVisitor"; }
};

// RTTI .?AVGetChatServerAddrResult@@
class GetChatServerAddrResult {
public:
    GetChatServerAddrResult();
    virtual ~GetChatServerAddrResult();
    virtual const char* GetClassName() const { return "GetChatServerAddrResult"; }
};

// RTTI .?AVGetUserGameInfoResult@@
class GetUserGameInfoResult {
public:
    GetUserGameInfoResult();
    virtual ~GetUserGameInfoResult();
    virtual const char* GetClassName() const { return "GetUserGameInfoResult"; }
};

// RTTI .?AVGoodsItem@@
class GoodsItem {
public:
    GoodsItem();
    virtual ~GoodsItem();
    virtual const char* GetClassName() const { return "GoodsItem"; }
};

// RTTI .?AVGoodsPackageItem@@
class GoodsPackageItem {
public:
    GoodsPackageItem();
    virtual ~GoodsPackageItem();
    virtual const char* GetClassName() const { return "GoodsPackageItem"; }
};

// RTTI .?AVGridItem@@
class GridItem {
public:
    GridItem();
    virtual ~GridItem();
    virtual const char* GetClassName() const { return "GridItem"; }
};

// RTTI .?AVGridItemData@@
class GridItemData {
public:
    GridItemData();
    virtual ~GridItemData();
    virtual const char* GetClassName() const { return "GridItemData"; }
};

namespace nsDlgGuild {
    // RTTI .?AVGuildBuffGridItemData@nsDlgGuild@@
    class GuildBuffGridItemData {
    public:
        GuildBuffGridItemData();
        virtual ~GuildBuffGridItemData();
        virtual const char* GetClassName() const { return "GuildBuffGridItemData"; }
    };
}

namespace nsDlgGuild {
    // RTTI .?AVGuildCraftGiveMaterialGridItemData@nsDlgGuild@@
    class GuildCraftGiveMaterialGridItemData {
    public:
        GuildCraftGiveMaterialGridItemData();
        virtual ~GuildCraftGiveMaterialGridItemData();
        virtual const char* GetClassName() const { return "GuildCraftGiveMaterialGridItemData"; }
    };
}

namespace nsDlgGuild {
    // RTTI .?AVGuildCraftGridItemData@nsDlgGuild@@
    class GuildCraftGridItemData {
    public:
        GuildCraftGridItemData();
        virtual ~GuildCraftGridItemData();
        virtual const char* GetClassName() const { return "GuildCraftGridItemData"; }
    };
}

namespace nsDlgGuild {
    // RTTI .?AVGuildCraftMaterialGridItemData@nsDlgGuild@@
    class GuildCraftMaterialGridItemData {
    public:
        GuildCraftMaterialGridItemData();
        virtual ~GuildCraftMaterialGridItemData();
        virtual const char* GetClassName() const { return "GuildCraftMaterialGridItemData"; }
    };
}

namespace nsDlgGuild {
    // RTTI .?AVGuildDonationGridItemData@nsDlgGuild@@
    class GuildDonationGridItemData {
    public:
        GuildDonationGridItemData();
        virtual ~GuildDonationGridItemData();
        virtual const char* GetClassName() const { return "GuildDonationGridItemData"; }
    };
}

// RTTI .?AVGuildEmblemMap@@
class GuildEmblemMap {
public:
    GuildEmblemMap();
    virtual ~GuildEmblemMap();
    virtual const char* GetClassName() const { return "GuildEmblemMap"; }
};

namespace nsDlgGuild {
    // RTTI .?AVGuildMissionGridItemData@nsDlgGuild@@
    class GuildMissionGridItemData {
    public:
        GuildMissionGridItemData();
        virtual ~GuildMissionGridItemData();
        virtual const char* GetClassName() const { return "GuildMissionGridItemData"; }
    };
}

namespace nsDlgGuild {
    // RTTI .?AVGuildRewardGridItemData@nsDlgGuild@@
    class GuildRewardGridItemData {
    public:
        GuildRewardGridItemData();
        virtual ~GuildRewardGridItemData();
        virtual const char* GetClassName() const { return "GuildRewardGridItemData"; }
    };
}

#include "../net/AionRouters.h"

// RTTI .?AVHomePageGridItemData@@
class HomePageGridItemData {
public:
    HomePageGridItemData();
    virtual ~HomePageGridItemData();
    virtual const char* GetClassName() const { return "HomePageGridItemData"; }
};

// RTTI .?AVIEventTimer@@
class IEventTimer {
public:
    IEventTimer();
    virtual ~IEventTimer();
    virtual const char* GetClassName() const { return "IEventTimer"; }
};

// RTTI .?AVIItemSelectHandler@@
class IItemSelectHandler {
public:
    IItemSelectHandler();
    virtual ~IItemSelectHandler();
    virtual const char* GetClassName() const { return "IItemSelectHandler"; }
};

// RTTI .?AVIMXWrapper@@
class IMXWrapper {
public:
    IMXWrapper();
    virtual ~IMXWrapper();
    virtual const char* GetClassName() const { return "IMXWrapper"; }
};

// RTTI .?AVIPhysicsEventClient@@
class IPhysicsEventClient {
public:
    IPhysicsEventClient();
    virtual ~IPhysicsEventClient();
    virtual const char* GetClassName() const { return "IPhysicsEventClient"; }
};

// RTTI .?AVIPhysicsStreamer@@
class IPhysicsStreamer {
public:
    IPhysicsStreamer();
    virtual ~IPhysicsStreamer();
    virtual const char* GetClassName() const { return "IPhysicsStreamer"; }
};

// RTTI .?AVIScriptMain@@
class IScriptMain {
public:
    IScriptMain();
    virtual ~IScriptMain();
    virtual const char* GetClassName() const { return "IScriptMain"; }
};

// RTTI .?AVInExName@@
class InExName {
public:
    InExName();
    virtual ~InExName();
    virtual const char* GetClassName() const { return "InExName"; }
};

namespace nsDlgProbabilityItemInfo {
    // RTTI .?AVIndexInfoGridItemData@nsDlgProbabilityItemInfo@@
    class IndexInfoGridItemData {
    public:
        IndexInfoGridItemData();
        virtual ~IndexInfoGridItemData();
        virtual const char* GetClassName() const { return "IndexInfoGridItemData"; }
    };
}

// RTTI .?AVIndunGridRewardItemData@@
class IndunGridRewardItemData {
public:
    IndunGridRewardItemData();
    virtual ~IndunGridRewardItemData();
    virtual const char* GetClassName() const { return "IndunGridRewardItemData"; }
};

// RTTI .?AVIndunGridStandardRewardItemData@@
class IndunGridStandardRewardItemData {
public:
    IndunGridStandardRewardItemData();
    virtual ~IndunGridStandardRewardItemData();
    virtual const char* GetClassName() const { return "IndunGridStandardRewardItemData"; }
};

namespace nsDlgToyPetItemInfo {
    // RTTI .?AVInfoGridItemData@nsDlgToyPetItemInfo@@
    class InfoGridItemData {
    public:
        InfoGridItemData();
        virtual ~InfoGridItemData();
        virtual const char* GetClassName() const { return "InfoGridItemData"; }
    };
}

// RTTI .?AVIngameShopItem@@
class IngameShopItem {
public:
    IngameShopItem();
    virtual ~IngameShopItem();
    virtual const char* GetClassName() const { return "IngameShopItem"; }
};

// RTTI .?AVInterfaceInventoryItemSlots@@
class InterfaceInventoryItemSlots {
public:
    InterfaceInventoryItemSlots();
    virtual ~InterfaceInventoryItemSlots();
    virtual const char* GetClassName() const { return "InterfaceInventoryItemSlots"; }
};

// RTTI .?AVInterfaceLoginEvent@@
class InterfaceLoginEvent {
public:
    InterfaceLoginEvent();
    virtual ~InterfaceLoginEvent();
    virtual const char* GetClassName() const { return "InterfaceLoginEvent"; }
};

// RTTI .?AVInvItemSelectHandler@@
class InvItemSelectHandler {
public:
    InvItemSelectHandler();
    virtual ~InvItemSelectHandler();
    virtual const char* GetClassName() const { return "InvItemSelectHandler"; }
};

// RTTI .?AVInvItemSelectHandler_EquipChange@@
class InvItemSelectHandler_EquipChange {
public:
    InvItemSelectHandler_EquipChange();
    virtual ~InvItemSelectHandler_EquipChange();
    virtual const char* GetClassName() const { return "InvItemSelectHandler_EquipChange"; }
};

// RTTI .?AVInvItemSelectHandler_Upgrade@@
class InvItemSelectHandler_Upgrade {
public:
    InvItemSelectHandler_Upgrade();
    virtual ~InvItemSelectHandler_Upgrade();
    virtual const char* GetClassName() const { return "InvItemSelectHandler_Upgrade"; }
};

// RTTI .?AVInventoryItemSlots@@
class InventoryItemSlots {
public:
    InventoryItemSlots();
    virtual ~InventoryItemSlots();
    virtual const char* GetClassName() const { return "InventoryItemSlots"; }
};

// RTTI .?AVInventoryItemSlotsNormal@@
class InventoryItemSlotsNormal {
public:
    InventoryItemSlotsNormal();
    virtual ~InventoryItemSlotsNormal();
    virtual const char* GetClassName() const { return "InventoryItemSlotsNormal"; }
};

// RTTI .?AVItemComposeNormalPage@@
class ItemComposeNormalPage {
public:
    ItemComposeNormalPage();
    virtual ~ItemComposeNormalPage();
    virtual const char* GetClassName() const { return "ItemComposeNormalPage"; }
};

// RTTI .?AVItemComposePage@@
class ItemComposePage {
public:
    ItemComposePage();
    virtual ~ItemComposePage();
    virtual const char* GetClassName() const { return "ItemComposePage"; }
};

// RTTI .?AVItemComposeUpgradePage@@
class ItemComposeUpgradePage {
public:
    ItemComposeUpgradePage();
    virtual ~ItemComposeUpgradePage();
    virtual const char* GetClassName() const { return "ItemComposeUpgradePage"; }
};

// RTTI .?AVItemPageGridItemData@@
class ItemPageGridItemData {
public:
    ItemPageGridItemData();
    virtual ~ItemPageGridItemData();
    virtual const char* GetClassName() const { return "ItemPageGridItemData"; }
};

// RTTI .?AVKinaVendorTab@@
class KinaVendorTab {
public:
    KinaVendorTab();
    virtual ~KinaVendorTab();
    virtual const char* GetClassName() const { return "KinaVendorTab"; }
};

// RTTI .?AVLeftChannelNotity@@
class LeftChannelNotity {
public:
    LeftChannelNotity();
    virtual ~LeftChannelNotity();
    virtual const char* GetClassName() const { return "LeftChannelNotity"; }
};

namespace MixerLib {
    // RTTI .?AVLineBase@MixerLib@@
    class LineBase {
    public:
        LineBase();
        virtual ~LineBase();
        virtual const char* GetClassName() const { return "LineBase"; }
    };
}

namespace LOG_LIB {
    // RTTI .?AVLogFileCreateException@LOG_LIB@@
    class LogFileCreateException {
    public:
        LogFileCreateException();
        virtual ~LogFileCreateException();
        virtual const char* GetClassName() const { return "LogFileCreateException"; }
    };
}

// RTTI .?AVMXWTimer@@
class MXWTimer {
public:
    MXWTimer();
    virtual ~MXWTimer();
    virtual const char* GetClassName() const { return "MXWTimer"; }
};

// RTTI .?AVMXWrapper@@
class MXWrapper {
public:
    MXWrapper();
    virtual ~MXWrapper();
    virtual const char* GetClassName() const { return "MXWrapper"; }
};

// RTTI .?AVMXWrapperCallback@@
class MXWrapperCallback {
public:
    MXWrapperCallback();
    virtual ~MXWrapperCallback();
    virtual const char* GetClassName() const { return "MXWrapperCallback"; }
};

// RTTI .?AVMacroItem@@
class MacroItem {
public:
    MacroItem();
    virtual ~MacroItem();
    virtual const char* GetClassName() const { return "MacroItem"; }
};

// RTTI .?AVMacroNode@@
class MacroNode {
public:
    MacroNode();
    virtual ~MacroNode();
    virtual const char* GetClassName() const { return "MacroNode"; }
};

namespace nsDlgSpinelShop {
    // RTTI .?AVMainGridItemData@nsDlgSpinelShop@@
    class MainGridItemData {
    public:
        MainGridItemData();
        virtual ~MainGridItemData();
        virtual const char* GetClassName() const { return "MainGridItemData"; }
    };
}

// RTTI .?AVMaterialGridItemData@@
class MaterialGridItemData {
public:
    MaterialGridItemData();
    virtual ~MaterialGridItemData();
    virtual const char* GetClassName() const { return "MaterialGridItemData"; }
};

// RTTI .?AVMaxCharNumHandler@@
class MaxCharNumHandler {
public:
    MaxCharNumHandler();
    virtual ~MaxCharNumHandler();
    virtual const char* GetClassName() const { return "MaxCharNumHandler"; }
};

// RTTI .?AVMaxLevelHandler@@
class MaxLevelHandler {
public:
    MaxLevelHandler();
    virtual ~MaxLevelHandler();
    virtual const char* GetClassName() const { return "MaxLevelHandler"; }
};

// RTTI .?AVMemoManager@@
class MemoManager {
public:
    MemoManager();
    virtual ~MemoManager();
    virtual const char* GetClassName() const { return "MemoManager"; }
};

// RTTI .?AVMinCharNumHandler@@
class MinCharNumHandler {
public:
    MinCharNumHandler();
    virtual ~MinCharNumHandler();
    virtual const char* GetClassName() const { return "MinCharNumHandler"; }
};

// RTTI .?AVMinLevelHandler@@
class MinLevelHandler {
public:
    MinLevelHandler();
    virtual ~MinLevelHandler();
    virtual const char* GetClassName() const { return "MinLevelHandler"; }
};

namespace MixerLib {
    // RTTI .?AVMixerBase@MixerLib@@
    class MixerBase {
    public:
        MixerBase();
        virtual ~MixerBase();
        virtual const char* GetClassName() const { return "MixerBase"; }
    };
}

namespace MixerLib {
    // RTTI .?AVMixerIn6@MixerLib@@
    class MixerIn6 {
    public:
        MixerIn6();
        virtual ~MixerIn6();
        virtual const char* GetClassName() const { return "MixerIn6"; }
    };
}

namespace MixerLib {
    // RTTI .?AVMixerIn@MixerLib@@
    class MixerIn {
    public:
        MixerIn();
        virtual ~MixerIn();
        virtual const char* GetClassName() const { return "MixerIn"; }
    };
}

namespace MixerLib {
    // RTTI .?AVMixerOut6@MixerLib@@
    class MixerOut6 {
    public:
        MixerOut6();
        virtual ~MixerOut6();
        virtual const char* GetClassName() const { return "MixerOut6"; }
    };
}

namespace MixerLib {
    // RTTI .?AVMixerOut@MixerLib@@
    class MixerOut {
    public:
        MixerOut();
        virtual ~MixerOut();
        virtual const char* GetClassName() const { return "MixerOut"; }
    };
}

// RTTI .?AVNCTalk@@
class NCTalk {
public:
    NCTalk();
    virtual ~NCTalk();
    virtual const char* GetClassName() const { return "NCTalk"; }
};

// RTTI .?AVNCTalkIpcServer@@
class NCTalkIpcServer {
public:
    NCTalkIpcServer();
    virtual ~NCTalkIpcServer();
    virtual const char* GetClassName() const { return "NCTalkIpcServer"; }
};

// RTTI .?AVNCTalkIpcServerHandler@@
class NCTalkIpcServerHandler {
public:
    NCTalkIpcServerHandler();
    virtual ~NCTalkIpcServerHandler();
    virtual const char* GetClassName() const { return "NCTalkIpcServerHandler"; }
};

// RTTI .?AVNCTalkTest@@
class NCTalkTest {
public:
    NCTalkTest();
    virtual ~NCTalkTest();
    virtual const char* GetClassName() const { return "NCTalkTest"; }
};

namespace NCSDK {
    // RTTI .?AVNcAuth@NCSDK@@
    class NcAuth {
    public:
        NcAuth();
        virtual ~NcAuth();
        virtual const char* GetClassName() const { return "NcAuth"; }
    };
}

namespace NCSDK {
    // RTTI .?AVNcConfiguration@NCSDK@@
    class NcConfiguration {
    public:
        NcConfiguration();
        virtual ~NcConfiguration();
        virtual const char* GetClassName() const { return "NcConfiguration"; }
    };
}

namespace NCSDK {
    // RTTI .?AVNcScv@NCSDK@@
    class NcScv {
    public:
        NcScv();
        virtual ~NcScv();
        virtual const char* GetClassName() const { return "NcScv"; }
    };
}

namespace NCSDK {
    // RTTI .?AVNcSecurityService@NCSDK@@
    class NcSecurityService {
    public:
        NcSecurityService();
        virtual ~NcSecurityService();
        virtual const char* GetClassName() const { return "NcSecurityService"; }
    };
}

// RTTI .?AVNewMapCtrl@@
class NewMapCtrl {
public:
    NewMapCtrl();
    virtual ~NewMapCtrl();
    virtual const char* GetClassName() const { return "NewMapCtrl"; }
};

// RTTI .?AVObjEnemyHandler@@
class ObjEnemyHandler {
public:
    ObjEnemyHandler();
    virtual ~ObjEnemyHandler();
    virtual const char* GetClassName() const { return "ObjEnemyHandler"; }
};

// RTTI .?AVObjTypeHandler@@
class ObjTypeHandler {
public:
    ObjTypeHandler();
    virtual ~ObjTypeHandler();
    virtual const char* GetClassName() const { return "ObjTypeHandler"; }
};

// RTTI .?AVOptionItemHandler@@
class OptionItemHandler {
public:
    OptionItemHandler();
    virtual ~OptionItemHandler();
    virtual const char* GetClassName() const { return "OptionItemHandler"; }
};

// RTTI .?AVOverseasEvent@@
class OverseasEvent {
public:
    OverseasEvent();
    virtual ~OverseasEvent();
    virtual const char* GetClassName() const { return "OverseasEvent"; }
};

// RTTI .?AVOverseasEventSystem@@
class OverseasEventSystem {
public:
    OverseasEventSystem();
    virtual ~OverseasEventSystem();
    virtual const char* GetClassName() const { return "OverseasEventSystem"; }
};

// RTTI .?AVPAUseDisassemblyItem@@
class PAUseDisassemblyItem {
public:
    PAUseDisassemblyItem();
    virtual ~PAUseDisassemblyItem();
    virtual const char* GetClassName() const { return "PAUseDisassemblyItem"; }
};

// RTTI .?AVPCDisassemblyItem@@
class PCDisassemblyItem {
public:
    PCDisassemblyItem();
    virtual ~PCDisassemblyItem();
    virtual const char* GetClassName() const { return "PCDisassemblyItem"; }
};

// RTTI .?AVPCItemUseEnded@@
class PCItemUseEnded {
public:
    PCItemUseEnded();
    virtual ~PCItemUseEnded();
    virtual const char* GetClassName() const { return "PCItemUseEnded"; }
};

// RTTI .?AVPartyItem@@
class PartyItem {
public:
    PartyItem();
    virtual ~PartyItem();
    virtual const char* GetClassName() const { return "PartyItem"; }
};

// RTTI .?AVPendingAction@@
class PendingAction {
public:
    PendingAction();
    virtual ~PendingAction();
    virtual const char* GetClassName() const { return "PendingAction"; }
};

// RTTI .?AVPendingCheck@@
class PendingCheck {
public:
    PendingCheck();
    virtual ~PendingCheck();
    virtual const char* GetClassName() const { return "PendingCheck"; }
};

// RTTI .?AVPetItem@@
class PetItem {
public:
    PetItem();
    virtual ~PetItem();
    virtual const char* GetClassName() const { return "PetItem"; }
};

// RTTI .?AVPing@@
class Ping {
public:
    Ping();
    virtual ~Ping();
    virtual const char* GetClassName() const { return "Ping"; }
};

// RTTI .?AVProjectileObject@@
class ProjectileObject {
public:
    ProjectileObject();
    virtual ~ProjectileObject();
    virtual const char* GetClassName() const { return "ProjectileObject"; }
};

namespace nsDlgPromotion {
    // RTTI .?AVPromotionGridItemData@nsDlgPromotion@@
    class PromotionGridItemData {
    public:
        PromotionGridItemData();
        virtual ~PromotionGridItemData();
        virtual const char* GetClassName() const { return "PromotionGridItemData"; }
    };
}

namespace CefResourceManager {
    // RTTI .?AVProvider@CefResourceManager@@
    class Provider {
    public:
        Provider();
        virtual ~Provider();
        virtual const char* GetClassName() const { return "Provider"; }
    };
}

// RTTI .?AVQuestIndicatorGridItemData@@
class QuestIndicatorGridItemData {
public:
    QuestIndicatorGridItemData();
    virtual ~QuestIndicatorGridItemData();
    virtual const char* GetClassName() const { return "QuestIndicatorGridItemData"; }
};

// RTTI .?AVQuestTabFrame_Working_NewMap@@
class QuestTabFrame_Working_NewMap {
public:
    QuestTabFrame_Working_NewMap();
    virtual ~QuestTabFrame_Working_NewMap();
    virtual const char* GetClassName() const { return "QuestTabFrame_Working_NewMap"; }
};

// RTTI .?AVQunaVendorTab@@
class QunaVendorTab {
public:
    QunaVendorTab();
    virtual ~QunaVendorTab();
    virtual const char* GetClassName() const { return "QunaVendorTab"; }
};

// RTTI .?AVReachSpec@@
class ReachSpec {
public:
    ReachSpec();
    virtual ~ReachSpec();
    virtual const char* GetClassName() const { return "ReachSpec"; }
};

// RTTI .?AVResultMessage@@
class ResultMessage {
public:
    ResultMessage();
    virtual ~ResultMessage();
    virtual const char* GetClassName() const { return "ResultMessage"; }
};

namespace NS_DlgResurrect {
    // RTTI .?AVResurrectItemData@NS_DlgResurrect@@
    class ResurrectItemData {
    public:
        ResurrectItemData();
        virtual ~ResurrectItemData();
        virtual const char* GetClassName() const { return "ResurrectItemData"; }
    };
}

// RTTI .?AVRopeObject@@
class RopeObject {
public:
    RopeObject();
    virtual ~RopeObject();
    virtual const char* GetClassName() const { return "RopeObject"; }
};

// RTTI .?AVSPAMCheckClient@@
class SPAMCheckClient {
public:
    SPAMCheckClient();
    virtual ~SPAMCheckClient();
    virtual const char* GetClassName() const { return "SPAMCheckClient"; }
};

// RTTI .?AVSceneManager@@
class SceneManager {
public:
    SceneManager();
    virtual ~SceneManager();
    virtual const char* GetClassName() const { return "SceneManager"; }
};

// RTTI .?AVSearchChannelResult@@
class SearchChannelResult {
public:
    SearchChannelResult();
    virtual ~SearchChannelResult();
    virtual const char* GetClassName() const { return "SearchChannelResult"; }
};

// RTTI .?AVServerGridItemData@@
class ServerGridItemData {
public:
    ServerGridItemData();
    virtual ~ServerGridItemData();
    virtual const char* GetClassName() const { return "ServerGridItemData"; }
};




// RTTI .?AVSlotFuncDefaultHandler@@
class SlotFuncDefaultHandler {
public:
    SlotFuncDefaultHandler();
    virtual ~SlotFuncDefaultHandler();
    virtual const char* GetClassName() const { return "SlotFuncDefaultHandler"; }
};

// RTTI .?AVSlotFuncHandler_ItemSelect@@
class SlotFuncHandler_ItemSelect {
public:
    SlotFuncHandler_ItemSelect();
    virtual ~SlotFuncHandler_ItemSelect();
    virtual const char* GetClassName() const { return "SlotFuncHandler_ItemSelect"; }
};

// RTTI .?AVSlotFuncHandler_UpgradeItem@@
class SlotFuncHandler_UpgradeItem {
public:
    SlotFuncHandler_UpgradeItem();
    virtual ~SlotFuncHandler_UpgradeItem();
    virtual const char* GetClassName() const { return "SlotFuncHandler_UpgradeItem"; }
};

// RTTI .?AVSlotFuncHandler_UpgradeMatItem@@
class SlotFuncHandler_UpgradeMatItem {
public:
    SlotFuncHandler_UpgradeMatItem();
    virtual ~SlotFuncHandler_UpgradeMatItem();
    virtual const char* GetClassName() const { return "SlotFuncHandler_UpgradeMatItem"; }
};

// RTTI .?AVSoundEntityEvent@@
class SoundEntityEvent {
public:
    SoundEntityEvent();
    virtual ~SoundEntityEvent();
    virtual const char* GetClassName() const { return "SoundEntityEvent"; }
};

// RTTI .?AVSoundObject@@
class SoundObject {
public:
    SoundObject();
    virtual ~SoundObject();
    virtual const char* GetClassName() const { return "SoundObject"; }
};

// RTTI .?AVSoundObjectRandomAmbient@@
class SoundObjectRandomAmbient {
public:
    SoundObjectRandomAmbient();
    virtual ~SoundObjectRandomAmbient();
    virtual const char* GetClassName() const { return "SoundObjectRandomAmbient"; }
};

// RTTI .?AVSoundObjectSpot@@
class SoundObjectSpot {
public:
    SoundObjectSpot();
    virtual ~SoundObjectSpot();
    virtual const char* GetClassName() const { return "SoundObjectSpot"; }
};

// RTTI .?AVSoundObjectWeatherAmbient@@
class SoundObjectWeatherAmbient {
public:
    SoundObjectWeatherAmbient();
    virtual ~SoundObjectWeatherAmbient();
    virtual const char* GetClassName() const { return "SoundObjectWeatherAmbient"; }
};

// RTTI .?AVSoundObjectWeatherSync@@
class SoundObjectWeatherSync {
public:
    SoundObjectWeatherSync();
    virtual ~SoundObjectWeatherSync();
    virtual const char* GetClassName() const { return "SoundObjectWeatherSync"; }
};

// RTTI .?AVSpecialCraftCommonItemPage@@
class SpecialCraftCommonItemPage {
public:
    SpecialCraftCommonItemPage();
    virtual ~SpecialCraftCommonItemPage();
    virtual const char* GetClassName() const { return "SpecialCraftCommonItemPage"; }
};

// RTTI .?AVSpecialCraftEventItemPage@@
class SpecialCraftEventItemPage {
public:
    SpecialCraftEventItemPage();
    virtual ~SpecialCraftEventItemPage();
    virtual const char* GetClassName() const { return "SpecialCraftEventItemPage"; }
};

// RTTI .?AVSpecialCraftFavoritesPage@@
class SpecialCraftFavoritesPage {
public:
    SpecialCraftFavoritesPage();
    virtual ~SpecialCraftFavoritesPage();
    virtual const char* GetClassName() const { return "SpecialCraftFavoritesPage"; }
};

// RTTI .?AVSpecialCraftHomePage@@
class SpecialCraftHomePage {
public:
    SpecialCraftHomePage();
    virtual ~SpecialCraftHomePage();
    virtual const char* GetClassName() const { return "SpecialCraftHomePage"; }
};

// RTTI .?AVSpecialCraftItemPage@@
class SpecialCraftItemPage {
public:
    SpecialCraftItemPage();
    virtual ~SpecialCraftItemPage();
    virtual const char* GetClassName() const { return "SpecialCraftItemPage"; }
};

// RTTI .?AVSpecialCraftLimitedItemPage@@
class SpecialCraftLimitedItemPage {
public:
    SpecialCraftLimitedItemPage();
    virtual ~SpecialCraftLimitedItemPage();
    virtual const char* GetClassName() const { return "SpecialCraftLimitedItemPage"; }
};

// RTTI .?AVSpecialCraftPage@@
class SpecialCraftPage {
public:
    SpecialCraftPage();
    virtual ~SpecialCraftPage();
    virtual const char* GetClassName() const { return "SpecialCraftPage"; }
};

// RTTI .?AVSpecialCraftPromotionItemPage@@
class SpecialCraftPromotionItemPage {
public:
    SpecialCraftPromotionItemPage();
    virtual ~SpecialCraftPromotionItemPage();
    virtual const char* GetClassName() const { return "SpecialCraftPromotionItemPage"; }
};

// RTTI .?AVSpecialCraftSpecialItemPage@@
class SpecialCraftSpecialItemPage {
public:
    SpecialCraftSpecialItemPage();
    virtual ~SpecialCraftSpecialItemPage();
    virtual const char* GetClassName() const { return "SpecialCraftSpecialItemPage"; }
};

namespace MixerLib {
    // RTTI .?AVSrcLine@MixerLib@@
    class SrcLine {
    public:
        SrcLine();
        virtual ~SrcLine();
        virtual const char* GetClassName() const { return "SrcLine"; }
    };
}



// RTTI .?AVTabBase@@
class TabBase {
public:
    TabBase();
    virtual ~TabBase();
    virtual const char* GetClassName() const { return "TabBase"; }
};

// RTTI .?AVTagPointManager@@
class TagPointManager {
public:
    TagPointManager();
    virtual ~TagPointManager();
    virtual const char* GetClassName() const { return "TagPointManager"; }
};

// RTTI .?AVTcpNodeHandler@@
class TcpNodeHandler {
public:
    TcpNodeHandler();
    virtual ~TcpNodeHandler();
    virtual const char* GetClassName() const { return "TcpNodeHandler"; }
};


// RTTI .?AVToyPetListItem@@
class ToyPetListItem {
public:
    ToyPetListItem();
    virtual ~ToyPetListItem();
    virtual const char* GetClassName() const { return "ToyPetListItem"; }
};

// RTTI .?AVTransparentMapCtrl@@
class TransparentMapCtrl {
public:
    TransparentMapCtrl();
    virtual ~TransparentMapCtrl();
    virtual const char* GetClassName() const { return "TransparentMapCtrl"; }
};

// RTTI .?AVTutorialObserver@@
class TutorialObserver {
public:
    TutorialObserver();
    virtual ~TutorialObserver();
    virtual const char* GetClassName() const { return "TutorialObserver"; }
};

// RTTI .?AVTwitterClient@@
class TwitterClient {
public:
    TwitterClient();
    virtual ~TwitterClient();
    virtual const char* GetClassName() const { return "TwitterClient"; }
};

// RTTI .?AVUIAction@@
class UIAction {
public:
    UIAction();
    virtual ~UIAction();
    virtual const char* GetClassName() const { return "UIAction"; }
};

// RTTI .?AVUIActionChangeValue@@
class UIActionChangeValue {
public:
    UIActionChangeValue();
    virtual ~UIActionChangeValue();
    virtual const char* GetClassName() const { return "UIActionChangeValue"; }
};

// RTTI .?AVUIActionCheckFlag@@
class UIActionCheckFlag {
public:
    UIActionCheckFlag();
    virtual ~UIActionCheckFlag();
    virtual const char* GetClassName() const { return "UIActionCheckFlag"; }
};

// RTTI .?AVUIActionDelay@@
class UIActionDelay {
public:
    UIActionDelay();
    virtual ~UIActionDelay();
    virtual const char* GetClassName() const { return "UIActionDelay"; }
};

// RTTI .?AVUIActionDuration@@
class UIActionDuration {
public:
    UIActionDuration();
    virtual ~UIActionDuration();
    virtual const char* GetClassName() const { return "UIActionDuration"; }
};

// RTTI .?AVUIActionImmediate@@
class UIActionImmediate {
public:
    UIActionImmediate();
    virtual ~UIActionImmediate();
    virtual const char* GetClassName() const { return "UIActionImmediate"; }
};

// RTTI .?AVUIActionMovePos@@
class UIActionMovePos {
public:
    UIActionMovePos();
    virtual ~UIActionMovePos();
    virtual const char* GetClassName() const { return "UIActionMovePos"; }
};

// RTTI .?AVUIActionMoveRect@@
class UIActionMoveRect {
public:
    UIActionMoveRect();
    virtual ~UIActionMoveRect();
    virtual const char* GetClassName() const { return "UIActionMoveRect"; }
};

// RTTI .?AVUIActionRemove@@
class UIActionRemove {
public:
    UIActionRemove();
    virtual ~UIActionRemove();
    virtual const char* GetClassName() const { return "UIActionRemove"; }
};

// RTTI .?AVUIActionSetState@@
class UIActionSetState {
public:
    UIActionSetState();
    virtual ~UIActionSetState();
    virtual const char* GetClassName() const { return "UIActionSetState"; }
};

// RTTI .?AVUIActionSetValue@@
class UIActionSetValue {
public:
    UIActionSetValue();
    virtual ~UIActionSetValue();
    virtual const char* GetClassName() const { return "UIActionSetValue"; }
};

// RTTI .?AVUIActionTexture@@
class UIActionTexture {
public:
    UIActionTexture();
    virtual ~UIActionTexture();
    virtual const char* GetClassName() const { return "UIActionTexture"; }
};

// RTTI .?AVUIActionUncheckFlag@@
class UIActionUncheckFlag {
public:
    UIActionUncheckFlag();
    virtual ~UIActionUncheckFlag();
    virtual const char* GetClassName() const { return "UIActionUncheckFlag"; }
};

// RTTI .?AVUIBasicImage@@
class UIBasicImage {
public:
    UIBasicImage();
    virtual ~UIBasicImage();
    virtual const char* GetClassName() const { return "UIBasicImage"; }
};

// RTTI .?AVUIColorSelect@@
class UIColorSelect {
public:
    UIColorSelect();
    virtual ~UIColorSelect();
    virtual const char* GetClassName() const { return "UIColorSelect"; }
};

// RTTI .?AVUIColorSlide@@
class UIColorSlide {
public:
    UIColorSlide();
    virtual ~UIColorSlide();
    virtual const char* GetClassName() const { return "UIColorSlide"; }
};

// RTTI .?AVUIComboBox@@
class UIComboBox {
public:
    UIComboBox();
    virtual ~UIComboBox();
    virtual const char* GetClassName() const { return "UIComboBox"; }
};

// RTTI .?AVUIComboBoxList@@
class UIComboBoxList {
public:
    UIComboBoxList();
    virtual ~UIComboBoxList();
    virtual const char* GetClassName() const { return "UIComboBoxList"; }
};

// RTTI .?AVUIContainer@@
class UIContainer {
public:
    UIContainer();
    virtual ~UIContainer();
    virtual const char* GetClassName() const { return "UIContainer"; }
};

// RTTI .?AVUIContainerEx@@
class UIContainerEx {
public:
    UIContainerEx();
    virtual ~UIContainerEx();
    virtual const char* GetClassName() const { return "UIContainerEx"; }
};

// RTTI .?AVUIExtensible@@
class UIExtensible {
public:
    UIExtensible();
    virtual ~UIExtensible();
    virtual const char* GetClassName() const { return "UIExtensible"; }
};

// RTTI .?AVUIGrid@@
class UIGrid {
public:
    UIGrid();
    virtual ~UIGrid();
    virtual const char* GetClassName() const { return "UIGrid"; }
};

// RTTI .?AVUIImage@@
class UIImage {
public:
    UIImage();
    virtual ~UIImage();
    virtual const char* GetClassName() const { return "UIImage"; }
};

// RTTI .?AVUIInGameBrowser@@
class UIInGameBrowser {
public:
    UIInGameBrowser();
    virtual ~UIInGameBrowser();
    virtual const char* GetClassName() const { return "UIInGameBrowser"; }
};

// RTTI .?AVUIKeyBox@@
class UIKeyBox {
public:
    UIKeyBox();
    virtual ~UIKeyBox();
    virtual const char* GetClassName() const { return "UIKeyBox"; }
};

// RTTI .?AVUIListBox@@
class UIListBox {
public:
    UIListBox();
    virtual ~UIListBox();
    virtual const char* GetClassName() const { return "UIListBox"; }
};

// RTTI .?AVUIMsgBox@@
class UIMsgBox {
public:
    UIMsgBox();
    virtual ~UIMsgBox();
    virtual const char* GetClassName() const { return "UIMsgBox"; }
};

// RTTI .?AVUINoticeBox@@
class UINoticeBox {
public:
    UINoticeBox();
    virtual ~UINoticeBox();
    virtual const char* GetClassName() const { return "UINoticeBox"; }
};

// RTTI .?AVUIRollingStatic@@
class UIRollingStatic {
public:
    UIRollingStatic();
    virtual ~UIRollingStatic();
    virtual const char* GetClassName() const { return "UIRollingStatic"; }
};

// RTTI .?AVUIScreen@@
class UIScreen {
public:
    UIScreen();
    virtual ~UIScreen();
    virtual const char* GetClassName() const { return "UIScreen"; }
};

// RTTI .?AVUIScreenEnding@@
class UIScreenEnding {
public:
    UIScreenEnding();
    virtual ~UIScreenEnding();
    virtual const char* GetClassName() const { return "UIScreenEnding"; }
};

// RTTI .?AVUIScrollable@@
class UIScrollable {
public:
    UIScrollable();
    virtual ~UIScrollable();
    virtual const char* GetClassName() const { return "UIScrollable"; }
};

// RTTI .?AVUISlide@@
class UISlide {
public:
    UISlide();
    virtual ~UISlide();
    virtual const char* GetClassName() const { return "UISlide"; }
};

// RTTI .?AVUISpin@@
class UISpin {
public:
    UISpin();
    virtual ~UISpin();
    virtual const char* GetClassName() const { return "UISpin"; }
};

// RTTI .?AVUISpinelWebPage@@
class UISpinelWebPage {
public:
    UISpinelWebPage();
    virtual ~UISpinelWebPage();
    virtual const char* GetClassName() const { return "UISpinelWebPage"; }
};

// RTTI .?AVUISpinelWebWithSubPage@@
class UISpinelWebWithSubPage {
public:
    UISpinelWebWithSubPage();
    virtual ~UISpinelWebWithSubPage();
    virtual const char* GetClassName() const { return "UISpinelWebWithSubPage"; }
};

// RTTI .?AVUISpinelWebWithoutSubPage@@
class UISpinelWebWithoutSubPage {
public:
    UISpinelWebWithoutSubPage();
    virtual ~UISpinelWebWithoutSubPage();
    virtual const char* GetClassName() const { return "UISpinelWebWithoutSubPage"; }
};

// RTTI .?AVUIStatic@@
class UIStatic {
public:
    UIStatic();
    virtual ~UIStatic();
    virtual const char* GetClassName() const { return "UIStatic"; }
};

// RTTI .?AVUIStaticEx@@
class UIStaticEx {
public:
    UIStaticEx();
    virtual ~UIStaticEx();
    virtual const char* GetClassName() const { return "UIStaticEx"; }
};

// RTTI .?AVUIStaticImage@@
class UIStaticImage {
public:
    UIStaticImage();
    virtual ~UIStaticImage();
    virtual const char* GetClassName() const { return "UIStaticImage"; }
};

// RTTI .?AVUIStaticImageEx@@
class UIStaticImageEx {
public:
    UIStaticImageEx();
    virtual ~UIStaticImageEx();
    virtual const char* GetClassName() const { return "UIStaticImageEx"; }
};

// RTTI .?AVUISystem@@
class UISystem {
public:
    UISystem();
    virtual ~UISystem();
    virtual const char* GetClassName() const { return "UISystem"; }
};

// RTTI .?AVUITab@@
class UITab {
public:
    UITab();
    virtual ~UITab();
    virtual const char* GetClassName() const { return "UITab"; }
};

// RTTI .?AVUITabPage@@
class UITabPage {
public:
    UITabPage();
    virtual ~UITabPage();
    virtual const char* GetClassName() const { return "UITabPage"; }
};

// RTTI .?AVUITabSheet@@
class UITabSheet {
public:
    UITabSheet();
    virtual ~UITabSheet();
    virtual const char* GetClassName() const { return "UITabSheet"; }
};

// RTTI .?AVUITiledImage@@
class UITiledImage {
public:
    UITiledImage();
    virtual ~UITiledImage();
    virtual const char* GetClassName() const { return "UITiledImage"; }
};

// RTTI .?AVUnicodeInputChJkpy@@
class UnicodeInputChJkpy {
public:
    UnicodeInputChJkpy();
    virtual ~UnicodeInputChJkpy();
    virtual const char* GetClassName() const { return "UnicodeInputChJkpy"; }
};

// RTTI .?AVUnicodeInputChSimple@@
class UnicodeInputChSimple {
public:
    UnicodeInputChSimple();
    virtual ~UnicodeInputChSimple();
    virtual const char* GetClassName() const { return "UnicodeInputChSimple"; }
};

// RTTI .?AVUnicodeInputChWubi@@
class UnicodeInputChWubi {
public:
    UnicodeInputChWubi();
    virtual ~UnicodeInputChWubi();
    virtual const char* GetClassName() const { return "UnicodeInputChWubi"; }
};

// RTTI .?AVUnicodeInputChp@@
class UnicodeInputChp {
public:
    UnicodeInputChp();
    virtual ~UnicodeInputChp();
    virtual const char* GetClassName() const { return "UnicodeInputChp"; }
};

// RTTI .?AVUnicodeInputCht@@
class UnicodeInputCht {
public:
    UnicodeInputCht();
    virtual ~UnicodeInputCht();
    virtual const char* GetClassName() const { return "UnicodeInputCht"; }
};

// RTTI .?AVUnicodeInputJp@@
class UnicodeInputJp {
public:
    UnicodeInputJp();
    virtual ~UnicodeInputJp();
    virtual const char* GetClassName() const { return "UnicodeInputJp"; }
};

// RTTI .?AVUnicodeInputKr@@
class UnicodeInputKr {
public:
    UnicodeInputKr();
    virtual ~UnicodeInputKr();
    virtual const char* GetClassName() const { return "UnicodeInputKr"; }
};

namespace Json {
    // RTTI .?AVValueAllocator@Json@@
    class ValueAllocator {
    public:
        ValueAllocator();
        virtual ~ValueAllocator();
        virtual const char* GetClassName() const { return "ValueAllocator"; }
    };
}

// RTTI .?AVVendorItem@@
class VendorItem {
public:
    VendorItem();
    virtual ~VendorItem();
    virtual const char* GetClassName() const { return "VendorItem"; }
};

// RTTI .?AVVendorTabBase@@
class VendorTabBase {
public:
    VendorTabBase();
    virtual ~VendorTabBase();
    virtual const char* GetClassName() const { return "VendorTabBase"; }
};

// RTTI .?AVVessel@@
class Vessel {
public:
    Vessel();
    virtual ~Vessel();
    virtual const char* GetClassName() const { return "Vessel"; }
};

// RTTI .?AVVoiceChatError@@
class VoiceChatError {
public:
    VoiceChatError();
    virtual ~VoiceChatError();
    virtual const char* GetClassName() const { return "VoiceChatError"; }
};

// RTTI .?AVVoiceChatMemberNotify@@
class VoiceChatMemberNotify {
public:
    VoiceChatMemberNotify();
    virtual ~VoiceChatMemberNotify();
    virtual const char* GetClassName() const { return "VoiceChatMemberNotify"; }
};

// RTTI .?AVVoiceChatStatus@@
class VoiceChatStatus {
public:
    VoiceChatStatus();
    virtual ~VoiceChatStatus();
    virtual const char* GetClassName() const { return "VoiceChatStatus"; }
};

// RTTI .?AVWardrobeChangeSkin@@
class WardrobeChangeSkin {
public:
    WardrobeChangeSkin();
    virtual ~WardrobeChangeSkin();
    virtual const char* GetClassName() const { return "WardrobeChangeSkin"; }
};

// RTTI .?AVWardrobeDye@@
class WardrobeDye {
public:
    WardrobeDye();
    virtual ~WardrobeDye();
    virtual const char* GetClassName() const { return "WardrobeDye"; }
};

// RTTI .?AVWardrobeHair@@
class WardrobeHair {
public:
    WardrobeHair();
    virtual ~WardrobeHair();
    virtual const char* GetClassName() const { return "WardrobeHair"; }
};

namespace WardrobeItemListUtil {
    // RTTI .?AVWardrobeItemGridData@WardrobeItemListUtil@@
    class WardrobeItemGridData {
    public:
        WardrobeItemGridData();
        virtual ~WardrobeItemGridData();
        virtual const char* GetClassName() const { return "WardrobeItemGridData"; }
    };
}

// RTTI .?AVWardrobeModel@@
class WardrobeModel {
public:
    WardrobeModel();
    virtual ~WardrobeModel();
    virtual const char* GetClassName() const { return "WardrobeModel"; }
};

// RTTI .?AVWardrobeStorage@@
class WardrobeStorage {
public:
    WardrobeStorage();
    virtual ~WardrobeStorage();
    virtual const char* GetClassName() const { return "WardrobeStorage"; }
};

// RTTI .?AVWardrobeUIBase@@
class WardrobeUIBase {
public:
    WardrobeUIBase();
    virtual ~WardrobeUIBase();
    virtual const char* GetClassName() const { return "WardrobeUIBase"; }
};

// RTTI .?AVWorldReturnGridItemData@@
class WorldReturnGridItemData {
public:
    WorldReturnGridItemData();
    virtual ~WorldReturnGridItemData();
    virtual const char* GetClassName() const { return "WorldReturnGridItemData"; }
};

// RTTI .?AVZoneContentHPItemData@@
class ZoneContentHPItemData {
public:
    ZoneContentHPItemData();
    virtual ~ZoneContentHPItemData();
    virtual const char* GetClassName() const { return "ZoneContentHPItemData"; }
};

// RTTI .?AVZoneContentProgressItemData@@
class ZoneContentProgressItemData {
public:
    ZoneContentProgressItemData();
    virtual ~ZoneContentProgressItemData();
    virtual const char* GetClassName() const { return "ZoneContentProgressItemData"; }
};

// RTTI .?AV_com_error@@
class _com_error {
public:
    _com_error();
    virtual ~_com_error();
    virtual const char* GetClassName() const { return "_com_error"; }
};

// RTTI .?AVcond_MxInit_plus3sec@@
class cond_MxInit_plus3sec {
public:
    cond_MxInit_plus3sec();
    virtual ~cond_MxInit_plus3sec();
    virtual const char* GetClassName() const { return "cond_MxInit_plus3sec"; }
};

// RTTI .?AVcond_MxInit_plusquartersec@@
class cond_MxInit_plusquartersec {
public:
    cond_MxInit_plusquartersec();
    virtual ~cond_MxInit_plusquartersec();
    virtual const char* GetClassName() const { return "cond_MxInit_plusquartersec"; }
};

// RTTI .?AVjob_CheckVoiceChatStatus@@
class job_CheckVoiceChatStatus {
public:
    job_CheckVoiceChatStatus();
    virtual ~job_CheckVoiceChatStatus();
    virtual const char* GetClassName() const { return "job_CheckVoiceChatStatus"; }
};

// RTTI .?AVjob_CreateGroup@@
class job_CreateGroup {
public:
    job_CreateGroup();
    virtual ~job_CreateGroup();
    virtual const char* GetClassName() const { return "job_CreateGroup"; }
};

// RTTI .?AVjob_JobChange@@
class job_JobChange {
public:
    job_JobChange();
    virtual ~job_JobChange();
    virtual const char* GetClassName() const { return "job_JobChange"; }
};

// RTTI .?AVjob_JoinGroup@@
class job_JoinGroup {
public:
    job_JoinGroup();
    virtual ~job_JoinGroup();
    virtual const char* GetClassName() const { return "job_JoinGroup"; }
};

// RTTI .?AVjob_JoinPredefinedChannel@@
class job_JoinPredefinedChannel {
public:
    job_JoinPredefinedChannel();
    virtual ~job_JoinPredefinedChannel();
    virtual const char* GetClassName() const { return "job_JoinPredefinedChannel"; }
};

// RTTI .?AVjob_LevelChange@@
class job_LevelChange {
public:
    job_LevelChange();
    virtual ~job_LevelChange();
    virtual const char* GetClassName() const { return "job_LevelChange"; }
};

// RTTI .?AVjob_StopVoiceChat@@
class job_StopVoiceChat {
public:
    job_StopVoiceChat();
    virtual ~job_StopVoiceChat();
    virtual const char* GetClassName() const { return "job_StopVoiceChat"; }
};

// RTTI .?AVjob_voiceChat@@
class job_voiceChat {
public:
    job_voiceChat();
    virtual ~job_voiceChat();
    virtual const char* GetClassName() const { return "job_voiceChat"; }
};

// RTTI .?AVncString@@
class ncString {
public:
    ncString();
    virtual ~ncString();
    virtual const char* GetClassName() const { return "ncString"; }
};

void RegisterAllGameplayExt();