using AcademyNoLag.Core.Algorithms;
using AcademyNoLag.Core.Models;
using Xunit;

namespace AcademyNoLag.Tests;

public class RouteQualityEngineTests
{
    [Fact]
    public void Evaluate_OptimalConnection_ReturnsHighCompositeScore()
    {
        var engine = new RouteQualityEngine();
        var stats = new NetworkAggregateStats(
            MinRttMs: 12.0,
            MeanRttMs: 15.0,
            MedianRttMs: 14.5,
            P90RttMs: 16.0,
            P95RttMs: 17.0,
            P99RttMs: 18.0,
            JitterMs: 1.2,
            PacketLossPercentage: 0.0,
            VarianceMs: 0.8,
            StandardDeviationMs: 0.9,
            TotalSamples: 50,
            SuccessfulSamples: 50
        );

        var score = engine.Evaluate(stats, 100.0);

        Assert.True(score.CompositeScore >= 90.0, $"Expected >= 90, got {score.CompositeScore}");
        Assert.Equal(RouteGrade.Optimal, score.Grade);
    }

    [Fact]
    public void Evaluate_HighPacketLoss_SeverelyPenalizesScore()
    {
        var engine = new RouteQualityEngine();
        var stats = new NetworkAggregateStats(
            MinRttMs: 20.0,
            MeanRttMs: 25.0,
            MedianRttMs: 25.0,
            P90RttMs: 28.0,
            P95RttMs: 30.0,
            P99RttMs: 35.0,
            JitterMs: 2.0,
            PacketLossPercentage: 4.0, // 4% loss is game-breaking
            VarianceMs: 2.0,
            StandardDeviationMs: 1.4,
            TotalSamples: 50,
            SuccessfulSamples: 48
        );

        var score = engine.Evaluate(stats, 100.0);

        Assert.True(score.LossScore == 0.0, "Loss score should be penalized to 0 with 4% packet loss");
        Assert.True(score.CompositeScore < 75.0);
    }

    [Fact]
    public void Weights_MustSumToOne()
    {
        var invalidWeights = new RouteQualityWeights(
            LatencyWeight: 0.5,
            LossWeight: 0.5,
            JitterWeight: 0.5,
            StabilityWeight: 0.0,
            NodeHealthWeight: 0.0
        );

        Assert.Throws<ArgumentException>(() => invalidWeights.Validate());
    }
}
