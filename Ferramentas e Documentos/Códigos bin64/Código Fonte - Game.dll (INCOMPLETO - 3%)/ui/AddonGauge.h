#pragma once
#include "AddonFrame.h"
#include <cstdint>

// Barra de progresso e medidor de status canônico extraído do RTTI (.?AVAddonGauge@@)
class AddonGauge : public AddonFrame {
public:
    AddonGauge(const std::string& name);
    virtual ~AddonGauge();

    void SetRange(int64_t minValue, int64_t maxValue);
    void SetValue(int64_t value);

    int64_t GetValue() const { return m_currentValue; }
    int64_t GetMinValue() const { return m_minValue; }
    int64_t GetMaxValue() const { return m_maxValue; }
    float GetPercentage() const;

    // Métodos canônicos de exibição e alerta
    std::string GetFormattedText() const;
    void SetWarningThreshold(int64_t threshold, bool triggerBelow = true);
    bool IsWarningActive() const;
    
    // Divisão em blocos percentuais (Ex: Barra de Exp dividida em 10 blocos de 10%)
    int GetFilledBlocks(int totalBlocks = 10) const;
    float GetCurrentBlockProgress(int totalBlocks = 10) const;

private:
    int64_t m_minValue;
    int64_t m_maxValue;
    int64_t m_currentValue;
    int64_t m_warningThreshold;
    bool m_bWarningBelow;
    bool m_bWarningActive;
};
