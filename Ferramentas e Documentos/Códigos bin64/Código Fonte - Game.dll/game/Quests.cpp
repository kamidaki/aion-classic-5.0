#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include "Quests.h"
#include "../core/GameLog.h"
#include <regex>
#include <sstream>
#include <cmath>

// -------------------------------------------------------------
// 5.3 DialogHtmlParser
// -------------------------------------------------------------
std::string DialogHtmlParser::StripHtmlTags(const std::string& html) {
    std::regex tagRegex("<[^>]*>");
    return std::regex_replace(html, tagRegex, "");
}

std::vector<ParsedHyperlink> DialogHtmlParser::ExtractHyperlinks(const std::string& text) {
    std::vector<ParsedHyperlink> links;
    // Regex para [item:ID], [pos:Nome;Mapa;X;Y;Z], [quest:ID]
    std::regex linkRegex("\\[(item|pos|quest):([^\\]]+)\\]");
    auto words_begin = std::sregex_iterator(text.begin(), text.end(), linkRegex);
    auto words_end = std::sregex_iterator();

    for (std::sregex_iterator i = words_begin; i != words_end; ++i) {
        std::smatch match = *i;
        std::string type = match[1].str();
        std::string payload = match[2].str();

        ParsedHyperlink link = {};
        link.type = type;

        if (type == "item") {
            link.id = static_cast<uint32_t>(std::stoul(payload));
        } else if (type == "quest") {
            link.id = static_cast<uint32_t>(std::stoul(payload));
        } else if (type == "pos") {
            // Formato: Nome;MapaId;X;Y;Z
            std::stringstream ss(payload);
            std::string segment;
            std::vector<std::string> parts;
            while (std::getline(ss, segment, ';')) {
                parts.push_back(segment);
            }
            if (parts.size() >= 5) {
                link.label = parts[0];
                link.mapId = static_cast<uint32_t>(std::stoul(parts[1]));
                link.x = std::stof(parts[2]);
                link.y = std::stof(parts[3]);
                link.z = std::stof(parts[4]);
            }
        }
        links.push_back(link);
    }
    return links;
}

std::string DialogHtmlParser::FormatItemLink(uint32_t itemId, const std::string& itemName) {
    return "[item:" + std::to_string(itemId) + "]";
}

std::string DialogHtmlParser::FormatPosLink(const std::string& posName, uint32_t mapId, float x, float y, float z) {
    char buf[128];
    snprintf(buf, sizeof(buf), "[pos:%s;%u;%.1f;%.1f;%.1f]", posName.c_str(), mapId, x, y, z);
    return std::string(buf);
}

std::string DialogHtmlParser::FormatQuestLink(uint32_t questId, const std::string& questTitle) {
    return "[quest:" + std::to_string(questId) + "]";
}

// -------------------------------------------------------------
// 5.2 QuestStepMachine
// -------------------------------------------------------------
QuestStepMachine& QuestStepMachine::GetInstance() {
    static QuestStepMachine s_instance;
    return s_instance;
}

QuestStepMachine::QuestStepMachine() {
    InitializeTemplates();
    GameLog_Info("QuestStepMachine: Motor de Quests, Campanhas e Diálogos inicializado.");
}

QuestStepMachine::~QuestStepMachine() {}

void QuestStepMachine::RegisterTemplate(const QuestTemplate& tmpl) {
    m_templates[tmpl.questId] = tmpl;
}

const QuestTemplate* QuestStepMachine::GetTemplate(uint32_t questId) const {
    auto it = m_templates.find(questId);
    if (it != m_templates.end()) {
        return &it->second;
    }
    return nullptr;
}

