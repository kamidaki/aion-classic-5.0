using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Interfaces;

public interface IEndpointDiscovery : IDisposable
{
    event EventHandler<GameEndpoint>? EndpointDiscovered;
    event EventHandler<GameEndpoint>? EndpointClosed;

    IReadOnlyList<GameEndpoint> ActiveEndpoints { get; }
    GameEndpoint? PrimaryGameServerEndpoint { get; }

    Task StartDiscoveryAsync(int targetProcessId, CancellationToken cancellationToken = default);
    Task StopDiscoveryAsync();
    IReadOnlyList<GameEndpoint> ScanEndpoints(int processId);
}
