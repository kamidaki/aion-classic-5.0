using AcademyNoLag.Core.Algorithms;
using AcademyNoLag.Core.Models;
using Xunit;

namespace AcademyNoLag.Tests;

public class HysteresisComparatorTests
{
    [Fact]
    public void EvaluateSwitch_InsignificantDifference_DoesNotSwitch()
    {
        var hysteresis = new HysteresisComparator
        {
            MinImprovementAbsoluteMs = 5.0,
            MinImprovementPercent = 8.0,
            RequiredConsecutiveCycles = 3
        };

        // 50ms vs 48ms (only 2ms diff = 4% improvement) -> Should NOT switch
        var direct = new NetworkAggregateStats(45, 50, 50, 52, 53, 55, 2, 0, 1, 1, 30, 30);
        var opt = new NetworkAggregateStats(44, 48, 48, 50, 51, 52, 2, 0, 1, 1, 30, 30);

        var qDirect = RouteQualityScore.Create(50, 2, 0, 1);
        var qOpt = RouteQualityScore.Create(48, 2, 0, 1);

        for (int i = 0; i < 5; i++)
        {
            var decision = hysteresis.EvaluateSwitch("Aion", null, direct, opt, qDirect, qOpt);
            Assert.False(decision.ShouldSwitch);
        }
    }

    [Fact]
    public void EvaluateSwitch_SignificantImprovement_RequiresConsecutiveCyclesBeforeSwitch()
    {
        var hysteresis = new HysteresisComparator
        {
            MinImprovementAbsoluteMs = 5.0,
            MinImprovementPercent = 8.0,
            RequiredConsecutiveCycles = 3
        };

        // 60ms vs 45ms (15ms diff = 25% improvement)
        var direct = new NetworkAggregateStats(55, 60, 60, 62, 63, 65, 3, 0, 2, 1.4, 30, 30);
        var opt = new NetworkAggregateStats(40, 45, 45, 47, 48, 50, 1, 0, 1, 1, 30, 30);

        var qDirect = RouteQualityScore.Create(60, 3, 0, 2);
        var qOpt = RouteQualityScore.Create(45, 1, 0, 1);

        // Cycle 1: should not switch yet
        var d1 = hysteresis.EvaluateSwitch("Aion", null, direct, opt, qDirect, qOpt);
        Assert.False(d1.ShouldSwitch);

        // Cycle 2: should not switch yet
        var d2 = hysteresis.EvaluateSwitch("Aion", null, direct, opt, qDirect, qOpt);
        Assert.False(d2.ShouldSwitch);

        // Cycle 3: verified 3 consecutive cycles -> Switch!
        var d3 = hysteresis.EvaluateSwitch("Aion", null, direct, opt, qDirect, qOpt);
        Assert.True(d3.ShouldSwitch);
        Assert.True(hysteresis.IsCurrentlyOptimized);
    }
}