void QuestStepMachine::InitializeTemplates() {
    // 5.1.1 Missão de Campanha Dourada (Ascension - Nível 9)
    QuestTemplate camp1 = {};
    camp1.questId = 1001;
    camp1.title = "A Ascensao de um Daeva";
    camp1.type = EQuestType::CAMPAIGN;
    camp1.minLevel = 9;
    camp1.maxLevel = 55;
    camp1.requiredRace = 0; // Elyos
    camp1.requiredClass = 255; // Qualquer
    camp1.cutsceneId = 101; // Cutscene da transformação
    camp1.maxRepeatCount = 1;

    // Passo 1: Eliminar 3 Kerubiels
    QuestStep step1 = {};
    step1.stepNumber = 1;
    step1.description = "Derrote 3 Ladroes Kerubiel no bosque.";
    QuestObjective obj1 = { QuestObjectiveType::KILL_NPC, 210001, 3, 0, 0, 0, 0, 0 };
    step1.objectives.push_back(obj1);
    camp1.steps.push_back(step1);

    // Passo 2: Visitar Pernos em coordenadas sagradas
    QuestStep step2 = {};
    step2.stepNumber = 2;
    step2.description = "Encontre o Eremita Pernos na Ilha Cliona.";
    QuestObjective obj2 = { QuestObjectiveType::VISIT_LOCATION, 0, 1, 0, 150.0f, 220.0f, 75.0f, 210010000 };
    step2.objectives.push_back(obj2);
    camp1.steps.push_back(step2);

    camp1.reward.expReward = 50000;
    camp1.reward.kinahReward = 10000;
    camp1.reward.apReward = 0;
    camp1.reward.titleRewardId = 10; // Título "Daeva Ascendido"
    camp1.reward.fixedItemIds = { 10000001 }; // Asas Básicas
    RegisterTemplate(camp1);

    // 5.1.2 Missão Normal Azul
    QuestTemplate norm1 = {};
    norm1.questId = 1050;
    norm1.title = "Alerta de Cacadores";
    norm1.type = EQuestType::NORMAL;
    norm1.minLevel = 12;
    norm1.maxLevel = 25;
    norm1.requiredRace = 0;
    norm1.requiredClass = 255;
    norm1.maxRepeatCount = 1;

    QuestStep nStep1 = {};
    nStep1.stepNumber = 1;
    nStep1.description = "Colete 5 Peles de Lobo.";
    QuestObjective nObj1 = { QuestObjectiveType::COLLECT_ITEM, 18200050, 5, 0, 0, 0, 0, 0 };
    nStep1.objectives.push_back(nObj1);
    norm1.steps.push_back(nStep1);

    norm1.reward.expReward = 15000;
    norm1.reward.kinahReward = 2500;
    RegisterTemplate(norm1);

    // 5.1.3 Missão Repetível de Moeda (Coin Quest)
    QuestTemplate rep1 = {};
    rep1.questId = 1100;
    rep1.title = "Dever de Guarda: Moedas de Bronze";
    rep1.type = EQuestType::REPEATABLE;
    rep1.minLevel = 20;
    rep1.maxLevel = 30;
    rep1.requiredRace = 0;
    rep1.requiredClass = 255;
    rep1.maxRepeatCount = 10; // Repetível 10 vezes

    QuestStep rStep1 = {};
    rStep1.stepNumber = 1;
    rStep1.description = "Derrote 10 Guardas Krall.";
    QuestObjective rObj1 = { QuestObjectiveType::KILL_NPC, 210100, 10, 0, 0, 0, 0, 0 };
    rStep1.objectives.push_back(rObj1);
    rep1.steps.push_back(rStep1);

    rep1.reward.expReward = 25000;
    rep1.reward.kinahReward = 5000;
    rep1.reward.fixedItemIds = { 186000001 }; // 1 Moeda de Bronze
    RegisterTemplate(rep1);

    // 5.1.4 Ordem de Trabalho de Ofício (Work Order)
    QuestTemplate wo1 = {};
    wo1.questId = 1200;
    wo1.title = "Ordem de Trabalho: Forja de Armas";
    wo1.type = EQuestType::WORK_ORDER;
    wo1.minLevel = 10;
    wo1.maxLevel = 50;
    wo1.requiredRace = 0;
    wo1.requiredClass = 255;
    wo1.maxRepeatCount = 999;

    QuestStep wStep1 = {};
    wStep1.stepNumber = 1;
    wStep1.description = "Forje 3 Adagas Simples usando a bancada.";
    QuestObjective wObj1 = { QuestObjectiveType::USE_QUEST_ITEM, 18200099, 3, 0, 0, 0, 0, 0 };
    wStep1.objectives.push_back(wObj1);
    wo1.steps.push_back(wStep1);

    wo1.reward.expReward = 8000;
    wo1.reward.kinahReward = 1200;
    RegisterTemplate(wo1);
}

