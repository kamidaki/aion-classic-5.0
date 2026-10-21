#pragma once
#include <cstdint>
#include <string>
#include <unordered_map>

// RTTI .?AVAbyssRaceBonusTable@@
class AbyssRaceBonusTable {
public:
    AbyssRaceBonusTable();
    virtual ~AbyssRaceBonusTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AbyssRaceBonusTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAbyssRankTable@@
class AbyssRankTable {
public:
    AbyssRankTable();
    virtual ~AbyssRankTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AbyssRankTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAbyssTypeRaceBonusesTable@@
class AbyssTypeRaceBonusesTable {
public:
    AbyssTypeRaceBonusesTable();
    virtual ~AbyssTypeRaceBonusesTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AbyssTypeRaceBonusesTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAccumulatedEnchantTable@@
class AccumulatedEnchantTable {
public:
    AccumulatedEnchantTable();
    virtual ~AccumulatedEnchantTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AccumulatedEnchantTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAionETCBaseStringTable@@
class AionETCBaseStringTable {
public:
    AionETCBaseStringTable();
    virtual ~AionETCBaseStringTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AionETCBaseStringTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAionHyperlinkTable@@
class AionHyperlinkTable {
public:
    AionHyperlinkTable();
    virtual ~AionHyperlinkTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AionHyperlinkTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAionLookDyeColorTable@@
class AionLookDyeColorTable {
public:
    AionLookDyeColorTable();
    virtual ~AionLookDyeColorTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AionLookDyeColorTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAionStringTable@@
class AionStringTable {
public:
    AionStringTable();
    virtual ~AionStringTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AionStringTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAssistOptionEnchantTypeTable@@
class AssistOptionEnchantTypeTable {
public:
    AssistOptionEnchantTypeTable();
    virtual ~AssistOptionEnchantTypeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AssistOptionEnchantTypeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVAssistOptionEnchantValueTable@@
class AssistOptionEnchantValueTable {
public:
    AssistOptionEnchantValueTable();
    virtual ~AssistOptionEnchantValueTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "AssistOptionEnchantValueTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBMAccountTable@@
class BMAccountTable {
public:
    BMAccountTable();
    virtual ~BMAccountTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BMAccountTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBMBoardFuncTable@@
class BMBoardFuncTable {
public:
    BMBoardFuncTable();
    virtual ~BMBoardFuncTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BMBoardFuncTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBMBoardPresetTable@@
class BMBoardPresetTable {
public:
    BMBoardPresetTable();
    virtual ~BMBoardPresetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BMBoardPresetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBMBoardSeasonTable@@
class BMBoardSeasonTable {
public:
    BMBoardSeasonTable();
    virtual ~BMBoardSeasonTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BMBoardSeasonTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBMConfigTable@@
class BMConfigTable {
public:
    BMConfigTable();
    virtual ~BMConfigTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BMConfigTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBMPackTable@@
class BMPackTable {
public:
    BMPackTable();
    virtual ~BMPackTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BMPackTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBaseTable@@
class BaseTable {
public:
    BaseTable();
    virtual ~BaseTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BaseTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBattlePassRewardTable@@
class BattlePassRewardTable {
public:
    BattlePassRewardTable();
    virtual ~BattlePassRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BattlePassRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVBattlePassSeasonTable@@
class BattlePassSeasonTable {
public:
    BattlePassSeasonTable();
    virtual ~BattlePassSeasonTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "BattlePassSeasonTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCharacterClassInfoTable@@
class CharacterClassInfoTable {
public:
    CharacterClassInfoTable();
    virtual ~CharacterClassInfoTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CharacterClassInfoTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVClassChangeCostTable@@
class ClassChangeCostTable {
public:
    ClassChangeCostTable();
    virtual ~ClassChangeCostTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ClassChangeCostTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCombatPowerRankBuffTable@@
class CombatPowerRankBuffTable {
public:
    CombatPowerRankBuffTable();
    virtual ~CombatPowerRankBuffTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CombatPowerRankBuffTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCombatPowerRewardTable@@
class CombatPowerRewardTable {
public:
    CombatPowerRewardTable();
    virtual ~CombatPowerRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CombatPowerRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCombatPowerRuleTable@@
class CombatPowerRuleTable {
public:
    CombatPowerRuleTable();
    virtual ~CombatPowerRuleTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CombatPowerRuleTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCombineGiveUpCostTable@@
class CombineGiveUpCostTable {
public:
    CombineGiveUpCostTable();
    virtual ~CombineGiveUpCostTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CombineGiveUpCostTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVContextSkillTable@@
class ContextSkillTable {
public:
    ContextSkillTable();
    virtual ~ContextSkillTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ContextSkillTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCosmeticItemTable@@
class CosmeticItemTable {
public:
    CosmeticItemTable();
    virtual ~CosmeticItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CosmeticItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCustomAnimTable@@
class CustomAnimTable {
public:
    CustomAnimTable();
    virtual ~CustomAnimTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CustomAnimTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVCutSceneNameTable@@
class CutSceneNameTable {
public:
    CutSceneNameTable();
    virtual ~CutSceneNameTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "CutSceneNameTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVDefaultKeyTable@@
class DefaultKeyTable {
public:
    DefaultKeyTable();
    virtual ~DefaultKeyTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "DefaultKeyTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVDialogStringTable@@
class DialogStringTable {
public:
    DialogStringTable();
    virtual ~DialogStringTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "DialogStringTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVDisassemblyItemCustomizeTable@@
class DisassemblyItemCustomizeTable {
public:
    DisassemblyItemCustomizeTable();
    virtual ~DisassemblyItemCustomizeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "DisassemblyItemCustomizeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVDisassemblyItemSetListTable@@
class DisassemblyItemSetListTable {
public:
    DisassemblyItemSetListTable();
    virtual ~DisassemblyItemSetListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "DisassemblyItemSetListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVDisassemblyItemSetTable@@
class DisassemblyItemSetTable {
public:
    DisassemblyItemSetTable();
    virtual ~DisassemblyItemSetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "DisassemblyItemSetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVEmotionTable@@
class EmotionTable {
public:
    EmotionTable();
    virtual ~EmotionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "EmotionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVEnchantCountProbTable@@
class EnchantCountProbTable {
public:
    EnchantCountProbTable();
    virtual ~EnchantCountProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "EnchantCountProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVEnchantGapLevelProbTable@@
class EnchantGapLevelProbTable {
public:
    EnchantGapLevelProbTable();
    virtual ~EnchantGapLevelProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "EnchantGapLevelProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVEnchantMatterProbTable@@
class EnchantMatterProbTable {
public:
    EnchantMatterProbTable();
    virtual ~EnchantMatterProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "EnchantMatterProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVEnchantOptionTable@@
class EnchantOptionTable {
public:
    EnchantOptionTable();
    virtual ~EnchantOptionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "EnchantOptionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVFFATable@@
class FFATable {
public:
    FFATable();
    virtual ~FFATable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "FFATable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGamePassExtraTable@@
class GamePassExtraTable {
public:
    GamePassExtraTable();
    virtual ~GamePassExtraTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GamePassExtraTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGameRuleOptionsTable@@
class GameRuleOptionsTable {
public:
    GameRuleOptionsTable();
    virtual ~GameRuleOptionsTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GameRuleOptionsTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGatherSourceTable@@
class GatherSourceTable {
public:
    GatherSourceTable();
    virtual ~GatherSourceTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GatherSourceTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGemMatterItemReforgeStatInfoDataTable@@
class GemMatterItemReforgeStatInfoDataTable {
public:
    GemMatterItemReforgeStatInfoDataTable();
    virtual ~GemMatterItemReforgeStatInfoDataTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GemMatterItemReforgeStatInfoDataTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGemMatterItemReforgeStatTable@@
class GemMatterItemReforgeStatTable {
public:
    GemMatterItemReforgeStatTable();
    virtual ~GemMatterItemReforgeStatTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GemMatterItemReforgeStatTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGemMatterItemReforgeTable@@
class GemMatterItemReforgeTable {
public:
    GemMatterItemReforgeTable();
    virtual ~GemMatterItemReforgeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GemMatterItemReforgeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGlobalTradeExchangeTable@@
class GlobalTradeExchangeTable {
public:
    GlobalTradeExchangeTable();
    virtual ~GlobalTradeExchangeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GlobalTradeExchangeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGoodsIconTable@@
class GoodsIconTable {
public:
    GoodsIconTable();
    virtual ~GoodsIconTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GoodsIconTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildBuffConfigTable@@
class GuildBuffConfigTable {
public:
    GuildBuffConfigTable();
    virtual ~GuildBuffConfigTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildBuffConfigTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildBuffTable@@
class GuildBuffTable {
public:
    GuildBuffTable();
    virtual ~GuildBuffTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildBuffTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildCraftTable@@
class GuildCraftTable {
public:
    GuildCraftTable();
    virtual ~GuildCraftTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildCraftTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildDonationRewardTable@@
class GuildDonationRewardTable {
public:
    GuildDonationRewardTable();
    virtual ~GuildDonationRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildDonationRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildDonationSettingTable@@
class GuildDonationSettingTable {
public:
    GuildDonationSettingTable();
    virtual ~GuildDonationSettingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildDonationSettingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildDonationTable@@
class GuildDonationTable {
public:
    GuildDonationTable();
    virtual ~GuildDonationTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildDonationTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildGrowthTable@@
class GuildGrowthTable {
public:
    GuildGrowthTable();
    virtual ~GuildGrowthTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildGrowthTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildScheduledMissionAchievementTable@@
class GuildScheduledMissionAchievementTable {
public:
    GuildScheduledMissionAchievementTable();
    virtual ~GuildScheduledMissionAchievementTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildScheduledMissionAchievementTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildScheduledMissionActionTable@@
class GuildScheduledMissionActionTable {
public:
    GuildScheduledMissionActionTable();
    virtual ~GuildScheduledMissionActionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildScheduledMissionActionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVGuildSettingTable@@
class GuildSettingTable {
public:
    GuildSettingTable();
    virtual ~GuildSettingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "GuildSettingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVHTMLStringTable@@
class HTMLStringTable {
public:
    HTMLStringTable();
    virtual ~HTMLStringTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "HTMLStringTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVHotSpotTable@@
class HotSpotTable {
public:
    HotSpotTable();
    virtual ~HotSpotTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "HotSpotTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVITable@@
class ITable {
public:
    ITable();
    virtual ~ITable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ITable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVIndunInitTable@@
class IndunInitTable {
public:
    IndunInitTable();
    virtual ~IndunInitTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "IndunInitTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVInfinityIndunRewardTable@@
class InfinityIndunRewardTable {
public:
    InfinityIndunRewardTable();
    virtual ~InfinityIndunRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "InfinityIndunRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVInstanceBonusTable@@
class InstanceBonusTable {
public:
    InstanceBonusTable();
    virtual ~InstanceBonusTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "InstanceBonusTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVInstantDungeonTable@@
class InstantDungeonTable {
public:
    InstantDungeonTable();
    virtual ~InstantDungeonTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "InstantDungeonTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemComposeTable@@
class ItemComposeTable {
public:
    ItemComposeTable();
    virtual ~ItemComposeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemComposeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemCrushTable@@
class ItemCrushTable {
public:
    ItemCrushTable();
    virtual ~ItemCrushTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemCrushTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemCustomSetTable@@
class ItemCustomSetTable {
public:
    ItemCustomSetTable();
    virtual ~ItemCustomSetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemCustomSetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemFlavorTable@@
class ItemFlavorTable {
public:
    ItemFlavorTable();
    virtual ~ItemFlavorTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemFlavorTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemOverrideIconTable@@
class ItemOverrideIconTable {
public:
    ItemOverrideIconTable();
    virtual ~ItemOverrideIconTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemOverrideIconTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemSkillEnchantCostTable@@
class ItemSkillEnchantCostTable {
public:
    ItemSkillEnchantCostTable();
    virtual ~ItemSkillEnchantCostTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemSkillEnchantCostTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemSkillEnchantTable@@
class ItemSkillEnchantTable {
public:
    ItemSkillEnchantTable();
    virtual ~ItemSkillEnchantTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemSkillEnchantTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemTable@@
class ItemTable {
public:
    ItemTable();
    virtual ~ItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVItemUpgradeTable@@
class ItemUpgradeTable {
public:
    ItemUpgradeTable();
    virtual ~ItemUpgradeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ItemUpgradeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVLoadingTipTable@@
class LoadingTipTable {
public:
    LoadingTipTable();
    virtual ~LoadingTipTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "LoadingTipTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVLoginEventTable@@
class LoginEventTable {
public:
    LoginEventTable();
    virtual ~LoginEventTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "LoginEventTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVLookSynergyTable@@
class LookSynergyTable {
public:
    LookSynergyTable();
    virtual ~LookSynergyTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "LookSynergyTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVMakeUpBonusTable@@
class MakeUpBonusTable {
public:
    MakeUpBonusTable();
    virtual ~MakeUpBonusTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "MakeUpBonusTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVMatchMakerIndunTable@@
class MatchMakerIndunTable {
public:
    MatchMakerIndunTable();
    virtual ~MatchMakerIndunTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "MatchMakerIndunTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVModelCamTable@@
class ModelCamTable {
public:
    ModelCamTable();
    virtual ~ModelCamTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ModelCamTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVMorosPointTable@@
class MorosPointTable {
public:
    MorosPointTable();
    virtual ~MorosPointTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "MorosPointTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVMorosTable@@
class MorosTable {
public:
    MorosTable();
    virtual ~MorosTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "MorosTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVMovieNameTable@@
class MovieNameTable {
public:
    MovieNameTable();
    virtual ~MovieNameTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "MovieNameTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNPCGoodsListBaseTable@@
class NPCGoodsListBaseTable {
public:
    NPCGoodsListBaseTable();
    virtual ~NPCGoodsListBaseTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NPCGoodsListBaseTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNPCGoodsListTable@@
class NPCGoodsListTable {
public:
    NPCGoodsListTable();
    virtual ~NPCGoodsListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NPCGoodsListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNPCGuideTable@@
class NPCGuideTable {
public:
    NPCGuideTable();
    virtual ~NPCGuideTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NPCGuideTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNPCPurchaseListTable@@
class NPCPurchaseListTable {
public:
    NPCPurchaseListTable();
    virtual ~NPCPurchaseListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NPCPurchaseListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNPCTable@@
class NPCTable {
public:
    NPCTable();
    virtual ~NPCTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NPCTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNPCUITable@@
class NPCUITable {
public:
    NPCUITable();
    virtual ~NPCUITable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NPCUITable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVNotConnectedPeriodRewardConfigTable@@
class NotConnectedPeriodRewardConfigTable {
public:
    NotConnectedPeriodRewardConfigTable();
    virtual ~NotConnectedPeriodRewardConfigTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "NotConnectedPeriodRewardConfigTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVOptionClearTable@@
class OptionClearTable {
public:
    OptionClearTable();
    virtual ~OptionClearTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "OptionClearTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVOverrideStringTable@@
class OverrideStringTable {
public:
    OverrideStringTable();
    virtual ~OverrideStringTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "OverrideStringTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVPCTable@@
class PCTable {
public:
    PCTable();
    virtual ~PCTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "PCTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVPcExpRewardTable@@
class PcExpRewardTable {
public:
    PcExpRewardTable();
    virtual ~PcExpRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "PcExpRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVPolymorphTempSkillTable@@
class PolymorphTempSkillTable {
public:
    PolymorphTempSkillTable();
    virtual ~PolymorphTempSkillTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "PolymorphTempSkillTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVPvPRankTable@@
class PvPRankTable {
public:
    PvPRankTable();
    virtual ~PvPRankTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "PvPRankTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVQuestMonsterTable@@
class QuestMonsterTable {
public:
    QuestMonsterTable();
    virtual ~QuestMonsterTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "QuestMonsterTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVQuestTable@@
class QuestTable {
public:
    QuestTable();
    virtual ~QuestTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "QuestTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVRankingBadgeTable@@
class RankingBadgeTable {
public:
    RankingBadgeTable();
    virtual ~RankingBadgeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "RankingBadgeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVRankingRewardTable@@
class RankingRewardTable {
public:
    RankingRewardTable();
    virtual ~RankingRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "RankingRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVRankingSeasonTable@@
class RankingSeasonTable {
public:
    RankingSeasonTable();
    virtual ~RankingSeasonTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "RankingSeasonTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVRecipeTable@@
class RecipeTable {
public:
    RecipeTable();
    virtual ~RecipeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "RecipeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVRvRRewardTable@@
class RvRRewardTable {
public:
    RvRRewardTable();
    virtual ~RvRRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "RvRRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVRvRScheduleTable@@
class RvRScheduleTable {
public:
    RvRScheduleTable();
    virtual ~RvRScheduleTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "RvRScheduleTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVScheduledMissionActionTable@@
class ScheduledMissionActionTable {
public:
    ScheduledMissionActionTable();
    virtual ~ScheduledMissionActionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ScheduledMissionActionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVScheduledMissionActionTableBase@@
class ScheduledMissionActionTableBase {
public:
    ScheduledMissionActionTableBase();
    virtual ~ScheduledMissionActionTableBase();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ScheduledMissionActionTableBase"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVScheduledMissionEventTable@@
class ScheduledMissionEventTable {
public:
    ScheduledMissionEventTable();
    virtual ~ScheduledMissionEventTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ScheduledMissionEventTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVScoreDamageIndunTable@@
class ScoreDamageIndunTable {
public:
    ScoreDamageIndunTable();
    virtual ~ScoreDamageIndunTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ScoreDamageIndunTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSerialKillerTable@@
class SerialKillerTable {
public:
    SerialKillerTable();
    virtual ~SerialKillerTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SerialKillerTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSetItemTable@@
class SetItemTable {
public:
    SetItemTable();
    virtual ~SetItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SetItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSkillBoosterTable@@
class SkillBoosterTable {
public:
    SkillBoosterTable();
    virtual ~SkillBoosterTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SkillBoosterTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSkillLearnTable@@
class SkillLearnTable {
public:
    SkillLearnTable();
    virtual ~SkillLearnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SkillLearnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSkillProhibitTable@@
class SkillProhibitTable {
public:
    SkillProhibitTable();
    virtual ~SkillProhibitTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SkillProhibitTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSkillSkinTable@@
class SkillSkinTable {
public:
    SkillSkinTable();
    virtual ~SkillSkinTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SkillSkinTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSkillTable@@
class SkillTable {
public:
    SkillTable();
    virtual ~SkillTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SkillTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpawnTable@@
class SpawnTable {
public:
    SpawnTable();
    virtual ~SpawnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpawnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2AbyssTable@@
class Special2AbyssTable {
public:
    Special2AbyssTable();
    virtual ~Special2AbyssTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2AbyssTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2AccumulatedEnchantTable@@
class Special2AccumulatedEnchantTable {
public:
    Special2AccumulatedEnchantTable();
    virtual ~Special2AccumulatedEnchantTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2AccumulatedEnchantTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2CombatPowerRewardTable@@
class Special2CombatPowerRewardTable {
public:
    Special2CombatPowerRewardTable();
    virtual ~Special2CombatPowerRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2CombatPowerRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2CraftItemTableV2@@
class Special2CraftItemTableV2 {
public:
    Special2CraftItemTableV2();
    virtual ~Special2CraftItemTableV2();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2CraftItemTableV2"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2DisassemblyItemSetListTable@@
class Special2DisassemblyItemSetListTable {
public:
    Special2DisassemblyItemSetListTable();
    virtual ~Special2DisassemblyItemSetListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2DisassemblyItemSetListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2DisassemblyItemSetTable@@
class Special2DisassemblyItemSetTable {
public:
    Special2DisassemblyItemSetTable();
    virtual ~Special2DisassemblyItemSetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2DisassemblyItemSetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2EnchantCountProbTable@@
class Special2EnchantCountProbTable {
public:
    Special2EnchantCountProbTable();
    virtual ~Special2EnchantCountProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2EnchantCountProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2EnchantGapLevelProbTable@@
class Special2EnchantGapLevelProbTable {
public:
    Special2EnchantGapLevelProbTable();
    virtual ~Special2EnchantGapLevelProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2EnchantGapLevelProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2EnchantOptionTable@@
class Special2EnchantOptionTable {
public:
    Special2EnchantOptionTable();
    virtual ~Special2EnchantOptionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2EnchantOptionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GamePassExtraTable@@
class Special2GamePassExtraTable {
public:
    Special2GamePassExtraTable();
    virtual ~Special2GamePassExtraTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GamePassExtraTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GameRuleOptionsTable@@
class Special2GameRuleOptionsTable {
public:
    Special2GameRuleOptionsTable();
    virtual ~Special2GameRuleOptionsTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GameRuleOptionsTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GatherSourceTable@@
class Special2GatherSourceTable {
public:
    Special2GatherSourceTable();
    virtual ~Special2GatherSourceTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GatherSourceTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GuildCraftTable@@
class Special2GuildCraftTable {
public:
    Special2GuildCraftTable();
    virtual ~Special2GuildCraftTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GuildCraftTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GuildDonationSettingTable@@
class Special2GuildDonationSettingTable {
public:
    Special2GuildDonationSettingTable();
    virtual ~Special2GuildDonationSettingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GuildDonationSettingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GuildScheduledMissionAchievementTable@@
class Special2GuildScheduledMissionAchievementTable {
public:
    Special2GuildScheduledMissionAchievementTable();
    virtual ~Special2GuildScheduledMissionAchievementTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GuildScheduledMissionAchievementTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2GuildScheduledMissionActionTable@@
class Special2GuildScheduledMissionActionTable {
public:
    Special2GuildScheduledMissionActionTable();
    virtual ~Special2GuildScheduledMissionActionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2GuildScheduledMissionActionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2HotSpotTable@@
class Special2HotSpotTable {
public:
    Special2HotSpotTable();
    virtual ~Special2HotSpotTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2HotSpotTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2IndunInitTable@@
class Special2IndunInitTable {
public:
    Special2IndunInitTable();
    virtual ~Special2IndunInitTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2IndunInitTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2InstantDungeonTable@@
class Special2InstantDungeonTable {
public:
    Special2InstantDungeonTable();
    virtual ~Special2InstantDungeonTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2InstantDungeonTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2ItemComposeTable@@
class Special2ItemComposeTable {
public:
    Special2ItemComposeTable();
    virtual ~Special2ItemComposeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2ItemComposeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2ItemCrushTable@@
class Special2ItemCrushTable {
public:
    Special2ItemCrushTable();
    virtual ~Special2ItemCrushTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2ItemCrushTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2ItemTable@@
class Special2ItemTable {
public:
    Special2ItemTable();
    virtual ~Special2ItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2ItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2ItemUpgradeTable@@
class Special2ItemUpgradeTable {
public:
    Special2ItemUpgradeTable();
    virtual ~Special2ItemUpgradeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2ItemUpgradeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2LookSynergyTable@@
class Special2LookSynergyTable {
public:
    Special2LookSynergyTable();
    virtual ~Special2LookSynergyTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2LookSynergyTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2MatchMakerIndunTable@@
class Special2MatchMakerIndunTable {
public:
    Special2MatchMakerIndunTable();
    virtual ~Special2MatchMakerIndunTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2MatchMakerIndunTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2NPCGoodsListTable@@
class Special2NPCGoodsListTable {
public:
    Special2NPCGoodsListTable();
    virtual ~Special2NPCGoodsListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2NPCGoodsListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2NPCPurchaseListTable@@
class Special2NPCPurchaseListTable {
public:
    Special2NPCPurchaseListTable();
    virtual ~Special2NPCPurchaseListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2NPCPurchaseListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2NPCTable@@
class Special2NPCTable {
public:
    Special2NPCTable();
    virtual ~Special2NPCTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2NPCTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2OptionClearTable@@
class Special2OptionClearTable {
public:
    Special2OptionClearTable();
    virtual ~Special2OptionClearTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2OptionClearTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2QuestMonsterTable@@
class Special2QuestMonsterTable {
public:
    Special2QuestMonsterTable();
    virtual ~Special2QuestMonsterTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2QuestMonsterTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2QuestTable@@
class Special2QuestTable {
public:
    Special2QuestTable();
    virtual ~Special2QuestTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2QuestTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2RankingRewardTable@@
class Special2RankingRewardTable {
public:
    Special2RankingRewardTable();
    virtual ~Special2RankingRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2RankingRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2RvRRewardTable@@
class Special2RvRRewardTable {
public:
    Special2RvRRewardTable();
    virtual ~Special2RvRRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2RvRRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2RvRScheduleTable@@
class Special2RvRScheduleTable {
public:
    Special2RvRScheduleTable();
    virtual ~Special2RvRScheduleTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2RvRScheduleTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2ScoreDamageIndunTable@@
class Special2ScoreDamageIndunTable {
public:
    Special2ScoreDamageIndunTable();
    virtual ~Special2ScoreDamageIndunTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2ScoreDamageIndunTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2SkillLearnTable@@
class Special2SkillLearnTable {
public:
    Special2SkillLearnTable();
    virtual ~Special2SkillLearnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2SkillLearnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2SkillSkinTable@@
class Special2SkillSkinTable {
public:
    Special2SkillSkinTable();
    virtual ~Special2SkillSkinTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2SkillSkinTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2SkillTable@@
class Special2SkillTable {
public:
    Special2SkillTable();
    virtual ~Special2SkillTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2SkillTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2SpawnTable@@
class Special2SpawnTable {
public:
    Special2SpawnTable();
    virtual ~Special2SpawnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2SpawnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2TradeInListTable@@
class Special2TradeInListTable {
public:
    Special2TradeInListTable();
    virtual ~Special2TradeInListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2TradeInListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2WorldIDTable@@
class Special2WorldIDTable {
public:
    Special2WorldIDTable();
    virtual ~Special2WorldIDTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2WorldIDTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecial2WorldReturnTable@@
class Special2WorldReturnTable {
public:
    Special2WorldReturnTable();
    virtual ~Special2WorldReturnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "Special2WorldReturnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialAbyssRankTable@@
class SpecialAbyssRankTable {
public:
    SpecialAbyssRankTable();
    virtual ~SpecialAbyssRankTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialAbyssRankTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialAbyssTable@@
class SpecialAbyssTable {
public:
    SpecialAbyssTable();
    virtual ~SpecialAbyssTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialAbyssTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialAccumulatedEnchantTable@@
class SpecialAccumulatedEnchantTable {
public:
    SpecialAccumulatedEnchantTable();
    virtual ~SpecialAccumulatedEnchantTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialAccumulatedEnchantTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialAssistOptionEnchantTypeTable@@
class SpecialAssistOptionEnchantTypeTable {
public:
    SpecialAssistOptionEnchantTypeTable();
    virtual ~SpecialAssistOptionEnchantTypeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialAssistOptionEnchantTypeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialAssistOptionEnchantValueTable@@
class SpecialAssistOptionEnchantValueTable {
public:
    SpecialAssistOptionEnchantValueTable();
    virtual ~SpecialAssistOptionEnchantValueTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialAssistOptionEnchantValueTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialCharacterClassInfoTable@@
class SpecialCharacterClassInfoTable {
public:
    SpecialCharacterClassInfoTable();
    virtual ~SpecialCharacterClassInfoTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialCharacterClassInfoTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialCombatPowerRankBuffTable@@
class SpecialCombatPowerRankBuffTable {
public:
    SpecialCombatPowerRankBuffTable();
    virtual ~SpecialCombatPowerRankBuffTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialCombatPowerRankBuffTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialCombatPowerRewardTable@@
class SpecialCombatPowerRewardTable {
public:
    SpecialCombatPowerRewardTable();
    virtual ~SpecialCombatPowerRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialCombatPowerRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialCraftItemTable@@
class SpecialCraftItemTable {
public:
    SpecialCraftItemTable();
    virtual ~SpecialCraftItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialCraftItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialCraftItemTableV2@@
class SpecialCraftItemTableV2 {
public:
    SpecialCraftItemTableV2();
    virtual ~SpecialCraftItemTableV2();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialCraftItemTableV2"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialDisassemblyItemSetListTable@@
class SpecialDisassemblyItemSetListTable {
public:
    SpecialDisassemblyItemSetListTable();
    virtual ~SpecialDisassemblyItemSetListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialDisassemblyItemSetListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialDisassemblyItemSetTable@@
class SpecialDisassemblyItemSetTable {
public:
    SpecialDisassemblyItemSetTable();
    virtual ~SpecialDisassemblyItemSetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialDisassemblyItemSetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialEnchantCountProbTable@@
class SpecialEnchantCountProbTable {
public:
    SpecialEnchantCountProbTable();
    virtual ~SpecialEnchantCountProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialEnchantCountProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialEnchantGapLevelProbTable@@
class SpecialEnchantGapLevelProbTable {
public:
    SpecialEnchantGapLevelProbTable();
    virtual ~SpecialEnchantGapLevelProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialEnchantGapLevelProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialEnchantMatterProbTable@@
class SpecialEnchantMatterProbTable {
public:
    SpecialEnchantMatterProbTable();
    virtual ~SpecialEnchantMatterProbTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialEnchantMatterProbTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialEnchantOptionTable@@
class SpecialEnchantOptionTable {
public:
    SpecialEnchantOptionTable();
    virtual ~SpecialEnchantOptionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialEnchantOptionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGamePassExtraTable@@
class SpecialGamePassExtraTable {
public:
    SpecialGamePassExtraTable();
    virtual ~SpecialGamePassExtraTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGamePassExtraTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGameRuleOptionsTable@@
class SpecialGameRuleOptionsTable {
public:
    SpecialGameRuleOptionsTable();
    virtual ~SpecialGameRuleOptionsTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGameRuleOptionsTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGatherSourceTable@@
class SpecialGatherSourceTable {
public:
    SpecialGatherSourceTable();
    virtual ~SpecialGatherSourceTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGatherSourceTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGemMatterItemReforgeStatInfoDataTable@@
class SpecialGemMatterItemReforgeStatInfoDataTable {
public:
    SpecialGemMatterItemReforgeStatInfoDataTable();
    virtual ~SpecialGemMatterItemReforgeStatInfoDataTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGemMatterItemReforgeStatInfoDataTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGemMatterItemReforgeStatTable@@
class SpecialGemMatterItemReforgeStatTable {
public:
    SpecialGemMatterItemReforgeStatTable();
    virtual ~SpecialGemMatterItemReforgeStatTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGemMatterItemReforgeStatTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGemMatterItemReforgeTable@@
class SpecialGemMatterItemReforgeTable {
public:
    SpecialGemMatterItemReforgeTable();
    virtual ~SpecialGemMatterItemReforgeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGemMatterItemReforgeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGuildCraftTable@@
class SpecialGuildCraftTable {
public:
    SpecialGuildCraftTable();
    virtual ~SpecialGuildCraftTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGuildCraftTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGuildDonationRewardTable@@
class SpecialGuildDonationRewardTable {
public:
    SpecialGuildDonationRewardTable();
    virtual ~SpecialGuildDonationRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGuildDonationRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGuildDonationSettingTable@@
class SpecialGuildDonationSettingTable {
public:
    SpecialGuildDonationSettingTable();
    virtual ~SpecialGuildDonationSettingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGuildDonationSettingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGuildScheduledMissionAchievementTable@@
class SpecialGuildScheduledMissionAchievementTable {
public:
    SpecialGuildScheduledMissionAchievementTable();
    virtual ~SpecialGuildScheduledMissionAchievementTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGuildScheduledMissionAchievementTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialGuildScheduledMissionActionTable@@
class SpecialGuildScheduledMissionActionTable {
public:
    SpecialGuildScheduledMissionActionTable();
    virtual ~SpecialGuildScheduledMissionActionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialGuildScheduledMissionActionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialHotSpotTable@@
class SpecialHotSpotTable {
public:
    SpecialHotSpotTable();
    virtual ~SpecialHotSpotTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialHotSpotTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialIndunInitTable@@
class SpecialIndunInitTable {
public:
    SpecialIndunInitTable();
    virtual ~SpecialIndunInitTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialIndunInitTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialInstantDungeonTable@@
class SpecialInstantDungeonTable {
public:
    SpecialInstantDungeonTable();
    virtual ~SpecialInstantDungeonTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialInstantDungeonTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialItemComposeTable@@
class SpecialItemComposeTable {
public:
    SpecialItemComposeTable();
    virtual ~SpecialItemComposeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialItemComposeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialItemCrushTable@@
class SpecialItemCrushTable {
public:
    SpecialItemCrushTable();
    virtual ~SpecialItemCrushTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialItemCrushTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialItemSkillEnchantCostTable@@
class SpecialItemSkillEnchantCostTable {
public:
    SpecialItemSkillEnchantCostTable();
    virtual ~SpecialItemSkillEnchantCostTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialItemSkillEnchantCostTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialItemTable@@
class SpecialItemTable {
public:
    SpecialItemTable();
    virtual ~SpecialItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialItemUpgradeTable@@
class SpecialItemUpgradeTable {
public:
    SpecialItemUpgradeTable();
    virtual ~SpecialItemUpgradeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialItemUpgradeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialLookSynergyTable@@
class SpecialLookSynergyTable {
public:
    SpecialLookSynergyTable();
    virtual ~SpecialLookSynergyTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialLookSynergyTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialMatchMakerIndunTable@@
class SpecialMatchMakerIndunTable {
public:
    SpecialMatchMakerIndunTable();
    virtual ~SpecialMatchMakerIndunTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialMatchMakerIndunTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialMorosTable@@
class SpecialMorosTable {
public:
    SpecialMorosTable();
    virtual ~SpecialMorosTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialMorosTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialNPCGoodsListTable@@
class SpecialNPCGoodsListTable {
public:
    SpecialNPCGoodsListTable();
    virtual ~SpecialNPCGoodsListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialNPCGoodsListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialNPCPurchaseListTable@@
class SpecialNPCPurchaseListTable {
public:
    SpecialNPCPurchaseListTable();
    virtual ~SpecialNPCPurchaseListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialNPCPurchaseListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialNPCTable@@
class SpecialNPCTable {
public:
    SpecialNPCTable();
    virtual ~SpecialNPCTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialNPCTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialOptionClearTable@@
class SpecialOptionClearTable {
public:
    SpecialOptionClearTable();
    virtual ~SpecialOptionClearTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialOptionClearTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialPcExpRewardTable@@
class SpecialPcExpRewardTable {
public:
    SpecialPcExpRewardTable();
    virtual ~SpecialPcExpRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialPcExpRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialQuestMonsterTable@@
class SpecialQuestMonsterTable {
public:
    SpecialQuestMonsterTable();
    virtual ~SpecialQuestMonsterTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialQuestMonsterTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialQuestTable@@
class SpecialQuestTable {
public:
    SpecialQuestTable();
    virtual ~SpecialQuestTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialQuestTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialRecipeTable@@
class SpecialRecipeTable {
public:
    SpecialRecipeTable();
    virtual ~SpecialRecipeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialRecipeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialRvRRewardTable@@
class SpecialRvRRewardTable {
public:
    SpecialRvRRewardTable();
    virtual ~SpecialRvRRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialRvRRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialRvRScheduleTable@@
class SpecialRvRScheduleTable {
public:
    SpecialRvRScheduleTable();
    virtual ~SpecialRvRScheduleTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialRvRScheduleTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSetItemTable@@
class SpecialSetItemTable {
public:
    SpecialSetItemTable();
    virtual ~SpecialSetItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSetItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSkillLearnTable@@
class SpecialSkillLearnTable {
public:
    SpecialSkillLearnTable();
    virtual ~SpecialSkillLearnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSkillLearnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSkillSkinTable@@
class SpecialSkillSkinTable {
public:
    SpecialSkillSkinTable();
    virtual ~SpecialSkillSkinTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSkillSkinTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSkillTable@@
class SpecialSkillTable {
public:
    SpecialSkillTable();
    virtual ~SpecialSkillTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSkillTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSkinMeshNameTable@@
class SpecialSkinMeshNameTable {
public:
    SpecialSkinMeshNameTable();
    virtual ~SpecialSkinMeshNameTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSkinMeshNameTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSkinTable@@
class SpecialSkinTable {
public:
    SpecialSkinTable();
    virtual ~SpecialSkinTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSkinTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialSpawnTable@@
class SpecialSpawnTable {
public:
    SpecialSpawnTable();
    virtual ~SpecialSpawnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialSpawnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialStoryBookRewardTable@@
class SpecialStoryBookRewardTable {
public:
    SpecialStoryBookRewardTable();
    virtual ~SpecialStoryBookRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialStoryBookRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialStoryBookTable@@
class SpecialStoryBookTable {
public:
    SpecialStoryBookTable();
    virtual ~SpecialStoryBookTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialStoryBookTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialTeleportTable@@
class SpecialTeleportTable {
public:
    SpecialTeleportTable();
    virtual ~SpecialTeleportTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialTeleportTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialToyPetTable@@
class SpecialToyPetTable {
public:
    SpecialToyPetTable();
    virtual ~SpecialToyPetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialToyPetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialTradeInListTable@@
class SpecialTradeInListTable {
public:
    SpecialTradeInListTable();
    virtual ~SpecialTradeInListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialTradeInListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialWorldIDTable@@
class SpecialWorldIDTable {
public:
    SpecialWorldIDTable();
    virtual ~SpecialWorldIDTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialWorldIDTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVSpecialWorldReturnTable@@
class SpecialWorldReturnTable {
public:
    SpecialWorldReturnTable();
    virtual ~SpecialWorldReturnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "SpecialWorldReturnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVStatInfoTable@@
class StatInfoTable {
public:
    StatInfoTable();
    virtual ~StatInfoTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "StatInfoTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVStigmaPageConfigTable@@
class StigmaPageConfigTable {
public:
    StigmaPageConfigTable();
    virtual ~StigmaPageConfigTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "StigmaPageConfigTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVStoryBookAppraiseTable@@
class StoryBookAppraiseTable {
public:
    StoryBookAppraiseTable();
    virtual ~StoryBookAppraiseTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "StoryBookAppraiseTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVStoryBookRewardTable@@
class StoryBookRewardTable {
public:
    StoryBookRewardTable();
    virtual ~StoryBookRewardTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "StoryBookRewardTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVStoryBookTable@@
class StoryBookTable {
public:
    StoryBookTable();
    virtual ~StoryBookTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "StoryBookTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTaskTable@@
class TaskTable {
public:
    TaskTable();
    virtual ~TaskTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TaskTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTeleportTable@@
class TeleportTable {
public:
    TeleportTable();
    virtual ~TeleportTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TeleportTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTimeGraphTable@@
class TimeGraphTable {
public:
    TimeGraphTable();
    virtual ~TimeGraphTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TimeGraphTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTitleCollectionTable@@
class TitleCollectionTable {
public:
    TitleCollectionTable();
    virtual ~TitleCollectionTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TitleCollectionTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTitleTable@@
class TitleTable {
public:
    TitleTable();
    virtual ~TitleTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TitleTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVToyPetDopingTable@@
class ToyPetDopingTable {
public:
    ToyPetDopingTable();
    virtual ~ToyPetDopingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ToyPetDopingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVToyPetFeedingTable@@
class ToyPetFeedingTable {
public:
    ToyPetFeedingTable();
    virtual ~ToyPetFeedingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ToyPetFeedingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVToyPetItemTable@@
class ToyPetItemTable {
public:
    ToyPetItemTable();
    virtual ~ToyPetItemTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ToyPetItemTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVToyPetLootingTable@@
class ToyPetLootingTable {
public:
    ToyPetLootingTable();
    virtual ~ToyPetLootingTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ToyPetLootingTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVToyPetTable@@
class ToyPetTable {
public:
    ToyPetTable();
    virtual ~ToyPetTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ToyPetTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVToyPetWarehouseTable@@
class ToyPetWarehouseTable {
public:
    ToyPetWarehouseTable();
    virtual ~ToyPetWarehouseTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ToyPetWarehouseTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTradeInListTable@@
class TradeInListTable {
public:
    TradeInListTable();
    virtual ~TradeInListTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TradeInListTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVTribeTable@@
class TribeTable {
public:
    TribeTable();
    virtual ~TribeTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "TribeTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVUIColorTable@@
class UIColorTable {
public:
    UIColorTable();
    virtual ~UIColorTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "UIColorTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVUltraSkillTable@@
class UltraSkillTable {
public:
    UltraSkillTable();
    virtual ~UltraSkillTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "UltraSkillTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVVitalPointTable@@
class VitalPointTable {
public:
    VitalPointTable();
    virtual ~VitalPointTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "VitalPointTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVWarFlagColorTable@@
class WarFlagColorTable {
public:
    WarFlagColorTable();
    virtual ~WarFlagColorTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "WarFlagColorTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVWardrobeConfigTable@@
class WardrobeConfigTable {
public:
    WardrobeConfigTable();
    virtual ~WardrobeConfigTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "WardrobeConfigTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVWebServiceTable@@
class WebServiceTable {
public:
    WebServiceTable();
    virtual ~WebServiceTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "WebServiceTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVWorldIDTable@@
class WorldIDTable {
public:
    WorldIDTable();
    virtual ~WorldIDTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "WorldIDTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVWorldReturnTable@@
class WorldReturnTable {
public:
    WorldReturnTable();
    virtual ~WorldReturnTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "WorldReturnTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVWorldTimeoutTable@@
class WorldTimeoutTable {
public:
    WorldTimeoutTable();
    virtual ~WorldTimeoutTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "WorldTimeoutTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVZoneContentUiTable@@
class ZoneContentUiTable {
public:
    ZoneContentUiTable();
    virtual ~ZoneContentUiTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ZoneContentUiTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVZoneMapColorTable@@
class ZoneMapColorTable {
public:
    ZoneMapColorTable();
    virtual ~ZoneMapColorTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ZoneMapColorTable"; }
private:
    bool m_bLoaded;
};

// RTTI .?AVZoneMapEventMarkerTable@@
class ZoneMapEventMarkerTable {
public:
    ZoneMapEventMarkerTable();
    virtual ~ZoneMapEventMarkerTable();
    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "ZoneMapEventMarkerTable"; }
private:
    bool m_bLoaded;
};

void RegisterAllGameTablesExt();