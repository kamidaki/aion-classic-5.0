using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Algorithms;

public record RouteQualityWeights(
    double LatencyWeight = 0.40,
    double LossWeight = 0.30,
    double JitterWeight = 0.15,
    double StabilityWeight = 0.10,
    double NodeHealthWeight = 0.05
)
{
    public static RouteQualityWeights Default => new();

    public void Validate()
    {
        double sum = LatencyWeight + LossWeight + JitterWeight + StabilityWeight + NodeHealthWeight;
        if (Math.Abs(sum - 1.0) > 0.001)
        {
            throw new ArgumentException($"Weights must sum to 1.0, current sum: {sum}");
        }
    }
}

/// <summary>
/// Evaluates and scores candidate network routes using weighted multi-factor metrics.
/// Supports distance-adaptive intercontinental scoring (e.g. transatlantic fiber routes).
/// </summary>
public class RouteQualityEngine
{
    public RouteQualityWeights Weights { get; set; }

    public RouteQualityEngine(RouteQualityWeights? weights = null)
    {
        Weights = weights ?? RouteQualityWeights.Default;
        Weights.Validate();
    }

    /// <summary>
    /// Computes a normalized RouteQualityScore (0 to 100) from aggregate stats and node health.
    /// </summary>
    public RouteQualityScore Evaluate(NetworkAggregateStats stats, double nodeHealthPercent = 100.0)
    {
        // 1. Distance-Adaptive Latency Score (0-100)
        // Uses P95 RTT to account for latency spikes, not just minimum ping.
        double effectiveLatency = stats.P95RttMs > 0 ? (stats.MeanRttMs * 0.4 + stats.P95RttMs * 0.6) : stats.MeanRttMs;
        double latencyScore;

        if (effectiveLatency <= 50.0)
        {
            // Domestic / Local Datacenter: 0ms = 100, 50ms = 90
            latencyScore = 100.0 - (effectiveLatency * 0.2);
        }
        else if (effectiveLatency <= 120.0)
        {
            // Continental / Regional: 50ms = 90, 120ms = ~80
            latencyScore = 90.0 - ((effectiveLatency - 50.0) * 0.14);
        }
        else if (effectiveLatency <= 230.0)
        {
            // Transatlantic / Intercontinental corridor (e.g. South America <-> Europe / USA)
            // Physical light speed transit in fiber is ~160-200ms. If steady, connection is high quality!
            latencyScore = 80.0 - ((effectiveLatency - 120.0) * 0.10);
        }
        else
        {
            // High latency / sub-optimal routing (> 230ms)
            latencyScore = Math.Max(0.0, 69.0 - ((effectiveLatency - 230.0) * 0.35));
        }

        latencyScore = Math.Clamp(latencyScore, 0.0, 100.0);

        // 2. Jitter Score (0-100): Lower is better. 0ms = 100, < 2ms = > 93, > 25ms = 0
        double jitterScore = Math.Clamp(100.0 - (stats.JitterMs * 3.5), 0.0, 100.0);

        // 3. Loss Score (0-100): Punishes packet loss severely (gaming experience drops drastically with even 1-2% loss)
        // 0% loss = 100, 1% loss = 75, 2% loss = 50, 4% loss = 0
        double lossScore = Math.Clamp(100.0 - (stats.PacketLossPercentage * 25.0), 0.0, 100.0);

        // 4. Stability Score (0-100): Standard deviation / variance penalty
        double stabilityScore = Math.Clamp(100.0 - (stats.StandardDeviationMs * 3.0), 0.0, 100.0);

        // 5. Node Health Score (0-100)
        double nodeHealth = Math.Clamp(nodeHealthPercent, 0.0, 100.0);

        double composite = (latencyScore * Weights.LatencyWeight) +
                           (lossScore * Weights.LossWeight) +
                           (jitterScore * Weights.JitterWeight) +
                           (stabilityScore * Weights.StabilityWeight) +
                           (nodeHealth * Weights.NodeHealthWeight);

        composite = Math.Round(composite, 1);

        RouteGrade grade = composite switch
        {
            >= 90 => RouteGrade.Optimal,
            >= 75 => RouteGrade.Excellent,
            >= 60 => RouteGrade.Good,
            >= 45 => RouteGrade.Fair,
            >= 25 => RouteGrade.Degraded,
            _ => RouteGrade.Unusable
        };

        string summary = $"Composite: {composite:F1}/100 [{grade}] | RTT: {stats.MeanRttMs:F1}ms (P95: {stats.P95RttMs:F1}ms), Jitter: {stats.JitterMs:F1}ms, Loss: {stats.PacketLossPercentage:F1}%";

        return new RouteQualityScore(
            composite,
            Math.Round(latencyScore, 1),
            Math.Round(jitterScore, 1),
            Math.Round(lossScore, 1),
            Math.Round(stabilityScore, 1),
            Math.Round(nodeHealth, 1),
            grade,
            summary
        );
    }
}
