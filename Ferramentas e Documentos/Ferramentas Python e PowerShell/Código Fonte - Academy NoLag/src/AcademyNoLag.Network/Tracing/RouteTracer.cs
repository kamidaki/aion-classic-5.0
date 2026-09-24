using System.Diagnostics;
using System.Net;
using System.Net.NetworkInformation;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Network.Tracing;

public class RouteTracer : IRouteTracer
{
    public event EventHandler<RouteHopInfo>? HopDiscovered;

    private readonly byte[] _buffer = new byte[32];

    public RouteTracer()
    {
        for (int i = 0; i < _buffer.Length; i++)
        {
            _buffer[i] = (byte)('A' + (i % 26));
        }
    }

    public async Task<RoutePath> TraceRouteAsync(
        IPAddress destination,
        int maxHops = 30,
        int timeoutMs = 1500,
        CancellationToken cancellationToken = default)
    {
        var hops = new List<RouteHopInfo>();
        bool reached = false;
        double totalRtt = 0;

        using var ping = new Ping();

        for (int ttl = 1; ttl <= maxHops; ttl++)
        {
            if (cancellationToken.IsCancellationRequested) break;

            var options = new PingOptions(ttl, true);
            long startTimestamp = Stopwatch.GetTimestamp();

            try
            {
                var reply = await ping.SendPingAsync(
                    destination,
                    timeoutMs,
                    _buffer,
                    options);

                double elapsedMs = Stopwatch.GetElapsedTime(startTimestamp).TotalMilliseconds;

                if (reply.Status == IPStatus.TtlExpired || reply.Status == IPStatus.Success)
                {
                    IPAddress hopIp = reply.Address;
                    string hostName = hopIp.ToString();

                    // Try reverse DNS lookup in background with short timeout
                    try
                    {
                        var entryTask = Dns.GetHostEntryAsync(hopIp);
                        if (await Task.WhenAny(entryTask, Task.Delay(200, cancellationToken)) == entryTask)
                        {
                            hostName = (await entryTask).HostName;
                        }
                    }
                    catch { /* Ignore reverse DNS failures */ }

                    double rtt = Math.Max(0.1, elapsedMs);
                    var hop = new RouteHopInfo(
                        HopIndex: ttl,
                        Address: hopIp,
                        HostName: hostName,
                        RttMs: Math.Round(rtt, 1),
                        PacketLossPercentage: 0,
                        Status: HopStatus.Active
                    );

                    hops.Add(hop);
                    HopDiscovered?.Invoke(this, hop);

                    if (reply.Status == IPStatus.Success || hopIp.Equals(destination))
                    {
                        reached = true;
                        totalRtt = rtt;
                        break;
                    }
                }
                else
                {
                    var hop = new RouteHopInfo(
                        HopIndex: ttl,
                        Address: null,
                        HostName: "* * *",
                        RttMs: -1,
                        PacketLossPercentage: 100.0,
                        Status: HopStatus.TimedOut
                    );

                    hops.Add(hop);
                    HopDiscovered?.Invoke(this, hop);
                }
            }
            catch (Exception)
            {
                var hop = new RouteHopInfo(
                    HopIndex: ttl,
                    Address: null,
                    HostName: "* * *",
                    RttMs: -1,
                    PacketLossPercentage: 100.0,
                    Status: HopStatus.TimedOut
                );

                hops.Add(hop);
                HopDiscovered?.Invoke(this, hop);
            }
        }

        return new RoutePath(
            Destination: destination,
            Hops: hops,
            DiscoveredAt: DateTime.UtcNow,
            TotalRttMs: totalRtt,
            ReachedDestination: reached
        );
    }
}
