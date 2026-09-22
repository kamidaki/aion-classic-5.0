using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Routing;

public class FailsafeController
{
    private readonly ITrafficRedirector _redirector;
    private int _degradationCounter = 0;
    private const int DegradationThreshold = 2;

    public event EventHandler<string>? FailsafeTriggered;

    public FailsafeController(ITrafficRedirector redirector)
    {
        _redirector = redirector;
    }

    public async Task EvaluateHealthAsync(
        NetworkAggregateStats directStats,
        NetworkAggregateStats optimizedStats)
    {
        if (!_redirector.IsActive)
        {
            _degradationCounter = 0;
            return;
        }

        // Check 1: Severe packet loss on optimized route (> 2% and worse than direct)
        bool hasLossDegradation = optimizedStats.PacketLossPercentage > 2.0 &&
                                 optimizedStats.PacketLossPercentage > directStats.PacketLossPercentage;

        // Check 2: Latency spike (optimized ping higher than direct by >= 15ms)
        bool hasLatencySpike = directStats.MeanRttMs > 0 &&
                               optimizedStats.MeanRttMs > directStats.MeanRttMs + 15.0;

        if (hasLossDegradation || hasLatencySpike)
        {
            _degradationCounter++;
            if (_degradationCounter >= DegradationThreshold)
            {
                string reason = hasLossDegradation
                    ? $"Optimized path packet loss reached {optimizedStats.PacketLossPercentage:F1}% (Direct: {directStats.PacketLossPercentage:F1}%)"
                    : $"Optimized path latency spiked to {optimizedStats.MeanRttMs:F1}ms (Direct: {directStats.MeanRttMs:F1}ms)";

                await TriggerFallbackAsync(reason);
            }
        }
        else
        {
            _degradationCounter = 0;
        }
    }

    public async Task TriggerFallbackAsync(string reason)
    {
        await _redirector.DisableRedirectionAsync();
        _degradationCounter = 0;
        FailsafeTriggered?.Invoke(this, $"Failsafe activated: {reason}. Reverted to default Windows route.");
    }
}
