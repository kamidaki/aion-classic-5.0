#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include "../ui/AddonFrame.h"

// -------------------------------------------------------------
// 5.1 Tipos de Missões
// -------------------------------------------------------------
enum class EQuestType : uint8_t {
    CAMPAIGN       = 0, // Missões de Campanha (Douradas - enredo principal com cutscene)
    NORMAL         = 1, // Missões Normais (Azuis - secundárias de postos)
    REPEATABLE     = 2, // Missões Repetíveis (Moedas: Bronze, Prata, Ouro, Platina)
    WORK_ORDER     = 3  // Ordens de Trabalho de Ofício (Crafting temporárias)
};

enum class QuestObjectiveType : uint8_t {
    KILL_NPC        = 0,
    COLLECT_ITEM    = 1,
    VISIT_LOCATION  = 2,
    USE_QUEST_ITEM  = 3
};

struct QuestObjective {
    QuestObjectiveType type;
    uint32_t           targetId;       // NpcId ou ItemId
    uint32_t           requiredCount;  // Quantidade alvo
    uint32_t           currentCount;   // Progresso atual
    float              targetX, targetY, targetZ; // Coordenadas para VISIT_LOCATION
    uint32_t           targetMapId;
};

struct QuestStep {
    uint32_t                    stepNumber;
    std::string                 description;
    std::vector<QuestObjective> objectives;
    bool                        isStepFinished;
};

struct QuestReward {
    int64_t               expReward;
    int64_t               kinahReward;
    uint32_t              apReward;
    uint32_t              titleRewardId; // Concessão de título
    std::vector<uint32_t> fixedItemIds;
    std::vector<uint32_t> selectableItemIds;
};

struct QuestTemplate {
    uint32_t                questId;
    std::string             title;
    EQuestType              type;
    uint32_t                minLevel;
    uint32_t                maxLevel;
    uint8_t                 requiredRace;  // 0: Elyos, 1: Asmodian, 2: Ambas
    uint8_t                 requiredClass; // 255: Qualquer classe
    uint32_t                prerequisiteQuestId;
    uint32_t                cutsceneId;    // Cutscene obrigatória se campanha
    uint32_t                maxRepeatCount; // > 1 para repetíveis
    std::vector<QuestStep>  steps;
    QuestReward             reward;
};

struct PlayerQuestState {
    uint32_t questId;
    uint32_t currentStep;
    uint32_t repeatCount;
    bool     isCompleted;
    std::vector<QuestObjective> currentObjectives;
};

// -------------------------------------------------------------
// 5.3 Parser de HTML e Hiperlinks em Diálogos
// -------------------------------------------------------------
struct ParsedHyperlink {
    std::string type; // "item", "pos", "quest"
    uint32_t    id;
    std::string label;
    uint32_t    mapId;
    float       x, y, z;
};

class DialogHtmlParser {
public:
    static std::string StripHtmlTags(const std::string& html);
    static std::vector<ParsedHyperlink> ExtractHyperlinks(const std::string& text);
    static std::string FormatItemLink(uint32_t itemId, const std::string& itemName);
    static std::string FormatPosLink(const std::string& posName, uint32_t mapId, float x, float y, float z);
    static std::string FormatQuestLink(uint32_t questId, const std::string& questTitle);
};

// -------------------------------------------------------------
// 5.2 Máquina de Passos de Missão (Quest Step Machine)
// -------------------------------------------------------------
class QuestStepMachine {
public:
    static QuestStepMachine& GetInstance();

    QuestStepMachine();
    ~QuestStepMachine();

    void InitializeTemplates();
    void RegisterTemplate(const QuestTemplate& tmpl);
    const QuestTemplate* GetTemplate(uint32_t questId) const;

    // 5.2.1 Verificação de Pré-requisitos
    bool CanAcceptQuest(uint32_t playerId, uint32_t questId, uint32_t playerLevel, uint8_t playerRace, uint8_t playerClass, std::string& outReason) const;

    // Início de Missão
    bool StartQuest(uint32_t playerId, uint32_t questId);

    // 5.2.2 Rastreamento de Objetivos
    bool NotifyNpcKilled(uint32_t playerId, uint32_t npcId);
    bool NotifyItemCollected(uint32_t playerId, uint32_t itemId, uint32_t count);
    bool NotifyLocationReached(uint32_t playerId, uint32_t mapId, float x, float y, float z);
    bool NotifyQuestItemUsed(uint32_t playerId, uint32_t itemId);

    // 5.2.3 Recompensas e Conclusão
    bool CompleteQuest(uint32_t playerId, uint32_t questId, int32_t selectedRewardIndex, QuestReward& outReward);

    const PlayerQuestState* GetPlayerQuest(uint32_t playerId, uint32_t questId) const;
    bool HasCompletedQuest(uint32_t playerId, uint32_t questId) const;

private:
    std::unordered_map<uint32_t, QuestTemplate> m_templates;
    // Map: (playerId << 32) | questId -> PlayerQuestState
    std::unordered_map<uint64_t, PlayerQuestState> m_playerQuests;
    // Map: (playerId << 32) | questId -> true se concluída
    std::unordered_map<uint64_t, bool> m_completedQuests;

    uint64_t MakeKey(uint32_t playerId, uint32_t questId) const {
        return (static_cast<uint64_t>(playerId) << 32) | questId;
    }
};

// -------------------------------------------------------------
// RTTI Classes Preservadas
// -------------------------------------------------------------

// Manipulador de passos numéricos de missões (.?AVQuestNumHandler@@)
class QuestNumHandler {
public:
    QuestNumHandler();
    ~QuestNumHandler();

    void SetStep(uint32_t questId, uint32_t step);
    uint32_t GetStep(uint32_t questId) const;

private:
    std::unordered_map<uint32_t, uint32_t> m_questSteps;
};

// Aba base de missões na interface (.?AVQuestTabFrame@@)
class QuestTabFrame : public AddonFrame {
public:
    QuestTabFrame(const std::string& name);
    virtual ~QuestTabFrame();

    virtual void RefreshQuests() = 0;
};

// Aba de missões ativas em andamento (.?AVQuestTabFrame_Working@@)
class QuestTabFrame_Working : public QuestTabFrame {
public:
    QuestTabFrame_Working();
    virtual ~QuestTabFrame_Working();

    virtual void RefreshQuests() override;
    void AddWorkingQuest(uint32_t questId, const std::string& title);

private:
    std::vector<std::pair<uint32_t, std::string>> m_activeQuests;
};

// Aba de missões concluídas (.?AVQuestTabFrame_Finished@@)
class QuestTabFrame_Finished : public QuestTabFrame {
public:
    QuestTabFrame_Finished();
    virtual ~QuestTabFrame_Finished();

    virtual void RefreshQuests() override;
    void AddFinishedQuest(uint32_t questId, const std::string& title);

private:
    std::vector<std::pair<uint32_t, std::string>> m_finishedQuests;
};

// Gerenciador de títulos do jogador (.?AVTitleDBWrapper@@)
class TitleDBWrapper {
public:
    TitleDBWrapper();
    ~TitleDBWrapper();

    bool LoadTitles();
    bool HasTitle(uint32_t titleId) const;
    void GrantTitle(uint32_t titleId);

private:
    std::unordered_map<uint32_t, bool> m_unlockedTitles;
};
