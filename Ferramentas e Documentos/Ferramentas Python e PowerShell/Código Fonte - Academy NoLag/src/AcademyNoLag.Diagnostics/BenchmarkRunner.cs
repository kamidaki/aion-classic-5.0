using System.Net;
using AcademyNoLag.Core.Algorithms;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;
using AcademyNoLag.Network.Probing;

namespace AcademyNoLag.Diagnostics;

public record BenchmarkReport(
    IPEndPoint Target,
    DateTime StartTime,
    DateTime EndTime,
    int TotalPacketsSent,
    NetworkAggregateStats Stats,
    RouteQualityScore QualityScore,
    List<double> RawSamples
);

public class BenchmarkRunner
{
    private readonly IMultiProtocolProber _prober;

    public event EventHandler<int>? ProgressChanged; // 0 to 100%

    public BenchmarkRunner(IMultiProtocolProber? prober = null)
    {
        _prober = prober ?? new MultiProtocolProber();
    }

    public async Task<BenchmarkReport> RunBenchmarkAsync(
        IPEndPoint target,
        int sampleCount = 50,
        int delayBetweenPacketsMs = 50,
        CancellationToken cancellationToken = default)
    {
        var rollingStats = new RollingStatistics(sampleCount);
        var qualityEngine = new RouteQualityEngine();
        var rawSamples = new List<double>(sampleCount);
        var startTime = DateTime.UtcNow;

        for (int i = 0; i < sampleCount; i++)
        {
            if (cancellationToken.IsCancellationRequested) break;

            var sample = await _prober.ProbeBestAsync(target, TimeSpan.FromMilliseconds(1500), cancellationToken);
            rollingStats.AddSample(sample.RttMs, sample.IsSuccess);
            if (sample.IsSuccess) rawSamples.Add(sample.RttMs);

            int progressPercent = (int)(((i + 1) / (double)sampleCount) * 100);
            ProgressChanged?.Invoke(this, progressPercent);

            if (delayBetweenPacketsMs > 0 && i < sampleCount - 1)
            {
                await Task.Delay(delayBetweenPacketsMs, cancellationToken);
            }
        }

        var endTime = DateTime.UtcNow;
        var stats = rollingStats.ComputeStats();
        var score = qualityEngine.Evaluate(stats);

        return new BenchmarkReport(
            Target: target,
            StartTime: startTime,
            EndTime: endTime,
            TotalPacketsSent: sampleCount,
            Stats: stats,
            QualityScore: score,
            RawSamples: rawSamples
        );
    }
}
