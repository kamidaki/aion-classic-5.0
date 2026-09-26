#pragma once
#include <string>

namespace BrService {

extern std::string g_clientLang;

inline bool IsEnglish() {
    return g_clientLang == "ENG" || g_clientLang == "ENU";
}

struct I18n {
    // Top Bar & Titles
    static const wchar_t* TitlePanel() {
        return L"Academy Show";
    }
    static const wchar_t* TitleDpsMeter() {
        return IsEnglish() ? L"DPS METER & COMBAT METRICS" : L"ANALISADOR DE COMBATE & DPS";
    }
    static const wchar_t* TitleTimeline() {
        return IsEnglish() ? L"COMBAT LOG & SKILLS" : L"HISTÓRICO DE COMBATE & SKILLS";
    }
    static const wchar_t* TitleSettings() {
        return IsEnglish() ? L"PANEL & ENGINE PREFERENCES" : L"PREFERÊNCIAS DO PAINEL & MOTOR";
    }
    static const wchar_t* SubtitleSettings() {
        return IsEnglish() ? L"Display, Combo UI and Visual Settings" : L"Ajustes de Exibição, Combo UI e Visuais";
    }

    // Target Section
    static const wchar_t* TargetNone() {
        return IsEnglish() ? L"Target: No Target Selected" : L"Alvo: Nenhum Alvo Selecionado";
    }
    static const wchar_t* TargetLabel() {
        return IsEnglish() ? L"Target: " : L"Alvo: ";
    }
    static const wchar_t* TargetDefeated() {
        return IsEnglish() ? L"0 / 0 (0.0%) [TARGET DEFEATED]" : L"0 / 0 (0.0%) [ALVO DERROTADO]";
    }

    // 4-Axis Radar Labels
    static const wchar_t* RadarCrit() {
        return IsEnglish() ? L"CRIT" : L"CRÍTICO";
    }
    static const wchar_t* RadarBlock() {
        return IsEnglish() ? L"BLOCK" : L"BLOQUEIO";
    }
    static const wchar_t* RadarDodge() {
        return IsEnglish() ? L"DODGE" : L"ESQUIVA";
    }
    static const wchar_t* RadarResist() {
        return IsEnglish() ? L"RESIST" : L"RESISTÊNCIA";
    }

    // Combat Stats Header
    static const wchar_t* BattleDuration() {
        return IsEnglish() ? L"Time: " : L"Tempo: ";
    }
    static const wchar_t* TotalDamage() {
        return IsEnglish() ? L"Total Dmg: " : L"Dano Total: ";
    }
    static const wchar_t* GroupDps() {
        return IsEnglish() ? L"Group DPS: " : L"DPS Grupo: ";
    }
    static const wchar_t* ResetBtn() {
        return IsEnglish() ? L"↺ Reset" : L"↺ Resetar";
    }

    // Table Headers
    static const wchar_t* ColPlayer() {
        return IsEnglish() ? L"PLAYER" : L"JOGADOR";
    }
    static const wchar_t* ColDps() {
        return IsEnglish() ? L"DPS" : L"DPS";
    }
    static const wchar_t* ColDamage() {
        return IsEnglish() ? L"DAMAGE" : L"DANO";
    }
    static const wchar_t* ColCrit() {
        return IsEnglish() ? L"CRIT%" : L"CRIT%";
    }
    static const wchar_t* ColSkill() {
        return IsEnglish() ? L"SKILL" : L"HABILIDADE";
    }
    static const wchar_t* ColHits() {
        return IsEnglish() ? L"HITS" : L"GOLPES";
    }

    // Empty Table Messages
    static const wchar_t* NoDamageRecorded() {
        return IsEnglish() ? L"Awaiting combat telemetry data..." : L"Aguardando dados de telemetria de combate...";
    }
    static const wchar_t* NoCombatEvents() {
        return IsEnglish() ? L"No combat actions recorded yet" : L"Nenhuma ação de combate registrada";
    }