bool QuestStepMachine::CanAcceptQuest(uint32_t playerId, uint32_t questId, uint32_t playerLevel, uint8_t playerRace, uint8_t playerClass, std::string& outReason) const {
    const QuestTemplate* tmpl = GetTemplate(questId);
    if (!tmpl) {
        outReason = "Missao inexistente.";
        return false;
    }

    if (playerLevel < tmpl->minLevel) {
        outReason = "Nivel insuficiente.";
        return false;
    }

    if (playerLevel > tmpl->maxLevel) {
        outReason = "Nivel acima do limite maximo permitido.";
        return false;
    }

    if (tmpl->requiredRace != 2 && tmpl->requiredRace != playerRace) {
        outReason = "Missao indisponivel para a sua raca.";
        return false;
    }

    if (tmpl->requiredClass != 255 && tmpl->requiredClass != playerClass) {
        outReason = "Missao indisponivel para a sua classe.";
        return false;
    }

    if (tmpl->prerequisiteQuestId > 0 && !HasCompletedQuest(playerId, tmpl->prerequisiteQuestId)) {
        outReason = "Missao previa obrigatoria nao concluida.";
        return false;
    }

    uint64_t key = MakeKey(playerId, questId);
    auto itActive = m_playerQuests.find(key);
    if (itActive != m_playerQuests.end() && !itActive->second.isCompleted) {
        outReason = "Missao ja se encontra em andamento.";
        return false;
    }

    auto itComp = m_completedQuests.find(key);
    if (itComp != m_completedQuests.end() && itComp->second) {
        if (itActive != m_playerQuests.end() && itActive->second.repeatCount >= tmpl->maxRepeatCount) {
            outReason = "Limite maximo de repeticoes alcancado.";
            return false;
        }
    }

    return true;
}

bool QuestStepMachine::StartQuest(uint32_t playerId, uint32_t questId) {
    const QuestTemplate* tmpl = GetTemplate(questId);
    if (!tmpl || tmpl->steps.empty()) return false;

    uint64_t key = MakeKey(playerId, questId);
    PlayerQuestState state = {};
    state.questId = questId;
    state.currentStep = 1;
    state.isCompleted = false;

    // Inicializa objetivos do Passo 1
    state.currentObjectives = tmpl->steps[0].objectives;
    m_playerQuests[key] = state;

    GameLog_Info("QuestStepMachine: Jogador %u aceitou Missao %u ('%s')", playerId, questId, tmpl->title.c_str());
    return true;
}

bool QuestStepMachine::NotifyNpcKilled(uint32_t playerId, uint32_t npcId) {
    bool progressMade = false;
    for (auto& pair : m_playerQuests) {
        uint32_t pId = static_cast<uint32_t>(pair.first >> 32);
        if (pId != playerId) continue;

        PlayerQuestState& qState = pair.second;
        if (qState.isCompleted) continue;

        const QuestTemplate* tmpl = GetTemplate(qState.questId);
        if (!tmpl) continue;

        for (auto& obj : qState.currentObjectives) {
            if (obj.type == QuestObjectiveType::KILL_NPC && obj.targetId == npcId) {
                if (obj.currentCount < obj.requiredCount) {
                    obj.currentCount++;
                    progressMade = true;
                    GameLog_Info("Quest %u: Abate de NPC %u (%u/%u)", qState.questId, npcId, obj.currentCount, obj.requiredCount);
                }
            }
        }

        // Verifica avanço de passo
        bool allDone = true;
        for (const auto& obj : qState.currentObjectives) {
            if (obj.currentCount < obj.requiredCount) {
                allDone = false;
                break;
            }
        }

        if (allDone) {
            if (qState.currentStep < tmpl->steps.size()) {
                qState.currentStep++;
                qState.currentObjectives = tmpl->steps[qState.currentStep - 1].objectives;
                GameLog_Info("Quest %u: Avancou para o Passo %u", qState.questId, qState.currentStep);
            }
        }
    }
    return progressMade;
}

