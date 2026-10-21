#include "SkillEngine.h"
#include "CombatEngine.h"
#include "../core/GameLog.h"
#include <algorithm>
#include <cstdlib>

SkillEngine& SkillEngine::GetInstance() {
    static SkillEngine s_instance;
    return s_instance;
}

SkillEngine::SkillEngine() {
    InitializeSkills();
    GameLog_Info("SkillEngine: Motor de habilidades, chains, DP e estigmas inicializado.");
}

SkillEngine::~SkillEngine() {
}

void SkillEngine::RegisterSkill(const SkillTemplate& skill) {
    m_skills[skill.skillId] = skill;
}

const SkillTemplate* SkillEngine::GetSkillTemplate(uint32_t skillId) const {
    auto it = m_skills.find(skillId);
    if (it != m_skills.end()) {
        return &it->second;
    }
    return nullptr;
}

void SkillEngine::InitializeSkills() {
    RegisterGladiatorSkills();
    RegisterTemplarSkills();
    RegisterAssassinSkills();
    RegisterRangerSkills();
    RegisterSorcererSkills();
    RegisterSpiritmasterSkills();
    RegisterClericSkills();
    RegisterChanterSkills();
}

// -------------------------------------------------------------
// 3.1.1 Guerreiro: Gladiator
// -------------------------------------------------------------
void SkillEngine::RegisterGladiatorSkills() {
    // Passo 1 Chain: Golpe Feroz (Ferocious Strike)
    RegisterSkill({
        1001, "Golpe Feroz I", AionPlayerClass::GLADIATOR, 1,
        25, 0, 0, 8000, 3.0f, false, 120, 1.2f,
        AbnormalStatus::None, 0, 0,
        "GLAD_FEROCIOUS", 1, 0, 100,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 2 Chain: Golpe Robusto (Robust Blow) - Requer 1001
    RegisterSkill({
        1002, "Golpe Robusto I", AionPlayerClass::GLADIATOR, 5,
        35, 0, 0, 0, 3.0f, false, 180, 1.4f,
        AbnormalStatus::None, 0, 0,
        "GLAD_FEROCIOUS", 2, 1001, 50, // 50% de liberar passo 3
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 3 Chain: Onda Colérica (Wrathful Wave) - Requer 1002, causa Stumble
    RegisterSkill({
        1003, "Onda Colerica I", AionPlayerClass::GLADIATOR, 10,
        50, 0, 0, 0, 4.0f, false, 260, 1.7f,
        AbnormalStatus::Stumble, 3000, 75,
        "GLAD_FEROCIOUS", 3, 1002, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // AoE: Clivagem (Cleave)
    RegisterSkill({
        1004, "Clivagem I", AionPlayerClass::GLADIATOR, 16,
        60, 0, 500, 12000, 5.0f, false, 210, 1.3f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 7.0f, false
    });

    // AoE: Turbilhão (Whirlwind)
    RegisterSkill({
        1005, "Turbilhao I", AionPlayerClass::GLADIATOR, 25,
        85, 0, 0, 24000, 6.0f, false, 350, 1.5f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 8.0f, false
    });

    // Golpe Esmagador (Crushing Blow) - Especial contra alvos em Stumble
    RegisterSkill({
        1006, "Golpe Esmagador I", AionPlayerClass::GLADIATOR, 22,
        45, 0, 0, 16000, 3.0f, false, 420, 2.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 2000: Fúria de Daeva (Daeva's Fury)
    RegisterSkill({
        1010, "Furia de Daeva I", AionPlayerClass::GLADIATOR, 10,
        0, 2000, 0, 1800000, 4.0f, false, 1250, 3.0f, // 30 min CD
        AbnormalStatus::Stumble, 4000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 4000: Onda de Terremoto (Earthquake Wave)
    RegisterSkill({
        1011, "Onda de Terremoto I", AionPlayerClass::GLADIATOR, 30,
        0, 4000, 1000, 3600000, 10.0f, false, 2800, 3.5f, // 1 hora CD
        AbnormalStatus::Stumble, 5000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 15.0f, false
    });

    // Stigma Regular: Lâmina de Sangue (Draining Blow)
    RegisterSkill({
        1020, "Lamina de Sangue I", AionPlayerClass::GLADIATOR, 20,
        40, 0, 0, 30000, 3.0f, false, 240, 1.3f,
        AbnormalStatus::Bleed, 6000, 100,
        "", 0, 0, 0,
        true, StigmaType::REGULAR, 40, 0, false, 0.0f, false
    });

    // Greater Stigma: Lâmina Firme (Lockdown)
    RegisterSkill({
        1025, "Bloqueio Fisico I", AionPlayerClass::GLADIATOR, 45,
        70, 0, 0, 60000, 3.0f, false, 320, 1.4f,
        AbnormalStatus::Root, 5000, 90,
        "", 0, 0, 0,
        true, StigmaType::GREATER, 150, 1020, false, 0.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.1 Guerreiro: Templar
// -------------------------------------------------------------
void SkillEngine::RegisterTemplarSkills() {
    // Provocação Básica (Taunt)
    RegisterSkill({
        1101, "Provocacao I", AionPlayerClass::TEMPLAR, 1,
        20, 0, 0, 6000, 15.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 1 Chain: Golpe de Escudo (Shield Strike)
    RegisterSkill({
        1102, "Golpe com Escudo I", AionPlayerClass::TEMPLAR, 5,
        25, 0, 0, 6000, 3.0f, false, 110, 1.1f,
        AbnormalStatus::None, 0, 0,
        "TEMP_SHIELD", 1, 0, 100,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 2 Chain: Investida de Escudo (Shield Bash - Stun)
    RegisterSkill({
        1103, "Investida de Escudo I", AionPlayerClass::TEMPLAR, 10,
        35, 0, 0, 0, 3.0f, false, 170, 1.3f,
        AbnormalStatus::Stun, 2500, 80,
        "TEMP_SHIELD", 2, 1102, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Puxão de Corrente: Maldição da Perdição (Doom Lure / Illusion Chains)
    RegisterSkill({
        1104, "Puxao de Corrente I", AionPlayerClass::TEMPLAR, 22,
        60, 0, 0, 30000, 17.5f, false, 150, 1.0f,
        AbnormalStatus::Stun, 2000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Buff: Armadura Empírea (Empyrean Armor - +50% HP e absorção)
    RegisterSkill({
        1105, "Armadura Empirea I", AionPlayerClass::TEMPLAR, 30,
        100, 0, 0, 180000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 2000: Mão da Cura (Hand of Healing)
    RegisterSkill({
        1110, "Mao da Cura I", AionPlayerClass::TEMPLAR, 10,
        0, 2000, 0, 1800000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 4000: Proteção Divina (Divine Protection - Escudo de Grupo 10000 dano)
    RegisterSkill({
        1111, "Protecao Divina I", AionPlayerClass::TEMPLAR, 30,
        0, 4000, 0, 3600000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 20.0f, false
    });

    // Stigma Regular: Couraça de Ferro (Iron Skin)
    RegisterSkill({
        1120, "Couraca de Ferro I", AionPlayerClass::TEMPLAR, 20,
        80, 0, 0, 300000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        true, StigmaType::REGULAR, 40, 0, false, 0.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.2 Rastreador: Assassin
// -------------------------------------------------------------
void SkillEngine::RegisterAssassinSkills() {
    // Furtividade I (Hide I)
    RegisterSkill({
        1201, "Furtividade I", AionPlayerClass::ASSASSIN, 5,
        30, 0, 0, 30000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Furtividade II (Hide II - Permite correr em stealth)
    RegisterSkill({
        1202, "Furtividade Avancada II", AionPlayerClass::ASSASSIN, 25,
        45, 0, 0, 60000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Apunhalar pelas Costas (Backstab)
    RegisterSkill({
        1203, "Golpe pelas Costas I", AionPlayerClass::ASSASSIN, 10,
        40, 0, 0, 12000, 2.5f, false, 280, 1.8f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 1 Chain: Golpe de Presas (Fang Strike)
    RegisterSkill({
        1205, "Golpe de Presas I", AionPlayerClass::ASSASSIN, 1,
        25, 0, 0, 8000, 2.5f, false, 130, 1.2f,
        AbnormalStatus::None, 0, 0,
        "SIN_FANG", 1, 0, 100,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 2 Chain: Chute da Fera (Beast Kick - 40% Stun)
    RegisterSkill({
        1206, "Chute da Fera I", AionPlayerClass::ASSASSIN, 7,
        35, 0, 0, 0, 2.5f, false, 210, 1.5f,
        AbnormalStatus::Stun, 2000, 40,
        "SIN_FANG", 2, 1205, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 2000: Passo Sombrio (Shadow Walk)
    RegisterSkill({
        1210, "Passo Sombrio I", AionPlayerClass::ASSASSIN, 10,
        0, 2000, 0, 1800000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 4000: Granada de Fumaça (Smoke Bomb - Cegueira em área)
    RegisterSkill({
        1211, "Granada de Fumaca I", AionPlayerClass::ASSASSIN, 30,
        0, 4000, 0, 3600000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::Blind, 15000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 10.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.2 Rastreador: Ranger
// -------------------------------------------------------------
void SkillEngine::RegisterRangerSkills() {
    // Passo 1 Chain: Tiro com Flecha (Arrow Strike)
    RegisterSkill({
        1301, "Tiro com Flecha I", AionPlayerClass::RANGER, 1,
        25, 0, 0, 6000, 25.0f, false, 110, 1.1f,
        AbnormalStatus::None, 0, 0,
        "RNG_ARROW", 1, 0, 100,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 2 Chain: Tiro Emaranhador (Entangling Shot - Root)
    RegisterSkill({
        1302, "Tiro Emaranhador I", AionPlayerClass::RANGER, 5,
        35, 0, 0, 0, 25.0f, false, 160, 1.3f,
        AbnormalStatus::Root, 6000, 100,
        "RNG_ARROW", 2, 1301, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Armadilha de Laço (Snare Trap)
    RegisterSkill({
        1304, "Armadilha de Laco I", AionPlayerClass::RANGER, 16,
        45, 0, 1000, 30000, 3.0f, false, 0, 1.0f,
        AbnormalStatus::Root, 8000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 5.0f, false
    });

    // Armadilha de Explosão (Explosion Trap)
    RegisterSkill({
        1305, "Armadilha de Explosao I", AionPlayerClass::RANGER, 25,
        60, 0, 1000, 45000, 3.0f, false, 450, 1.8f,
        AbnormalStatus::Stumble, 3000, 80,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 6.0f, false
    });

    // DP 2000: Forma de Mau (Mau Form - +20% move speed e atk)
    RegisterSkill({
        1310, "Forma de Mau I", AionPlayerClass::RANGER, 10,
        0, 2000, 0, 1800000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 4000: Flecha Espiral (Spiral Arrow)
    RegisterSkill({
        1311, "Flecha Espiral I", AionPlayerClass::RANGER, 30,
        0, 4000, 1500, 3600000, 25.0f, false, 2400, 3.0f,
        AbnormalStatus::Stumble, 4000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.3 Mago: Sorcerer
// -------------------------------------------------------------
void SkillEngine::RegisterSorcererSkills() {
    // Passo 1 Chain: Dardo de Fogo (Flame Bolt)
    RegisterSkill({
        1401, "Dardo de Fogo I", AionPlayerClass::SORCERER, 1,
        40, 0, 1500, 6000, 25.0f, true, 220, 1.4f,
        AbnormalStatus::None, 0, 0,
        "SORC_FIRE", 1, 0, 100,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 2 Chain: Labareda (Blaze)
    RegisterSkill({
        1402, "Labareda I", AionPlayerClass::SORCERER, 7,
        55, 0, 1000, 0, 25.0f, true, 310, 1.6f,
        AbnormalStatus::None, 0, 0,
        "SORC_FIRE", 2, 1401, 30, // 30% de liberar Fogo Infernal
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Passo 3 Chain: Fogo Infernal (Hellfire)
    RegisterSkill({
        1403, "Fogo Infernal I", AionPlayerClass::SORCERER, 16,
        80, 0, 2000, 0, 25.0f, true, 580, 2.2f,
        AbnormalStatus::None, 0, 0,
        "SORC_FIRE", 3, 1402, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Teleporte de Escape (Flash Teleport - 15m adiante)
    RegisterSkill({
        1406, "Teleporte Rapido I", AionPlayerClass::SORCERER, 20,
        50, 0, 0, 30000, 15.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Sono (Sleep - Incapacitação total quebrada por dano)
    RegisterSkill({
        1407, "Sono I", AionPlayerClass::SORCERER, 13,
        60, 0, 2000, 15000, 20.0f, true, 0, 1.0f,
        AbnormalStatus::Sleep, 15000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Sono em Nuvem (Sleeping Cloud - Sono em Área)
    RegisterSkill({
        1408, "Nuvem de Sono I", AionPlayerClass::SORCERER, 37,
        120, 0, 3000, 60000, 25.0f, true, 0, 1.0f,
        AbnormalStatus::Sleep, 20000, 100,
        "", 0, 0, 0,
        true, StigmaType::REGULAR, 75, 0, true, 10.0f, false
    });

    // DP 2000: Fúria de Kaisinel (Kaisinel's Wrath)
    RegisterSkill({
        1410, "Furia de Kaisinel I", AionPlayerClass::SORCERER, 10,
        0, 2000, 3000, 1800000, 25.0f, true, 3200, 3.8f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 12.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.3 Mago: Spiritmaster
// -------------------------------------------------------------
void SkillEngine::RegisterSpiritmasterSkills() {
    // Invocação dos 4 Espíritos Elementais
    RegisterSkill({
        1501, "Invocar Espirito do Fogo I", AionPlayerClass::SPIRIT_MASTER, 10,
        90, 0, 4000, 10000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });
    RegisterSkill({
        1502, "Invocar Espirito da Terra I", AionPlayerClass::SPIRIT_MASTER, 13,
        90, 0, 4000, 10000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });
    RegisterSkill({
        1503, "Invocar Espirito do Vento I", AionPlayerClass::SPIRIT_MASTER, 16,
        90, 0, 4000, 10000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });
    RegisterSkill({
        1504, "Invocar Espirito da Agua I", AionPlayerClass::SPIRIT_MASTER, 19,
        90, 0, 4000, 10000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Dissipar Magia (Ignite Aether - Remove até 3 buffs do alvo)
    RegisterSkill({
        1505, "Acender Eter I", AionPlayerClass::SPIRIT_MASTER, 25,
        75, 0, 1000, 30000, 25.0f, true, 200, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Medo em Área (Fear Shriek - Pânico generalizado)
    RegisterSkill({
        1508, "Grito de Medo I", AionPlayerClass::SPIRIT_MASTER, 50,
        150, 0, 2500, 60000, 15.0f, true, 0, 1.0f,
        AbnormalStatus::Fear, 15000, 100,
        "", 0, 0, 0,
        true, StigmaType::GREATER, 180, 0, true, 15.0f, false
    });

    // DP 2000: Armadura Elemental (Elemental Armor)
    RegisterSkill({
        1510, "Armadura Elemental I", AionPlayerClass::SPIRIT_MASTER, 10,
        0, 2000, 0, 1800000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.4 Sacerdote: Cleric
// -------------------------------------------------------------
void SkillEngine::RegisterClericSkills() {
    // Luz Curativa (Healing Light - Cura Direta)
    RegisterSkill({
        1601, "Luz Curativa I", AionPlayerClass::CLERIC, 1,
        45, 0, 2000, 0, 25.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Clarão Radiante (Radiant Flash - Cura Instantânea Forte)
    RegisterSkill({
        1602, "Clarao Radiante I", AionPlayerClass::CLERIC, 19,
        90, 0, 0, 30000, 25.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Luz do Rejuvenescimento (Light of Rejuvenation - HoT Regenerativo)
    RegisterSkill({
        1603, "Luz do Rejuvenescimento I", AionPlayerClass::CLERIC, 7,
        35, 0, 1000, 0, 25.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Purificação (Purification - Remove Debuffs)
    RegisterSkill({
        1604, "Purificacao I", AionPlayerClass::CLERIC, 10,
        30, 0, 1000, 0, 25.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // Ressurreição (Resurrection)
    RegisterSkill({
        1605, "Ressurreicao I", AionPlayerClass::CLERIC, 10,
        150, 0, 6000, 0, 25.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 2000: Cortina Divina (Divine Curtain - Barreira para o grupo)
    RegisterSkill({
        1610, "Cortina Divina I", AionPlayerClass::CLERIC, 10,
        0, 2000, 1000, 1800000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 20.0f, false
    });

    // DP 4000: Renascimento (Rebirth - Auto-reviver passivo pós-morte)
    RegisterSkill({
        1611, "Renascimento I", AionPlayerClass::CLERIC, 30,
        0, 4000, 0, 3600000, 0.0f, true, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });
}

// -------------------------------------------------------------
// 3.1.4 Sacerdote: Chanter
// -------------------------------------------------------------
void SkillEngine::RegisterChanterSkills() {
    // Mantras (Auras de Grupo Passivas Contínuas)
    RegisterSkill({
        1701, "Mantra da Vitoria I", AionPlayerClass::CHANTER, 10,
        0, 0, 0, 0, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 20.0f, true
    });
    RegisterSkill({
        1702, "Mantra do Escudo I", AionPlayerClass::CHANTER, 13,
        0, 0, 0, 0, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 20.0f, true
    });
    RegisterSkill({
        1703, "Mantra da Revitalizacao I", AionPlayerClass::CHANTER, 19,
        0, 0, 0, 0, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 20.0f, true
    });

    // Palavra do Vento (Word of Wind - +50% move speed e +20% atk speed grupo)
    RegisterSkill({
        1704, "Palavra do Vento I", AionPlayerClass::CHANTER, 50,
        150, 0, 0, 600000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        true, StigmaType::GREATER, 160, 0, true, 25.0f, false
    });

    // Palavra da Rapidez (Word of Quickness - -50% tempo de cast grupo)
    RegisterSkill({
        1705, "Palavra da Rapidez I", AionPlayerClass::CHANTER, 45,
        120, 0, 0, 300000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        true, StigmaType::GREATER, 140, 0, true, 25.0f, false
    });

    // Atordoamento de Cajado: Ataque Meteoro (Meteor Strike - Stun)
    RegisterSkill({
        1706, "Ataque Meteoro I", AionPlayerClass::CHANTER, 22,
        45, 0, 0, 16000, 3.0f, false, 230, 1.4f,
        AbnormalStatus::Stun, 2000, 80,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 2000: Golpe Divino (Divine Strike)
    RegisterSkill({
        1710, "Golpe Divino I", AionPlayerClass::CHANTER, 10,
        0, 2000, 0, 1800000, 3.0f, false, 1100, 2.5f,
        AbnormalStatus::Stumble, 3000, 100,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, false, 0.0f, false
    });

    // DP 4000: Graça de Aion (Aion's Grace - Imunidade temporária)
    RegisterSkill({
        1711, "Graca de Aion I", AionPlayerClass::CHANTER, 30,
        0, 4000, 0, 3600000, 0.0f, false, 0, 1.0f,
        AbnormalStatus::None, 0, 0,
        "", 0, 0, 0,
        false, StigmaType::NONE, 0, 0, true, 25.0f, false
    });
}

// -------------------------------------------------------------
// Execução de Habilidade (CastSkill)
// -------------------------------------------------------------
SkillCastResult SkillEngine::CastSkill(
    uint32_t casterId,
    AionPlayerClass casterClass,
    uint32_t casterLevel,
    int32_t& casterMp,
    int32_t& casterDp,
    uint32_t targetId,
    uint32_t skillId,
    float distanceToTarget,
    const DefenseParams& targetDef,
    uint64_t currentTimeMs
) {
    SkillCastResult res = {};
    res.success = false;

    const SkillTemplate* tmpl = GetSkillTemplate(skillId);
    if (!tmpl) {
        res.failureReason = "Habilidade desconhecida.";
        return res;
    }

    if (casterLevel < tmpl->minLevel) {
        res.failureReason = "Nivel insuficiente para conjurar a habilidade.";
        return res;
    }

    if (tmpl->rangeMeters > 0.0f && distanceToTarget > (tmpl->rangeMeters + 1.0f)) {
        res.failureReason = "Alvo fora do alcance da habilidade.";
        return res;
    }

    if (casterMp < tmpl->mpCost) {
        res.failureReason = "MP insuficiente.";
        return res;
    }

    if (tmpl->dpCost > 0 && casterDp < tmpl->dpCost) {
        res.failureReason = "Divine Power (DP) insuficiente.";
        return res;
    }

    if (IsOnCooldown(casterId, skillId, currentTimeMs)) {
        res.failureReason = "Habilidade em tempo de recarga (cooldown).";
        return res;
    }

    // Validação de Chain Combo
    if (tmpl->chainStep > 1) {
        if (!CanExecuteChainStep(casterId, skillId, currentTimeMs)) {
            res.failureReason = "Condicao de Chain Combo nao atingida ou expirada.";
            return res;
        }
    }

    // Sucesso: deduz MP e DP
    casterMp -= tmpl->mpCost;
    casterDp -= tmpl->dpCost;
    res.mpConsumed = tmpl->mpCost;
    res.dpConsumed = tmpl->dpCost;

    // Dispara cooldown se aplicável
    if (tmpl->cooldownMs > 0) {
        TriggerCooldown(casterId, skillId, tmpl->cooldownMs, currentTimeMs);
    }

    // Dano ou Cura
    if (tmpl->baseDamage > 0) {
        AttackParams atk = {};
        atk.attackerId = casterId;
        atk.targetId = targetId;
        atk.attackerAttack = 150;
        atk.attackerCritRate = 250;
        atk.attackerAccuracy = 300;
        atk.attackerMagicBoost = 500;
        atk.skillId = tmpl->skillId;
        atk.skillBaseDamage = tmpl->baseDamage;
        atk.skillMultiplier = tmpl->skillMultiplier;
        atk.isMagical = tmpl->isMagical;

        CombatDamageResult dmgRes = CombatEngine::GetInstance().CalculateDamage(atk, targetDef);
        res.damageDealt = dmgRes.damage;

        // Aplicação de Status Anormal se houver
        if (tmpl->appliedStatus != AbnormalStatus::None && tmpl->statusChance > 0) {
            uint32_t roll = static_cast<uint32_t>(rand() % 100);
            if (roll < tmpl->statusChance) {
                res.statusApplied = tmpl->appliedStatus;
            }
        }
    } else if (tmpl->skillId == 1601 || tmpl->skillId == 1602) {
        // Cura direta
        res.hpHealed = 350 + static_cast<int32_t>(casterLevel * 15);
    }

    // Atualização do Sistema de Chains
    if (!tmpl->chainCategory.empty()) {
        uint32_t roll = static_cast<uint32_t>(rand() % 100);
        if (roll < tmpl->chainTriggerChance) {
            // Sucesso na ativação do próximo passo do Chain
            PlayerChainState chain = {};
            chain.activeCategory = tmpl->chainCategory;
            chain.currentStep = tmpl->chainStep;
            chain.lastExecutedSkillId = skillId;
            chain.expirationTimestampMs = currentTimeMs + 4000; // Janela canônica de 4 segundos

            // Procura skills subsequentes
            for (const auto& pair : m_skills) {
                if (pair.second.chainCategory == tmpl->chainCategory && pair.second.preChainSkillId == skillId) {
                    chain.nextAvailableSkills.push_back(pair.second.skillId);
                    res.nextChainSkillId = pair.second.skillId;
                }
            }

            if (!chain.nextAvailableSkills.empty()) {
                m_playerChains[casterId] = chain;
                res.chainTriggered = true;
            } else {
                ResetChain(casterId);
            }
        } else {
            ResetChain(casterId);
        }
    } else {
        // Habilidade independente: não altera chain ativo a menos que expire
    }

    res.success = true;
    return res;
}

// -------------------------------------------------------------
// 3.2 Sistema de Chains
// -------------------------------------------------------------
bool SkillEngine::CanExecuteChainStep(uint32_t playerId, uint32_t skillId, uint64_t currentTimeMs) const {
    auto it = m_playerChains.find(playerId);
    if (it == m_playerChains.end()) {
        return false;
    }

    const PlayerChainState& state = it->second;
    if (currentTimeMs > state.expirationTimestampMs) {
        return false;
    }

    for (uint32_t allowedId : state.nextAvailableSkills) {
        if (allowedId == skillId) {
            return true;
        }
    }

    return false;
}

void SkillEngine::ResetChain(uint32_t playerId) {
    m_playerChains.erase(playerId);
}

const PlayerChainState* SkillEngine::GetChainState(uint32_t playerId) const {
    auto it = m_playerChains.find(playerId);
    if (it != m_playerChains.end()) {
        return &it->second;
    }
    return nullptr;
}

void SkillEngine::UpdateExpiredChains(uint64_t currentTimeMs) {
    for (auto it = m_playerChains.begin(); it != m_playerChains.end(); ) {
        if (currentTimeMs > it->second.expirationTimestampMs) {
            it = m_playerChains.erase(it);
        } else {
            ++it;
        }
    }
}

// -------------------------------------------------------------
// 3.3 Divine Power (DP)
// -------------------------------------------------------------
int32_t SkillEngine::CalculateMonsterKillDp(uint32_t playerLevel, uint32_t monsterLevel, uint8_t monsterRank) const {
    if (playerLevel > monsterLevel + 8) {
        return 0; // Penalidade por monstros de nível excessivamente baixo
    }

    int32_t baseDp = 15;
    switch (monsterRank) {
        case 0: baseDp = 15;  break; // Normal
        case 1: baseDp = 40;  break; // Elite
        case 2: baseDp = 120; break; // Hero
        case 3: baseDp = 300; break; // Legendary / World Boss
        default: baseDp = 15; break;
    }
    return baseDp;
}

int32_t SkillEngine::CalculatePvpKillDp(uint32_t playerLevel, uint32_t victimLevel, uint32_t victimAbyssRank) const {
    if (playerLevel > victimLevel + 10) {
        return 0;
    }

    // Ganho canônico baseado no Abyss Rank da vítima (Soldier a General/Governor)
    int32_t basePvpDp = 150 + (static_cast<int32_t>(victimAbyssRank) * 25);
    if (basePvpDp > 600) {
        basePvpDp = 600;
    }
    return basePvpDp;
}

bool SkillEngine::CanUseDpSkill(int32_t currentDp, uint32_t skillId) const {
    const SkillTemplate* tmpl = GetSkillTemplate(skillId);
    if (!tmpl) return false;
    return (currentDp >= tmpl->dpCost);
}

// -------------------------------------------------------------
// 3.4 Sistema de Stigmas
// -------------------------------------------------------------
uint8_t SkillEngine::GetMaxRegularStigmaSlots(uint32_t level, bool questCompleted) const {
    if (!questCompleted || level < 20) return 0;
    if (level < 30) return 1;
    if (level < 40) return 2;
    if (level < 45) return 3;
    if (level < 50) return 4;
    if (level < 55) return 5;
    return 6;
}

uint8_t SkillEngine::GetMaxGreaterStigmaSlots(uint32_t level, bool questCompleted) const {
    if (!questCompleted || level < 45) return 0;
    if (level < 50) return 1;
    if (level < 55) return 2;
    return 3;
}

bool SkillEngine::CanEquipStigma(
    AionPlayerClass playerClass,
    uint32_t playerLevel,
    bool regularQuestCompleted,
    bool greaterQuestCompleted,
    const std::vector<EquippedStigma>& currentStigmas,
    uint32_t stigmaSkillId,
    uint32_t playerShards,
    int64_t playerKinah,
    std::string& outErrorMessage
) const {
    const SkillTemplate* tmpl = GetSkillTemplate(stigmaSkillId);
    if (!tmpl || !tmpl->isStigma) {
        outErrorMessage = "Item nao e uma pedra de estigma valida.";
        return false;
    }

    if (tmpl->playerClass != playerClass) {
        outErrorMessage = "Estigma incompativel com a classe do personagem.";
        return false;
    }

    if (playerLevel < tmpl->minLevel) {
        outErrorMessage = "Nivel insuficiente para equipar este estigma.";
        return false;
    }

    if (playerShards < tmpl->stigmaShardCost) {
        outErrorMessage = "Fragmentos de Estigma (Stigma Shards) insuficientes.";
        return false;
    }

    // Custo de Kinah de serviço de engaste
    int64_t requiredKinah = (tmpl->stigmaType == StigmaType::GREATER) ? 100000 : 25000;
    if (playerKinah < requiredKinah) {
        outErrorMessage = "Kinah insuficiente para a taxa do mestre de estigmas.";
        return false;
    }

    // Contagem de slots ocupados
    uint8_t regEquipped = 0;
    uint8_t advEquipped = 0;
    for (const auto& s : currentStigmas) {
        if (s.grantedSkillId == stigmaSkillId) {
            outErrorMessage = "Este estigma ja esta equipado.";
            return false;
        }
        if (s.type == StigmaType::REGULAR) regEquipped++;
        else if (s.type == StigmaType::GREATER) advEquipped++;
    }

    if (tmpl->stigmaType == StigmaType::REGULAR) {
        uint8_t maxReg = GetMaxRegularStigmaSlots(playerLevel, regularQuestCompleted);
        if (regEquipped >= maxReg) {
            outErrorMessage = "Todos os slots de Estigma Regular estao ocupados.";
            return false;
        }
    } else if (tmpl->stigmaType == StigmaType::GREATER) {
        uint8_t maxAdv = GetMaxGreaterStigmaSlots(playerLevel, greaterQuestCompleted);
        if (advEquipped >= maxAdv) {
            outErrorMessage = "Todos os slots de Estigma Maior (Greater) estao ocupados.";
            return false;
        }

        // Validação de pré-requisito da árvore de estigmas
        if (tmpl->prerequisiteStigmaId > 0) {
            bool hasPrereq = false;
            for (const auto& s : currentStigmas) {
                if (s.grantedSkillId == tmpl->prerequisiteStigmaId) {
                    hasPrereq = true;
                    break;
                }
            }
            if (!hasPrereq) {
                outErrorMessage = "Requer o estigma previo da arvore para ser engastado.";
                return false;
            }
        }
    }

    return true;
}

// -------------------------------------------------------------
// Mantras do Chanter (Máximo 3 simultâneos)
// -------------------------------------------------------------
bool SkillEngine::RegisterChanterMantra(uint32_t chanterId, uint32_t mantraSkillId, std::vector<uint32_t>& activeMantras) {
    const SkillTemplate* tmpl = GetSkillTemplate(mantraSkillId);
    if (!tmpl || !tmpl->isMantra) return false;

    // Se já estiver ativo, desativa (toggle off)
    auto it = std::find(activeMantras.begin(), activeMantras.end(), mantraSkillId);
    if (it != activeMantras.end()) {
        activeMantras.erase(it);
        return true;
    }

    // Se já tem 3 mantras, remove o mais antigo (FIFO)
    if (activeMantras.size() >= 3) {
        activeMantras.erase(activeMantras.begin());
    }

    activeMantras.push_back(mantraSkillId);
    return true;
}

// -------------------------------------------------------------
// Cooldowns
// -------------------------------------------------------------
bool SkillEngine::IsOnCooldown(uint32_t playerId, uint32_t skillId, uint64_t currentTimeMs) const {
    uint64_t key = (static_cast<uint64_t>(playerId) << 32) | skillId;
    auto it = m_cooldowns.find(key);
    if (it != m_cooldowns.end()) {
        return (currentTimeMs < it->second);
    }
    return false;
}

void SkillEngine::TriggerCooldown(uint32_t playerId, uint32_t skillId, uint32_t durationMs, uint64_t currentTimeMs) {
    uint64_t key = (static_cast<uint64_t>(playerId) << 32) | skillId;
    m_cooldowns[key] = currentTimeMs + durationMs;
}

// -------------------------------------------------------------
// Utilitários de Classe
// -------------------------------------------------------------
#ifdef GetClassName
#undef GetClassName
#endif

const char* SkillEngine::GetPlayerClassName(AionPlayerClass pClass) {
    switch (pClass) {
        case AionPlayerClass::WARRIOR:       return "Warrior";
        case AionPlayerClass::GLADIATOR:     return "Gladiator";
        case AionPlayerClass::TEMPLAR:       return "Templar";
        case AionPlayerClass::SCOUT:         return "Scout";
        case AionPlayerClass::ASSASSIN:      return "Assassin";
        case AionPlayerClass::RANGER:        return "Ranger";
        case AionPlayerClass::MAGE:          return "Mage";
        case AionPlayerClass::SORCERER:      return "Sorcerer";
        case AionPlayerClass::SPIRIT_MASTER: return "Spiritmaster";
        case AionPlayerClass::PRIEST:        return "Priest";
        case AionPlayerClass::CLERIC:        return "Cleric";
        case AionPlayerClass::CHANTER:       return "Chanter";
        case AionPlayerClass::ENGINEER:      return "Engineer";
        case AionPlayerClass::RIDER:         return "Rider";
        case AionPlayerClass::GUNNER:        return "Gunner";
        case AionPlayerClass::ARTIST:        return "Artist";
        case AionPlayerClass::BARD:          return "Bard";
        default:                             return "Unknown";
    }
}

AionPlayerClass SkillEngine::GetStartingClass(AionPlayerClass pClass) {
    switch (pClass) {
        case AionPlayerClass::GLADIATOR:
        case AionPlayerClass::TEMPLAR:
            return AionPlayerClass::WARRIOR;
        case AionPlayerClass::ASSASSIN:
        case AionPlayerClass::RANGER:
            return AionPlayerClass::SCOUT;
        case AionPlayerClass::SORCERER:
        case AionPlayerClass::SPIRIT_MASTER:
            return AionPlayerClass::MAGE;
        case AionPlayerClass::CLERIC:
        case AionPlayerClass::CHANTER:
            return AionPlayerClass::PRIEST;
        case AionPlayerClass::RIDER:
        case AionPlayerClass::GUNNER:
            return AionPlayerClass::ENGINEER;
        case AionPlayerClass::BARD:
            return AionPlayerClass::ARTIST;
        default:
            return pClass;
    }
}

bool SkillEngine::IsStartingClass(AionPlayerClass pClass) {
    return (pClass == AionPlayerClass::WARRIOR ||
            pClass == AionPlayerClass::SCOUT ||
            pClass == AionPlayerClass::MAGE ||
            pClass == AionPlayerClass::PRIEST ||
            pClass == AionPlayerClass::ENGINEER ||
            pClass == AionPlayerClass::ARTIST);
}
