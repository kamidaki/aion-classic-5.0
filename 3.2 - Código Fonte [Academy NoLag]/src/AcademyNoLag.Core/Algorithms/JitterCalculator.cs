namespace AcademyNoLag.Core.Algorithms;

/// <summary>
/// Implements RFC 3550 Interarrival Jitter calculation algorithm and IPDV (Inter-Packet Delay Variation).
/// </summary>
public class JitterCalculator
{
    private double _jitter;
    private double _previousRtt;
    private bool _hasPreviousRtt;
    private readonly object _lock = new();

    public double CurrentJitterMs
    {
        get
        {
            lock (_lock)
            {
                return Math.Round(_jitter, 2);
            }
        }
    }

    public double LastDifferenceMs { get; private set; }

    public int SampleCount { get; private set; }

    /// <summary>
    /// Updates the RFC 3550 smoothed jitter with a new RTT measurement sample in milliseconds.
    /// Formula: J(i) = J(i-1) + (|D(i-1, i)| - J(i-1)) / 16
    /// </summary>
    public double UpdateRtt(double rttMs)
    {
        if (rttMs < 0) return CurrentJitterMs;

        lock (_lock)
        {
            SampleCount++;

            if (!_hasPreviousRtt)
            {
                _previousRtt = rttMs;
                _hasPreviousRtt = true;
                _jitter = 0.0;
                LastDifferenceMs = 0.0;
                return 0.0;
            }

            double diff = Math.Abs(rttMs - _previousRtt);
            LastDifferenceMs = diff;
            _previousRtt = rttMs;

            // RFC 3550 smoothing factor 1/16 (0.0625)
            _jitter += (diff - _jitter) / 16.0;

            return Math.Round(_jitter, 2);
        }
    }

    /// <summary>
    /// Updates jitter using one-way transit arrival and departure timestamps.
    /// D(i-1, i) = (R_i - R_{i-1}) - (S_i - S_{i-1})
    /// </summary>
    public double UpdateOneWay(double sendTimeMs, double arrivalTimeMs)
    {
        lock (_lock)
        {
            double transitTime = arrivalTimeMs - sendTimeMs;
            return UpdateRtt(transitTime);
        }
    }

    public void Reset()
    {
        lock (_lock)
        {
            _jitter = 0.0;
            _previousRtt = 0.0;
            _hasPreviousRtt = false;
            LastDifferenceMs = 0.0;
            SampleCount = 0;
        }
    }
}
