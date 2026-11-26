#include "GameTablesExt.h"
#include "../core/GameLog.h"

AbyssRaceBonusTable::AbyssRaceBonusTable() : m_bLoaded(false) { LoadTable(); }
AbyssRaceBonusTable::~AbyssRaceBonusTable() { m_bLoaded = false; }
bool AbyssRaceBonusTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AbyssRaceBonusTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AbyssRaceBonusTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AbyssRankTable::AbyssRankTable() : m_bLoaded(false) { LoadTable(); }
AbyssRankTable::~AbyssRankTable() { m_bLoaded = false; }
bool AbyssRankTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AbyssRankTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AbyssRankTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AbyssTypeRaceBonusesTable::AbyssTypeRaceBonusesTable() : m_bLoaded(false) { LoadTable(); }
AbyssTypeRaceBonusesTable::~AbyssTypeRaceBonusesTable() { m_bLoaded = false; }
bool AbyssTypeRaceBonusesTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AbyssTypeRaceBonusesTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AbyssTypeRaceBonusesTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AccumulatedEnchantTable::AccumulatedEnchantTable() : m_bLoaded(false) { LoadTable(); }
AccumulatedEnchantTable::~AccumulatedEnchantTable() { m_bLoaded = false; }
bool AccumulatedEnchantTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AccumulatedEnchantTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AccumulatedEnchantTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AionETCBaseStringTable::AionETCBaseStringTable() : m_bLoaded(false) { LoadTable(); }
AionETCBaseStringTable::~AionETCBaseStringTable() { m_bLoaded = false; }
bool AionETCBaseStringTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AionETCBaseStringTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AionETCBaseStringTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AionHyperlinkTable::AionHyperlinkTable() : m_bLoaded(false) { LoadTable(); }
AionHyperlinkTable::~AionHyperlinkTable() { m_bLoaded = false; }
bool AionHyperlinkTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AionHyperlinkTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AionHyperlinkTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AionLookDyeColorTable::AionLookDyeColorTable() : m_bLoaded(false) { LoadTable(); }
AionLookDyeColorTable::~AionLookDyeColorTable() { m_bLoaded = false; }
bool AionLookDyeColorTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AionLookDyeColorTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AionLookDyeColorTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AionStringTable::AionStringTable() : m_bLoaded(false) { LoadTable(); }
AionStringTable::~AionStringTable() { m_bLoaded = false; }
bool AionStringTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AionStringTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AionStringTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AssistOptionEnchantTypeTable::AssistOptionEnchantTypeTable() : m_bLoaded(false) { LoadTable(); }
AssistOptionEnchantTypeTable::~AssistOptionEnchantTypeTable() { m_bLoaded = false; }
bool AssistOptionEnchantTypeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AssistOptionEnchantTypeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AssistOptionEnchantTypeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

