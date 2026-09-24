using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Algorithms;

public class HysteresisComparator
{
    public double MinImprovementPercent { get; set; } = 7.0; // At least 7% better
    public double MinImprovementAbsoluteMs { get; set; } = 4.0; // Or at least 4ms lower latency
    public int RequiredConsecutiveCycles { get; set; } = 3;

    private int _consecutiveImprovementCount = 0;
    private int _consecutiveDegradationCount = 0;
    private bool _isCurrentlyOptimized = false;

    public bool IsCurrentlyOptimized => _isCurrentlyOptimized;

    public OptimizationDecision EvaluateSwitch(
        string gameId,
        RelayNodeInfo? candidateNode,
        NetworkAggregateStats directStats,
        NetworkAggregateStats optimizedStats,
        RouteQualityScore directQuality,
        RouteQualityScore optimizedQuality)
    {
        double diffMs = directStats.MeanRttMs - optimizedStats.MeanRttMs;
        double percent = directStats.MeanRttMs > 0 ? (diffMs / directStats.MeanRttMs) * 100.0 : 0.0;

        // Severe degradation check: if optimized route has higher packet loss than direct route
        // or latency is worse by >= 5ms, trigger immediate fallback!
        if (_isCurrentlyOptimized)
        {
            if (optimizedStats.PacketLossPercentage > directStats.PacketLossPercentage + 1.0 ||
                optimizedStats.MeanRttMs > directStats.MeanRttMs + 5.0)
            {
                _consecutiveDegradationCount++;
                if (_consecutiveDegradationCount >= 2)
                {
                    _isCurrentlyOptimized = false;
                    _consecutiveImprovementCount = 0;
                    _consecutiveDegradationCount = 0;

                    return new OptimizationDecision(
                        gameId,
                        candidateNode,
                        directStats,
                        optimizedStats,
                        directQuality,
                        optimizedQuality,
                        Math.Round(diffMs, 1),
                        Math.Round(percent, 1),
                        ShouldSwitch: false,
                        Reason: $"Failsafe fallback: Optimized route degraded (Loss: {optimizedStats.PacketLossPercentage:F1}%, RTT: {optimizedStats.MeanRttMs:F1}ms vs Direct {directStats.MeanRttMs:F1}ms)",
                        Timestamp: DateTime.UtcNow
                    );
                }
            }
            else
            {
                _consecutiveDegradationCount = 0;
            }
        }

        // Check if candidate route satisfies hysteresis improvement threshold
        bool qualityBetter = optimizedQuality.CompositeScore > directQuality.CompositeScore;
        bool meetsThreshold = (diffMs >= MinImprovementAbsoluteMs || percent >= MinImprovementPercent) &&
                              optimizedStats.PacketLossPercentage <= directStats.PacketLossPercentage;

        if (qualityBetter && meetsThreshold)
        {
            _consecutiveImprovementCount++;
            if (_consecutiveImprovementCount >= RequiredConsecutiveCycles)
            {
                _isCurrentlyOptimized = true;
                _consecutiveDegradationCount = 0;

                return new OptimizationDecision(
                    gameId,
                    candidateNode,
                    directStats,
                    optimizedStats,
                    directQuality,
                    optimizedQuality,
                    Math.Round(diffMs, 1),
                    Math.Round(percent, 1),
                    ShouldSwitch: true,
                    Reason: $"Optimization verified: Sustained improvement over {_consecutiveImprovementCount} cycles (-{diffMs:F1}ms, {percent:F1}% better)",
                    Timestamp: DateTime.UtcNow
                );
            }
            else
            {
                return new OptimizationDecision(
                    gameId,
                    candidateNode,
                    directStats,
                    optimizedStats,
                    directQuality,
                    optimizedQuality,
                    Math.Round(diffMs, 1),
                    Math.Round(percent, 1),
                    ShouldSwitch: false,
                    Reason: $"Candidate path improving ({_consecutiveImprovementCount}/{RequiredConsecutiveCycles} cycles verified)",
                    Timestamp: DateTime.UtcNow
                );
            }
        }
        else
        {
            _consecutiveImprovementCount = 0;
            return new OptimizationDecision(
                gameId,
                candidateNode,
                directStats,
                optimizedStats,
                directQuality,
                optimizedQuality,
                Math.Round(diffMs, 1),
                Math.Round(percent, 1),
                ShouldSwitch: false,
                Reason: "Candidate path does not significantly outperform direct ISP route (Zero-Fake Policy)",
                Timestamp: DateTime.UtcNow
            );
        }
    }

    public void Reset()
    {
        _consecutiveImprovementCount = 0;
        _consecutiveDegradationCount = 0;
        _isCurrentlyOptimized = false;
    }
}
