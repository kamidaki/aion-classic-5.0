using System.Net;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;
using AcademyNoLag.Network.Native;

namespace AcademyNoLag.Detection;

public class EndpointDiscoveryEngine : IEndpointDiscovery
{
    public event EventHandler<GameEndpoint>? EndpointDiscovered;
    public event EventHandler<GameEndpoint>? EndpointClosed;

    private readonly Dictionary<string, GameEndpoint> _activeEndpoints = [];
    private readonly object _lock = new();
    private CancellationTokenSource? _cts;
    private Task? _pollTask;
    private int _targetProcessId = -1;

    public IReadOnlyList<GameEndpoint> ActiveEndpoints
    {
        get
        {
            lock (_lock)
            {
                return _activeEndpoints.Values.ToList();
            }
        }
    }

    public GameEndpoint? PrimaryGameServerEndpoint
    {
        get
        {
            lock (_lock)
            {
                var candidates = _activeEndpoints.Values
                    .Where(e => e.IsActive &&
                                !IPAddress.IsLoopback(e.RemoteAddress) &&
                                !e.RemoteAddress.ToString().StartsWith("127.") &&
                                !e.RemoteAddress.ToString().StartsWith("169.254.") &&
                                !e.RemoteAddress.Equals(IPAddress.Any) &&
                                e.RemotePort > 0 &&
                                e.RemotePort != 80 && e.RemotePort != 443)
                    .ToList();

                // 1. Prefer known GameServer ports (6600 EU, 7777 NA, 10241)
                var gameServer = candidates.FirstOrDefault(e => e.RemotePort is 6600 or 7777 or 10241 ||
                                                               (e.Role == EndpointRole.GameServer && e.Protocol == NetworkTransportProtocol.Tcp));
                if (gameServer != null) return gameServer;

                // 2. Fallback to any active TCP game server candidate
                var tcpCandidate = candidates.FirstOrDefault(e => e.Protocol == NetworkTransportProtocol.Tcp);
                if (tcpCandidate != null) return tcpCandidate;

                // 3. Fallback to any remaining valid candidate
                return candidates.FirstOrDefault();
            }
        }
    }

    public Task StartDiscoveryAsync(int targetProcessId, CancellationToken cancellationToken = default)
    {
        _targetProcessId = targetProcessId;
        _cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        _pollTask = RunDiscoveryLoopAsync(_cts.Token);
        return Task.CompletedTask;
    }

    public async Task StopDiscoveryAsync()
    {
        if (_cts != null)
        {
            _cts.Cancel();
            if (_pollTask != null)
            {
                try { await _pollTask; }
                catch (OperationCanceledException) { }
            }
            _cts.Dispose();
            _cts = null;
            _pollTask = null;
        }

        lock (_lock)
        {
            _activeEndpoints.Clear();
            _targetProcessId = -1;
        }
    }

    private async Task RunDiscoveryLoopAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            try
            {
                if (_targetProcessId > 0)
                {
                    ScanEndpoints(_targetProcessId);
                }
            }
            catch (Exception)
            {
                // Continue loop
            }

