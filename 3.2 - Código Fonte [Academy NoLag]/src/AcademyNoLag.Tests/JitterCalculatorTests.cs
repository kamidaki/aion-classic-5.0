using AcademyNoLag.Core.Algorithms;
using Xunit;

namespace AcademyNoLag.Tests;

public class JitterCalculatorTests
{
    [Fact]
    public void UpdateRtt_FirstSample_ReturnsZero()
    {
        var calculator = new JitterCalculator();
        double jitter = calculator.UpdateRtt(50.0);
        Assert.Equal(0.0, jitter);
        Assert.Equal(1, calculator.SampleCount);
    }

    [Fact]
    public void UpdateRtt_ConstantLatency_ConvergesToZero()
    {
        var calculator = new JitterCalculator();
        calculator.UpdateRtt(50.0);

        for (int i = 0; i < 50; i++)
        {
            calculator.UpdateRtt(50.0);
        }

        Assert.Equal(0.0, calculator.CurrentJitterMs);
    }

    [Fact]
    public void UpdateRtt_OscillatingLatency_CalculatesRfc3550SmoothedJitter()
    {
        var calculator = new JitterCalculator();
        calculator.UpdateRtt(40.0); // Sample 0

        // Diff = |60 - 40| = 20. J1 = 0 + (20 - 0)/16 = 1.25
        double j1 = calculator.UpdateRtt(60.0);
        Assert.Equal(1.25, j1);

        // Diff = |40 - 60| = 20. J2 = 1.25 + (20 - 1.25)/16 = 1.25 + 1.171875 = 2.42
        double j2 = calculator.UpdateRtt(40.0);
        Assert.Equal(2.42, j2);
    }

    [Fact]
    public void Reset_ClearsState()
    {
        var calculator = new JitterCalculator();
        calculator.UpdateRtt(40.0);
        calculator.UpdateRtt(80.0);
        Assert.True(calculator.CurrentJitterMs > 0);

        calculator.Reset();
        Assert.Equal(0.0, calculator.CurrentJitterMs);
        Assert.Equal(0, calculator.SampleCount);
    }
}
