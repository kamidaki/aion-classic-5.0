using System.Net;

namespace AcademyNoLag.Core.Models;

public record NetworkInterfaceInfo(
    string Id,
    string Name,
    string Description,
    string InterfaceType,
    List<IPAddress> IPv4Addresses,
    List<IPAddress> IPv6Addresses,
    IPAddress? GatewayIPv4,
    IPAddress? GatewayIPv6,
    List<IPAddress> DnsServers,
    long SpeedBitsPerSec,
    string OperationalStatus,
    int Mtu,
    bool IsDefaultGateway
)
{
    public string DisplaySpeed
    {
        get
        {
            if (SpeedBitsPerSec >= 1_000_000_000)
                return $"{SpeedBitsPerSec / 1_000_000_000.0:F1} Gbps";
            if (SpeedBitsPerSec >= 1_000_000)
                return $"{SpeedBitsPerSec / 1_000_000.0:F0} Mbps";
            if (SpeedBitsPerSec > 0)
                return $"{SpeedBitsPerSec / 1_000.0:F0} Kbps";
            return "Unknown";
        }
    }

    public string PrimaryIpDisplay => IPv4Addresses.FirstOrDefault()?.ToString() ?? "No IPv4";

    public override string ToString() =>
        $"{Name} ({InterfaceType}) - {PrimaryIpDisplay} - Gateway: {GatewayIPv4} - Speed: {DisplaySpeed}";
}
