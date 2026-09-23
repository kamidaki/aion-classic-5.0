using AcademyNoLag.Core.Algorithms;
using Xunit;

namespace AcademyNoLag.Tests;

public class RollingStatisticsTests
{
    [Fact]
    public void ComputeStats_KnownDataset_ComputesAccurateMetrics()
    {
        var stats = new RollingStatistics(10);
        // Samples: 10, 20, 30, 40, 50
        double[] values = [10.0, 20.0, 30.0, 40.0, 50.0];
        foreach (var v in values)
        {
            stats.AddSample(v, true);
        }

        var agg = stats.ComputeStats();

        Assert.Equal(10.0, agg.MinRttMs);
        Assert.Equal(30.0, agg.MeanRttMs);
        Assert.Equal(30.0, agg.MedianRttMs);
        Assert.Equal(49.6, agg.P99RttMs);
        Assert.Equal(0.0, agg.PacketLossPercentage);
        Assert.Equal(5, agg.SuccessfulSamples);
        Assert.Equal(5, agg.TotalSamples);
    }

    [Fact]
    public void ComputeStats_WithDroppedPackets_ComputesAccurateLossPercentage()
    {
        var stats = new RollingStatistics(10);
        // 8 successes, 2 failures = 20% loss
        for (int i = 0; i < 8; i++) stats.AddSample(25.0, true);
        stats.AddSample(-1.0, false);
        stats.AddSample(-1.0, false);

        var agg = stats.ComputeStats();

        Assert.Equal(20.0, agg.PacketLossPercentage);
        Assert.Equal(8, agg.SuccessfulSamples);
        Assert.Equal(10, agg.TotalSamples);
        Assert.Equal(25.0, agg.MeanRttMs);
    }

    [Fact]
    public void Clear_EmptiesAllData()
    {
        var stats = new RollingStatistics(10);
        stats.AddSample(50.0, true);
        stats.Clear();

        var agg = stats.ComputeStats();
        Assert.Equal(0, agg.TotalSamples);
    }
}
