namespace AcademyNoLag.Core.Models;

public enum RouteGrade
{
    Optimal,
    Excellent,
    Good,
    Fair,
    Degraded,
    Unusable
}

public record RouteQualityScore(
    double CompositeScore,
    double LatencyScore,
    double JitterScore,
    double LossScore,
    double StabilityScore,
    double NodeHealthScore,
    RouteGrade Grade,
    string Summary
)
{
    public static RouteQualityScore Create(
        double latencyMs,
        double jitterMs,
        double lossPercent,
        double stabilityVariance,
        double nodeHealthPercent = 100.0)
    {
        // 1. Latency Score (0-100): Lower is better. 0-20ms = 100, 200ms = 0
        double latencyScore = Math.Clamp(100.0 - (latencyMs / 2.0), 0.0, 100.0);

        // 2. Jitter Score (0-100): Lower is better. 0ms = 100, 30ms = 0
        double jitterScore = Math.Clamp(100.0 - (jitterMs * 3.33), 0.0, 100.0);

        // 3. Loss Score (0-100): 0% loss = 100, 5% loss = 0 (punish packet loss severely)
        double lossScore = Math.Clamp(100.0 - (lossPercent * 20.0), 0.0, 100.0);

        // 4. Stability Score (0-100): Standard deviation / variance penalization
        double stabilityScore = Math.Clamp(100.0 - (stabilityVariance * 2.0), 0.0, 100.0);

        // 5. Node Health Score (0-100)
        double nodeHealth = Math.Clamp(nodeHealthPercent, 0.0, 100.0);

        // Formal weighted combination:
        // Latency: 40%, Loss: 30%, Jitter: 15%, Stability: 10%, NodeHealth: 5%
        double composite = (latencyScore * 0.40) +
                           (lossScore * 0.30) +
                           (jitterScore * 0.15) +
                           (stabilityScore * 0.10) +
                           (nodeHealth * 0.05);

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

        string summary = $"Quality: {composite}/100 [{grade}] - RTT: {latencyMs:F1}ms, Jitter: {jitterMs:F1}ms, Loss: {lossPercent:F1}%";

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