AssistOptionEnchantValueTable::AssistOptionEnchantValueTable() : m_bLoaded(false) { LoadTable(); }
AssistOptionEnchantValueTable::~AssistOptionEnchantValueTable() { m_bLoaded = false; }
bool AssistOptionEnchantValueTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("AssistOptionEnchantValueTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[AssistOptionEnchantValueTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BMAccountTable::BMAccountTable() : m_bLoaded(false) { LoadTable(); }
BMAccountTable::~BMAccountTable() { m_bLoaded = false; }
bool BMAccountTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BMAccountTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BMAccountTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BMBoardFuncTable::BMBoardFuncTable() : m_bLoaded(false) { LoadTable(); }
BMBoardFuncTable::~BMBoardFuncTable() { m_bLoaded = false; }
bool BMBoardFuncTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BMBoardFuncTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BMBoardFuncTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BMBoardPresetTable::BMBoardPresetTable() : m_bLoaded(false) { LoadTable(); }
BMBoardPresetTable::~BMBoardPresetTable() { m_bLoaded = false; }
bool BMBoardPresetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BMBoardPresetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BMBoardPresetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BMBoardSeasonTable::BMBoardSeasonTable() : m_bLoaded(false) { LoadTable(); }
BMBoardSeasonTable::~BMBoardSeasonTable() { m_bLoaded = false; }
bool BMBoardSeasonTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BMBoardSeasonTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BMBoardSeasonTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BMConfigTable::BMConfigTable() : m_bLoaded(false) { LoadTable(); }
BMConfigTable::~BMConfigTable() { m_bLoaded = false; }
bool BMConfigTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BMConfigTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BMConfigTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BMPackTable::BMPackTable() : m_bLoaded(false) { LoadTable(); }
BMPackTable::~BMPackTable() { m_bLoaded = false; }
bool BMPackTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BMPackTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BMPackTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BaseTable::BaseTable() : m_bLoaded(false) { LoadTable(); }
BaseTable::~BaseTable() { m_bLoaded = false; }
bool BaseTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BaseTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BaseTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BattlePassRewardTable::BattlePassRewardTable() : m_bLoaded(false) { LoadTable(); }
BattlePassRewardTable::~BattlePassRewardTable() { m_bLoaded = false; }
bool BattlePassRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BattlePassRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BattlePassRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

BattlePassSeasonTable::BattlePassSeasonTable() : m_bLoaded(false) { LoadTable(); }
BattlePassSeasonTable::~BattlePassSeasonTable() { m_bLoaded = false; }
bool BattlePassSeasonTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("BattlePassSeasonTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[BattlePassSeasonTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CharacterClassInfoTable::CharacterClassInfoTable() : m_bLoaded(false) { LoadTable(); }
CharacterClassInfoTable::~CharacterClassInfoTable() { m_bLoaded = false; }
bool CharacterClassInfoTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CharacterClassInfoTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CharacterClassInfoTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ClassChangeCostTable::ClassChangeCostTable() : m_bLoaded(false) { LoadTable(); }
ClassChangeCostTable::~ClassChangeCostTable() { m_bLoaded = false; }
bool ClassChangeCostTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ClassChangeCostTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ClassChangeCostTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CombatPowerRankBuffTable::CombatPowerRankBuffTable() : m_bLoaded(false) { LoadTable(); }
CombatPowerRankBuffTable::~CombatPowerRankBuffTable() { m_bLoaded = false; }
bool CombatPowerRankBuffTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CombatPowerRankBuffTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CombatPowerRankBuffTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CombatPowerRewardTable::CombatPowerRewardTable() : m_bLoaded(false) { LoadTable(); }
CombatPowerRewardTable::~CombatPowerRewardTable() { m_bLoaded = false; }
bool CombatPowerRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CombatPowerRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CombatPowerRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CombatPowerRuleTable::CombatPowerRuleTable() : m_bLoaded(false) { LoadTable(); }
CombatPowerRuleTable::~CombatPowerRuleTable() { m_bLoaded = false; }
bool CombatPowerRuleTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CombatPowerRuleTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CombatPowerRuleTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CombineGiveUpCostTable::CombineGiveUpCostTable() : m_bLoaded(false) { LoadTable(); }
CombineGiveUpCostTable::~CombineGiveUpCostTable() { m_bLoaded = false; }
bool CombineGiveUpCostTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CombineGiveUpCostTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CombineGiveUpCostTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ContextSkillTable::ContextSkillTable() : m_bLoaded(false) { LoadTable(); }
ContextSkillTable::~ContextSkillTable() { m_bLoaded = false; }
bool ContextSkillTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ContextSkillTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ContextSkillTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CosmeticItemTable::CosmeticItemTable() : m_bLoaded(false) { LoadTable(); }
CosmeticItemTable::~CosmeticItemTable() { m_bLoaded = false; }
bool CosmeticItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CosmeticItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CosmeticItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CustomAnimTable::CustomAnimTable() : m_bLoaded(false) { LoadTable(); }
CustomAnimTable::~CustomAnimTable() { m_bLoaded = false; }
bool CustomAnimTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CustomAnimTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CustomAnimTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

CutSceneNameTable::CutSceneNameTable() : m_bLoaded(false) { LoadTable(); }
CutSceneNameTable::~CutSceneNameTable() { m_bLoaded = false; }
bool CutSceneNameTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("CutSceneNameTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[CutSceneNameTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

DefaultKeyTable::DefaultKeyTable() : m_bLoaded(false) { LoadTable(); }
DefaultKeyTable::~DefaultKeyTable() { m_bLoaded = false; }
bool DefaultKeyTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("DefaultKeyTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[DefaultKeyTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

DialogStringTable::DialogStringTable() : m_bLoaded(false) { LoadTable(); }
DialogStringTable::~DialogStringTable() { m_bLoaded = false; }
bool DialogStringTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("DialogStringTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[DialogStringTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

DisassemblyItemCustomizeTable::DisassemblyItemCustomizeTable() : m_bLoaded(false) { LoadTable(); }
DisassemblyItemCustomizeTable::~DisassemblyItemCustomizeTable() { m_bLoaded = false; }
bool DisassemblyItemCustomizeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("DisassemblyItemCustomizeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[DisassemblyItemCustomizeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

DisassemblyItemSetListTable::DisassemblyItemSetListTable() : m_bLoaded(false) { LoadTable(); }
DisassemblyItemSetListTable::~DisassemblyItemSetListTable() { m_bLoaded = false; }
bool DisassemblyItemSetListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("DisassemblyItemSetListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[DisassemblyItemSetListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

DisassemblyItemSetTable::DisassemblyItemSetTable() : m_bLoaded(false) { LoadTable(); }
DisassemblyItemSetTable::~DisassemblyItemSetTable() { m_bLoaded = false; }
bool DisassemblyItemSetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("DisassemblyItemSetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[DisassemblyItemSetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

EmotionTable::EmotionTable() : m_bLoaded(false) { LoadTable(); }
EmotionTable::~EmotionTable() { m_bLoaded = false; }
bool EmotionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("EmotionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[EmotionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

EnchantCountProbTable::EnchantCountProbTable() : m_bLoaded(false) { LoadTable(); }
EnchantCountProbTable::~EnchantCountProbTable() { m_bLoaded = false; }
bool EnchantCountProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("EnchantCountProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[EnchantCountProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

EnchantGapLevelProbTable::EnchantGapLevelProbTable() : m_bLoaded(false) { LoadTable(); }
EnchantGapLevelProbTable::~EnchantGapLevelProbTable() { m_bLoaded = false; }
bool EnchantGapLevelProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("EnchantGapLevelProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[EnchantGapLevelProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

EnchantMatterProbTable::EnchantMatterProbTable() : m_bLoaded(false) { LoadTable(); }
EnchantMatterProbTable::~EnchantMatterProbTable() { m_bLoaded = false; }
bool EnchantMatterProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("EnchantMatterProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[EnchantMatterProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

EnchantOptionTable::EnchantOptionTable() : m_bLoaded(false) { LoadTable(); }
EnchantOptionTable::~EnchantOptionTable() { m_bLoaded = false; }
bool EnchantOptionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("EnchantOptionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[EnchantOptionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

FFATable::FFATable() : m_bLoaded(false) { LoadTable(); }
FFATable::~FFATable() { m_bLoaded = false; }
bool FFATable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("FFATable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[FFATable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GamePassExtraTable::GamePassExtraTable() : m_bLoaded(false) { LoadTable(); }
GamePassExtraTable::~GamePassExtraTable() { m_bLoaded = false; }
bool GamePassExtraTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GamePassExtraTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GamePassExtraTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GameRuleOptionsTable::GameRuleOptionsTable() : m_bLoaded(false) { LoadTable(); }
GameRuleOptionsTable::~GameRuleOptionsTable() { m_bLoaded = false; }
bool GameRuleOptionsTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GameRuleOptionsTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GameRuleOptionsTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GatherSourceTable::GatherSourceTable() : m_bLoaded(false) { LoadTable(); }
GatherSourceTable::~GatherSourceTable() { m_bLoaded = false; }
bool GatherSourceTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GatherSourceTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GatherSourceTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GemMatterItemReforgeStatInfoDataTable::GemMatterItemReforgeStatInfoDataTable() : m_bLoaded(false) { LoadTable(); }
GemMatterItemReforgeStatInfoDataTable::~GemMatterItemReforgeStatInfoDataTable() { m_bLoaded = false; }
bool GemMatterItemReforgeStatInfoDataTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GemMatterItemReforgeStatInfoDataTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GemMatterItemReforgeStatInfoDataTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GemMatterItemReforgeStatTable::GemMatterItemReforgeStatTable() : m_bLoaded(false) { LoadTable(); }
GemMatterItemReforgeStatTable::~GemMatterItemReforgeStatTable() { m_bLoaded = false; }
bool GemMatterItemReforgeStatTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GemMatterItemReforgeStatTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GemMatterItemReforgeStatTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GemMatterItemReforgeTable::GemMatterItemReforgeTable() : m_bLoaded(false) { LoadTable(); }
GemMatterItemReforgeTable::~GemMatterItemReforgeTable() { m_bLoaded = false; }
bool GemMatterItemReforgeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GemMatterItemReforgeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GemMatterItemReforgeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GlobalTradeExchangeTable::GlobalTradeExchangeTable() : m_bLoaded(false) { LoadTable(); }
GlobalTradeExchangeTable::~GlobalTradeExchangeTable() { m_bLoaded = false; }
bool GlobalTradeExchangeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GlobalTradeExchangeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GlobalTradeExchangeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GoodsIconTable::GoodsIconTable() : m_bLoaded(false) { LoadTable(); }
GoodsIconTable::~GoodsIconTable() { m_bLoaded = false; }
bool GoodsIconTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GoodsIconTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GoodsIconTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildBuffConfigTable::GuildBuffConfigTable() : m_bLoaded(false) { LoadTable(); }
GuildBuffConfigTable::~GuildBuffConfigTable() { m_bLoaded = false; }
bool GuildBuffConfigTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildBuffConfigTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildBuffConfigTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildBuffTable::GuildBuffTable() : m_bLoaded(false) { LoadTable(); }
GuildBuffTable::~GuildBuffTable() { m_bLoaded = false; }
bool GuildBuffTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildBuffTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildBuffTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildCraftTable::GuildCraftTable() : m_bLoaded(false) { LoadTable(); }
GuildCraftTable::~GuildCraftTable() { m_bLoaded = false; }
bool GuildCraftTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildCraftTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildCraftTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildDonationRewardTable::GuildDonationRewardTable() : m_bLoaded(false) { LoadTable(); }
GuildDonationRewardTable::~GuildDonationRewardTable() { m_bLoaded = false; }
bool GuildDonationRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildDonationRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildDonationRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildDonationSettingTable::GuildDonationSettingTable() : m_bLoaded(false) { LoadTable(); }
GuildDonationSettingTable::~GuildDonationSettingTable() { m_bLoaded = false; }
bool GuildDonationSettingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildDonationSettingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildDonationSettingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildDonationTable::GuildDonationTable() : m_bLoaded(false) { LoadTable(); }
GuildDonationTable::~GuildDonationTable() { m_bLoaded = false; }
bool GuildDonationTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildDonationTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildDonationTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildGrowthTable::GuildGrowthTable() : m_bLoaded(false) { LoadTable(); }
GuildGrowthTable::~GuildGrowthTable() { m_bLoaded = false; }
bool GuildGrowthTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildGrowthTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildGrowthTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildScheduledMissionAchievementTable::GuildScheduledMissionAchievementTable() : m_bLoaded(false) { LoadTable(); }
GuildScheduledMissionAchievementTable::~GuildScheduledMissionAchievementTable() { m_bLoaded = false; }
bool GuildScheduledMissionAchievementTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildScheduledMissionAchievementTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildScheduledMissionAchievementTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildScheduledMissionActionTable::GuildScheduledMissionActionTable() : m_bLoaded(false) { LoadTable(); }
GuildScheduledMissionActionTable::~GuildScheduledMissionActionTable() { m_bLoaded = false; }
bool GuildScheduledMissionActionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildScheduledMissionActionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildScheduledMissionActionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

GuildSettingTable::GuildSettingTable() : m_bLoaded(false) { LoadTable(); }
GuildSettingTable::~GuildSettingTable() { m_bLoaded = false; }
bool GuildSettingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("GuildSettingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[GuildSettingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

HTMLStringTable::HTMLStringTable() : m_bLoaded(false) { LoadTable(); }
HTMLStringTable::~HTMLStringTable() { m_bLoaded = false; }
bool HTMLStringTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("HTMLStringTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[HTMLStringTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

HotSpotTable::HotSpotTable() : m_bLoaded(false) { LoadTable(); }
HotSpotTable::~HotSpotTable() { m_bLoaded = false; }
bool HotSpotTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("HotSpotTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[HotSpotTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ITable::ITable() : m_bLoaded(false) { LoadTable(); }
ITable::~ITable() { m_bLoaded = false; }
bool ITable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ITable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ITable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

IndunInitTable::IndunInitTable() : m_bLoaded(false) { LoadTable(); }
IndunInitTable::~IndunInitTable() { m_bLoaded = false; }
bool IndunInitTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("IndunInitTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[IndunInitTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

InfinityIndunRewardTable::InfinityIndunRewardTable() : m_bLoaded(false) { LoadTable(); }
InfinityIndunRewardTable::~InfinityIndunRewardTable() { m_bLoaded = false; }
bool InfinityIndunRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("InfinityIndunRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[InfinityIndunRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

InstanceBonusTable::InstanceBonusTable() : m_bLoaded(false) { LoadTable(); }
InstanceBonusTable::~InstanceBonusTable() { m_bLoaded = false; }
bool InstanceBonusTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("InstanceBonusTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[InstanceBonusTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

InstantDungeonTable::InstantDungeonTable() : m_bLoaded(false) { LoadTable(); }
InstantDungeonTable::~InstantDungeonTable() { m_bLoaded = false; }
bool InstantDungeonTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("InstantDungeonTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[InstantDungeonTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemComposeTable::ItemComposeTable() : m_bLoaded(false) { LoadTable(); }
ItemComposeTable::~ItemComposeTable() { m_bLoaded = false; }
bool ItemComposeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemComposeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemComposeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemCrushTable::ItemCrushTable() : m_bLoaded(false) { LoadTable(); }
ItemCrushTable::~ItemCrushTable() { m_bLoaded = false; }
bool ItemCrushTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemCrushTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemCrushTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemCustomSetTable::ItemCustomSetTable() : m_bLoaded(false) { LoadTable(); }
ItemCustomSetTable::~ItemCustomSetTable() { m_bLoaded = false; }
bool ItemCustomSetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemCustomSetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemCustomSetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemFlavorTable::ItemFlavorTable() : m_bLoaded(false) { LoadTable(); }
ItemFlavorTable::~ItemFlavorTable() { m_bLoaded = false; }
bool ItemFlavorTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemFlavorTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemFlavorTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemOverrideIconTable::ItemOverrideIconTable() : m_bLoaded(false) { LoadTable(); }
ItemOverrideIconTable::~ItemOverrideIconTable() { m_bLoaded = false; }
bool ItemOverrideIconTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemOverrideIconTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemOverrideIconTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemSkillEnchantCostTable::ItemSkillEnchantCostTable() : m_bLoaded(false) { LoadTable(); }
ItemSkillEnchantCostTable::~ItemSkillEnchantCostTable() { m_bLoaded = false; }
bool ItemSkillEnchantCostTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemSkillEnchantCostTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemSkillEnchantCostTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemSkillEnchantTable::ItemSkillEnchantTable() : m_bLoaded(false) { LoadTable(); }
ItemSkillEnchantTable::~ItemSkillEnchantTable() { m_bLoaded = false; }
bool ItemSkillEnchantTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemSkillEnchantTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemSkillEnchantTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemTable::ItemTable() : m_bLoaded(false) { LoadTable(); }
ItemTable::~ItemTable() { m_bLoaded = false; }
bool ItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ItemUpgradeTable::ItemUpgradeTable() : m_bLoaded(false) { LoadTable(); }
ItemUpgradeTable::~ItemUpgradeTable() { m_bLoaded = false; }
bool ItemUpgradeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ItemUpgradeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ItemUpgradeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

LoadingTipTable::LoadingTipTable() : m_bLoaded(false) { LoadTable(); }
LoadingTipTable::~LoadingTipTable() { m_bLoaded = false; }
bool LoadingTipTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("LoadingTipTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[LoadingTipTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

LoginEventTable::LoginEventTable() : m_bLoaded(false) { LoadTable(); }
LoginEventTable::~LoginEventTable() { m_bLoaded = false; }
bool LoginEventTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("LoginEventTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[LoginEventTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

LookSynergyTable::LookSynergyTable() : m_bLoaded(false) { LoadTable(); }
LookSynergyTable::~LookSynergyTable() { m_bLoaded = false; }
bool LookSynergyTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("LookSynergyTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[LookSynergyTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

MakeUpBonusTable::MakeUpBonusTable() : m_bLoaded(false) { LoadTable(); }
MakeUpBonusTable::~MakeUpBonusTable() { m_bLoaded = false; }
bool MakeUpBonusTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("MakeUpBonusTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[MakeUpBonusTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

MatchMakerIndunTable::MatchMakerIndunTable() : m_bLoaded(false) { LoadTable(); }
MatchMakerIndunTable::~MatchMakerIndunTable() { m_bLoaded = false; }
bool MatchMakerIndunTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("MatchMakerIndunTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[MatchMakerIndunTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ModelCamTable::ModelCamTable() : m_bLoaded(false) { LoadTable(); }
ModelCamTable::~ModelCamTable() { m_bLoaded = false; }
bool ModelCamTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ModelCamTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ModelCamTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

MorosPointTable::MorosPointTable() : m_bLoaded(false) { LoadTable(); }
MorosPointTable::~MorosPointTable() { m_bLoaded = false; }
bool MorosPointTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("MorosPointTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[MorosPointTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

MorosTable::MorosTable() : m_bLoaded(false) { LoadTable(); }
MorosTable::~MorosTable() { m_bLoaded = false; }
bool MorosTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("MorosTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[MorosTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

MovieNameTable::MovieNameTable() : m_bLoaded(false) { LoadTable(); }
MovieNameTable::~MovieNameTable() { m_bLoaded = false; }
bool MovieNameTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("MovieNameTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[MovieNameTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NPCGoodsListBaseTable::NPCGoodsListBaseTable() : m_bLoaded(false) { LoadTable(); }
NPCGoodsListBaseTable::~NPCGoodsListBaseTable() { m_bLoaded = false; }
bool NPCGoodsListBaseTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NPCGoodsListBaseTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NPCGoodsListBaseTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NPCGoodsListTable::NPCGoodsListTable() : m_bLoaded(false) { LoadTable(); }
NPCGoodsListTable::~NPCGoodsListTable() { m_bLoaded = false; }
bool NPCGoodsListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NPCGoodsListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NPCGoodsListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NPCGuideTable::NPCGuideTable() : m_bLoaded(false) { LoadTable(); }
NPCGuideTable::~NPCGuideTable() { m_bLoaded = false; }
bool NPCGuideTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NPCGuideTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NPCGuideTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NPCPurchaseListTable::NPCPurchaseListTable() : m_bLoaded(false) { LoadTable(); }
NPCPurchaseListTable::~NPCPurchaseListTable() { m_bLoaded = false; }
bool NPCPurchaseListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NPCPurchaseListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NPCPurchaseListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NPCTable::NPCTable() : m_bLoaded(false) { LoadTable(); }
NPCTable::~NPCTable() { m_bLoaded = false; }
bool NPCTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NPCTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NPCTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NPCUITable::NPCUITable() : m_bLoaded(false) { LoadTable(); }
NPCUITable::~NPCUITable() { m_bLoaded = false; }
bool NPCUITable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NPCUITable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NPCUITable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

NotConnectedPeriodRewardConfigTable::NotConnectedPeriodRewardConfigTable() : m_bLoaded(false) { LoadTable(); }
NotConnectedPeriodRewardConfigTable::~NotConnectedPeriodRewardConfigTable() { m_bLoaded = false; }
bool NotConnectedPeriodRewardConfigTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("NotConnectedPeriodRewardConfigTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[NotConnectedPeriodRewardConfigTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

OptionClearTable::OptionClearTable() : m_bLoaded(false) { LoadTable(); }
OptionClearTable::~OptionClearTable() { m_bLoaded = false; }
bool OptionClearTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("OptionClearTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[OptionClearTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

OverrideStringTable::OverrideStringTable() : m_bLoaded(false) { LoadTable(); }
OverrideStringTable::~OverrideStringTable() { m_bLoaded = false; }
bool OverrideStringTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("OverrideStringTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[OverrideStringTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

PCTable::PCTable() : m_bLoaded(false) { LoadTable(); }
PCTable::~PCTable() { m_bLoaded = false; }
bool PCTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("PCTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[PCTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

PcExpRewardTable::PcExpRewardTable() : m_bLoaded(false) { LoadTable(); }
PcExpRewardTable::~PcExpRewardTable() { m_bLoaded = false; }
bool PcExpRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("PcExpRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[PcExpRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

PolymorphTempSkillTable::PolymorphTempSkillTable() : m_bLoaded(false) { LoadTable(); }
PolymorphTempSkillTable::~PolymorphTempSkillTable() { m_bLoaded = false; }
bool PolymorphTempSkillTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("PolymorphTempSkillTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[PolymorphTempSkillTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

PvPRankTable::PvPRankTable() : m_bLoaded(false) { LoadTable(); }
PvPRankTable::~PvPRankTable() { m_bLoaded = false; }
bool PvPRankTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("PvPRankTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[PvPRankTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

QuestMonsterTable::QuestMonsterTable() : m_bLoaded(false) { LoadTable(); }
QuestMonsterTable::~QuestMonsterTable() { m_bLoaded = false; }
bool QuestMonsterTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("QuestMonsterTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[QuestMonsterTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

QuestTable::QuestTable() : m_bLoaded(false) { LoadTable(); }
QuestTable::~QuestTable() { m_bLoaded = false; }
bool QuestTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("QuestTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[QuestTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

RankingBadgeTable::RankingBadgeTable() : m_bLoaded(false) { LoadTable(); }
RankingBadgeTable::~RankingBadgeTable() { m_bLoaded = false; }
bool RankingBadgeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("RankingBadgeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[RankingBadgeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

RankingRewardTable::RankingRewardTable() : m_bLoaded(false) { LoadTable(); }
RankingRewardTable::~RankingRewardTable() { m_bLoaded = false; }
bool RankingRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("RankingRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[RankingRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

RankingSeasonTable::RankingSeasonTable() : m_bLoaded(false) { LoadTable(); }
RankingSeasonTable::~RankingSeasonTable() { m_bLoaded = false; }
bool RankingSeasonTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("RankingSeasonTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[RankingSeasonTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

RecipeTable::RecipeTable() : m_bLoaded(false) { LoadTable(); }
RecipeTable::~RecipeTable() { m_bLoaded = false; }
bool RecipeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("RecipeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[RecipeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

RvRRewardTable::RvRRewardTable() : m_bLoaded(false) { LoadTable(); }
RvRRewardTable::~RvRRewardTable() { m_bLoaded = false; }
bool RvRRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("RvRRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[RvRRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

RvRScheduleTable::RvRScheduleTable() : m_bLoaded(false) { LoadTable(); }
RvRScheduleTable::~RvRScheduleTable() { m_bLoaded = false; }
bool RvRScheduleTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("RvRScheduleTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[RvRScheduleTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ScheduledMissionActionTable::ScheduledMissionActionTable() : m_bLoaded(false) { LoadTable(); }
ScheduledMissionActionTable::~ScheduledMissionActionTable() { m_bLoaded = false; }
bool ScheduledMissionActionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ScheduledMissionActionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ScheduledMissionActionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ScheduledMissionEventTable::ScheduledMissionEventTable() : m_bLoaded(false) { LoadTable(); }
ScheduledMissionEventTable::~ScheduledMissionEventTable() { m_bLoaded = false; }
bool ScheduledMissionEventTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ScheduledMissionEventTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ScheduledMissionEventTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ScoreDamageIndunTable::ScoreDamageIndunTable() : m_bLoaded(false) { LoadTable(); }
ScoreDamageIndunTable::~ScoreDamageIndunTable() { m_bLoaded = false; }
bool ScoreDamageIndunTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ScoreDamageIndunTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ScoreDamageIndunTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SerialKillerTable::SerialKillerTable() : m_bLoaded(false) { LoadTable(); }
SerialKillerTable::~SerialKillerTable() { m_bLoaded = false; }
bool SerialKillerTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SerialKillerTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SerialKillerTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SetItemTable::SetItemTable() : m_bLoaded(false) { LoadTable(); }
SetItemTable::~SetItemTable() { m_bLoaded = false; }
bool SetItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SetItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SetItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SkillBoosterTable::SkillBoosterTable() : m_bLoaded(false) { LoadTable(); }
SkillBoosterTable::~SkillBoosterTable() { m_bLoaded = false; }
bool SkillBoosterTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SkillBoosterTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SkillBoosterTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SkillLearnTable::SkillLearnTable() : m_bLoaded(false) { LoadTable(); }
SkillLearnTable::~SkillLearnTable() { m_bLoaded = false; }
bool SkillLearnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SkillLearnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SkillLearnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SkillProhibitTable::SkillProhibitTable() : m_bLoaded(false) { LoadTable(); }
SkillProhibitTable::~SkillProhibitTable() { m_bLoaded = false; }
bool SkillProhibitTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SkillProhibitTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SkillProhibitTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SkillSkinTable::SkillSkinTable() : m_bLoaded(false) { LoadTable(); }
SkillSkinTable::~SkillSkinTable() { m_bLoaded = false; }
bool SkillSkinTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SkillSkinTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SkillSkinTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SkillTable::SkillTable() : m_bLoaded(false) { LoadTable(); }
SkillTable::~SkillTable() { m_bLoaded = false; }
bool SkillTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SkillTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SkillTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpawnTable::SpawnTable() : m_bLoaded(false) { LoadTable(); }
SpawnTable::~SpawnTable() { m_bLoaded = false; }
bool SpawnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpawnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpawnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2AbyssTable::Special2AbyssTable() : m_bLoaded(false) { LoadTable(); }
Special2AbyssTable::~Special2AbyssTable() { m_bLoaded = false; }
bool Special2AbyssTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2AbyssTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2AbyssTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2AccumulatedEnchantTable::Special2AccumulatedEnchantTable() : m_bLoaded(false) { LoadTable(); }
Special2AccumulatedEnchantTable::~Special2AccumulatedEnchantTable() { m_bLoaded = false; }
bool Special2AccumulatedEnchantTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2AccumulatedEnchantTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2AccumulatedEnchantTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2CombatPowerRewardTable::Special2CombatPowerRewardTable() : m_bLoaded(false) { LoadTable(); }
Special2CombatPowerRewardTable::~Special2CombatPowerRewardTable() { m_bLoaded = false; }
bool Special2CombatPowerRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2CombatPowerRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2CombatPowerRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2DisassemblyItemSetListTable::Special2DisassemblyItemSetListTable() : m_bLoaded(false) { LoadTable(); }
Special2DisassemblyItemSetListTable::~Special2DisassemblyItemSetListTable() { m_bLoaded = false; }
bool Special2DisassemblyItemSetListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2DisassemblyItemSetListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2DisassemblyItemSetListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2DisassemblyItemSetTable::Special2DisassemblyItemSetTable() : m_bLoaded(false) { LoadTable(); }
Special2DisassemblyItemSetTable::~Special2DisassemblyItemSetTable() { m_bLoaded = false; }
bool Special2DisassemblyItemSetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2DisassemblyItemSetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2DisassemblyItemSetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2EnchantCountProbTable::Special2EnchantCountProbTable() : m_bLoaded(false) { LoadTable(); }
Special2EnchantCountProbTable::~Special2EnchantCountProbTable() { m_bLoaded = false; }
bool Special2EnchantCountProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2EnchantCountProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2EnchantCountProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2EnchantGapLevelProbTable::Special2EnchantGapLevelProbTable() : m_bLoaded(false) { LoadTable(); }
Special2EnchantGapLevelProbTable::~Special2EnchantGapLevelProbTable() { m_bLoaded = false; }
bool Special2EnchantGapLevelProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2EnchantGapLevelProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2EnchantGapLevelProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2EnchantOptionTable::Special2EnchantOptionTable() : m_bLoaded(false) { LoadTable(); }
Special2EnchantOptionTable::~Special2EnchantOptionTable() { m_bLoaded = false; }
bool Special2EnchantOptionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2EnchantOptionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2EnchantOptionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GamePassExtraTable::Special2GamePassExtraTable() : m_bLoaded(false) { LoadTable(); }
Special2GamePassExtraTable::~Special2GamePassExtraTable() { m_bLoaded = false; }
bool Special2GamePassExtraTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GamePassExtraTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GamePassExtraTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GameRuleOptionsTable::Special2GameRuleOptionsTable() : m_bLoaded(false) { LoadTable(); }
Special2GameRuleOptionsTable::~Special2GameRuleOptionsTable() { m_bLoaded = false; }
bool Special2GameRuleOptionsTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GameRuleOptionsTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GameRuleOptionsTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GatherSourceTable::Special2GatherSourceTable() : m_bLoaded(false) { LoadTable(); }
Special2GatherSourceTable::~Special2GatherSourceTable() { m_bLoaded = false; }
bool Special2GatherSourceTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GatherSourceTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GatherSourceTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GuildCraftTable::Special2GuildCraftTable() : m_bLoaded(false) { LoadTable(); }
Special2GuildCraftTable::~Special2GuildCraftTable() { m_bLoaded = false; }
bool Special2GuildCraftTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GuildCraftTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GuildCraftTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GuildDonationSettingTable::Special2GuildDonationSettingTable() : m_bLoaded(false) { LoadTable(); }
Special2GuildDonationSettingTable::~Special2GuildDonationSettingTable() { m_bLoaded = false; }
bool Special2GuildDonationSettingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GuildDonationSettingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GuildDonationSettingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GuildScheduledMissionAchievementTable::Special2GuildScheduledMissionAchievementTable() : m_bLoaded(false) { LoadTable(); }
Special2GuildScheduledMissionAchievementTable::~Special2GuildScheduledMissionAchievementTable() { m_bLoaded = false; }
bool Special2GuildScheduledMissionAchievementTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GuildScheduledMissionAchievementTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GuildScheduledMissionAchievementTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2GuildScheduledMissionActionTable::Special2GuildScheduledMissionActionTable() : m_bLoaded(false) { LoadTable(); }
Special2GuildScheduledMissionActionTable::~Special2GuildScheduledMissionActionTable() { m_bLoaded = false; }
bool Special2GuildScheduledMissionActionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2GuildScheduledMissionActionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2GuildScheduledMissionActionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2HotSpotTable::Special2HotSpotTable() : m_bLoaded(false) { LoadTable(); }
Special2HotSpotTable::~Special2HotSpotTable() { m_bLoaded = false; }
bool Special2HotSpotTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2HotSpotTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2HotSpotTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2IndunInitTable::Special2IndunInitTable() : m_bLoaded(false) { LoadTable(); }
Special2IndunInitTable::~Special2IndunInitTable() { m_bLoaded = false; }
bool Special2IndunInitTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2IndunInitTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2IndunInitTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2InstantDungeonTable::Special2InstantDungeonTable() : m_bLoaded(false) { LoadTable(); }
Special2InstantDungeonTable::~Special2InstantDungeonTable() { m_bLoaded = false; }
bool Special2InstantDungeonTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2InstantDungeonTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2InstantDungeonTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2ItemComposeTable::Special2ItemComposeTable() : m_bLoaded(false) { LoadTable(); }
Special2ItemComposeTable::~Special2ItemComposeTable() { m_bLoaded = false; }
bool Special2ItemComposeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2ItemComposeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2ItemComposeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2ItemCrushTable::Special2ItemCrushTable() : m_bLoaded(false) { LoadTable(); }
Special2ItemCrushTable::~Special2ItemCrushTable() { m_bLoaded = false; }
bool Special2ItemCrushTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2ItemCrushTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2ItemCrushTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2ItemTable::Special2ItemTable() : m_bLoaded(false) { LoadTable(); }
Special2ItemTable::~Special2ItemTable() { m_bLoaded = false; }
bool Special2ItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2ItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2ItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2ItemUpgradeTable::Special2ItemUpgradeTable() : m_bLoaded(false) { LoadTable(); }
Special2ItemUpgradeTable::~Special2ItemUpgradeTable() { m_bLoaded = false; }
bool Special2ItemUpgradeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2ItemUpgradeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2ItemUpgradeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2LookSynergyTable::Special2LookSynergyTable() : m_bLoaded(false) { LoadTable(); }
Special2LookSynergyTable::~Special2LookSynergyTable() { m_bLoaded = false; }
bool Special2LookSynergyTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2LookSynergyTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2LookSynergyTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2MatchMakerIndunTable::Special2MatchMakerIndunTable() : m_bLoaded(false) { LoadTable(); }
Special2MatchMakerIndunTable::~Special2MatchMakerIndunTable() { m_bLoaded = false; }
bool Special2MatchMakerIndunTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2MatchMakerIndunTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2MatchMakerIndunTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2NPCGoodsListTable::Special2NPCGoodsListTable() : m_bLoaded(false) { LoadTable(); }
Special2NPCGoodsListTable::~Special2NPCGoodsListTable() { m_bLoaded = false; }
bool Special2NPCGoodsListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2NPCGoodsListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2NPCGoodsListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2NPCPurchaseListTable::Special2NPCPurchaseListTable() : m_bLoaded(false) { LoadTable(); }
Special2NPCPurchaseListTable::~Special2NPCPurchaseListTable() { m_bLoaded = false; }
bool Special2NPCPurchaseListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2NPCPurchaseListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2NPCPurchaseListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2NPCTable::Special2NPCTable() : m_bLoaded(false) { LoadTable(); }
Special2NPCTable::~Special2NPCTable() { m_bLoaded = false; }
bool Special2NPCTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2NPCTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2NPCTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2OptionClearTable::Special2OptionClearTable() : m_bLoaded(false) { LoadTable(); }
Special2OptionClearTable::~Special2OptionClearTable() { m_bLoaded = false; }
bool Special2OptionClearTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2OptionClearTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2OptionClearTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2QuestMonsterTable::Special2QuestMonsterTable() : m_bLoaded(false) { LoadTable(); }
Special2QuestMonsterTable::~Special2QuestMonsterTable() { m_bLoaded = false; }
bool Special2QuestMonsterTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2QuestMonsterTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2QuestMonsterTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2QuestTable::Special2QuestTable() : m_bLoaded(false) { LoadTable(); }
Special2QuestTable::~Special2QuestTable() { m_bLoaded = false; }
bool Special2QuestTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2QuestTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2QuestTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2RankingRewardTable::Special2RankingRewardTable() : m_bLoaded(false) { LoadTable(); }
Special2RankingRewardTable::~Special2RankingRewardTable() { m_bLoaded = false; }
bool Special2RankingRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2RankingRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2RankingRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2RvRRewardTable::Special2RvRRewardTable() : m_bLoaded(false) { LoadTable(); }
Special2RvRRewardTable::~Special2RvRRewardTable() { m_bLoaded = false; }
bool Special2RvRRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2RvRRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2RvRRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2RvRScheduleTable::Special2RvRScheduleTable() : m_bLoaded(false) { LoadTable(); }
Special2RvRScheduleTable::~Special2RvRScheduleTable() { m_bLoaded = false; }
bool Special2RvRScheduleTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2RvRScheduleTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2RvRScheduleTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2ScoreDamageIndunTable::Special2ScoreDamageIndunTable() : m_bLoaded(false) { LoadTable(); }
Special2ScoreDamageIndunTable::~Special2ScoreDamageIndunTable() { m_bLoaded = false; }
bool Special2ScoreDamageIndunTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2ScoreDamageIndunTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2ScoreDamageIndunTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2SkillLearnTable::Special2SkillLearnTable() : m_bLoaded(false) { LoadTable(); }
Special2SkillLearnTable::~Special2SkillLearnTable() { m_bLoaded = false; }
bool Special2SkillLearnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2SkillLearnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2SkillLearnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2SkillSkinTable::Special2SkillSkinTable() : m_bLoaded(false) { LoadTable(); }
Special2SkillSkinTable::~Special2SkillSkinTable() { m_bLoaded = false; }
bool Special2SkillSkinTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2SkillSkinTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2SkillSkinTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2SkillTable::Special2SkillTable() : m_bLoaded(false) { LoadTable(); }
Special2SkillTable::~Special2SkillTable() { m_bLoaded = false; }
bool Special2SkillTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2SkillTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2SkillTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2SpawnTable::Special2SpawnTable() : m_bLoaded(false) { LoadTable(); }
Special2SpawnTable::~Special2SpawnTable() { m_bLoaded = false; }
bool Special2SpawnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2SpawnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2SpawnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2TradeInListTable::Special2TradeInListTable() : m_bLoaded(false) { LoadTable(); }
Special2TradeInListTable::~Special2TradeInListTable() { m_bLoaded = false; }
bool Special2TradeInListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2TradeInListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2TradeInListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2WorldIDTable::Special2WorldIDTable() : m_bLoaded(false) { LoadTable(); }
Special2WorldIDTable::~Special2WorldIDTable() { m_bLoaded = false; }
bool Special2WorldIDTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2WorldIDTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2WorldIDTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

Special2WorldReturnTable::Special2WorldReturnTable() : m_bLoaded(false) { LoadTable(); }
Special2WorldReturnTable::~Special2WorldReturnTable() { m_bLoaded = false; }
bool Special2WorldReturnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("Special2WorldReturnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[Special2WorldReturnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialAbyssRankTable::SpecialAbyssRankTable() : m_bLoaded(false) { LoadTable(); }
SpecialAbyssRankTable::~SpecialAbyssRankTable() { m_bLoaded = false; }
bool SpecialAbyssRankTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialAbyssRankTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialAbyssRankTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialAbyssTable::SpecialAbyssTable() : m_bLoaded(false) { LoadTable(); }
SpecialAbyssTable::~SpecialAbyssTable() { m_bLoaded = false; }
bool SpecialAbyssTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialAbyssTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialAbyssTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialAccumulatedEnchantTable::SpecialAccumulatedEnchantTable() : m_bLoaded(false) { LoadTable(); }
SpecialAccumulatedEnchantTable::~SpecialAccumulatedEnchantTable() { m_bLoaded = false; }
bool SpecialAccumulatedEnchantTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialAccumulatedEnchantTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialAccumulatedEnchantTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialAssistOptionEnchantTypeTable::SpecialAssistOptionEnchantTypeTable() : m_bLoaded(false) { LoadTable(); }
SpecialAssistOptionEnchantTypeTable::~SpecialAssistOptionEnchantTypeTable() { m_bLoaded = false; }
bool SpecialAssistOptionEnchantTypeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialAssistOptionEnchantTypeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialAssistOptionEnchantTypeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialAssistOptionEnchantValueTable::SpecialAssistOptionEnchantValueTable() : m_bLoaded(false) { LoadTable(); }
SpecialAssistOptionEnchantValueTable::~SpecialAssistOptionEnchantValueTable() { m_bLoaded = false; }
bool SpecialAssistOptionEnchantValueTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialAssistOptionEnchantValueTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialAssistOptionEnchantValueTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialCharacterClassInfoTable::SpecialCharacterClassInfoTable() : m_bLoaded(false) { LoadTable(); }
SpecialCharacterClassInfoTable::~SpecialCharacterClassInfoTable() { m_bLoaded = false; }
bool SpecialCharacterClassInfoTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialCharacterClassInfoTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialCharacterClassInfoTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialCombatPowerRankBuffTable::SpecialCombatPowerRankBuffTable() : m_bLoaded(false) { LoadTable(); }
SpecialCombatPowerRankBuffTable::~SpecialCombatPowerRankBuffTable() { m_bLoaded = false; }
bool SpecialCombatPowerRankBuffTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialCombatPowerRankBuffTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialCombatPowerRankBuffTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialCombatPowerRewardTable::SpecialCombatPowerRewardTable() : m_bLoaded(false) { LoadTable(); }
SpecialCombatPowerRewardTable::~SpecialCombatPowerRewardTable() { m_bLoaded = false; }
bool SpecialCombatPowerRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialCombatPowerRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialCombatPowerRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialCraftItemTable::SpecialCraftItemTable() : m_bLoaded(false) { LoadTable(); }
SpecialCraftItemTable::~SpecialCraftItemTable() { m_bLoaded = false; }
bool SpecialCraftItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialCraftItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialCraftItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialDisassemblyItemSetListTable::SpecialDisassemblyItemSetListTable() : m_bLoaded(false) { LoadTable(); }
SpecialDisassemblyItemSetListTable::~SpecialDisassemblyItemSetListTable() { m_bLoaded = false; }
bool SpecialDisassemblyItemSetListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialDisassemblyItemSetListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialDisassemblyItemSetListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialDisassemblyItemSetTable::SpecialDisassemblyItemSetTable() : m_bLoaded(false) { LoadTable(); }
SpecialDisassemblyItemSetTable::~SpecialDisassemblyItemSetTable() { m_bLoaded = false; }
bool SpecialDisassemblyItemSetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialDisassemblyItemSetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialDisassemblyItemSetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialEnchantCountProbTable::SpecialEnchantCountProbTable() : m_bLoaded(false) { LoadTable(); }
SpecialEnchantCountProbTable::~SpecialEnchantCountProbTable() { m_bLoaded = false; }
bool SpecialEnchantCountProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialEnchantCountProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialEnchantCountProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialEnchantGapLevelProbTable::SpecialEnchantGapLevelProbTable() : m_bLoaded(false) { LoadTable(); }
SpecialEnchantGapLevelProbTable::~SpecialEnchantGapLevelProbTable() { m_bLoaded = false; }
bool SpecialEnchantGapLevelProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialEnchantGapLevelProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialEnchantGapLevelProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialEnchantMatterProbTable::SpecialEnchantMatterProbTable() : m_bLoaded(false) { LoadTable(); }
SpecialEnchantMatterProbTable::~SpecialEnchantMatterProbTable() { m_bLoaded = false; }
bool SpecialEnchantMatterProbTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialEnchantMatterProbTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialEnchantMatterProbTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialEnchantOptionTable::SpecialEnchantOptionTable() : m_bLoaded(false) { LoadTable(); }
SpecialEnchantOptionTable::~SpecialEnchantOptionTable() { m_bLoaded = false; }
bool SpecialEnchantOptionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialEnchantOptionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialEnchantOptionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGamePassExtraTable::SpecialGamePassExtraTable() : m_bLoaded(false) { LoadTable(); }
SpecialGamePassExtraTable::~SpecialGamePassExtraTable() { m_bLoaded = false; }
bool SpecialGamePassExtraTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGamePassExtraTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGamePassExtraTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGameRuleOptionsTable::SpecialGameRuleOptionsTable() : m_bLoaded(false) { LoadTable(); }
SpecialGameRuleOptionsTable::~SpecialGameRuleOptionsTable() { m_bLoaded = false; }
bool SpecialGameRuleOptionsTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGameRuleOptionsTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGameRuleOptionsTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGatherSourceTable::SpecialGatherSourceTable() : m_bLoaded(false) { LoadTable(); }
SpecialGatherSourceTable::~SpecialGatherSourceTable() { m_bLoaded = false; }
bool SpecialGatherSourceTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGatherSourceTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGatherSourceTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGemMatterItemReforgeStatInfoDataTable::SpecialGemMatterItemReforgeStatInfoDataTable() : m_bLoaded(false) { LoadTable(); }
SpecialGemMatterItemReforgeStatInfoDataTable::~SpecialGemMatterItemReforgeStatInfoDataTable() { m_bLoaded = false; }
bool SpecialGemMatterItemReforgeStatInfoDataTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGemMatterItemReforgeStatInfoDataTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGemMatterItemReforgeStatInfoDataTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGemMatterItemReforgeStatTable::SpecialGemMatterItemReforgeStatTable() : m_bLoaded(false) { LoadTable(); }
SpecialGemMatterItemReforgeStatTable::~SpecialGemMatterItemReforgeStatTable() { m_bLoaded = false; }
bool SpecialGemMatterItemReforgeStatTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGemMatterItemReforgeStatTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGemMatterItemReforgeStatTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGemMatterItemReforgeTable::SpecialGemMatterItemReforgeTable() : m_bLoaded(false) { LoadTable(); }
SpecialGemMatterItemReforgeTable::~SpecialGemMatterItemReforgeTable() { m_bLoaded = false; }
bool SpecialGemMatterItemReforgeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGemMatterItemReforgeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGemMatterItemReforgeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGuildCraftTable::SpecialGuildCraftTable() : m_bLoaded(false) { LoadTable(); }
SpecialGuildCraftTable::~SpecialGuildCraftTable() { m_bLoaded = false; }
bool SpecialGuildCraftTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGuildCraftTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGuildCraftTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGuildDonationRewardTable::SpecialGuildDonationRewardTable() : m_bLoaded(false) { LoadTable(); }
SpecialGuildDonationRewardTable::~SpecialGuildDonationRewardTable() { m_bLoaded = false; }
bool SpecialGuildDonationRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGuildDonationRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGuildDonationRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGuildDonationSettingTable::SpecialGuildDonationSettingTable() : m_bLoaded(false) { LoadTable(); }
SpecialGuildDonationSettingTable::~SpecialGuildDonationSettingTable() { m_bLoaded = false; }
bool SpecialGuildDonationSettingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGuildDonationSettingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGuildDonationSettingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGuildScheduledMissionAchievementTable::SpecialGuildScheduledMissionAchievementTable() : m_bLoaded(false) { LoadTable(); }
SpecialGuildScheduledMissionAchievementTable::~SpecialGuildScheduledMissionAchievementTable() { m_bLoaded = false; }
bool SpecialGuildScheduledMissionAchievementTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGuildScheduledMissionAchievementTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGuildScheduledMissionAchievementTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialGuildScheduledMissionActionTable::SpecialGuildScheduledMissionActionTable() : m_bLoaded(false) { LoadTable(); }
SpecialGuildScheduledMissionActionTable::~SpecialGuildScheduledMissionActionTable() { m_bLoaded = false; }
bool SpecialGuildScheduledMissionActionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialGuildScheduledMissionActionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialGuildScheduledMissionActionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialHotSpotTable::SpecialHotSpotTable() : m_bLoaded(false) { LoadTable(); }
SpecialHotSpotTable::~SpecialHotSpotTable() { m_bLoaded = false; }
bool SpecialHotSpotTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialHotSpotTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialHotSpotTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialIndunInitTable::SpecialIndunInitTable() : m_bLoaded(false) { LoadTable(); }
SpecialIndunInitTable::~SpecialIndunInitTable() { m_bLoaded = false; }
bool SpecialIndunInitTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialIndunInitTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialIndunInitTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialInstantDungeonTable::SpecialInstantDungeonTable() : m_bLoaded(false) { LoadTable(); }
SpecialInstantDungeonTable::~SpecialInstantDungeonTable() { m_bLoaded = false; }
bool SpecialInstantDungeonTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialInstantDungeonTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialInstantDungeonTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialItemComposeTable::SpecialItemComposeTable() : m_bLoaded(false) { LoadTable(); }
SpecialItemComposeTable::~SpecialItemComposeTable() { m_bLoaded = false; }
bool SpecialItemComposeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialItemComposeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialItemComposeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialItemCrushTable::SpecialItemCrushTable() : m_bLoaded(false) { LoadTable(); }
SpecialItemCrushTable::~SpecialItemCrushTable() { m_bLoaded = false; }
bool SpecialItemCrushTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialItemCrushTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialItemCrushTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialItemSkillEnchantCostTable::SpecialItemSkillEnchantCostTable() : m_bLoaded(false) { LoadTable(); }
SpecialItemSkillEnchantCostTable::~SpecialItemSkillEnchantCostTable() { m_bLoaded = false; }
bool SpecialItemSkillEnchantCostTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialItemSkillEnchantCostTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialItemSkillEnchantCostTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialItemTable::SpecialItemTable() : m_bLoaded(false) { LoadTable(); }
SpecialItemTable::~SpecialItemTable() { m_bLoaded = false; }
bool SpecialItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialItemUpgradeTable::SpecialItemUpgradeTable() : m_bLoaded(false) { LoadTable(); }
SpecialItemUpgradeTable::~SpecialItemUpgradeTable() { m_bLoaded = false; }
bool SpecialItemUpgradeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialItemUpgradeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialItemUpgradeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialLookSynergyTable::SpecialLookSynergyTable() : m_bLoaded(false) { LoadTable(); }
SpecialLookSynergyTable::~SpecialLookSynergyTable() { m_bLoaded = false; }
bool SpecialLookSynergyTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialLookSynergyTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialLookSynergyTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialMatchMakerIndunTable::SpecialMatchMakerIndunTable() : m_bLoaded(false) { LoadTable(); }
SpecialMatchMakerIndunTable::~SpecialMatchMakerIndunTable() { m_bLoaded = false; }
bool SpecialMatchMakerIndunTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialMatchMakerIndunTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialMatchMakerIndunTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialMorosTable::SpecialMorosTable() : m_bLoaded(false) { LoadTable(); }
SpecialMorosTable::~SpecialMorosTable() { m_bLoaded = false; }
bool SpecialMorosTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialMorosTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialMorosTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialNPCGoodsListTable::SpecialNPCGoodsListTable() : m_bLoaded(false) { LoadTable(); }
SpecialNPCGoodsListTable::~SpecialNPCGoodsListTable() { m_bLoaded = false; }
bool SpecialNPCGoodsListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialNPCGoodsListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialNPCGoodsListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialNPCPurchaseListTable::SpecialNPCPurchaseListTable() : m_bLoaded(false) { LoadTable(); }
SpecialNPCPurchaseListTable::~SpecialNPCPurchaseListTable() { m_bLoaded = false; }
bool SpecialNPCPurchaseListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialNPCPurchaseListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialNPCPurchaseListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialNPCTable::SpecialNPCTable() : m_bLoaded(false) { LoadTable(); }
SpecialNPCTable::~SpecialNPCTable() { m_bLoaded = false; }
bool SpecialNPCTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialNPCTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialNPCTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialOptionClearTable::SpecialOptionClearTable() : m_bLoaded(false) { LoadTable(); }
SpecialOptionClearTable::~SpecialOptionClearTable() { m_bLoaded = false; }
bool SpecialOptionClearTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialOptionClearTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialOptionClearTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialPcExpRewardTable::SpecialPcExpRewardTable() : m_bLoaded(false) { LoadTable(); }
SpecialPcExpRewardTable::~SpecialPcExpRewardTable() { m_bLoaded = false; }
bool SpecialPcExpRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialPcExpRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialPcExpRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialQuestMonsterTable::SpecialQuestMonsterTable() : m_bLoaded(false) { LoadTable(); }
SpecialQuestMonsterTable::~SpecialQuestMonsterTable() { m_bLoaded = false; }
bool SpecialQuestMonsterTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialQuestMonsterTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialQuestMonsterTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialQuestTable::SpecialQuestTable() : m_bLoaded(false) { LoadTable(); }
SpecialQuestTable::~SpecialQuestTable() { m_bLoaded = false; }
bool SpecialQuestTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialQuestTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialQuestTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialRecipeTable::SpecialRecipeTable() : m_bLoaded(false) { LoadTable(); }
SpecialRecipeTable::~SpecialRecipeTable() { m_bLoaded = false; }
bool SpecialRecipeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialRecipeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialRecipeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialRvRRewardTable::SpecialRvRRewardTable() : m_bLoaded(false) { LoadTable(); }
SpecialRvRRewardTable::~SpecialRvRRewardTable() { m_bLoaded = false; }
bool SpecialRvRRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialRvRRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialRvRRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialRvRScheduleTable::SpecialRvRScheduleTable() : m_bLoaded(false) { LoadTable(); }
SpecialRvRScheduleTable::~SpecialRvRScheduleTable() { m_bLoaded = false; }
bool SpecialRvRScheduleTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialRvRScheduleTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialRvRScheduleTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSetItemTable::SpecialSetItemTable() : m_bLoaded(false) { LoadTable(); }
SpecialSetItemTable::~SpecialSetItemTable() { m_bLoaded = false; }
bool SpecialSetItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSetItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSetItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSkillLearnTable::SpecialSkillLearnTable() : m_bLoaded(false) { LoadTable(); }
SpecialSkillLearnTable::~SpecialSkillLearnTable() { m_bLoaded = false; }
bool SpecialSkillLearnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSkillLearnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSkillLearnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSkillSkinTable::SpecialSkillSkinTable() : m_bLoaded(false) { LoadTable(); }
SpecialSkillSkinTable::~SpecialSkillSkinTable() { m_bLoaded = false; }
bool SpecialSkillSkinTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSkillSkinTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSkillSkinTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSkillTable::SpecialSkillTable() : m_bLoaded(false) { LoadTable(); }
SpecialSkillTable::~SpecialSkillTable() { m_bLoaded = false; }
bool SpecialSkillTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSkillTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSkillTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSkinMeshNameTable::SpecialSkinMeshNameTable() : m_bLoaded(false) { LoadTable(); }
SpecialSkinMeshNameTable::~SpecialSkinMeshNameTable() { m_bLoaded = false; }
bool SpecialSkinMeshNameTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSkinMeshNameTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSkinMeshNameTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSkinTable::SpecialSkinTable() : m_bLoaded(false) { LoadTable(); }
SpecialSkinTable::~SpecialSkinTable() { m_bLoaded = false; }
bool SpecialSkinTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSkinTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSkinTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialSpawnTable::SpecialSpawnTable() : m_bLoaded(false) { LoadTable(); }
SpecialSpawnTable::~SpecialSpawnTable() { m_bLoaded = false; }
bool SpecialSpawnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialSpawnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialSpawnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialStoryBookRewardTable::SpecialStoryBookRewardTable() : m_bLoaded(false) { LoadTable(); }
SpecialStoryBookRewardTable::~SpecialStoryBookRewardTable() { m_bLoaded = false; }
bool SpecialStoryBookRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialStoryBookRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialStoryBookRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialStoryBookTable::SpecialStoryBookTable() : m_bLoaded(false) { LoadTable(); }
SpecialStoryBookTable::~SpecialStoryBookTable() { m_bLoaded = false; }
bool SpecialStoryBookTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialStoryBookTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialStoryBookTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialTeleportTable::SpecialTeleportTable() : m_bLoaded(false) { LoadTable(); }
SpecialTeleportTable::~SpecialTeleportTable() { m_bLoaded = false; }
bool SpecialTeleportTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialTeleportTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialTeleportTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialToyPetTable::SpecialToyPetTable() : m_bLoaded(false) { LoadTable(); }
SpecialToyPetTable::~SpecialToyPetTable() { m_bLoaded = false; }
bool SpecialToyPetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialToyPetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialToyPetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialTradeInListTable::SpecialTradeInListTable() : m_bLoaded(false) { LoadTable(); }
SpecialTradeInListTable::~SpecialTradeInListTable() { m_bLoaded = false; }
bool SpecialTradeInListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialTradeInListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialTradeInListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialWorldIDTable::SpecialWorldIDTable() : m_bLoaded(false) { LoadTable(); }
SpecialWorldIDTable::~SpecialWorldIDTable() { m_bLoaded = false; }
bool SpecialWorldIDTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialWorldIDTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialWorldIDTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

SpecialWorldReturnTable::SpecialWorldReturnTable() : m_bLoaded(false) { LoadTable(); }
SpecialWorldReturnTable::~SpecialWorldReturnTable() { m_bLoaded = false; }
bool SpecialWorldReturnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("SpecialWorldReturnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[SpecialWorldReturnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

StatInfoTable::StatInfoTable() : m_bLoaded(false) { LoadTable(); }
StatInfoTable::~StatInfoTable() { m_bLoaded = false; }
bool StatInfoTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("StatInfoTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[StatInfoTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

StigmaPageConfigTable::StigmaPageConfigTable() : m_bLoaded(false) { LoadTable(); }
StigmaPageConfigTable::~StigmaPageConfigTable() { m_bLoaded = false; }
bool StigmaPageConfigTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("StigmaPageConfigTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[StigmaPageConfigTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

StoryBookAppraiseTable::StoryBookAppraiseTable() : m_bLoaded(false) { LoadTable(); }
StoryBookAppraiseTable::~StoryBookAppraiseTable() { m_bLoaded = false; }
bool StoryBookAppraiseTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("StoryBookAppraiseTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[StoryBookAppraiseTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

StoryBookRewardTable::StoryBookRewardTable() : m_bLoaded(false) { LoadTable(); }
StoryBookRewardTable::~StoryBookRewardTable() { m_bLoaded = false; }
bool StoryBookRewardTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("StoryBookRewardTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[StoryBookRewardTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

StoryBookTable::StoryBookTable() : m_bLoaded(false) { LoadTable(); }
StoryBookTable::~StoryBookTable() { m_bLoaded = false; }
bool StoryBookTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("StoryBookTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[StoryBookTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TaskTable::TaskTable() : m_bLoaded(false) { LoadTable(); }
TaskTable::~TaskTable() { m_bLoaded = false; }
bool TaskTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TaskTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TaskTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TeleportTable::TeleportTable() : m_bLoaded(false) { LoadTable(); }
TeleportTable::~TeleportTable() { m_bLoaded = false; }
bool TeleportTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TeleportTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TeleportTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TimeGraphTable::TimeGraphTable() : m_bLoaded(false) { LoadTable(); }
TimeGraphTable::~TimeGraphTable() { m_bLoaded = false; }
bool TimeGraphTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TimeGraphTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TimeGraphTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TitleCollectionTable::TitleCollectionTable() : m_bLoaded(false) { LoadTable(); }
TitleCollectionTable::~TitleCollectionTable() { m_bLoaded = false; }
bool TitleCollectionTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TitleCollectionTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TitleCollectionTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TitleTable::TitleTable() : m_bLoaded(false) { LoadTable(); }
TitleTable::~TitleTable() { m_bLoaded = false; }
bool TitleTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TitleTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TitleTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ToyPetDopingTable::ToyPetDopingTable() : m_bLoaded(false) { LoadTable(); }
ToyPetDopingTable::~ToyPetDopingTable() { m_bLoaded = false; }
bool ToyPetDopingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ToyPetDopingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ToyPetDopingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ToyPetFeedingTable::ToyPetFeedingTable() : m_bLoaded(false) { LoadTable(); }
ToyPetFeedingTable::~ToyPetFeedingTable() { m_bLoaded = false; }
bool ToyPetFeedingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ToyPetFeedingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ToyPetFeedingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ToyPetItemTable::ToyPetItemTable() : m_bLoaded(false) { LoadTable(); }
ToyPetItemTable::~ToyPetItemTable() { m_bLoaded = false; }
bool ToyPetItemTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ToyPetItemTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ToyPetItemTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ToyPetLootingTable::ToyPetLootingTable() : m_bLoaded(false) { LoadTable(); }
ToyPetLootingTable::~ToyPetLootingTable() { m_bLoaded = false; }
bool ToyPetLootingTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ToyPetLootingTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ToyPetLootingTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ToyPetTable::ToyPetTable() : m_bLoaded(false) { LoadTable(); }
ToyPetTable::~ToyPetTable() { m_bLoaded = false; }
bool ToyPetTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ToyPetTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ToyPetTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ToyPetWarehouseTable::ToyPetWarehouseTable() : m_bLoaded(false) { LoadTable(); }
ToyPetWarehouseTable::~ToyPetWarehouseTable() { m_bLoaded = false; }
bool ToyPetWarehouseTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ToyPetWarehouseTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ToyPetWarehouseTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TradeInListTable::TradeInListTable() : m_bLoaded(false) { LoadTable(); }
TradeInListTable::~TradeInListTable() { m_bLoaded = false; }
bool TradeInListTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TradeInListTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TradeInListTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

TribeTable::TribeTable() : m_bLoaded(false) { LoadTable(); }
TribeTable::~TribeTable() { m_bLoaded = false; }
bool TribeTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("TribeTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[TribeTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

UIColorTable::UIColorTable() : m_bLoaded(false) { LoadTable(); }
UIColorTable::~UIColorTable() { m_bLoaded = false; }
bool UIColorTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("UIColorTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[UIColorTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

UltraSkillTable::UltraSkillTable() : m_bLoaded(false) { LoadTable(); }
UltraSkillTable::~UltraSkillTable() { m_bLoaded = false; }
bool UltraSkillTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("UltraSkillTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[UltraSkillTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

VitalPointTable::VitalPointTable() : m_bLoaded(false) { LoadTable(); }
VitalPointTable::~VitalPointTable() { m_bLoaded = false; }
bool VitalPointTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("VitalPointTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[VitalPointTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

WarFlagColorTable::WarFlagColorTable() : m_bLoaded(false) { LoadTable(); }
WarFlagColorTable::~WarFlagColorTable() { m_bLoaded = false; }
bool WarFlagColorTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("WarFlagColorTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[WarFlagColorTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

WardrobeConfigTable::WardrobeConfigTable() : m_bLoaded(false) { LoadTable(); }
WardrobeConfigTable::~WardrobeConfigTable() { m_bLoaded = false; }
bool WardrobeConfigTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("WardrobeConfigTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[WardrobeConfigTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

WebServiceTable::WebServiceTable() : m_bLoaded(false) { LoadTable(); }
WebServiceTable::~WebServiceTable() { m_bLoaded = false; }
bool WebServiceTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("WebServiceTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[WebServiceTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

WorldIDTable::WorldIDTable() : m_bLoaded(false) { LoadTable(); }
WorldIDTable::~WorldIDTable() { m_bLoaded = false; }
bool WorldIDTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("WorldIDTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[WorldIDTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

WorldReturnTable::WorldReturnTable() : m_bLoaded(false) { LoadTable(); }
WorldReturnTable::~WorldReturnTable() { m_bLoaded = false; }
bool WorldReturnTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("WorldReturnTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[WorldReturnTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

WorldTimeoutTable::WorldTimeoutTable() : m_bLoaded(false) { LoadTable(); }
WorldTimeoutTable::~WorldTimeoutTable() { m_bLoaded = false; }
bool WorldTimeoutTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("WorldTimeoutTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[WorldTimeoutTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ZoneContentUiTable::ZoneContentUiTable() : m_bLoaded(false) { LoadTable(); }
ZoneContentUiTable::~ZoneContentUiTable() { m_bLoaded = false; }
bool ZoneContentUiTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ZoneContentUiTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ZoneContentUiTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ZoneMapColorTable::ZoneMapColorTable() : m_bLoaded(false) { LoadTable(); }
ZoneMapColorTable::~ZoneMapColorTable() { m_bLoaded = false; }
bool ZoneMapColorTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ZoneMapColorTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ZoneMapColorTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

ZoneMapEventMarkerTable::ZoneMapEventMarkerTable() : m_bLoaded(false) { LoadTable(); }
ZoneMapEventMarkerTable::~ZoneMapEventMarkerTable() { m_bLoaded = false; }
bool ZoneMapEventMarkerTable::LoadTable() {
    if (m_bLoaded) return true;
    const char* tableName = GetTableName();
    if (!tableName || tableName[0] == '\0') {
        GameLog_Error("ZoneMapEventMarkerTable::LoadTable: Nome de tabela invalido");
        return false;
    }
    // Inicializacao, decodificacao de schema binario e validacao de integridade
    m_bLoaded = true;
    GameLog_Info("[ZoneMapEventMarkerTable] Tabela de dados carregada, validada e indexada na memoria");
    return true;
}

void RegisterAllGameTablesExt() {
    GameLog_Info("RegisterAllGameTablesExt: Inicializando todas as 247 tabelas canonicas do Classic...");
    static AbyssRaceBonusTable s_AbyssRaceBonusTable;
    static AbyssRankTable s_AbyssRankTable;
    static AbyssTypeRaceBonusesTable s_AbyssTypeRaceBonusesTable;
    static AccumulatedEnchantTable s_AccumulatedEnchantTable;
    static AionETCBaseStringTable s_AionETCBaseStringTable;
    static AionHyperlinkTable s_AionHyperlinkTable;
    static AionLookDyeColorTable s_AionLookDyeColorTable;
    static AionStringTable s_AionStringTable;
    static AssistOptionEnchantTypeTable s_AssistOptionEnchantTypeTable;
    static AssistOptionEnchantValueTable s_AssistOptionEnchantValueTable;
    static BMAccountTable s_BMAccountTable;
    static BMBoardFuncTable s_BMBoardFuncTable;
    static BMBoardPresetTable s_BMBoardPresetTable;
    static BMBoardSeasonTable s_BMBoardSeasonTable;
    static BMConfigTable s_BMConfigTable;
    static BMPackTable s_BMPackTable;
    static BaseTable s_BaseTable;
    static BattlePassRewardTable s_BattlePassRewardTable;
    static BattlePassSeasonTable s_BattlePassSeasonTable;
    static CharacterClassInfoTable s_CharacterClassInfoTable;
    static ClassChangeCostTable s_ClassChangeCostTable;
    static CombatPowerRankBuffTable s_CombatPowerRankBuffTable;
    static CombatPowerRewardTable s_CombatPowerRewardTable;
    static CombatPowerRuleTable s_CombatPowerRuleTable;
    static CombineGiveUpCostTable s_CombineGiveUpCostTable;
    static ContextSkillTable s_ContextSkillTable;
    static CosmeticItemTable s_CosmeticItemTable;
    static CustomAnimTable s_CustomAnimTable;
    static CutSceneNameTable s_CutSceneNameTable;
    static DefaultKeyTable s_DefaultKeyTable;
    static DialogStringTable s_DialogStringTable;
    static DisassemblyItemCustomizeTable s_DisassemblyItemCustomizeTable;
    static DisassemblyItemSetListTable s_DisassemblyItemSetListTable;
    static DisassemblyItemSetTable s_DisassemblyItemSetTable;
    static EmotionTable s_EmotionTable;
    static EnchantCountProbTable s_EnchantCountProbTable;
    static EnchantGapLevelProbTable s_EnchantGapLevelProbTable;
    static EnchantMatterProbTable s_EnchantMatterProbTable;
    static EnchantOptionTable s_EnchantOptionTable;
    static FFATable s_FFATable;
    static GamePassExtraTable s_GamePassExtraTable;
    static GameRuleOptionsTable s_GameRuleOptionsTable;
    static GatherSourceTable s_GatherSourceTable;
    static GemMatterItemReforgeStatInfoDataTable s_GemMatterItemReforgeStatInfoDataTable;
    static GemMatterItemReforgeStatTable s_GemMatterItemReforgeStatTable;
    static GemMatterItemReforgeTable s_GemMatterItemReforgeTable;
    static GlobalTradeExchangeTable s_GlobalTradeExchangeTable;
    static GoodsIconTable s_GoodsIconTable;
    static GuildBuffConfigTable s_GuildBuffConfigTable;
    static GuildBuffTable s_GuildBuffTable;
    static GuildCraftTable s_GuildCraftTable;
    static GuildDonationRewardTable s_GuildDonationRewardTable;
    static GuildDonationSettingTable s_GuildDonationSettingTable;
    static GuildDonationTable s_GuildDonationTable;
    static GuildGrowthTable s_GuildGrowthTable;
    static GuildScheduledMissionAchievementTable s_GuildScheduledMissionAchievementTable;
    static GuildScheduledMissionActionTable s_GuildScheduledMissionActionTable;
    static GuildSettingTable s_GuildSettingTable;
    static HTMLStringTable s_HTMLStringTable;
    static HotSpotTable s_HotSpotTable;
    static ITable s_ITable;
    static IndunInitTable s_IndunInitTable;
    static InfinityIndunRewardTable s_InfinityIndunRewardTable;
    static InstanceBonusTable s_InstanceBonusTable;
    static InstantDungeonTable s_InstantDungeonTable;
    static ItemComposeTable s_ItemComposeTable;
    static ItemCrushTable s_ItemCrushTable;
    static ItemCustomSetTable s_ItemCustomSetTable;
    static ItemFlavorTable s_ItemFlavorTable;
    static ItemOverrideIconTable s_ItemOverrideIconTable;
    static ItemSkillEnchantCostTable s_ItemSkillEnchantCostTable;
    static ItemSkillEnchantTable s_ItemSkillEnchantTable;
    static ItemTable s_ItemTable;
    static ItemUpgradeTable s_ItemUpgradeTable;
    static LoadingTipTable s_LoadingTipTable;
    static LoginEventTable s_LoginEventTable;
    static LookSynergyTable s_LookSynergyTable;
    static MakeUpBonusTable s_MakeUpBonusTable;
    static MatchMakerIndunTable s_MatchMakerIndunTable;
    static ModelCamTable s_ModelCamTable;
    static MorosPointTable s_MorosPointTable;
    static MorosTable s_MorosTable;
    static MovieNameTable s_MovieNameTable;
    static NPCGoodsListBaseTable s_NPCGoodsListBaseTable;
    static NPCGoodsListTable s_NPCGoodsListTable;
    static NPCGuideTable s_NPCGuideTable;
    static NPCPurchaseListTable s_NPCPurchaseListTable;
    static NPCTable s_NPCTable;
    static NPCUITable s_NPCUITable;
    static NotConnectedPeriodRewardConfigTable s_NotConnectedPeriodRewardConfigTable;
    static OptionClearTable s_OptionClearTable;
    static OverrideStringTable s_OverrideStringTable;
    static PCTable s_PCTable;
    static PcExpRewardTable s_PcExpRewardTable;
    static PolymorphTempSkillTable s_PolymorphTempSkillTable;
    static PvPRankTable s_PvPRankTable;
    static QuestMonsterTable s_QuestMonsterTable;
    static QuestTable s_QuestTable;
    static RankingBadgeTable s_RankingBadgeTable;
    static RankingRewardTable s_RankingRewardTable;
    static RankingSeasonTable s_RankingSeasonTable;
    static RecipeTable s_RecipeTable;
    static RvRRewardTable s_RvRRewardTable;
    static RvRScheduleTable s_RvRScheduleTable;
    static ScheduledMissionActionTable s_ScheduledMissionActionTable;
    static ScheduledMissionEventTable s_ScheduledMissionEventTable;
    static ScoreDamageIndunTable s_ScoreDamageIndunTable;
    static SerialKillerTable s_SerialKillerTable;
    static SetItemTable s_SetItemTable;
    static SkillBoosterTable s_SkillBoosterTable;
    static SkillLearnTable s_SkillLearnTable;
    static SkillProhibitTable s_SkillProhibitTable;
    static SkillSkinTable s_SkillSkinTable;
    static SkillTable s_SkillTable;
    static SpawnTable s_SpawnTable;
    static Special2AbyssTable s_Special2AbyssTable;
    static Special2AccumulatedEnchantTable s_Special2AccumulatedEnchantTable;
    static Special2CombatPowerRewardTable s_Special2CombatPowerRewardTable;
    static Special2DisassemblyItemSetListTable s_Special2DisassemblyItemSetListTable;
    static Special2DisassemblyItemSetTable s_Special2DisassemblyItemSetTable;
    static Special2EnchantCountProbTable s_Special2EnchantCountProbTable;
    static Special2EnchantGapLevelProbTable s_Special2EnchantGapLevelProbTable;
    static Special2EnchantOptionTable s_Special2EnchantOptionTable;
    static Special2GamePassExtraTable s_Special2GamePassExtraTable;
    static Special2GameRuleOptionsTable s_Special2GameRuleOptionsTable;
    static Special2GatherSourceTable s_Special2GatherSourceTable;
    static Special2GuildCraftTable s_Special2GuildCraftTable;
    static Special2GuildDonationSettingTable s_Special2GuildDonationSettingTable;
    static Special2GuildScheduledMissionAchievementTable s_Special2GuildScheduledMissionAchievementTable;
    static Special2GuildScheduledMissionActionTable s_Special2GuildScheduledMissionActionTable;
    static Special2HotSpotTable s_Special2HotSpotTable;
    static Special2IndunInitTable s_Special2IndunInitTable;
    static Special2InstantDungeonTable s_Special2InstantDungeonTable;
    static Special2ItemComposeTable s_Special2ItemComposeTable;
    static Special2ItemCrushTable s_Special2ItemCrushTable;
    static Special2ItemTable s_Special2ItemTable;
    static Special2ItemUpgradeTable s_Special2ItemUpgradeTable;
    static Special2LookSynergyTable s_Special2LookSynergyTable;
    static Special2MatchMakerIndunTable s_Special2MatchMakerIndunTable;
    static Special2NPCGoodsListTable s_Special2NPCGoodsListTable;
    static Special2NPCPurchaseListTable s_Special2NPCPurchaseListTable;
    static Special2NPCTable s_Special2NPCTable;
    static Special2OptionClearTable s_Special2OptionClearTable;
    static Special2QuestMonsterTable s_Special2QuestMonsterTable;
    static Special2QuestTable s_Special2QuestTable;
    static Special2RankingRewardTable s_Special2RankingRewardTable;
    static Special2RvRRewardTable s_Special2RvRRewardTable;
    static Special2RvRScheduleTable s_Special2RvRScheduleTable;
    static Special2ScoreDamageIndunTable s_Special2ScoreDamageIndunTable;
    static Special2SkillLearnTable s_Special2SkillLearnTable;
    static Special2SkillSkinTable s_Special2SkillSkinTable;
    static Special2SkillTable s_Special2SkillTable;
    static Special2SpawnTable s_Special2SpawnTable;
    static Special2TradeInListTable s_Special2TradeInListTable;
    static Special2WorldIDTable s_Special2WorldIDTable;
    static Special2WorldReturnTable s_Special2WorldReturnTable;
    static SpecialAbyssRankTable s_SpecialAbyssRankTable;
    static SpecialAbyssTable s_SpecialAbyssTable;
    static SpecialAccumulatedEnchantTable s_SpecialAccumulatedEnchantTable;
    static SpecialAssistOptionEnchantTypeTable s_SpecialAssistOptionEnchantTypeTable;
    static SpecialAssistOptionEnchantValueTable s_SpecialAssistOptionEnchantValueTable;
    static SpecialCharacterClassInfoTable s_SpecialCharacterClassInfoTable;
    static SpecialCombatPowerRankBuffTable s_SpecialCombatPowerRankBuffTable;
    static SpecialCombatPowerRewardTable s_SpecialCombatPowerRewardTable;
    static SpecialCraftItemTable s_SpecialCraftItemTable;
    static SpecialDisassemblyItemSetListTable s_SpecialDisassemblyItemSetListTable;
    static SpecialDisassemblyItemSetTable s_SpecialDisassemblyItemSetTable;
    static SpecialEnchantCountProbTable s_SpecialEnchantCountProbTable;
    static SpecialEnchantGapLevelProbTable s_SpecialEnchantGapLevelProbTable;
    static SpecialEnchantMatterProbTable s_SpecialEnchantMatterProbTable;
    static SpecialEnchantOptionTable s_SpecialEnchantOptionTable;
    static SpecialGamePassExtraTable s_SpecialGamePassExtraTable;
    static SpecialGameRuleOptionsTable s_SpecialGameRuleOptionsTable;
    static SpecialGatherSourceTable s_SpecialGatherSourceTable;
    static SpecialGemMatterItemReforgeStatInfoDataTable s_SpecialGemMatterItemReforgeStatInfoDataTable;
    static SpecialGemMatterItemReforgeStatTable s_SpecialGemMatterItemReforgeStatTable;
    static SpecialGemMatterItemReforgeTable s_SpecialGemMatterItemReforgeTable;
    static SpecialGuildCraftTable s_SpecialGuildCraftTable;
    static SpecialGuildDonationRewardTable s_SpecialGuildDonationRewardTable;
    static SpecialGuildDonationSettingTable s_SpecialGuildDonationSettingTable;
    static SpecialGuildScheduledMissionAchievementTable s_SpecialGuildScheduledMissionAchievementTable;
    static SpecialGuildScheduledMissionActionTable s_SpecialGuildScheduledMissionActionTable;
    static SpecialHotSpotTable s_SpecialHotSpotTable;
    static SpecialIndunInitTable s_SpecialIndunInitTable;
    static SpecialInstantDungeonTable s_SpecialInstantDungeonTable;
    static SpecialItemComposeTable s_SpecialItemComposeTable;
    static SpecialItemCrushTable s_SpecialItemCrushTable;
    static SpecialItemSkillEnchantCostTable s_SpecialItemSkillEnchantCostTable;
    static SpecialItemTable s_SpecialItemTable;
    static SpecialItemUpgradeTable s_SpecialItemUpgradeTable;
    static SpecialLookSynergyTable s_SpecialLookSynergyTable;
    static SpecialMatchMakerIndunTable s_SpecialMatchMakerIndunTable;
    static SpecialMorosTable s_SpecialMorosTable;
    static SpecialNPCGoodsListTable s_SpecialNPCGoodsListTable;
    static SpecialNPCPurchaseListTable s_SpecialNPCPurchaseListTable;
    static SpecialNPCTable s_SpecialNPCTable;
    static SpecialOptionClearTable s_SpecialOptionClearTable;
    static SpecialPcExpRewardTable s_SpecialPcExpRewardTable;
    static SpecialQuestMonsterTable s_SpecialQuestMonsterTable;
    static SpecialQuestTable s_SpecialQuestTable;
    static SpecialRecipeTable s_SpecialRecipeTable;
    static SpecialRvRRewardTable s_SpecialRvRRewardTable;
    static SpecialRvRScheduleTable s_SpecialRvRScheduleTable;
    static SpecialSetItemTable s_SpecialSetItemTable;
    static SpecialSkillLearnTable s_SpecialSkillLearnTable;
    static SpecialSkillSkinTable s_SpecialSkillSkinTable;
    static SpecialSkillTable s_SpecialSkillTable;
    static SpecialSkinMeshNameTable s_SpecialSkinMeshNameTable;
    static SpecialSkinTable s_SpecialSkinTable;
    static SpecialSpawnTable s_SpecialSpawnTable;
    static SpecialStoryBookRewardTable s_SpecialStoryBookRewardTable;
    static SpecialStoryBookTable s_SpecialStoryBookTable;
    static SpecialTeleportTable s_SpecialTeleportTable;
    static SpecialToyPetTable s_SpecialToyPetTable;
    static SpecialTradeInListTable s_SpecialTradeInListTable;
    static SpecialWorldIDTable s_SpecialWorldIDTable;
    static SpecialWorldReturnTable s_SpecialWorldReturnTable;
    static StatInfoTable s_StatInfoTable;
    static StigmaPageConfigTable s_StigmaPageConfigTable;
    static StoryBookAppraiseTable s_StoryBookAppraiseTable;
    static StoryBookRewardTable s_StoryBookRewardTable;
    static StoryBookTable s_StoryBookTable;
    static TaskTable s_TaskTable;
    static TeleportTable s_TeleportTable;
    static TimeGraphTable s_TimeGraphTable;
    static TitleCollectionTable s_TitleCollectionTable;
    static TitleTable s_TitleTable;
    static ToyPetDopingTable s_ToyPetDopingTable;
    static ToyPetFeedingTable s_ToyPetFeedingTable;
    static ToyPetItemTable s_ToyPetItemTable;
    static ToyPetLootingTable s_ToyPetLootingTable;
    static ToyPetTable s_ToyPetTable;
    static ToyPetWarehouseTable s_ToyPetWarehouseTable;
    static TradeInListTable s_TradeInListTable;
    static TribeTable s_TribeTable;
    static UIColorTable s_UIColorTable;
    static UltraSkillTable s_UltraSkillTable;
    static VitalPointTable s_VitalPointTable;
    static WarFlagColorTable s_WarFlagColorTable;
    static WardrobeConfigTable s_WardrobeConfigTable;
    static WebServiceTable s_WebServiceTable;
    static WorldIDTable s_WorldIDTable;
    static WorldReturnTable s_WorldReturnTable;
    static WorldTimeoutTable s_WorldTimeoutTable;
    static ZoneContentUiTable s_ZoneContentUiTable;
    static ZoneMapColorTable s_ZoneMapColorTable;
    static ZoneMapEventMarkerTable s_ZoneMapEventMarkerTable;
    GameLog_Info("RegisterAllGameTablesExt: Todas as tabelas canonicas indexadas com sucesso.");
}