bool QuestStepMachine::NotifyItemCollected(uint32_t playerId, uint32_t itemId, uint32_t count) {
    bool progressMade = false;
    for (auto& pair : m_playerQuests) {
        uint32_t pId = static_cast<uint32_t>(pair.first >> 32);
        if (pId != playerId) continue;

        PlayerQuestState& qState = pair.second;
        if (qState.isCompleted) continue;

        const QuestTemplate* tmpl = GetTemplate(qState.questId);
        if (!tmpl) continue;

        for (auto& obj : qState.currentObjectives) {
            if (obj.type == QuestObjectiveType::COLLECT_ITEM && obj.targetId == itemId) {
                obj.currentCount = (std::min)(obj.requiredCount, obj.currentCount + count);
                progressMade = true;
                GameLog_Info("Quest %u: Item coletado %u (%u/%u)", qState.questId, itemId, obj.currentCount, obj.requiredCount);
            }
        }

        bool allDone = true;
        for (const auto& obj : qState.currentObjectives) {
            if (obj.currentCount < obj.requiredCount) {
                allDone = false;
                break;
            }
        }

        if (allDone && qState.currentStep < tmpl->steps.size()) {
            qState.currentStep++;
            qState.currentObjectives = tmpl->steps[qState.currentStep - 1].objectives;
        }
    }
    return progressMade;
}

bool QuestStepMachine::NotifyLocationReached(uint32_t playerId, uint32_t mapId, float x, float y, float z) {
    bool progressMade = false;
    for (auto& pair : m_playerQuests) {
        uint32_t pId = static_cast<uint32_t>(pair.first >> 32);
        if (pId != playerId) continue;

        PlayerQuestState& qState = pair.second;
        if (qState.isCompleted) continue;

        const QuestTemplate* tmpl = GetTemplate(qState.questId);
        if (!tmpl) continue;

        for (auto& obj : qState.currentObjectives) {
            if (obj.type == QuestObjectiveType::VISIT_LOCATION && obj.targetMapId == mapId) {
                float dx = x - obj.targetX;
                float dy = y - obj.targetY;
                float dz = z - obj.targetZ;
                float dist = std::sqrt(dx * dx + dy * dy + dz * dz);
                if (dist <= 15.0f) { // Raio de chegada 15 metros
                    obj.currentCount = 1;
                    progressMade = true;
                    GameLog_Info("Quest %u: Localizacao visitada com sucesso!", qState.questId);
                }
            }
        }

        bool allDone = true;
        for (const auto& obj : qState.currentObjectives) {
            if (obj.currentCount < obj.requiredCount) {
                allDone = false;
                break;
            }
        }

        if (allDone && qState.currentStep < tmpl->steps.size()) {
            qState.currentStep++;
            qState.currentObjectives = tmpl->steps[qState.currentStep - 1].objectives;
        }
    }
    return progressMade;
}

bool QuestStepMachine::NotifyQuestItemUsed(uint32_t playerId, uint32_t itemId) {
    bool progressMade = false;
    for (auto& pair : m_playerQuests) {
        uint32_t pId = static_cast<uint32_t>(pair.first >> 32);
        if (pId != playerId) continue;

        PlayerQuestState& qState = pair.second;
        if (qState.isCompleted) continue;

        for (auto& obj : qState.currentObjectives) {
            if (obj.type == QuestObjectiveType::USE_QUEST_ITEM && obj.targetId == itemId) {
                if (obj.currentCount < obj.requiredCount) {
                    obj.currentCount++;
                    progressMade = true;
                }
            }
        }
    }
    return progressMade;
}

