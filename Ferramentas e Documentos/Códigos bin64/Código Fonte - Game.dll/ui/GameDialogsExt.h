#pragma once
#include "AddonFrame.h"
#include <string>

// RTTI .?AVDlgStoryBook@@ e seus tabs aninhados
class DlgStoryBook : public AddonFrame {
public:
    DlgStoryBook(const std::string& name = "DlgStoryBook");
    virtual ~DlgStoryBook();
    virtual void Show(bool bShow) override;
    virtual void Update() override;

    // RTTI .?AVAdventureTab@DlgStoryBook@@
    class AdventureTab : public AddonFrame {
    public:
        AdventureTab(const std::string& name = "AdventureTab");
        virtual ~AdventureTab();
        virtual void Show(bool bShow) override;
        virtual void Update() override;
    };

    // RTTI .?AVBaseTab@DlgStoryBook@@
    class BaseTab : public AddonFrame {
    public:
        BaseTab(const std::string& name = "BaseTab");
        virtual ~BaseTab();
        virtual void Show(bool bShow) override;
        virtual void Update() override;
    };

    // RTTI .?AVNatureTab@DlgStoryBook@@
    class NatureTab : public AddonFrame {
    public:
        NatureTab(const std::string& name = "NatureTab");
        virtual ~NatureTab();
        virtual void Show(bool bShow) override;
        virtual void Update() override;
    };

    // RTTI .?AVPuzzleTab@DlgStoryBook@@
    class PuzzleTab : public AddonFrame {
    public:
        PuzzleTab(const std::string& name = "PuzzleTab");
        virtual ~PuzzleTab();
        virtual void Show(bool bShow) override;
        virtual void Update() override;
    };
};

