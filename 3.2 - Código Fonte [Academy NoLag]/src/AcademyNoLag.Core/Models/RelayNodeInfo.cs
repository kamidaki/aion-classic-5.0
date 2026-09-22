namespace AcademyNoLag.Core.Models;

public record RelayNodeInfo(
    string Id,
    string Name,
    string Region,
    string CountryCode,
    string Host,
    int Port,
    string? PublicKey = null
)
{
    public double PingMs { get; set; } = -1;
    public double JitterMs { get; set; } = 0;
    public double PacketLossPercentage { get; set; } = 0;
    public double LoadPercentage { get; set; } = 0;
    public bool IsOnline { get; set; } = false;
    public bool IsHealthy => IsOnline && PacketLossPercentage < 3.0 && PingMs > 0;
    public DateTime LastChecked { get; set; } = DateTime.MinValue;
    public double CalculatedScore { get; set; } = 0;

    public string LocationDisplay => $"{Region} ({CountryCode})";
    public string LatencyDisplay => PingMs > 0 ? $"{PingMs:F0} ms" : "--";
    public string StatusDisplay => IsOnline ? (IsHealthy ? "Healthy" : "Degraded") : "Offline";

    public override string ToString() =>
        $"[{Id}] {Name} - {Host}:{Port} ({LocationDisplay}) - {LatencyDisplay}";
}
