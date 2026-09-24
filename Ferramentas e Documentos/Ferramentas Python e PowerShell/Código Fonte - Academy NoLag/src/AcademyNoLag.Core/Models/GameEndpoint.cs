using System.Net;

namespace AcademyNoLag.Core.Models;

public enum NetworkTransportProtocol
{
    Tcp,
    Udp
}

public enum EndpointRole
{
    Unknown,
    Authentication,
    GameServer,
    ChatServer,
    VoiceServer,
    Cdn
}

public record GameEndpoint(
    int ProcessId,
    NetworkTransportProtocol Protocol,
    IPEndPoint LocalEndPoint,
    IPEndPoint RemoteEndPoint,
    string State,
    EndpointRole Role = EndpointRole.Unknown
)
{
    public IPAddress RemoteAddress => RemoteEndPoint.Address;
    public int RemotePort => RemoteEndPoint.Port;
    public DateTime FirstSeen { get; init; } = DateTime.UtcNow;
    public DateTime LastSeen { get; set; } = DateTime.UtcNow;
    public long PacketCount { get; set; } = 0;
    public bool IsActive { get; set; } = true;

    public string EndpointKey => $"{Protocol}:{RemoteAddress}:{RemotePort}";

    public override string ToString() =>
        $"[{Protocol}] {RemoteAddress}:{RemotePort} ({Role}) - State: {State}";
}
