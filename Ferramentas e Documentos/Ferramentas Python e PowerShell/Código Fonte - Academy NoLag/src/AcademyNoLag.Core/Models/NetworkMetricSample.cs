using System.Net;

namespace AcademyNoLag.Core.Models;

public record NetworkMetricSample(
    DateTime Timestamp,
    IPEndPoint TargetEndPoint,
    string Protocol,
    double RttMs,
    bool IsSuccess,
    string? ErrorMessage = null
)
{
    public static NetworkMetricSample Success(IPEndPoint target, string protocol, double rttMs) =>
        new(DateTime.UtcNow, target, protocol, Math.Max(0.1, rttMs), true);

    public static NetworkMetricSample Failure(IPEndPoint target, string protocol, string error = "Timeout") =>
        new(DateTime.UtcNow, target, protocol, -1, false, error);
}

public record NetworkAggregateStats(
    double MinRttMs,
    double MeanRttMs,
    double MedianRttMs,
    double P90RttMs,
    double P95RttMs,
    double P99RttMs,
    double JitterMs,
    double PacketLossPercentage,
    double VarianceMs,
    double StandardDeviationMs,
    int TotalSamples,
    int SuccessfulSamples
)
{
    public static NetworkAggregateStats Empty =>
        new(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

    public override string ToString() =>
        $"RTT: {MeanRttMs:F1}ms (Med: {MedianRttMs:F1}ms, P95: {P95RttMs:F1}ms) | Jitter: {JitterMs:F1}ms | Loss: {PacketLossPercentage:F1}% (Samples: {SuccessfulSamples}/{TotalSamples})";
}
