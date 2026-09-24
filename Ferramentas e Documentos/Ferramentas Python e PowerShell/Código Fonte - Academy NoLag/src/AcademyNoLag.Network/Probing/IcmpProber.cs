using System.Diagnostics;
using System.Net;
using System.Net.NetworkInformation;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Network.Probing;

public class IcmpProber : INetworkProber
{
    public string ProtocolName => "ICMP";
    private readonly byte[] _payload;

    public IcmpProber(int payloadSize = 32)
    {
        _payload = new byte[payloadSize];
        for (int i = 0; i < payloadSize; i++)
        {
            _payload[i] = (byte)('a' + (i % 26));
        }
    }

    public async Task<NetworkMetricSample> ProbeAsync(
        IPEndPoint target,
        TimeSpan timeout,
        CancellationToken cancellationToken = default)
    {
        return await ProbeAddressAsync(target.Address, timeout, cancellationToken);
    }

    public async Task<NetworkMetricSample> ProbeAddressAsync(
        IPAddress targetAddress,
        TimeSpan timeout,
        CancellationToken cancellationToken = default)
    {
        long startTimestamp = Stopwatch.GetTimestamp();

        try
        {
            using var ping = new Ping();
            var options = new PingOptions(64, true);

            var reply = await ping.SendPingAsync(
                targetAddress,
                (int)timeout.TotalMilliseconds,
                _payload,
                options);

            double elapsedMs = Stopwatch.GetElapsedTime(startTimestamp).TotalMilliseconds;

            if (reply.Status == IPStatus.Success)
            {
                // reply.RoundtripTime is integer-millisecond resolution from Windows ICMP driver.
                // elapsedMs from Stopwatch includes async dispatch overhead (+0-3ms on busy CPU).
                // Use elapsedMs for sub-millisecond precision when it's within 5ms of the ICMP value;
                // fall back to reply.RoundtripTime if async overhead inflated the measurement.
                double elapsedFloor = Math.Max(0.1, elapsedMs);
                double icmpMs = reply.RoundtripTime;

                // If async overhead < 5ms, elapsedMs ≈ real RTT (sub-ms accurate)
                // If async overhead >= 5ms, trust the kernel's integer ICMP timestamp instead
                double preciseRtt = (elapsedFloor <= icmpMs + 5.0)
                    ? elapsedFloor
                    : icmpMs;
                preciseRtt = Math.Max(0.1, preciseRtt);

                return NetworkMetricSample.Success(new IPEndPoint(targetAddress, 0), ProtocolName, preciseRtt);
            }

            return NetworkMetricSample.Failure(
                new IPEndPoint(targetAddress, 0),
                ProtocolName,
                $"ICMP status: {reply.Status}");
        }
        catch (Exception ex)
        {
            return NetworkMetricSample.Failure(
                new IPEndPoint(targetAddress, 0),
                ProtocolName,
                ex.Message);
        }
    }

    public void Dispose()
    {
        GC.SuppressFinalize(this);
    }
}