// RTTI .?AVCefDialogHandler@@
class CefDialogHandler : public AddonFrame {
public:
    CefDialogHandler(const std::string& name = "CefDialogHandler");
    virtual ~CefDialogHandler();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVCefJSDialogHandler@@
class CefJSDialogHandler : public AddonFrame {
public:
    CefJSDialogHandler(const std::string& name = "CefJSDialogHandler");
    virtual ~CefJSDialogHandler();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAbyssRank@@
class DlgAbyssRank : public AddonFrame {
public:
    DlgAbyssRank(const std::string& name = "DlgAbyssRank");
    virtual ~DlgAbyssRank();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAccountInfo@@
class DlgAccountInfo : public AddonFrame {
public:
    DlgAccountInfo(const std::string& name = "DlgAccountInfo");
    virtual ~DlgAccountInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAccumulatedEnchantResult@@
class DlgAccumulatedEnchantResult : public AddonFrame {
public:
    DlgAccumulatedEnchantResult(const std::string& name = "DlgAccumulatedEnchantResult");
    virtual ~DlgAccumulatedEnchantResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAddItemProc@@
class DlgAddItemProc : public AddonFrame {
public:
    DlgAddItemProc(const std::string& name = "DlgAddItemProc");
    virtual ~DlgAddItemProc();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAionLook@@
class DlgAionLook : public AddonFrame {
public:
    DlgAionLook(const std::string& name = "DlgAionLook");
    virtual ~DlgAionLook();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAionLookDisassemblyItemInfo@@
class DlgAionLookDisassemblyItemInfo : public AddonFrame {
public:
    DlgAionLookDisassemblyItemInfo(const std::string& name = "DlgAionLookDisassemblyItemInfo");
    virtual ~DlgAionLookDisassemblyItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAirlineService@@
class DlgAirlineService : public AddonFrame {
public:
    DlgAirlineService(const std::string& name = "DlgAirlineService");
    virtual ~DlgAirlineService();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAlterConsole@@
class DlgAlterConsole : public AddonFrame {
public:
    DlgAlterConsole(const std::string& name = "DlgAlterConsole");
    virtual ~DlgAlterConsole();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAlterInfo@@
class DlgAlterInfo : public AddonFrame {
public:
    DlgAlterInfo(const std::string& name = "DlgAlterInfo");
    virtual ~DlgAlterInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgArtDev@@
class DlgArtDev : public AddonFrame {
public:
    DlgArtDev(const std::string& name = "DlgArtDev");
    virtual ~DlgArtDev();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgArtDevLobby@@
class DlgArtDevLobby : public AddonFrame {
public:
    DlgArtDevLobby(const std::string& name = "DlgArtDevLobby");
    virtual ~DlgArtDevLobby();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgArtifact@@
class DlgArtifact : public AddonFrame {
public:
    DlgArtifact(const std::string& name = "DlgArtifact");
    virtual ~DlgArtifact();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAssemblyItemInfo@@
class DlgAssemblyItemInfo : public AddonFrame {
public:
    DlgAssemblyItemInfo(const std::string& name = "DlgAssemblyItemInfo");
    virtual ~DlgAssemblyItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAssistOptionEnchantCancel@@
class DlgAssistOptionEnchantCancel : public AddonFrame {
public:
    DlgAssistOptionEnchantCancel(const std::string& name = "DlgAssistOptionEnchantCancel");
    virtual ~DlgAssistOptionEnchantCancel();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgAssistOptionEnchantProbs@@
class DlgAssistOptionEnchantProbs : public AddonFrame {
public:
    DlgAssistOptionEnchantProbs(const std::string& name = "DlgAssistOptionEnchantProbs");
    virtual ~DlgAssistOptionEnchantProbs();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBI@@
class DlgBI : public AddonFrame {
public:
    DlgBI(const std::string& name = "DlgBI");
    virtual ~DlgBI();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBaseBuff@@
class DlgBaseBuff : public AddonFrame {
public:
    DlgBaseBuff(const std::string& name = "DlgBaseBuff");
    virtual ~DlgBaseBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBasicStatus@@
class DlgBasicStatus : public AddonFrame {
public:
    DlgBasicStatus(const std::string& name = "DlgBasicStatus");
    virtual ~DlgBasicStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBattlePass@@
class DlgBattlePass : public AddonFrame {
public:
    DlgBattlePass(const std::string& name = "DlgBattlePass");
    virtual ~DlgBattlePass();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBattlePassNotice@@
class DlgBattlePassNotice : public AddonFrame {
public:
    DlgBattlePassNotice(const std::string& name = "DlgBattlePassNotice");
    virtual ~DlgBattlePassNotice();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBoardBm@@
class DlgBoardBm : public AddonFrame {
public:
    DlgBoardBm(const std::string& name = "DlgBoardBm");
    virtual ~DlgBoardBm();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBuffStatus@@
class DlgBuffStatus : public AddonFrame {
public:
    DlgBuffStatus(const std::string& name = "DlgBuffStatus");
    virtual ~DlgBuffStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBuilderDev@@
class DlgBuilderDev : public AddonFrame {
public:
    DlgBuilderDev(const std::string& name = "DlgBuilderDev");
    virtual ~DlgBuilderDev();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgBuilderOptionLoad@@
class DlgBuilderOptionLoad : public AddonFrame {
public:
    DlgBuilderOptionLoad(const std::string& name = "DlgBuilderOptionLoad");
    virtual ~DlgBuilderOptionLoad();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCannon@@
class DlgCannon : public AddonFrame {
public:
    DlgCannon(const std::string& name = "DlgCannon");
    virtual ~DlgCannon();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCaptcha@@
class DlgCaptcha : public AddonFrame {
public:
    DlgCaptcha(const std::string& name = "DlgCaptcha");
    virtual ~DlgCaptcha();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChannel@@
class DlgChannel : public AddonFrame {
public:
    DlgChannel(const std::string& name = "DlgChannel");
    virtual ~DlgChannel();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChange@@
class DlgCharacterChange : public AddonFrame {
public:
    DlgCharacterChange(const std::string& name = "DlgCharacterChange");
    virtual ~DlgCharacterChange();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeAgreement@@
class DlgCharacterChangeAgreement : public AddonFrame {
public:
    DlgCharacterChangeAgreement(const std::string& name = "DlgCharacterChangeAgreement");
    virtual ~DlgCharacterChangeAgreement();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeComparePopup@@
class DlgCharacterChangeComparePopup : public AddonFrame {
public:
    DlgCharacterChangeComparePopup(const std::string& name = "DlgCharacterChangeComparePopup");
    virtual ~DlgCharacterChangeComparePopup();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeDetail@@
class DlgCharacterChangeDetail : public AddonFrame {
public:
    DlgCharacterChangeDetail(const std::string& name = "DlgCharacterChangeDetail");
    virtual ~DlgCharacterChangeDetail();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeSelectItem@@
class DlgCharacterChangeSelectItem : public AddonFrame {
public:
    DlgCharacterChangeSelectItem(const std::string& name = "DlgCharacterChangeSelectItem");
    virtual ~DlgCharacterChangeSelectItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeSelectSkill@@
class DlgCharacterChangeSelectSkill : public AddonFrame {
public:
    DlgCharacterChangeSelectSkill(const std::string& name = "DlgCharacterChangeSelectSkill");
    virtual ~DlgCharacterChangeSelectSkill();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeSelectSkillItem@@
class DlgCharacterChangeSelectSkillItem : public AddonFrame {
public:
    DlgCharacterChangeSelectSkillItem(const std::string& name = "DlgCharacterChangeSelectSkillItem");
    virtual ~DlgCharacterChangeSelectSkillItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCharacterChangeSelectableOptionItem@@
class DlgCharacterChangeSelectableOptionItem : public AddonFrame {
public:
    DlgCharacterChangeSelectableOptionItem(const std::string& name = "DlgCharacterChangeSelectableOptionItem");
    virtual ~DlgCharacterChangeSelectableOptionItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChargeItem@@
class DlgChargeItem : public AddonFrame {
public:
    DlgChargeItem(const std::string& name = "DlgChargeItem");
    virtual ~DlgChargeItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChat@@
class DlgChat : public AddonFrame {
public:
    DlgChat(const std::string& name = "DlgChat");
    virtual ~DlgChat();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChatInput@@
class DlgChatInput : public AddonFrame {
public:
    DlgChatInput(const std::string& name = "DlgChatInput");
    virtual ~DlgChatInput();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChatOption@@
class DlgChatOption : public AddonFrame {
public:
    DlgChatOption(const std::string& name = "DlgChatOption");
    virtual ~DlgChatOption();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChatSep@@
class DlgChatSep : public AddonFrame {
public:
    DlgChatSep(const std::string& name = "DlgChatSep");
    virtual ~DlgChatSep();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChoice@@
class DlgChoice : public AddonFrame {
public:
    DlgChoice(const std::string& name = "DlgChoice");
    virtual ~DlgChoice();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChoiceOne@@
class DlgChoiceOne : public AddonFrame {
public:
    DlgChoiceOne(const std::string& name = "DlgChoiceOne");
    virtual ~DlgChoiceOne();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgChoiceThree@@
class DlgChoiceThree : public AddonFrame {
public:
    DlgChoiceThree(const std::string& name = "DlgChoiceThree");
    virtual ~DlgChoiceThree();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgColorSelect@@
class DlgColorSelect : public AddonFrame {
public:
    DlgColorSelect(const std::string& name = "DlgColorSelect");
    virtual ~DlgColorSelect();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCombatPowerRankReward@@
class DlgCombatPowerRankReward : public AddonFrame {
public:
    DlgCombatPowerRankReward(const std::string& name = "DlgCombatPowerRankReward");
    virtual ~DlgCombatPowerRankReward();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCombatPowerRankerWatch@@
class DlgCombatPowerRankerWatch : public AddonFrame {
public:
    DlgCombatPowerRankerWatch(const std::string& name = "DlgCombatPowerRankerWatch");
    virtual ~DlgCombatPowerRankerWatch();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCombatPowerRanking@@
class DlgCombatPowerRanking : public AddonFrame {
public:
    DlgCombatPowerRanking(const std::string& name = "DlgCombatPowerRanking");
    virtual ~DlgCombatPowerRanking();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCombatPowerRankingReward@@
class DlgCombatPowerRankingReward : public AddonFrame {
public:
    DlgCombatPowerRankingReward(const std::string& name = "DlgCombatPowerRankingReward");
    virtual ~DlgCombatPowerRankingReward();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCombineProbabilityItemInfo@@
class DlgCombineProbabilityItemInfo : public AddonFrame {
public:
    DlgCombineProbabilityItemInfo(const std::string& name = "DlgCombineProbabilityItemInfo");
    virtual ~DlgCombineProbabilityItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCommand@@
class DlgCommand : public AddonFrame {
public:
    DlgCommand(const std::string& name = "DlgCommand");
    virtual ~DlgCommand();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCommonAlert@@
class DlgCommonAlert : public AddonFrame {
public:
    DlgCommonAlert(const std::string& name = "DlgCommonAlert");
    virtual ~DlgCommonAlert();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCompoundWeapon@@
class DlgCompoundWeapon : public AddonFrame {
public:
    DlgCompoundWeapon(const std::string& name = "DlgCompoundWeapon");
    virtual ~DlgCompoundWeapon();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCraftMultiResult@@
class DlgCraftMultiResult : public AddonFrame {
public:
    DlgCraftMultiResult(const std::string& name = "DlgCraftMultiResult");
    virtual ~DlgCraftMultiResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCreateChar@@
class DlgCreateChar : public AddonFrame {
public:
    DlgCreateChar(const std::string& name = "DlgCreateChar");
    virtual ~DlgCreateChar();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCreateClass@@
class DlgCreateClass : public AddonFrame {
public:
    DlgCreateClass(const std::string& name = "DlgCreateClass");
    virtual ~DlgCreateClass();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCreateRace@@
class DlgCreateRace : public AddonFrame {
public:
    DlgCreateRace(const std::string& name = "DlgCreateRace");
    virtual ~DlgCreateRace();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCredit@@
class DlgCredit : public AddonFrame {
public:
    DlgCredit(const std::string& name = "DlgCredit");
    virtual ~DlgCredit();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgCustomizing@@
class DlgCustomizing : public AddonFrame {
public:
    DlgCustomizing(const std::string& name = "DlgCustomizing");
    virtual ~DlgCustomizing();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDebuffStatus@@
class DlgDebuffStatus : public AddonFrame {
public:
    DlgDebuffStatus(const std::string& name = "DlgDebuffStatus");
    virtual ~DlgDebuffStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDecompoundWeapon@@
class DlgDecompoundWeapon : public AddonFrame {
public:
    DlgDecompoundWeapon(const std::string& name = "DlgDecompoundWeapon");
    virtual ~DlgDecompoundWeapon();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDevaSchedule@@
class DlgDevaSchedule : public AddonFrame {
public:
    DlgDevaSchedule(const std::string& name = "DlgDevaSchedule");
    virtual ~DlgDevaSchedule();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDialog@@
class DlgDialog : public AddonFrame {
public:
    DlgDialog(const std::string& name = "DlgDialog");
    virtual ~DlgDialog();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDictionary@@
class DlgDictionary : public AddonFrame {
public:
    DlgDictionary(const std::string& name = "DlgDictionary");
    virtual ~DlgDictionary();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDirectory@@
class DlgDirectory : public AddonFrame {
public:
    DlgDirectory(const std::string& name = "DlgDirectory");
    virtual ~DlgDirectory();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDisassemblyItemInfo@@
class DlgDisassemblyItemInfo : public AddonFrame {
public:
    DlgDisassemblyItemInfo(const std::string& name = "DlgDisassemblyItemInfo");
    virtual ~DlgDisassemblyItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgDisassemblyItemList@@
class DlgDisassemblyItemList : public AddonFrame {
public:
    DlgDisassemblyItemList(const std::string& name = "DlgDisassemblyItemList");
    virtual ~DlgDisassemblyItemList();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgECard@@
class DlgECard : public AddonFrame {
public:
    DlgECard(const std::string& name = "DlgECard");
    virtual ~DlgECard();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEmblem@@
class DlgEmblem : public AddonFrame {
public:
    DlgEmblem(const std::string& name = "DlgEmblem");
    virtual ~DlgEmblem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEmoticon@@
class DlgEmoticon : public AddonFrame {
public:
    DlgEmoticon(const std::string& name = "DlgEmoticon");
    virtual ~DlgEmoticon();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEmotionAway@@
class DlgEmotionAway : public AddonFrame {
public:
    DlgEmotionAway(const std::string& name = "DlgEmotionAway");
    virtual ~DlgEmotionAway();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEnchantMaterial@@
class DlgEnchantMaterial : public AddonFrame {
public:
    DlgEnchantMaterial(const std::string& name = "DlgEnchantMaterial");
    virtual ~DlgEnchantMaterial();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEnchantOption@@
class DlgEnchantOption : public AddonFrame {
public:
    DlgEnchantOption(const std::string& name = "DlgEnchantOption");
    virtual ~DlgEnchantOption();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEnchantRenewal@@
class DlgEnchantRenewal : public AddonFrame {
public:
    DlgEnchantRenewal(const std::string& name = "DlgEnchantRenewal");
    virtual ~DlgEnchantRenewal();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEquipmentChange@@
class DlgEquipmentChange : public AddonFrame {
public:
    DlgEquipmentChange(const std::string& name = "DlgEquipmentChange");
    virtual ~DlgEquipmentChange();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEquippedItemChargePoint@@
class DlgEquippedItemChargePoint : public AddonFrame {
public:
    DlgEquippedItemChargePoint(const std::string& name = "DlgEquippedItemChargePoint");
    virtual ~DlgEquippedItemChargePoint();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgEventShortCut@@
class DlgEventShortCut : public AddonFrame {
public:
    DlgEventShortCut(const std::string& name = "DlgEventShortCut");
    virtual ~DlgEventShortCut();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgExchange@@
class DlgExchange : public AddonFrame {
public:
    DlgExchange(const std::string& name = "DlgExchange");
    virtual ~DlgExchange();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgExpBar@@
class DlgExpBar : public AddonFrame {
public:
    DlgExpBar(const std::string& name = "DlgExpBar");
    virtual ~DlgExpBar();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgFXTitle@@
class DlgFXTitle : public AddonFrame {
public:
    DlgFXTitle(const std::string& name = "DlgFXTitle");
    virtual ~DlgFXTitle();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgFatigue@@
class DlgFatigue : public AddonFrame {
public:
    DlgFatigue(const std::string& name = "DlgFatigue");
    virtual ~DlgFatigue();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgFileSearch@@
class DlgFileSearch : public AddonFrame {
public:
    DlgFileSearch(const std::string& name = "DlgFileSearch");
    virtual ~DlgFileSearch();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgFont@@
class DlgFont : public AddonFrame {
public:
    DlgFont(const std::string& name = "DlgFont");
    virtual ~DlgFont();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgForce@@
class DlgForce : public AddonFrame {
public:
    DlgForce(const std::string& name = "DlgForce");
    virtual ~DlgForce();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgForceReady@@
class DlgForceReady : public AddonFrame {
public:
    DlgForceReady(const std::string& name = "DlgForceReady");
    virtual ~DlgForceReady();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgForceSepBuff@@
class DlgForceSepBuff : public AddonFrame {
public:
    DlgForceSepBuff(const std::string& name = "DlgForceSepBuff");
    virtual ~DlgForceSepBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgForceSepGroup@@
class DlgForceSepGroup : public AddonFrame {
public:
    DlgForceSepGroup(const std::string& name = "DlgForceSepGroup");
    virtual ~DlgForceSepGroup();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgForceSepMember@@
class DlgForceSepMember : public AddonFrame {
public:
    DlgForceSepMember(const std::string& name = "DlgForceSepMember");
    virtual ~DlgForceSepMember();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGM@@
class DlgGM : public AddonFrame {
public:
    DlgGM(const std::string& name = "DlgGM");
    virtual ~DlgGM();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGMBookmark@@
class DlgGMBookmark : public AddonFrame {
public:
    DlgGMBookmark(const std::string& name = "DlgGMBookmark");
    virtual ~DlgGMBookmark();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGMMemo@@
class DlgGMMemo : public AddonFrame {
public:
    DlgGMMemo(const std::string& name = "DlgGMMemo");
    virtual ~DlgGMMemo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGMPacketSave@@
class DlgGMPacketSave : public AddonFrame {
public:
    DlgGMPacketSave(const std::string& name = "DlgGMPacketSave");
    virtual ~DlgGMPacketSave();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGMPoll@@
class DlgGMPoll : public AddonFrame {
public:
    DlgGMPoll(const std::string& name = "DlgGMPoll");
    virtual ~DlgGMPoll();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGameGrade@@
class DlgGameGrade : public AddonFrame {
public:
    DlgGameGrade(const std::string& name = "DlgGameGrade");
    virtual ~DlgGameGrade();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGameMenu@@
class DlgGameMenu : public AddonFrame {
public:
    DlgGameMenu(const std::string& name = "DlgGameMenu");
    virtual ~DlgGameMenu();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGameMenuBookmark@@
class DlgGameMenuBookmark : public AddonFrame {
public:
    DlgGameMenuBookmark(const std::string& name = "DlgGameMenuBookmark");
    virtual ~DlgGameMenuBookmark();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGateFortifier@@
class DlgGateFortifier : public AddonFrame {
public:
    DlgGateFortifier(const std::string& name = "DlgGateFortifier");
    virtual ~DlgGateFortifier();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGathaEnchant@@
class DlgGathaEnchant : public AddonFrame {
public:
    DlgGathaEnchant(const std::string& name = "DlgGathaEnchant");
    virtual ~DlgGathaEnchant();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGathaHelp@@
class DlgGathaHelp : public AddonFrame {
public:
    DlgGathaHelp(const std::string& name = "DlgGathaHelp");
    virtual ~DlgGathaHelp();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGathaReward@@
class DlgGathaReward : public AddonFrame {
public:
    DlgGathaReward(const std::string& name = "DlgGathaReward");
    virtual ~DlgGathaReward();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGatherSelect@@
class DlgGatherSelect : public AddonFrame {
public:
    DlgGatherSelect(const std::string& name = "DlgGatherSelect");
    virtual ~DlgGatherSelect();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGathering@@
class DlgGathering : public AddonFrame {
public:
    DlgGathering(const std::string& name = "DlgGathering");
    virtual ~DlgGathering();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGemMatterOptionProbs@@
class DlgGemMatterOptionProbs : public AddonFrame {
public:
    DlgGemMatterOptionProbs(const std::string& name = "DlgGemMatterOptionProbs");
    virtual ~DlgGemMatterOptionProbs();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGemMatterOptionTool@@
class DlgGemMatterOptionTool : public AddonFrame {
public:
    DlgGemMatterOptionTool(const std::string& name = "DlgGemMatterOptionTool");
    virtual ~DlgGemMatterOptionTool();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGeneralGauge@@
class DlgGeneralGauge : public AddonFrame {
public:
    DlgGeneralGauge(const std::string& name = "DlgGeneralGauge");
    virtual ~DlgGeneralGauge();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGlideAttackCut@@
class DlgGlideAttackCut : public AddonFrame {
public:
    DlgGlideAttackCut(const std::string& name = "DlgGlideAttackCut");
    virtual ~DlgGlideAttackCut();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGlobalOption@@
class DlgGlobalOption : public AddonFrame {
public:
    DlgGlobalOption(const std::string& name = "DlgGlobalOption");
    virtual ~DlgGlobalOption();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGoodsInfo@@
class DlgGoodsInfo : public AddonFrame {
public:
    DlgGoodsInfo(const std::string& name = "DlgGoodsInfo");
    virtual ~DlgGoodsInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildActivity@@
class DlgGuildActivity : public AddonFrame {
public:
    DlgGuildActivity(const std::string& name = "DlgGuildActivity");
    virtual ~DlgGuildActivity();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildAuth@@
class DlgGuildAuth : public AddonFrame {
public:
    DlgGuildAuth(const std::string& name = "DlgGuildAuth");
    virtual ~DlgGuildAuth();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildBuffBuy@@
class DlgGuildBuffBuy : public AddonFrame {
public:
    DlgGuildBuffBuy(const std::string& name = "DlgGuildBuffBuy");
    virtual ~DlgGuildBuffBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildBuffOpen@@
class DlgGuildBuffOpen : public AddonFrame {
public:
    DlgGuildBuffOpen(const std::string& name = "DlgGuildBuffOpen");
    virtual ~DlgGuildBuffOpen();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildCraftGiveMaterial@@
class DlgGuildCraftGiveMaterial : public AddonFrame {
public:
    DlgGuildCraftGiveMaterial(const std::string& name = "DlgGuildCraftGiveMaterial");
    virtual ~DlgGuildCraftGiveMaterial();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildCreate@@
class DlgGuildCreate : public AddonFrame {
public:
    DlgGuildCreate(const std::string& name = "DlgGuildCreate");
    virtual ~DlgGuildCreate();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildHistory@@
class DlgGuildHistory : public AddonFrame {
public:
    DlgGuildHistory(const std::string& name = "DlgGuildHistory");
    virtual ~DlgGuildHistory();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildInfo@@
class DlgGuildInfo : public AddonFrame {
public:
    DlgGuildInfo(const std::string& name = "DlgGuildInfo");
    virtual ~DlgGuildInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildJoin@@
class DlgGuildJoin : public AddonFrame {
public:
    DlgGuildJoin(const std::string& name = "DlgGuildJoin");
    virtual ~DlgGuildJoin();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildNotice@@
class DlgGuildNotice : public AddonFrame {
public:
    DlgGuildNotice(const std::string& name = "DlgGuildNotice");
    virtual ~DlgGuildNotice();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGuildOtherInfo@@
class DlgGuildOtherInfo : public AddonFrame {
public:
    DlgGuildOtherInfo(const std::string& name = "DlgGuildOtherInfo");
    virtual ~DlgGuildOtherInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgGunnerSkill@@
class DlgGunnerSkill : public AddonFrame {
public:
    DlgGunnerSkill(const std::string& name = "DlgGunnerSkill");
    virtual ~DlgGunnerSkill();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgHelpIndicator@@
class DlgHelpIndicator : public AddonFrame {
public:
    DlgHelpIndicator(const std::string& name = "DlgHelpIndicator");
    virtual ~DlgHelpIndicator();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgHudEditMode@@
class DlgHudEditMode : public AddonFrame {
public:
    DlgHudEditMode(const std::string& name = "DlgHudEditMode");
    virtual ~DlgHudEditMode();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIDArenaPvPRank@@
class DlgIDArenaPvPRank : public AddonFrame {
public:
    DlgIDArenaPvPRank(const std::string& name = "DlgIDArenaPvPRank");
    virtual ~DlgIDArenaPvPRank();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIDArenaTeam@@
class DlgIDArenaTeam : public AddonFrame {
public:
    DlgIDArenaTeam(const std::string& name = "DlgIDArenaTeam");
    virtual ~DlgIDArenaTeam();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIDArenaTeamRank@@
class DlgIDArenaTeamRank : public AddonFrame {
public:
    DlgIDArenaTeamRank(const std::string& name = "DlgIDArenaTeamRank");
    virtual ~DlgIDArenaTeamRank();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIDInfinity@@
class DlgIDInfinity : public AddonFrame {
public:
    DlgIDInfinity(const std::string& name = "DlgIDInfinity");
    virtual ~DlgIDInfinity();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIDScoreDamageResult@@
class DlgIDScoreDamageResult : public AddonFrame {
public:
    DlgIDScoreDamageResult(const std::string& name = "DlgIDScoreDamageResult");
    virtual ~DlgIDScoreDamageResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIDScoreDamageStandard@@
class DlgIDScoreDamageStandard : public AddonFrame {
public:
    DlgIDScoreDamageStandard(const std::string& name = "DlgIDScoreDamageStandard");
    virtual ~DlgIDScoreDamageStandard();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDArena@@
class DlgIndunAccountIDArena : public AddonFrame {
public:
    DlgIndunAccountIDArena(const std::string& name = "DlgIndunAccountIDArena");
    virtual ~DlgIndunAccountIDArena();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDDragonTwin@@
class DlgIndunAccountIDDragonTwin : public AddonFrame {
public:
    DlgIndunAccountIDDragonTwin(const std::string& name = "DlgIndunAccountIDDragonTwin");
    virtual ~DlgIndunAccountIDDragonTwin();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDDrana@@
class DlgIndunAccountIDDrana : public AddonFrame {
public:
    DlgIndunAccountIDDrana(const std::string& name = "DlgIndunAccountIDDrana");
    virtual ~DlgIndunAccountIDDrana();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDDre@@
class DlgIndunAccountIDDre : public AddonFrame {
public:
    DlgIndunAccountIDDre(const std::string& name = "DlgIndunAccountIDDre");
    virtual ~DlgIndunAccountIDDre();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDDre2@@
class DlgIndunAccountIDDre2 : public AddonFrame {
public:
    DlgIndunAccountIDDre2(const std::string& name = "DlgIndunAccountIDDre2");
    virtual ~DlgIndunAccountIDDre2();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDEvent@@
class DlgIndunAccountIDEvent : public AddonFrame {
public:
    DlgIndunAccountIDEvent(const std::string& name = "DlgIndunAccountIDEvent");
    virtual ~DlgIndunAccountIDEvent();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDEvent4@@
class DlgIndunAccountIDEvent4 : public AddonFrame {
public:
    DlgIndunAccountIDEvent4(const std::string& name = "DlgIndunAccountIDEvent4");
    virtual ~DlgIndunAccountIDEvent4();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDF4ReSolo@@
class DlgIndunAccountIDF4ReSolo : public AddonFrame {
public:
    DlgIndunAccountIDF4ReSolo(const std::string& name = "DlgIndunAccountIDF4ReSolo");
    virtual ~DlgIndunAccountIDF4ReSolo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDFist@@
class DlgIndunAccountIDFist : public AddonFrame {
public:
    DlgIndunAccountIDFist(const std::string& name = "DlgIndunAccountIDFist");
    virtual ~DlgIndunAccountIDFist();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDLF1@@
class DlgIndunAccountIDLF1 : public AddonFrame {
public:
    DlgIndunAccountIDLF1(const std::string& name = "DlgIndunAccountIDLF1");
    virtual ~DlgIndunAccountIDLF1();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunAccountIDNewDre@@
class DlgIndunAccountIDNewDre : public AddonFrame {
public:
    DlgIndunAccountIDNewDre(const std::string& name = "DlgIndunAccountIDNewDre");
    virtual ~DlgIndunAccountIDNewDre();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunCooltime@@
class DlgIndunCooltime : public AddonFrame {
public:
    DlgIndunCooltime(const std::string& name = "DlgIndunCooltime");
    virtual ~DlgIndunCooltime();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunCooltimeReset@@
class DlgIndunCooltimeReset : public AddonFrame {
public:
    DlgIndunCooltimeReset(const std::string& name = "DlgIndunCooltimeReset");
    virtual ~DlgIndunCooltimeReset();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunEnter@@
class DlgIndunEnter : public AddonFrame {
public:
    DlgIndunEnter(const std::string& name = "DlgIndunEnter");
    virtual ~DlgIndunEnter();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunInfo@@
class DlgIndunInfo : public AddonFrame {
public:
    DlgIndunInfo(const std::string& name = "DlgIndunInfo");
    virtual ~DlgIndunInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunRegister@@
class DlgIndunRegister : public AddonFrame {
public:
    DlgIndunRegister(const std::string& name = "DlgIndunRegister");
    virtual ~DlgIndunRegister();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunTitleIDArena@@
class DlgIndunTitleIDArena : public AddonFrame {
public:
    DlgIndunTitleIDArena(const std::string& name = "DlgIndunTitleIDArena");
    virtual ~DlgIndunTitleIDArena();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunTitleIDArenaPvP@@
class DlgIndunTitleIDArenaPvP : public AddonFrame {
public:
    DlgIndunTitleIDArenaPvP(const std::string& name = "DlgIndunTitleIDArenaPvP");
    virtual ~DlgIndunTitleIDArenaPvP();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunTitleIDArenaStageEnd@@
class DlgIndunTitleIDArenaStageEnd : public AddonFrame {
public:
    DlgIndunTitleIDArenaStageEnd(const std::string& name = "DlgIndunTitleIDArenaStageEnd");
    virtual ~DlgIndunTitleIDArenaStageEnd();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIndunWaitInfo@@
class DlgIndunWaitInfo : public AddonFrame {
public:
    DlgIndunWaitInfo(const std::string& name = "DlgIndunWaitInfo");
    virtual ~DlgIndunWaitInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameHelp@@
class DlgIngameHelp : public AddonFrame {
public:
    DlgIngameHelp(const std::string& name = "DlgIngameHelp");
    virtual ~DlgIngameHelp();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameShop@@
class DlgIngameShop : public AddonFrame {
public:
    DlgIngameShop(const std::string& name = "DlgIngameShop");
    virtual ~DlgIngameShop();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameShopBuy@@
class DlgIngameShopBuy : public AddonFrame {
public:
    DlgIngameShopBuy(const std::string& name = "DlgIngameShopBuy");
    virtual ~DlgIngameShopBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameShopGift@@
class DlgIngameShopGift : public AddonFrame {
public:
    DlgIngameShopGift(const std::string& name = "DlgIngameShopGift");
    virtual ~DlgIngameShopGift();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameShopPopupBase@@
class DlgIngameShopPopupBase : public AddonFrame {
public:
    DlgIngameShopPopupBase(const std::string& name = "DlgIngameShopPopupBase");
    virtual ~DlgIngameShopPopupBase();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameWebBrowser@@
class DlgIngameWebBrowser : public AddonFrame {
public:
    DlgIngameWebBrowser(const std::string& name = "DlgIngameWebBrowser");
    virtual ~DlgIngameWebBrowser();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIngameWebShop@@
class DlgIngameWebShop : public AddonFrame {
public:
    DlgIngameWebShop(const std::string& name = "DlgIngameWebShop");
    virtual ~DlgIngameWebShop();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgIntroductionWrite@@
class DlgIntroductionWrite : public AddonFrame {
public:
    DlgIntroductionWrite(const std::string& name = "DlgIntroductionWrite");
    virtual ~DlgIntroductionWrite();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgInventory@@
class DlgInventory : public AddonFrame {
public:
    DlgInventory(const std::string& name = "DlgInventory");
    virtual ~DlgInventory();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgInventoryCoin@@
class DlgInventoryCoin : public AddonFrame {
public:
    DlgInventoryCoin(const std::string& name = "DlgInventoryCoin");
    virtual ~DlgInventoryCoin();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgInventoryCoinOther@@
class DlgInventoryCoinOther : public AddonFrame {
public:
    DlgInventoryCoinOther(const std::string& name = "DlgInventoryCoinOther");
    virtual ~DlgInventoryCoinOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgInventoryDevaPass@@
class DlgInventoryDevaPass : public AddonFrame {
public:
    DlgInventoryDevaPass(const std::string& name = "DlgInventoryDevaPass");
    virtual ~DlgInventoryDevaPass();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgInventoryOther@@
class DlgInventoryOther : public AddonFrame {
public:
    DlgInventoryOther(const std::string& name = "DlgInventoryOther");
    virtual ~DlgInventoryOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemCompose@@
class DlgItemCompose : public AddonFrame {
public:
    DlgItemCompose(const std::string& name = "DlgItemCompose");
    virtual ~DlgItemCompose();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemComposeProb@@
class DlgItemComposeProb : public AddonFrame {
public:
    DlgItemComposeProb(const std::string& name = "DlgItemComposeProb");
    virtual ~DlgItemComposeProb();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemComposeResult@@
class DlgItemComposeResult : public AddonFrame {
public:
    DlgItemComposeResult(const std::string& name = "DlgItemComposeResult");
    virtual ~DlgItemComposeResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemCount@@
class DlgItemCount : public AddonFrame {
public:
    DlgItemCount(const std::string& name = "DlgItemCount");
    virtual ~DlgItemCount();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemCrush@@
class DlgItemCrush : public AddonFrame {
public:
    DlgItemCrush(const std::string& name = "DlgItemCrush");
    virtual ~DlgItemCrush();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemCrushInfo@@
class DlgItemCrushInfo : public AddonFrame {
public:
    DlgItemCrushInfo(const std::string& name = "DlgItemCrushInfo");
    virtual ~DlgItemCrushInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemCrushResult@@
class DlgItemCrushResult : public AddonFrame {
public:
    DlgItemCrushResult(const std::string& name = "DlgItemCrushResult");
    virtual ~DlgItemCrushResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemEnchantDelay@@
class DlgItemEnchantDelay : public AddonFrame {
public:
    DlgItemEnchantDelay(const std::string& name = "DlgItemEnchantDelay");
    virtual ~DlgItemEnchantDelay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemInfo@@
class DlgItemInfo : public AddonFrame {
public:
    DlgItemInfo(const std::string& name = "DlgItemInfo");
    virtual ~DlgItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemLink@@
class DlgItemLink : public AddonFrame {
public:
    DlgItemLink(const std::string& name = "DlgItemLink");
    virtual ~DlgItemLink();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemPrice@@
class DlgItemPrice : public AddonFrame {
public:
    DlgItemPrice(const std::string& name = "DlgItemPrice");
    virtual ~DlgItemPrice();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemPriceCount@@
class DlgItemPriceCount : public AddonFrame {
public:
    DlgItemPriceCount(const std::string& name = "DlgItemPriceCount");
    virtual ~DlgItemPriceCount();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemQuickMenu@@
class DlgItemQuickMenu : public AddonFrame {
public:
    DlgItemQuickMenu(const std::string& name = "DlgItemQuickMenu");
    virtual ~DlgItemQuickMenu();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemSkillEnchant@@
class DlgItemSkillEnchant : public AddonFrame {
public:
    DlgItemSkillEnchant(const std::string& name = "DlgItemSkillEnchant");
    virtual ~DlgItemSkillEnchant();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemSkillEnchantInfo@@
class DlgItemSkillEnchantInfo : public AddonFrame {
public:
    DlgItemSkillEnchantInfo(const std::string& name = "DlgItemSkillEnchantInfo");
    virtual ~DlgItemSkillEnchantInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemSkinChange@@
class DlgItemSkinChange : public AddonFrame {
public:
    DlgItemSkinChange(const std::string& name = "DlgItemSkinChange");
    virtual ~DlgItemSkinChange();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgItemUpgradeResult@@
class DlgItemUpgradeResult : public AddonFrame {
public:
    DlgItemUpgradeResult(const std::string& name = "DlgItemUpgradeResult");
    virtual ~DlgItemUpgradeResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLobbyOptionCreate@@
class DlgLobbyOptionCreate : public AddonFrame {
public:
    DlgLobbyOptionCreate(const std::string& name = "DlgLobbyOptionCreate");
    virtual ~DlgLobbyOptionCreate();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLobbyOptionLogin@@
class DlgLobbyOptionLogin : public AddonFrame {
public:
    DlgLobbyOptionLogin(const std::string& name = "DlgLobbyOptionLogin");
    virtual ~DlgLobbyOptionLogin();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLobbyOptionSelect@@
class DlgLobbyOptionSelect : public AddonFrame {
public:
    DlgLobbyOptionSelect(const std::string& name = "DlgLobbyOptionSelect");
    virtual ~DlgLobbyOptionSelect();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLogin@@
class DlgLogin : public AddonFrame {
public:
    DlgLogin(const std::string& name = "DlgLogin");
    virtual ~DlgLogin();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLoginEvent@@
class DlgLoginEvent : public AddonFrame {
public:
    DlgLoginEvent(const std::string& name = "DlgLoginEvent");
    virtual ~DlgLoginEvent();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLoginEventInARowDay@@
class DlgLoginEventInARowDay : public AddonFrame {
public:
    DlgLoginEventInARowDay(const std::string& name = "DlgLoginEventInARowDay");
    virtual ~DlgLoginEventInARowDay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLoginReplenish@@
class DlgLoginReplenish : public AddonFrame {
public:
    DlgLoginReplenish(const std::string& name = "DlgLoginReplenish");
    virtual ~DlgLoginReplenish();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLootOption@@
class DlgLootOption : public AddonFrame {
public:
    DlgLootOption(const std::string& name = "DlgLootOption");
    virtual ~DlgLootOption();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLootRoll@@
class DlgLootRoll : public AddonFrame {
public:
    DlgLootRoll(const std::string& name = "DlgLootRoll");
    virtual ~DlgLootRoll();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgLooting@@
class DlgLooting : public AddonFrame {
public:
    DlgLooting(const std::string& name = "DlgLooting");
    virtual ~DlgLooting();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMacro@@
class DlgMacro : public AddonFrame {
public:
    DlgMacro(const std::string& name = "DlgMacro");
    virtual ~DlgMacro();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMacroName@@
class DlgMacroName : public AddonFrame {
public:
    DlgMacroName(const std::string& name = "DlgMacroName");
    virtual ~DlgMacroName();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMailBox@@
class DlgMailBox : public AddonFrame {
public:
    DlgMailBox(const std::string& name = "DlgMailBox");
    virtual ~DlgMailBox();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMailBoxOther@@
class DlgMailBoxOther : public AddonFrame {
public:
    DlgMailBoxOther(const std::string& name = "DlgMailBoxOther");
    virtual ~DlgMailBoxOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMailLetter@@
class DlgMailLetter : public AddonFrame {
public:
    DlgMailLetter(const std::string& name = "DlgMailLetter");
    virtual ~DlgMailLetter();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMailLetterOther@@
class DlgMailLetterOther : public AddonFrame {
public:
    DlgMailLetterOther(const std::string& name = "DlgMailLetterOther");
    virtual ~DlgMailLetterOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMaking@@
class DlgMaking : public AddonFrame {
public:
    DlgMaking(const std::string& name = "DlgMaking");
    virtual ~DlgMaking();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMakingTool@@
class DlgMakingTool : public AddonFrame {
public:
    DlgMakingTool(const std::string& name = "DlgMakingTool");
    virtual ~DlgMakingTool();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMegaphone@@
class DlgMegaphone : public AddonFrame {
public:
    DlgMegaphone(const std::string& name = "DlgMegaphone");
    virtual ~DlgMegaphone();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMemo@@
class DlgMemo : public AddonFrame {
public:
    DlgMemo(const std::string& name = "DlgMemo");
    virtual ~DlgMemo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMercenary@@
class DlgMercenary : public AddonFrame {
public:
    DlgMercenary(const std::string& name = "DlgMercenary");
    virtual ~DlgMercenary();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMercenaryBuff@@
class DlgMercenaryBuff : public AddonFrame {
public:
    DlgMercenaryBuff(const std::string& name = "DlgMercenaryBuff");
    virtual ~DlgMercenaryBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMissionAchievement@@
class DlgMissionAchievement : public AddonFrame {
public:
    DlgMissionAchievement(const std::string& name = "DlgMissionAchievement");
    virtual ~DlgMissionAchievement();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMoros@@
class DlgMoros : public AddonFrame {
public:
    DlgMoros(const std::string& name = "DlgMoros");
    virtual ~DlgMoros();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMorosSkillProto@@
class DlgMorosSkillProto : public AddonFrame {
public:
    DlgMorosSkillProto(const std::string& name = "DlgMorosSkillProto");
    virtual ~DlgMorosSkillProto();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMoveState@@
class DlgMoveState : public AddonFrame {
public:
    DlgMoveState(const std::string& name = "DlgMoveState");
    virtual ~DlgMoveState();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgMsgDialogue@@
class DlgMsgDialogue : public AddonFrame {
public:
    DlgMsgDialogue(const std::string& name = "DlgMsgDialogue");
    virtual ~DlgMsgDialogue();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgNPCGuide@@
class DlgNPCGuide : public AddonFrame {
public:
    DlgNPCGuide(const std::string& name = "DlgNPCGuide");
    virtual ~DlgNPCGuide();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgNewMap@@
class DlgNewMap : public AddonFrame {
public:
    DlgNewMap(const std::string& name = "DlgNewMap");
    virtual ~DlgNewMap();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgNotConnectedPeriodReward@@
class DlgNotConnectedPeriodReward : public AddonFrame {
public:
    DlgNotConnectedPeriodReward(const std::string& name = "DlgNotConnectedPeriodReward");
    virtual ~DlgNotConnectedPeriodReward();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgOptionClear@@
class DlgOptionClear : public AddonFrame {
public:
    DlgOptionClear(const std::string& name = "DlgOptionClear");
    virtual ~DlgOptionClear();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPaperDoll@@
class DlgPaperDoll : public AddonFrame {
public:
    DlgPaperDoll(const std::string& name = "DlgPaperDoll");
    virtual ~DlgPaperDoll();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgParty@@
class DlgParty : public AddonFrame {
public:
    DlgParty(const std::string& name = "DlgParty");
    virtual ~DlgParty();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyBuff@@
class DlgPartyBuff : public AddonFrame {
public:
    DlgPartyBuff(const std::string& name = "DlgPartyBuff");
    virtual ~DlgPartyBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatch@@
class DlgPartyMatch : public AddonFrame {
public:
    DlgPartyMatch(const std::string& name = "DlgPartyMatch");
    virtual ~DlgPartyMatch();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatchInstanceOffer@@
class DlgPartyMatchInstanceOffer : public AddonFrame {
public:
    DlgPartyMatchInstanceOffer(const std::string& name = "DlgPartyMatchInstanceOffer");
    virtual ~DlgPartyMatchInstanceOffer();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatchInstanceStandBy@@
class DlgPartyMatchInstanceStandBy : public AddonFrame {
public:
    DlgPartyMatchInstanceStandBy(const std::string& name = "DlgPartyMatchInstanceStandBy");
    virtual ~DlgPartyMatchInstanceStandBy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatchNewInstanceOffer@@
class DlgPartyMatchNewInstanceOffer : public AddonFrame {
public:
    DlgPartyMatchNewInstanceOffer(const std::string& name = "DlgPartyMatchNewInstanceOffer");
    virtual ~DlgPartyMatchNewInstanceOffer();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatchOffer@@
class DlgPartyMatchOffer : public AddonFrame {
public:
    DlgPartyMatchOffer(const std::string& name = "DlgPartyMatchOffer");
    virtual ~DlgPartyMatchOffer();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatchSeek@@
class DlgPartyMatchSeek : public AddonFrame {
public:
    DlgPartyMatchSeek(const std::string& name = "DlgPartyMatchSeek");
    virtual ~DlgPartyMatchSeek();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartyMatchTournamentStandBy@@
class DlgPartyMatchTournamentStandBy : public AddonFrame {
public:
    DlgPartyMatchTournamentStandBy(const std::string& name = "DlgPartyMatchTournamentStandBy");
    virtual ~DlgPartyMatchTournamentStandBy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartySub@@
class DlgPartySub : public AddonFrame {
public:
    DlgPartySub(const std::string& name = "DlgPartySub");
    virtual ~DlgPartySub();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPartySubBuff@@
class DlgPartySubBuff : public AddonFrame {
public:
    DlgPartySubBuff(const std::string& name = "DlgPartySubBuff");
    virtual ~DlgPartySubBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPersonalChannel@@
class DlgPersonalChannel : public AddonFrame {
public:
    DlgPersonalChannel(const std::string& name = "DlgPersonalChannel");
    virtual ~DlgPersonalChannel();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPersonalChannelRoom@@
class DlgPersonalChannelRoom : public AddonFrame {
public:
    DlgPersonalChannelRoom(const std::string& name = "DlgPersonalChannelRoom");
    virtual ~DlgPersonalChannelRoom();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPersonalShop@@
class DlgPersonalShop : public AddonFrame {
public:
    DlgPersonalShop(const std::string& name = "DlgPersonalShop");
    virtual ~DlgPersonalShop();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPet@@
class DlgPet : public AddonFrame {
public:
    DlgPet(const std::string& name = "DlgPet");
    virtual ~DlgPet();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPetBuffStatus@@
class DlgPetBuffStatus : public AddonFrame {
public:
    DlgPetBuffStatus(const std::string& name = "DlgPetBuffStatus");
    virtual ~DlgPetBuffStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPetCommand@@
class DlgPetCommand : public AddonFrame {
public:
    DlgPetCommand(const std::string& name = "DlgPetCommand");
    virtual ~DlgPetCommand();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPetition@@
class DlgPetition : public AddonFrame {
public:
    DlgPetition(const std::string& name = "DlgPetition");
    virtual ~DlgPetition();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPetitionEval@@
class DlgPetitionEval : public AddonFrame {
public:
    DlgPetitionEval(const std::string& name = "DlgPetitionEval");
    virtual ~DlgPetitionEval();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPetitionStatus@@
class DlgPetitionStatus : public AddonFrame {
public:
    DlgPetitionStatus(const std::string& name = "DlgPetitionStatus");
    virtual ~DlgPetitionStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPickupUserDopItem@@
class DlgPickupUserDopItem : public AddonFrame {
public:
    DlgPickupUserDopItem(const std::string& name = "DlgPickupUserDopItem");
    virtual ~DlgPickupUserDopItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPlayerInfo@@
class DlgPlayerInfo : public AddonFrame {
public:
    DlgPlayerInfo(const std::string& name = "DlgPlayerInfo");
    virtual ~DlgPlayerInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPlayerInfoOther@@
class DlgPlayerInfoOther : public AddonFrame {
public:
    DlgPlayerInfoOther(const std::string& name = "DlgPlayerInfoOther");
    virtual ~DlgPlayerInfoOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPogusGameBoard@@
class DlgPogusGameBoard : public AddonFrame {
public:
    DlgPogusGameBoard(const std::string& name = "DlgPogusGameBoard");
    virtual ~DlgPogusGameBoard();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPremiumInventory@@
class DlgPremiumInventory : public AddonFrame {
public:
    DlgPremiumInventory(const std::string& name = "DlgPremiumInventory");
    virtual ~DlgPremiumInventory();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgProbResultList@@
class DlgProbResultList : public AddonFrame {
public:
    DlgProbResultList(const std::string& name = "DlgProbResultList");
    virtual ~DlgProbResultList();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgProbabilityGuidePage@@
class DlgProbabilityGuidePage : public AddonFrame {
public:
    DlgProbabilityGuidePage(const std::string& name = "DlgProbabilityGuidePage");
    virtual ~DlgProbabilityGuidePage();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgProbabilityItemInfo@@
class DlgProbabilityItemInfo : public AddonFrame {
public:
    DlgProbabilityItemInfo(const std::string& name = "DlgProbabilityItemInfo");
    virtual ~DlgProbabilityItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPromotion@@
class DlgPromotion : public AddonFrame {
public:
    DlgPromotion(const std::string& name = "DlgPromotion");
    virtual ~DlgPromotion();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgProphet@@
class DlgProphet : public AddonFrame {
public:
    DlgProphet(const std::string& name = "DlgProphet");
    virtual ~DlgProphet();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgPvpAbyssChange@@
class DlgPvpAbyssChange : public AddonFrame {
public:
    DlgPvpAbyssChange(const std::string& name = "DlgPvpAbyssChange");
    virtual ~DlgPvpAbyssChange();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgQuest@@
class DlgQuest : public AddonFrame {
public:
    DlgQuest(const std::string& name = "DlgQuest");
    virtual ~DlgQuest();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgQuestIndicator@@
class DlgQuestIndicator : public AddonFrame {
public:
    DlgQuestIndicator(const std::string& name = "DlgQuestIndicator");
    virtual ~DlgQuestIndicator();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgQuestOther@@
class DlgQuestOther : public AddonFrame {
public:
    DlgQuestOther(const std::string& name = "DlgQuestOther");
    virtual ~DlgQuestOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgQuitAlert@@
class DlgQuitAlert : public AddonFrame {
public:
    DlgQuitAlert(const std::string& name = "DlgQuitAlert");
    virtual ~DlgQuitAlert();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRadar@@
class DlgRadar : public AddonFrame {
public:
    DlgRadar(const std::string& name = "DlgRadar");
    virtual ~DlgRadar();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRadarMini@@
class DlgRadarMini : public AddonFrame {
public:
    DlgRadarMini(const std::string& name = "DlgRadarMini");
    virtual ~DlgRadarMini();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRandomLooting@@
class DlgRandomLooting : public AddonFrame {
public:
    DlgRandomLooting(const std::string& name = "DlgRandomLooting");
    virtual ~DlgRandomLooting();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRanking@@
class DlgRanking : public AddonFrame {
public:
    DlgRanking(const std::string& name = "DlgRanking");
    virtual ~DlgRanking();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRankingBadge@@
class DlgRankingBadge : public AddonFrame {
public:
    DlgRankingBadge(const std::string& name = "DlgRankingBadge");
    virtual ~DlgRankingBadge();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRankingInfo@@
class DlgRankingInfo : public AddonFrame {
public:
    DlgRankingInfo(const std::string& name = "DlgRankingInfo");
    virtual ~DlgRankingInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgReadItem@@
class DlgReadItem : public AddonFrame {
public:
    DlgReadItem(const std::string& name = "DlgReadItem");
    virtual ~DlgReadItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRecipeLink@@
class DlgRecipeLink : public AddonFrame {
public:
    DlgRecipeLink(const std::string& name = "DlgRecipeLink");
    virtual ~DlgRecipeLink();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRegisterItem@@
class DlgRegisterItem : public AddonFrame {
public:
    DlgRegisterItem(const std::string& name = "DlgRegisterItem");
    virtual ~DlgRegisterItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRemoveItemOption@@
class DlgRemoveItemOption : public AddonFrame {
public:
    DlgRemoveItemOption(const std::string& name = "DlgRemoveItemOption");
    virtual ~DlgRemoveItemOption();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgResurrect@@
class DlgResurrect : public AddonFrame {
public:
    DlgResurrect(const std::string& name = "DlgResurrect");
    virtual ~DlgResurrect();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgResurrectOther@@
class DlgResurrectOther : public AddonFrame {
public:
    DlgResurrectOther(const std::string& name = "DlgResurrectOther");
    virtual ~DlgResurrectOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRollingMegaphone@@
class DlgRollingMegaphone : public AddonFrame {
public:
    DlgRollingMegaphone(const std::string& name = "DlgRollingMegaphone");
    virtual ~DlgRollingMegaphone();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgRollingMegaphoneInput@@
class DlgRollingMegaphoneInput : public AddonFrame {
public:
    DlgRollingMegaphoneInput(const std::string& name = "DlgRollingMegaphoneInput");
    virtual ~DlgRollingMegaphoneInput();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgScene@@
class DlgScene : public AddonFrame {
public:
    DlgScene(const std::string& name = "DlgScene");
    virtual ~DlgScene();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSearchGuild@@
class DlgSearchGuild : public AddonFrame {
public:
    DlgSearchGuild(const std::string& name = "DlgSearchGuild");
    virtual ~DlgSearchGuild();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSecondPassword@@
class DlgSecondPassword : public AddonFrame {
public:
    DlgSecondPassword(const std::string& name = "DlgSecondPassword");
    virtual ~DlgSecondPassword();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSelectChar@@
class DlgSelectChar : public AddonFrame {
public:
    DlgSelectChar(const std::string& name = "DlgSelectChar");
    virtual ~DlgSelectChar();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSelectDisassemblyItem@@
class DlgSelectDisassemblyItem : public AddonFrame {
public:
    DlgSelectDisassemblyItem(const std::string& name = "DlgSelectDisassemblyItem");
    virtual ~DlgSelectDisassemblyItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSelectRetryDisassemblyItem@@
class DlgSelectRetryDisassemblyItem : public AddonFrame {
public:
    DlgSelectRetryDisassemblyItem(const std::string& name = "DlgSelectRetryDisassemblyItem");
    virtual ~DlgSelectRetryDisassemblyItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSelectServer@@
class DlgSelectServer : public AddonFrame {
public:
    DlgSelectServer(const std::string& name = "DlgSelectServer");
    virtual ~DlgSelectServer();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgShortCut@@
class DlgShortCut : public AddonFrame {
public:
    DlgShortCut(const std::string& name = "DlgShortCut");
    virtual ~DlgShortCut();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgShortCutAlt@@
class DlgShortCutAlt : public AddonFrame {
public:
    DlgShortCutAlt(const std::string& name = "DlgShortCutAlt");
    virtual ~DlgShortCutAlt();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgShortCutBase@@
class DlgShortCutBase : public AddonFrame {
public:
    DlgShortCutBase(const std::string& name = "DlgShortCutBase");
    virtual ~DlgShortCutBase();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgShortCutCtrl@@
class DlgShortCutCtrl : public AddonFrame {
public:
    DlgShortCutCtrl(const std::string& name = "DlgShortCutCtrl");
    virtual ~DlgShortCutCtrl();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgShortCutExtra@@
class DlgShortCutExtra : public AddonFrame {
public:
    DlgShortCutExtra(const std::string& name = "DlgShortCutExtra");
    virtual ~DlgShortCutExtra();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgShortCutSep@@
class DlgShortCutSep : public AddonFrame {
public:
    DlgShortCutSep(const std::string& name = "DlgShortCutSep");
    virtual ~DlgShortCutSep();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkill@@
class DlgSkill : public AddonFrame {
public:
    DlgSkill(const std::string& name = "DlgSkill");
    virtual ~DlgSkill();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillDelay@@
class DlgSkillDelay : public AddonFrame {
public:
    DlgSkillDelay(const std::string& name = "DlgSkillDelay");
    virtual ~DlgSkillDelay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillDic@@
class DlgSkillDic : public AddonFrame {
public:
    DlgSkillDic(const std::string& name = "DlgSkillDic");
    virtual ~DlgSkillDic();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillInfo@@
class DlgSkillInfo : public AddonFrame {
public:
    DlgSkillInfo(const std::string& name = "DlgSkillInfo");
    virtual ~DlgSkillInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillOther@@
class DlgSkillOther : public AddonFrame {
public:
    DlgSkillOther(const std::string& name = "DlgSkillOther");
    virtual ~DlgSkillOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillPenaltyStatus@@
class DlgSkillPenaltyStatus : public AddonFrame {
public:
    DlgSkillPenaltyStatus(const std::string& name = "DlgSkillPenaltyStatus");
    virtual ~DlgSkillPenaltyStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillSkin@@
class DlgSkillSkin : public AddonFrame {
public:
    DlgSkillSkin(const std::string& name = "DlgSkillSkin");
    virtual ~DlgSkillSkin();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSkillVideo@@
class DlgSkillVideo : public AddonFrame {
public:
    DlgSkillVideo(const std::string& name = "DlgSkillVideo");
    virtual ~DlgSkillVideo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpecialCraft@@
class DlgSpecialCraft : public AddonFrame {
public:
    DlgSpecialCraft(const std::string& name = "DlgSpecialCraft");
    virtual ~DlgSpecialCraft();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpecialCraftItemInfo@@
class DlgSpecialCraftItemInfo : public AddonFrame {
public:
    DlgSpecialCraftItemInfo(const std::string& name = "DlgSpecialCraftItemInfo");
    virtual ~DlgSpecialCraftItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpecialCraftMaterial@@
class DlgSpecialCraftMaterial : public AddonFrame {
public:
    DlgSpecialCraftMaterial(const std::string& name = "DlgSpecialCraftMaterial");
    virtual ~DlgSpecialCraftMaterial();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpecialCraftResult@@
class DlgSpecialCraftResult : public AddonFrame {
public:
    DlgSpecialCraftResult(const std::string& name = "DlgSpecialCraftResult");
    virtual ~DlgSpecialCraftResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpecialDyeItemInfo@@
class DlgSpecialDyeItemInfo : public AddonFrame {
public:
    DlgSpecialDyeItemInfo(const std::string& name = "DlgSpecialDyeItemInfo");
    virtual ~DlgSpecialDyeItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpectator@@
class DlgSpectator : public AddonFrame {
public:
    DlgSpectator(const std::string& name = "DlgSpectator");
    virtual ~DlgSpectator();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpectatorGroup@@
class DlgSpectatorGroup : public AddonFrame {
public:
    DlgSpectatorGroup(const std::string& name = "DlgSpectatorGroup");
    virtual ~DlgSpectatorGroup();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpectatorGroupBG@@
class DlgSpectatorGroupBG : public AddonFrame {
public:
    DlgSpectatorGroupBG(const std::string& name = "DlgSpectatorGroupBG");
    virtual ~DlgSpectatorGroupBG();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpectatorGroupBuff@@
class DlgSpectatorGroupBuff : public AddonFrame {
public:
    DlgSpectatorGroupBuff(const std::string& name = "DlgSpectatorGroupBuff");
    virtual ~DlgSpectatorGroupBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpectatorGroupSkill@@
class DlgSpectatorGroupSkill : public AddonFrame {
public:
    DlgSpectatorGroupSkill(const std::string& name = "DlgSpectatorGroupSkill");
    virtual ~DlgSpectatorGroupSkill();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpectatorWorld@@
class DlgSpectatorWorld : public AddonFrame {
public:
    DlgSpectatorWorld(const std::string& name = "DlgSpectatorWorld");
    virtual ~DlgSpectatorWorld();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpinelShopBuy@@
class DlgSpinelShopBuy : public AddonFrame {
public:
    DlgSpinelShopBuy(const std::string& name = "DlgSpinelShopBuy");
    virtual ~DlgSpinelShopBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpinelShopBuyAll@@
class DlgSpinelShopBuyAll : public AddonFrame {
public:
    DlgSpinelShopBuyAll(const std::string& name = "DlgSpinelShopBuyAll");
    virtual ~DlgSpinelShopBuyAll();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpinelShopHistory@@
class DlgSpinelShopHistory : public AddonFrame {
public:
    DlgSpinelShopHistory(const std::string& name = "DlgSpinelShopHistory");
    virtual ~DlgSpinelShopHistory();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSpinelShopRenewal@@
class DlgSpinelShopRenewal : public AddonFrame {
public:
    DlgSpinelShopRenewal(const std::string& name = "DlgSpinelShopRenewal");
    virtual ~DlgSpinelShopRenewal();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStatInfo@@
class DlgStatInfo : public AddonFrame {
public:
    DlgStatInfo(const std::string& name = "DlgStatInfo");
    virtual ~DlgStatInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStigmaPageChangeDelay@@
class DlgStigmaPageChangeDelay : public AddonFrame {
public:
    DlgStigmaPageChangeDelay(const std::string& name = "DlgStigmaPageChangeDelay");
    virtual ~DlgStigmaPageChangeDelay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookAppraise@@
class DlgStoryBookAppraise : public AddonFrame {
public:
    DlgStoryBookAppraise(const std::string& name = "DlgStoryBookAppraise");
    virtual ~DlgStoryBookAppraise();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookAppraiseItemInfo@@
class DlgStoryBookAppraiseItemInfo : public AddonFrame {
public:
    DlgStoryBookAppraiseItemInfo(const std::string& name = "DlgStoryBookAppraiseItemInfo");
    virtual ~DlgStoryBookAppraiseItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookAppraiseResult@@
class DlgStoryBookAppraiseResult : public AddonFrame {
public:
    DlgStoryBookAppraiseResult(const std::string& name = "DlgStoryBookAppraiseResult");
    virtual ~DlgStoryBookAppraiseResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookDisassemble@@
class DlgStoryBookDisassemble : public AddonFrame {
public:
    DlgStoryBookDisassemble(const std::string& name = "DlgStoryBookDisassemble");
    virtual ~DlgStoryBookDisassemble();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookDisassembleItemInfo@@
class DlgStoryBookDisassembleItemInfo : public AddonFrame {
public:
    DlgStoryBookDisassembleItemInfo(const std::string& name = "DlgStoryBookDisassembleItemInfo");
    virtual ~DlgStoryBookDisassembleItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookDisassembleResult@@
class DlgStoryBookDisassembleResult : public AddonFrame {
public:
    DlgStoryBookDisassembleResult(const std::string& name = "DlgStoryBookDisassembleResult");
    virtual ~DlgStoryBookDisassembleResult();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgStoryBookFullScreenImage@@
class DlgStoryBookFullScreenImage : public AddonFrame {
public:
    DlgStoryBookFullScreenImage(const std::string& name = "DlgStoryBookFullScreenImage");
    virtual ~DlgStoryBookFullScreenImage();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSummon@@
class DlgSummon : public AddonFrame {
public:
    DlgSummon(const std::string& name = "DlgSummon");
    virtual ~DlgSummon();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgSupportShortCut@@
class DlgSupportShortCut : public AddonFrame {
public:
    DlgSupportShortCut(const std::string& name = "DlgSupportShortCut");
    virtual ~DlgSupportShortCut();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTarget@@
class DlgTarget : public AddonFrame {
public:
    DlgTarget(const std::string& name = "DlgTarget");
    virtual ~DlgTarget();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTargetAssist@@
class DlgTargetAssist : public AddonFrame {
public:
    DlgTargetAssist(const std::string& name = "DlgTargetAssist");
    virtual ~DlgTargetAssist();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTargetAssistDelay@@
class DlgTargetAssistDelay : public AddonFrame {
public:
    DlgTargetAssistDelay(const std::string& name = "DlgTargetAssistDelay");
    virtual ~DlgTargetAssistDelay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTargetBuffStatus@@
class DlgTargetBuffStatus : public AddonFrame {
public:
    DlgTargetBuffStatus(const std::string& name = "DlgTargetBuffStatus");
    virtual ~DlgTargetBuffStatus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTargetDebuffExpand@@
class DlgTargetDebuffExpand : public AddonFrame {
public:
    DlgTargetDebuffExpand(const std::string& name = "DlgTargetDebuffExpand");
    virtual ~DlgTargetDebuffExpand();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTargetDelay@@
class DlgTargetDelay : public AddonFrame {
public:
    DlgTargetDelay(const std::string& name = "DlgTargetDelay");
    virtual ~DlgTargetDelay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTargetLockSkill@@
class DlgTargetLockSkill : public AddonFrame {
public:
    DlgTargetLockSkill(const std::string& name = "DlgTargetLockSkill");
    virtual ~DlgTargetLockSkill();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTevaOnlyTimerHUD@@
class DlgTevaOnlyTimerHUD : public AddonFrame {
public:
    DlgTevaOnlyTimerHUD(const std::string& name = "DlgTevaOnlyTimerHUD");
    virtual ~DlgTevaOnlyTimerHUD();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTimer@@
class DlgTimer : public AddonFrame {
public:
    DlgTimer(const std::string& name = "DlgTimer");
    virtual ~DlgTimer();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTitleCollection@@
class DlgTitleCollection : public AddonFrame {
public:
    DlgTitleCollection(const std::string& name = "DlgTitleCollection");
    virtual ~DlgTitleCollection();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTitleInfo@@
class DlgTitleInfo : public AddonFrame {
public:
    DlgTitleInfo(const std::string& name = "DlgTitleInfo");
    virtual ~DlgTitleInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipAbyss@@
class DlgTooltipAbyss : public AddonFrame {
public:
    DlgTooltipAbyss(const std::string& name = "DlgTooltipAbyss");
    virtual ~DlgTooltipAbyss();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipAccumulatedEnchant@@
class DlgTooltipAccumulatedEnchant : public AddonFrame {
public:
    DlgTooltipAccumulatedEnchant(const std::string& name = "DlgTooltipAccumulatedEnchant");
    virtual ~DlgTooltipAccumulatedEnchant();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipAllEquippedItemChargePoint@@
class DlgTooltipAllEquippedItemChargePoint : public AddonFrame {
public:
    DlgTooltipAllEquippedItemChargePoint(const std::string& name = "DlgTooltipAllEquippedItemChargePoint");
    virtual ~DlgTooltipAllEquippedItemChargePoint();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipAlterDebuff@@
class DlgTooltipAlterDebuff : public AddonFrame {
public:
    DlgTooltipAlterDebuff(const std::string& name = "DlgTooltipAlterDebuff");
    virtual ~DlgTooltipAlterDebuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipArcanium@@
class DlgTooltipArcanium : public AddonFrame {
public:
    DlgTooltipArcanium(const std::string& name = "DlgTooltipArcanium");
    virtual ~DlgTooltipArcanium();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipBoostEvent@@
class DlgTooltipBoostEvent : public AddonFrame {
public:
    DlgTooltipBoostEvent(const std::string& name = "DlgTooltipBoostEvent");
    virtual ~DlgTooltipBoostEvent();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipCharLink@@
class DlgTooltipCharLink : public AddonFrame {
public:
    DlgTooltipCharLink(const std::string& name = "DlgTooltipCharLink");
    virtual ~DlgTooltipCharLink();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipClassChangeConditions@@
class DlgTooltipClassChangeConditions : public AddonFrame {
public:
    DlgTooltipClassChangeConditions(const std::string& name = "DlgTooltipClassChangeConditions");
    virtual ~DlgTooltipClassChangeConditions();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipClassicGamePass@@
class DlgTooltipClassicGamePass : public AddonFrame {
public:
    DlgTooltipClassicGamePass(const std::string& name = "DlgTooltipClassicGamePass");
    virtual ~DlgTooltipClassicGamePass();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipCurMotion@@
class DlgTooltipCurMotion : public AddonFrame {
public:
    DlgTooltipCurMotion(const std::string& name = "DlgTooltipCurMotion");
    virtual ~DlgTooltipCurMotion();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipDirectPortal@@
class DlgTooltipDirectPortal : public AddonFrame {
public:
    DlgTooltipDirectPortal(const std::string& name = "DlgTooltipDirectPortal");
    virtual ~DlgTooltipDirectPortal();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipEquipmentChange@@
class DlgTooltipEquipmentChange : public AddonFrame {
public:
    DlgTooltipEquipmentChange(const std::string& name = "DlgTooltipEquipmentChange");
    virtual ~DlgTooltipEquipmentChange();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipEquipmentChangeInvalid@@
class DlgTooltipEquipmentChangeInvalid : public AddonFrame {
public:
    DlgTooltipEquipmentChangeInvalid(const std::string& name = "DlgTooltipEquipmentChangeInvalid");
    virtual ~DlgTooltipEquipmentChangeInvalid();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipExpBoost@@
class DlgTooltipExpBoost : public AddonFrame {
public:
    DlgTooltipExpBoost(const std::string& name = "DlgTooltipExpBoost");
    virtual ~DlgTooltipExpBoost();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipFatigue@@
class DlgTooltipFatigue : public AddonFrame {
public:
    DlgTooltipFatigue(const std::string& name = "DlgTooltipFatigue");
    virtual ~DlgTooltipFatigue();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipFlag@@
class DlgTooltipFlag : public AddonFrame {
public:
    DlgTooltipFlag(const std::string& name = "DlgTooltipFlag");
    virtual ~DlgTooltipFlag();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipFlying@@
class DlgTooltipFlying : public AddonFrame {
public:
    DlgTooltipFlying(const std::string& name = "DlgTooltipFlying");
    virtual ~DlgTooltipFlying();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipForceLink@@
class DlgTooltipForceLink : public AddonFrame {
public:
    DlgTooltipForceLink(const std::string& name = "DlgTooltipForceLink");
    virtual ~DlgTooltipForceLink();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipFuncNpc@@
class DlgTooltipFuncNpc : public AddonFrame {
public:
    DlgTooltipFuncNpc(const std::string& name = "DlgTooltipFuncNpc");
    virtual ~DlgTooltipFuncNpc();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipGetExp@@
class DlgTooltipGetExp : public AddonFrame {
public:
    DlgTooltipGetExp(const std::string& name = "DlgTooltipGetExp");
    virtual ~DlgTooltipGetExp();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipGuildBuff@@
class DlgTooltipGuildBuff : public AddonFrame {
public:
    DlgTooltipGuildBuff(const std::string& name = "DlgTooltipGuildBuff");
    virtual ~DlgTooltipGuildBuff();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipHotspot@@
class DlgTooltipHotspot : public AddonFrame {
public:
    DlgTooltipHotspot(const std::string& name = "DlgTooltipHotspot");
    virtual ~DlgTooltipHotspot();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipIndunSharedCooltime@@
class DlgTooltipIndunSharedCooltime : public AddonFrame {
public:
    DlgTooltipIndunSharedCooltime(const std::string& name = "DlgTooltipIndunSharedCooltime");
    virtual ~DlgTooltipIndunSharedCooltime();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipInstanceBonus@@
class DlgTooltipInstanceBonus : public AddonFrame {
public:
    DlgTooltipInstanceBonus(const std::string& name = "DlgTooltipInstanceBonus");
    virtual ~DlgTooltipInstanceBonus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipMacro@@
class DlgTooltipMacro : public AddonFrame {
public:
    DlgTooltipMacro(const std::string& name = "DlgTooltipMacro");
    virtual ~DlgTooltipMacro();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipMakeUpBonus@@
class DlgTooltipMakeUpBonus : public AddonFrame {
public:
    DlgTooltipMakeUpBonus(const std::string& name = "DlgTooltipMakeUpBonus");
    virtual ~DlgTooltipMakeUpBonus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipMissionAchv@@
class DlgTooltipMissionAchv : public AddonFrame {
public:
    DlgTooltipMissionAchv(const std::string& name = "DlgTooltipMissionAchv");
    virtual ~DlgTooltipMissionAchv();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipObj@@
class DlgTooltipObj : public AddonFrame {
public:
    DlgTooltipObj(const std::string& name = "DlgTooltipObj");
    virtual ~DlgTooltipObj();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipParty@@
class DlgTooltipParty : public AddonFrame {
public:
    DlgTooltipParty(const std::string& name = "DlgTooltipParty");
    virtual ~DlgTooltipParty();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipPartyLink@@
class DlgTooltipPartyLink : public AddonFrame {
public:
    DlgTooltipPartyLink(const std::string& name = "DlgTooltipPartyLink");
    virtual ~DlgTooltipPartyLink();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipPcExpReward@@
class DlgTooltipPcExpReward : public AddonFrame {
public:
    DlgTooltipPcExpReward(const std::string& name = "DlgTooltipPcExpReward");
    virtual ~DlgTooltipPcExpReward();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipPet@@
class DlgTooltipPet : public AddonFrame {
public:
    DlgTooltipPet(const std::string& name = "DlgTooltipPet");
    virtual ~DlgTooltipPet();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRaceBonus@@
class DlgTooltipRaceBonus : public AddonFrame {
public:
    DlgTooltipRaceBonus(const std::string& name = "DlgTooltipRaceBonus");
    virtual ~DlgTooltipRaceBonus();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRaceBonusFromAbyssAType@@
class DlgTooltipRaceBonusFromAbyssAType : public AddonFrame {
public:
    DlgTooltipRaceBonusFromAbyssAType(const std::string& name = "DlgTooltipRaceBonusFromAbyssAType");
    virtual ~DlgTooltipRaceBonusFromAbyssAType();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRaceChangeConditions@@
class DlgTooltipRaceChangeConditions : public AddonFrame {
public:
    DlgTooltipRaceChangeConditions(const std::string& name = "DlgTooltipRaceChangeConditions");
    virtual ~DlgTooltipRaceChangeConditions();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRankingBadgeList@@
class DlgTooltipRankingBadgeList : public AddonFrame {
public:
    DlgTooltipRankingBadgeList(const std::string& name = "DlgTooltipRankingBadgeList");
    virtual ~DlgTooltipRankingBadgeList();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRankingReward@@
class DlgTooltipRankingReward : public AddonFrame {
public:
    DlgTooltipRankingReward(const std::string& name = "DlgTooltipRankingReward");
    virtual ~DlgTooltipRankingReward();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRecipe@@
class DlgTooltipRecipe : public AddonFrame {
public:
    DlgTooltipRecipe(const std::string& name = "DlgTooltipRecipe");
    virtual ~DlgTooltipRecipe();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipRvR@@
class DlgTooltipRvR : public AddonFrame {
public:
    DlgTooltipRvR(const std::string& name = "DlgTooltipRvR");
    virtual ~DlgTooltipRvR();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipSerialKiller@@
class DlgTooltipSerialKiller : public AddonFrame {
public:
    DlgTooltipSerialKiller(const std::string& name = "DlgTooltipSerialKiller");
    virtual ~DlgTooltipSerialKiller();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipSpinelShopPackage@@
class DlgTooltipSpinelShopPackage : public AddonFrame {
public:
    DlgTooltipSpinelShopPackage(const std::string& name = "DlgTooltipSpinelShopPackage");
    virtual ~DlgTooltipSpinelShopPackage();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipToyPet@@
class DlgTooltipToyPet : public AddonFrame {
public:
    DlgTooltipToyPet(const std::string& name = "DlgTooltipToyPet");
    virtual ~DlgTooltipToyPet();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipToyPetFeeling@@
class DlgTooltipToyPetFeeling : public AddonFrame {
public:
    DlgTooltipToyPetFeeling(const std::string& name = "DlgTooltipToyPetFeeling");
    virtual ~DlgTooltipToyPetFeeling();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipVitalPoint@@
class DlgTooltipVitalPoint : public AddonFrame {
public:
    DlgTooltipVitalPoint(const std::string& name = "DlgTooltipVitalPoint");
    virtual ~DlgTooltipVitalPoint();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipWebItemDesc@@
class DlgTooltipWebItemDesc : public AddonFrame {
public:
    DlgTooltipWebItemDesc(const std::string& name = "DlgTooltipWebItemDesc");
    virtual ~DlgTooltipWebItemDesc();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipWindBoost@@
class DlgTooltipWindBoost : public AddonFrame {
public:
    DlgTooltipWindBoost(const std::string& name = "DlgTooltipWindBoost");
    virtual ~DlgTooltipWindBoost();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTooltipZoneMapQuestNpc@@
class DlgTooltipZoneMapQuestNpc : public AddonFrame {
public:
    DlgTooltipZoneMapQuestNpc(const std::string& name = "DlgTooltipZoneMapQuestNpc");
    virtual ~DlgTooltipZoneMapQuestNpc();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetAbandon@@
class DlgToyPetAbandon : public AddonFrame {
public:
    DlgToyPetAbandon(const std::string& name = "DlgToyPetAbandon");
    virtual ~DlgToyPetAbandon();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetAbandonConfirm@@
class DlgToyPetAbandonConfirm : public AddonFrame {
public:
    DlgToyPetAbandonConfirm(const std::string& name = "DlgToyPetAbandonConfirm");
    virtual ~DlgToyPetAbandonConfirm();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetFeedDelay@@
class DlgToyPetFeedDelay : public AddonFrame {
public:
    DlgToyPetFeedDelay(const std::string& name = "DlgToyPetFeedDelay");
    virtual ~DlgToyPetFeedDelay();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetInfo@@
class DlgToyPetInfo : public AddonFrame {
public:
    DlgToyPetInfo(const std::string& name = "DlgToyPetInfo");
    virtual ~DlgToyPetInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetItemInfo@@
class DlgToyPetItemInfo : public AddonFrame {
public:
    DlgToyPetItemInfo(const std::string& name = "DlgToyPetItemInfo");
    virtual ~DlgToyPetItemInfo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetList@@
class DlgToyPetList : public AddonFrame {
public:
    DlgToyPetList(const std::string& name = "DlgToyPetList");
    virtual ~DlgToyPetList();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetPaperDoll@@
class DlgToyPetPaperDoll : public AddonFrame {
public:
    DlgToyPetPaperDoll(const std::string& name = "DlgToyPetPaperDoll");
    virtual ~DlgToyPetPaperDoll();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetTame@@
class DlgToyPetTame : public AddonFrame {
public:
    DlgToyPetTame(const std::string& name = "DlgToyPetTame");
    virtual ~DlgToyPetTame();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgToyPetWarehouse@@
class DlgToyPetWarehouse : public AddonFrame {
public:
    DlgToyPetWarehouse(const std::string& name = "DlgToyPetWarehouse");
    virtual ~DlgToyPetWarehouse();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTrade@@
class DlgTrade : public AddonFrame {
public:
    DlgTrade(const std::string& name = "DlgTrade");
    virtual ~DlgTrade();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTransparentMap@@
class DlgTransparentMap : public AddonFrame {
public:
    DlgTransparentMap(const std::string& name = "DlgTransparentMap");
    virtual ~DlgTransparentMap();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTutorial@@
class DlgTutorial : public AddonFrame {
public:
    DlgTutorial(const std::string& name = "DlgTutorial");
    virtual ~DlgTutorial();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTutorialHighlight@@
class DlgTutorialHighlight : public AddonFrame {
public:
    DlgTutorialHighlight(const std::string& name = "DlgTutorialHighlight");
    virtual ~DlgTutorialHighlight();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgTutorialKeyGuide@@
class DlgTutorialKeyGuide : public AddonFrame {
public:
    DlgTutorialKeyGuide(const std::string& name = "DlgTutorialKeyGuide");
    virtual ~DlgTutorialKeyGuide();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgUnion@@
class DlgUnion : public AddonFrame {
public:
    DlgUnion(const std::string& name = "DlgUnion");
    virtual ~DlgUnion();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgUserAgreement@@
class DlgUserAgreement : public AddonFrame {
public:
    DlgUserAgreement(const std::string& name = "DlgUserAgreement");
    virtual ~DlgUserAgreement();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorBuyEach@@
class DlgVendorBuyEach : public AddonFrame {
public:
    DlgVendorBuyEach(const std::string& name = "DlgVendorBuyEach");
    virtual ~DlgVendorBuyEach();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorSellStack@@
class DlgVendorSellStack : public AddonFrame {
public:
    DlgVendorSellStack(const std::string& name = "DlgVendorSellStack");
    virtual ~DlgVendorSellStack();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorSingleBuy@@
class DlgVendorSingleBuy : public AddonFrame {
public:
    DlgVendorSingleBuy(const std::string& name = "DlgVendorSingleBuy");
    virtual ~DlgVendorSingleBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorWorldItemSingleBuy@@
class DlgVendorWorldItemSingleBuy : public AddonFrame {
public:
    DlgVendorWorldItemSingleBuy(const std::string& name = "DlgVendorWorldItemSingleBuy");
    virtual ~DlgVendorWorldItemSingleBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorWorldItemStackBuy@@
class DlgVendorWorldItemStackBuy : public AddonFrame {
public:
    DlgVendorWorldItemStackBuy(const std::string& name = "DlgVendorWorldItemStackBuy");
    virtual ~DlgVendorWorldItemStackBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorWorldQinaBuy@@
class DlgVendorWorldQinaBuy : public AddonFrame {
public:
    DlgVendorWorldQinaBuy(const std::string& name = "DlgVendorWorldQinaBuy");
    virtual ~DlgVendorWorldQinaBuy();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorWorldSaleConfirm@@
class DlgVendorWorldSaleConfirm : public AddonFrame {
public:
    DlgVendorWorldSaleConfirm(const std::string& name = "DlgVendorWorldSaleConfirm");
    virtual ~DlgVendorWorldSaleConfirm();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorWorldSellItem@@
class DlgVendorWorldSellItem : public AddonFrame {
public:
    DlgVendorWorldSellItem(const std::string& name = "DlgVendorWorldSellItem");
    virtual ~DlgVendorWorldSellItem();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVendorWorldSellQina@@
class DlgVendorWorldSellQina : public AddonFrame {
public:
    DlgVendorWorldSellQina(const std::string& name = "DlgVendorWorldSellQina");
    virtual ~DlgVendorWorldSellQina();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgVideo@@
class DlgVideo : public AddonFrame {
public:
    DlgVideo(const std::string& name = "DlgVideo");
    virtual ~DlgVideo();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWait@@
class DlgWait : public AddonFrame {
public:
    DlgWait(const std::string& name = "DlgWait");
    virtual ~DlgWait();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWardrobeConfirm@@
class DlgWardrobeConfirm : public AddonFrame {
public:
    DlgWardrobeConfirm(const std::string& name = "DlgWardrobeConfirm");
    virtual ~DlgWardrobeConfirm();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWarehouse@@
class DlgWarehouse : public AddonFrame {
public:
    DlgWarehouse(const std::string& name = "DlgWarehouse");
    virtual ~DlgWarehouse();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWatch@@
class DlgWatch : public AddonFrame {
public:
    DlgWatch(const std::string& name = "DlgWatch");
    virtual ~DlgWatch();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWebBoard@@
class DlgWebBoard : public AddonFrame {
public:
    DlgWebBoard(const std::string& name = "DlgWebBoard");
    virtual ~DlgWebBoard();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWebPetition@@
class DlgWebPetition : public AddonFrame {
public:
    DlgWebPetition(const std::string& name = "DlgWebPetition");
    virtual ~DlgWebPetition();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWebService@@
class DlgWebService : public AddonFrame {
public:
    DlgWebService(const std::string& name = "DlgWebService");
    virtual ~DlgWebService();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWho@@
class DlgWho : public AddonFrame {
public:
    DlgWho(const std::string& name = "DlgWho");
    virtual ~DlgWho();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWhoOther@@
class DlgWhoOther : public AddonFrame {
public:
    DlgWhoOther(const std::string& name = "DlgWhoOther");
    virtual ~DlgWhoOther();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWindShortCut@@
class DlgWindShortCut : public AddonFrame {
public:
    DlgWindShortCut(const std::string& name = "DlgWindShortCut");
    virtual ~DlgWindShortCut();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWorldInfluence@@
class DlgWorldInfluence : public AddonFrame {
public:
    DlgWorldInfluence(const std::string& name = "DlgWorldInfluence");
    virtual ~DlgWorldInfluence();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgWorldVendor@@
class DlgWorldVendor : public AddonFrame {
public:
    DlgWorldVendor(const std::string& name = "DlgWorldVendor");
    virtual ~DlgWorldVendor();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgZoneContentGauge@@
class DlgZoneContentGauge : public AddonFrame {
public:
    DlgZoneContentGauge(const std::string& name = "DlgZoneContentGauge");
    virtual ~DlgZoneContentGauge();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgZoneContentHp@@
class DlgZoneContentHp : public AddonFrame {
public:
    DlgZoneContentHp(const std::string& name = "DlgZoneContentHp");
    virtual ~DlgZoneContentHp();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgZoneContentHpSub@@
class DlgZoneContentHpSub : public AddonFrame {
public:
    DlgZoneContentHpSub(const std::string& name = "DlgZoneContentHpSub");
    virtual ~DlgZoneContentHpSub();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVDlgZoneContentTimer@@
class DlgZoneContentTimer : public AddonFrame {
public:
    DlgZoneContentTimer(const std::string& name = "DlgZoneContentTimer");
    virtual ~DlgZoneContentTimer();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVUIDialog@@
class UIDialog : public AddonFrame {
public:
    UIDialog(const std::string& name = "UIDialog");
    virtual ~UIDialog();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

// RTTI .?AVUIWebDialog@@
class UIWebDialog : public AddonFrame {
public:
    UIWebDialog(const std::string& name = "UIWebDialog");
    virtual ~UIWebDialog();
    virtual void Show(bool bShow) override;
    virtual void Update() override;
};

void RegisterAllGameDialogsExt();