using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Algorithms;

/// <summary>
/// High-performance rolling statistical aggregator with a fixed-capacity circular buffer.
/// Calculates Min, Max, Mean, Median, P90, P95, P99, Variance, Standard Deviation, and Packet Loss.
/// </summary>
public class RollingStatistics
{
    private readonly double[] _samples;
    private readonly bool[] _successes;
    private readonly int _capacity;
    private int _head = 0;
    private int _count = 0;
    private readonly object _lock = new();

    private readonly JitterCalculator _jitterCalculator = new();

    public RollingStatistics(int capacity = 60)
    {
        if (capacity <= 0) throw new ArgumentOutOfRangeException(nameof(capacity));
        _capacity = capacity;
        _samples = new double[capacity];
        _successes = new bool[capacity];
    }

    public void AddSample(double rttMs, bool isSuccess)
    {
        lock (_lock)
        {
            _samples[_head] = isSuccess ? Math.Max(0.1, rttMs) : -1.0;
            _successes[_head] = isSuccess;
            _head = (_head + 1) % _capacity;

            if (_count < _capacity)
                _count++;

            if (isSuccess)
            {
                _jitterCalculator.UpdateRtt(rttMs);
            }
        }
    }

    public NetworkAggregateStats ComputeStats()
    {
        lock (_lock)
        {
            if (_count == 0) return NetworkAggregateStats.Empty;

            int total = _count;
            int successful = 0;
            double sum = 0;

            // Collect valid samples for percentiles
            List<double> validSamples = new(_count);

            for (int i = 0; i < _count; i++)
            {
                if (_successes[i] && _samples[i] >= 0)
                {
                    successful++;
                    sum += _samples[i];
                    validSamples.Add(_samples[i]);
                }
            }

            int lost = total - successful;
            double lossPercent = total > 0 ? (lost / (double)total) * 100.0 : 0.0;

            if (validSamples.Count == 0)
            {
                return new NetworkAggregateStats(
                    MinRttMs: 0,
                    MeanRttMs: 0,
                    MedianRttMs: 0,
                    P90RttMs: 0,
                    P95RttMs: 0,
                    P99RttMs: 0,
                    JitterMs: 0,
                    PacketLossPercentage: Math.Round(lossPercent, 1),
                    VarianceMs: 0,
                    StandardDeviationMs: 0,
                    TotalSamples: total,
                    SuccessfulSamples: 0
                );
            }

            validSamples.Sort();

            double min = validSamples[0];
            double max = validSamples[^1];
            double mean = sum / validSamples.Count;

            double median = GetPercentile(validSamples, 50);
            double p90 = GetPercentile(validSamples, 90);
            double p95 = GetPercentile(validSamples, 95);
            double p99 = GetPercentile(validSamples, 99);

            // Variance and StdDev
            double varianceSum = 0;
            foreach (double val in validSamples)
            {
                double d = val - mean;
                varianceSum += d * d;
            }
            double variance = varianceSum / validSamples.Count;
            double stdDev = Math.Sqrt(variance);

            return new NetworkAggregateStats(
                MinRttMs: Math.Round(min, 1),
                MeanRttMs: Math.Round(mean, 1),
                MedianRttMs: Math.Round(median, 1),
                P90RttMs: Math.Round(p90, 1),
                P95RttMs: Math.Round(p95, 1),
                P99RttMs: Math.Round(p99, 1),
                JitterMs: Math.Round(_jitterCalculator.CurrentJitterMs, 1),
                PacketLossPercentage: Math.Round(lossPercent, 1),
                VarianceMs: Math.Round(variance, 2),
                StandardDeviationMs: Math.Round(stdDev, 2),
                TotalSamples: total,
                SuccessfulSamples: successful
            );
        }
    }

    private static double GetPercentile(List<double> sorted, double percentile)
    {
        if (sorted.Count == 0) return 0;
        if (percentile <= 0) return sorted[0];
        if (percentile >= 100) return sorted[^1];

        double rank = (percentile / 100.0) * (sorted.Count - 1);
        int low = (int)Math.Floor(rank);
        int high = (int)Math.Ceiling(rank);
        double fraction = rank - low;

        if (low == high) return sorted[low];
        return sorted[low] + (fraction * (sorted[high] - sorted[low]));
    }

    public void Clear()
    {
        lock (_lock)
        {
            _head = 0;
            _count = 0;
            _jitterCalculator.Reset();
            Array.Clear(_samples);
            Array.Clear(_successes);
        }
    }
}