bool QuestStepMachine::CompleteQuest(uint32_t playerId, uint32_t questId, int32_t selectedRewardIndex, QuestReward& outReward) {
    uint64_t key = MakeKey(playerId, questId);
    auto it = m_playerQuests.find(key);
    if (it == m_playerQuests.end() || it->second.isCompleted) {
        return false;
    }

    const QuestTemplate* tmpl = GetTemplate(questId);
    if (!tmpl) return false;

    // Valida se todos os objetivos do último passo foram cumpridos
    for (const auto& obj : it->second.currentObjectives) {
        if (obj.currentCount < obj.requiredCount) {
            return false;
        }
    }

    it->second.isCompleted = true;
    it->second.repeatCount++;
    m_completedQuests[key] = true;

    outReward = tmpl->reward;
    GameLog_Info("QuestStepMachine: Jogador %u CONCLUIU Missao %u ('%s')! Exp=%lld Kinah=%lld",
        playerId, questId, tmpl->title.c_str(), outReward.expReward, outReward.kinahReward);
    return true;
}

const PlayerQuestState* QuestStepMachine::GetPlayerQuest(uint32_t playerId, uint32_t questId) const {
    uint64_t key = MakeKey(playerId, questId);
    auto it = m_playerQuests.find(key);
    if (it != m_playerQuests.end()) {
        return &it->second;
    }
    return nullptr;
}

bool QuestStepMachine::HasCompletedQuest(uint32_t playerId, uint32_t questId) const {
    uint64_t key = MakeKey(playerId, questId);
    auto it = m_completedQuests.find(key);
    return (it != m_completedQuests.end() && it->second);
}

// -------------------------------------------------------------
// RTTI Classes Preservadas
// -------------------------------------------------------------
QuestNumHandler::QuestNumHandler() {}
QuestNumHandler::~QuestNumHandler() { m_questSteps.clear(); }
void QuestNumHandler::SetStep(uint32_t questId, uint32_t step) {
    m_questSteps[questId] = step;
    GameLog_Info("QuestNumHandler: Quest=%u Step=%u", questId, step);
}
uint32_t QuestNumHandler::GetStep(uint32_t questId) const {
    auto it = m_questSteps.find(questId);
    return it != m_questSteps.end() ? it->second : 0;
}

QuestTabFrame::QuestTabFrame(const std::string& name) : AddonFrame(name) {}
QuestTabFrame::~QuestTabFrame() {}

QuestTabFrame_Working::QuestTabFrame_Working() : QuestTabFrame("QuestTabFrame_Working") {}
QuestTabFrame_Working::~QuestTabFrame_Working() { m_activeQuests.clear(); }
void QuestTabFrame_Working::RefreshQuests() {
    GameLog_Info("QuestTabFrame_Working: Atualizando %zu missões ativas.", m_activeQuests.size());
}
void QuestTabFrame_Working::AddWorkingQuest(uint32_t questId, const std::string& title) {
    m_activeQuests.push_back({ questId, title });
}

QuestTabFrame_Finished::QuestTabFrame_Finished() : QuestTabFrame("QuestTabFrame_Finished") {}
QuestTabFrame_Finished::~QuestTabFrame_Finished() { m_finishedQuests.clear(); }
void QuestTabFrame_Finished::RefreshQuests() {
    GameLog_Info("QuestTabFrame_Finished: Atualizando %zu missões concluídas.", m_finishedQuests.size());
}
void QuestTabFrame_Finished::AddFinishedQuest(uint32_t questId, const std::string& title) {
    m_finishedQuests.push_back({ questId, title });
}

TitleDBWrapper::TitleDBWrapper() { LoadTitles(); }
TitleDBWrapper::~TitleDBWrapper() { m_unlockedTitles.clear(); }
bool TitleDBWrapper::LoadTitles() {
    m_unlockedTitles.clear();
    m_unlockedTitles[1] = true; // Título padrão
    return true;
}
bool TitleDBWrapper::HasTitle(uint32_t titleId) const {
    auto it = m_unlockedTitles.find(titleId);
    return it != m_unlockedTitles.end() && it->second;
}
void TitleDBWrapper::GrantTitle(uint32_t titleId) {
    m_unlockedTitles[titleId] = true;
    GameLog_Info("TitleDBWrapper: Título concedido: %u", titleId);
}
