namespace AcademyNoLag.Core.Models;

public record OptimizationDecision(
    string GameId,
    RelayNodeInfo? SelectedNode,
    NetworkAggregateStats DirectStats,
    NetworkAggregateStats OptimizedStats,
    RouteQualityScore DirectQuality,
    RouteQualityScore OptimizedQuality,
    double ImprovementMs,
    double ImprovementPercent,
    bool ShouldSwitch,
    string Reason,
    DateTime Timestamp
)
{
    public bool IsImprovement => ImprovementMs > 0 || (ImprovementMs >= -2.0 && OptimizedStats.PacketLossPercentage < DirectStats.PacketLossPercentage);

    public override string ToString() =>
        $"Decision for {GameId}: Switch={ShouldSwitch} (Reason: {Reason}) | Direct: {DirectStats.MeanRttMs:F1}ms / Opt: {OptimizedStats.MeanRttMs:F1}ms (Diff: {ImprovementMs:F1}ms / {ImprovementPercent:F1}%)";
}
