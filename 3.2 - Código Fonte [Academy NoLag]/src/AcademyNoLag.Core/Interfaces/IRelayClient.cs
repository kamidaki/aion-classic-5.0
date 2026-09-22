using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Interfaces;

public interface IRelayClient : IDisposable
{
    bool IsConnected { get; }
    RelayNodeInfo? CurrentNode { get; }
    double CurrentTunnelPingMs { get; }

    Task<bool> ConnectAsync(RelayNodeInfo node, CancellationToken cancellationToken = default);
    Task DisconnectAsync();
    Task<double> MeasureNodeLatencyAsync(RelayNodeInfo node, CancellationToken cancellationToken = default);
}

public interface IRelayNodeRegistry
{
    IReadOnlyList<RelayNodeInfo> GetNodes();
    void RegisterNode(RelayNodeInfo node);
    void RemoveNode(string nodeId);
    Task RefreshAllNodesHealthAsync(CancellationToken cancellationToken = default);
}
