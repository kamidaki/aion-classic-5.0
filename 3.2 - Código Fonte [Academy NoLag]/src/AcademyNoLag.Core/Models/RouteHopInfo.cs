using System.Net;

namespace AcademyNoLag.Core.Models;

public enum HopStatus
{
    Active,
    TimedOut,
    Unreachable,
    Resolved
}

public record RouteHopInfo(
    int HopIndex,
    IPAddress? Address,
    string HostName,
    double RttMs,
    double PacketLossPercentage = 0,
    string? Asn = null,
    string? Isp = null,
    HopStatus Status = HopStatus.Active
)
{
    public bool IsGateway => HopIndex == 1;
    public string DisplayAddress => Address?.ToString() ?? "* * *";

    public override string ToString() =>
        $"Hop {HopIndex:D2}: {DisplayAddress} ({HostName}) - {RttMs:F1}ms (Loss: {PacketLossPercentage:F1}%)";
}

public record RoutePath(
    IPAddress Destination,
    IReadOnlyList<RouteHopInfo> Hops,
    DateTime DiscoveredAt,
    double TotalRttMs,
    bool ReachedDestination
)
{
    public int TotalHops => Hops.Count;
    public RouteHopInfo? GatewayHop => Hops.FirstOrDefault(h => h.HopIndex == 1);
    public RouteHopInfo? DestinationHop => Hops.LastOrDefault();
}
