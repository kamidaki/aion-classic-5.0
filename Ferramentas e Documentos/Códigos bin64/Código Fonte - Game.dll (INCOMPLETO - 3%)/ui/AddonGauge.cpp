#include "AddonGauge.h"
#include "../core/GameLog.h"

AddonGauge::AddonGauge(const std::string& name)
    : AddonFrame(name)
    , m_minValue(0)
    , m_maxValue(100)
    , m_currentValue(0)
    , m_warningThreshold(-1)
    , m_bWarningBelow(true)
    , m_bWarningActive(false)
{
}

AddonGauge::~AddonGauge() {
}

void AddonGauge::SetRange(int64_t minValue, int64_t maxValue) {
    m_minValue = minValue;
    m_maxValue = maxValue;
    if (m_currentValue < m_minValue) m_currentValue = m_minValue;
    if (m_currentValue > m_maxValue) m_currentValue = m_maxValue;
}

void AddonGauge::SetValue(int64_t value) {
    m_currentValue = value;
    if (m_currentValue < m_minValue) m_currentValue = m_minValue;
    if (m_currentValue > m_maxValue) m_currentValue = m_maxValue;

    if (m_warningThreshold >= 0) {
        if (m_bWarningBelow) {
            m_bWarningActive = (m_currentValue <= m_warningThreshold);
        } else {
            m_bWarningActive = (m_currentValue >= m_warningThreshold);
        }
    }
}

float AddonGauge::GetPercentage() const {
    int64_t diff = m_maxValue - m_minValue;
    if (diff <= 0) return 0.0f;
    return static_cast<float>(m_currentValue - m_minValue) / static_cast<float>(diff);
}

std::string AddonGauge::GetFormattedText() const {
    char buf[64];
    snprintf(buf, sizeof(buf), "%lld / %lld", (long long)m_currentValue, (long long)m_maxValue);
    return std::string(buf);
}

void AddonGauge::SetWarningThreshold(int64_t threshold, bool triggerBelow) {
    m_warningThreshold = threshold;
    m_bWarningBelow = triggerBelow;
    if (m_warningThreshold >= 0) {
        if (m_bWarningBelow) {
            m_bWarningActive = (m_currentValue <= m_warningThreshold);
        } else {
            m_bWarningActive = (m_currentValue >= m_warningThreshold);
        }
    } else {
        m_bWarningActive = false;
    }
}

bool AddonGauge::IsWarningActive() const {
    return m_bWarningActive;
}

int AddonGauge::GetFilledBlocks(int totalBlocks) const {
    if (totalBlocks <= 0) return 0;
    float pct = GetPercentage();
    int filled = static_cast<int>(pct * totalBlocks);
    if (filled > totalBlocks) filled = totalBlocks;
    if (filled < 0) filled = 0;
    return filled;
}

float AddonGauge::GetCurrentBlockProgress(int totalBlocks) const {
    if (totalBlocks <= 0) return 0.0f;
    float pct = GetPercentage();
    float blockWidth = 1.0f / static_cast<float>(totalBlocks);
    int currentBlock = static_cast<int>(pct / blockWidth);
    if (currentBlock >= totalBlocks) return 1.0f;
    float blockStart = currentBlock * blockWidth;
    return (pct - blockStart) / blockWidth;
}