    // Settings Modal
    static const wchar_t* PanelDimensions() {
        return IsEnglish() ? L"Panel Dimensions: %d x %d px" : L"Dimensões do Painel: %d x %d px";
    }
    static const wchar_t* PresetDefault() {
        return IsEnglish() ? L"Default (460x580)" : L"Padrão (460x580)";
    }
    static const wchar_t* PresetWide() {
        return IsEnglish() ? L"Wide (560x680)" : L"Amplo (560x680)";
    }
    static const wchar_t* PresetCompact() {
        return IsEnglish() ? L"Compact (420x500)" : L"Compacto (420x500)";
    }
    static const wchar_t* FineTune() {
        return IsEnglish() ? L"Fine Tuning:" : L"Ajuste Fino:";
    }
    static const wchar_t* Width() {
        return IsEnglish() ? L"Width" : L"Largura";
    }
    static const wchar_t* Height() {
        return IsEnglish() ? L"Height" : L"Altura";
    }
    static const wchar_t* PanelOpacity() {
        return IsEnglish() ? L"Window Opacity: %d%%" : L"Opacidade da Janela: %d%%";
    }
    static const wchar_t* DisplayModes() {
        return IsEnglish() ? L"DISPLAY MODES" : L"MODOS DE EXIBIÇÃO";
    }
    static const wchar_t* CompactModeActive() {
        return IsEnglish() ? L"✔ Compact Mode: ENABLED" : L"✔ Modo Compacto: ATIVADO";
    }
    static const wchar_t* CompactModeInactive() {
        return IsEnglish() ? L"✖ Compact Mode: DISABLED" : L"✖ Modo Compacto: DESATIVADO";
    }
    static const wchar_t* CompactModeDesc() {
        return IsEnglish() ? L"(Hides radar charts and 3D preview)" : L"(Oculta gráficos de radar e prévia 3D)";
    }

    // COMBO UI Settings
    static const wchar_t* ComboUiSection() {
        return IsEnglish() ? L"COMBO UI & PARTICIPATION POINTS" : L"COMBO UI & PONTOS DE PARTICIPAÇÃO";
    }
    static const wchar_t* ComboUiToggleActive() {
        return IsEnglish() ? L"✔ Combo UI: ENABLED" : L"✔ Combo UI: ATIVADO";
    }
    static const wchar_t* ComboUiToggleInactive() {
        return IsEnglish() ? L"✖ Combo UI: HIDDEN" : L"✖ Combo UI: OCULTO";
    }
    static const wchar_t* ComboUiToggleDesc() {
        return IsEnglish() ? L"(If hidden, participation points are NOT counted)" : L"(Se oculto, pontos de participação NÃO são contabilizados)";
    }
    static const wchar_t* ComboUiOpacity() {
        return IsEnglish() ? L"Combo UI Opacity: %d%%" : L"Opacidade do Combo UI: %d%%";
    }
    static const wchar_t* ComboUiScale() {
        return IsEnglish() ? L"Combo UI Scale: %d%%" : L"Escala do Combo UI: %d%%";
    }

    // COMBO UI Screen Position
    static const wchar_t* ComboUiPosition() {
        return IsEnglish() ? L"Combo UI Position:" : L"Posição do Combo UI:";
    }
    static const wchar_t* ComboPosTop() {
        return IsEnglish() ? L"Top" : L"Topo";
    }
    static const wchar_t* ComboPosMidRight() {
        return IsEnglish() ? L"Mid-Right" : L"Centro-Dir";
    }
    static const wchar_t* ComboPosCenter() {
        return IsEnglish() ? L"Center" : L"Centro";
    }
    static const wchar_t* ComboPosLeft() {
        return IsEnglish() ? L"Mid-Left" : L"Centro-Esq";
    }
    static const wchar_t* PosX() {
        return L"X";
    }
    static const wchar_t* PosY() {
        return L"Y";
    }

    static const wchar_t* SaveAndClose() {
        return IsEnglish() ? L"Save & Close" : L"Salvar & Fechar";
    }
};

} // namespace BrService