            try
            {
                await Task.Delay(500, cancellationToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    public IReadOnlyList<GameEndpoint> ScanEndpoints(int processId)
    {
        var discoveredThisCycle = new HashSet<string>();
        var result = new List<GameEndpoint>();

        // 1. Scan TCP Connections
        try
        {
            var tcpRows = IpHlpApi.GetAllTcpConnections();
            foreach (var row in tcpRows)
            {
                if (row.ProcessId != processId) continue;

                // Ignore listening sockets, loopback IPC, APIPA, or invalid remote ports
                if (row.RemoteAddress.Equals(IPAddress.Any) ||
                    row.RemotePort == 0 ||
                    IPAddress.IsLoopback(row.RemoteAddress) ||
                    row.RemoteAddress.ToString().StartsWith("127.") ||
                    row.RemoteAddress.ToString().StartsWith("169.254."))
                    continue;

                var localEp = new IPEndPoint(row.LocalAddress, row.LocalPort);
                var remoteEp = new IPEndPoint(row.RemoteAddress, row.RemotePort);

                EndpointRole role = ClassifyEndpoint(row.RemotePort);

                var endpoint = new GameEndpoint(
                    ProcessId: processId,
                    Protocol: NetworkTransportProtocol.Tcp,
                    LocalEndPoint: localEp,
                    RemoteEndPoint: remoteEp,
                    State: row.State.ToString(),
                    Role: role
                );

                string key = endpoint.EndpointKey;
                discoveredThisCycle.Add(key);

                lock (_lock)
                {
                    if (!_activeEndpoints.ContainsKey(key))
                    {
                        _activeEndpoints[key] = endpoint;
                        EndpointDiscovered?.Invoke(this, endpoint);
                    }
                    else
                    {
                        _activeEndpoints[key].LastSeen = DateTime.UtcNow;
                        _activeEndpoints[key].IsActive = true;
                    }

                    result.Add(_activeEndpoints[key]);
                }
            }
        }
        catch { /* Ignore API errors */ }

        // 2. Scan UDP Endpoints
        try
        {
            var udpRows = IpHlpApi.GetAllUdpEndpoints();
            foreach (var row in udpRows)
            {
                if (row.ProcessId != processId) continue;

                var localEp = new IPEndPoint(row.LocalAddress, row.LocalPort);
                // UDP is connectionless; remote IP will be tracked upon traffic observation
                var remoteEp = new IPEndPoint(IPAddress.Any, 0);

                var endpoint = new GameEndpoint(
                    ProcessId: processId,
                    Protocol: NetworkTransportProtocol.Udp,
                    LocalEndPoint: localEp,
                    RemoteEndPoint: remoteEp,
                    State: "Open",
                    Role: EndpointRole.GameServer
                );

                string key = endpoint.EndpointKey;
                discoveredThisCycle.Add(key);

                lock (_lock)
                {
                    if (!_activeEndpoints.ContainsKey(key))
                    {
                        _activeEndpoints[key] = endpoint;
                        EndpointDiscovered?.Invoke(this, endpoint);
                    }
                }
            }
        }
        catch { /* Ignore API errors */ }

        // 3. Mark closed endpoints
        lock (_lock)
        {
            var toRemove = new List<string>();
            foreach (var (key, ep) in _activeEndpoints)
            {
                if (!discoveredThisCycle.Contains(key))
                {
                    if (DateTime.UtcNow - ep.LastSeen > TimeSpan.FromSeconds(5))
                    {
                        ep.IsActive = false;
                        toRemove.Add(key);
                        EndpointClosed?.Invoke(this, ep);
                    }
                }
            }

            foreach (var key in toRemove)
            {
                _activeEndpoints.Remove(key);
            }
        }

        return result;
    }

    private static EndpointRole ClassifyEndpoint(int port)
    {
        return port switch
        {
            2106 or 27500 => EndpointRole.Authentication, // Aion Login Server
            6600 or 7777 => EndpointRole.GameServer,     // Aion Game Server (6600 EU / 7777 NA)
            10241 => EndpointRole.ChatServer,            // Aion Chat Server
            80 or 443 => EndpointRole.Cdn,               // Web / Launcher / Patching
            _ => EndpointRole.GameServer                 // Default assumption for game process sockets
        };
    }

    public void AddManualEndpoint(GameEndpoint endpoint)
    {
        lock (_lock)
        {
            _activeEndpoints[endpoint.EndpointKey] = endpoint;
            EndpointDiscovered?.Invoke(this, endpoint);
        }
    }

    public void Dispose()
    {
        _cts?.Cancel();
        _cts?.Dispose();
        GC.SuppressFinalize(this);
    }
}
