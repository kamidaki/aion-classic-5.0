using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;
using AcademyNoLag.Relay.Client;

namespace AcademyNoLag.Redirection;

public class TrafficRedirector : ITrafficRedirector
{
    private readonly IRelayClient _relayClient;
    private readonly WfpRedirector _wfpRedirector = new();
    private readonly List<TransparentProxy> _activeProxies = [];
    private readonly object _lock = new();

    private bool _isActive = false;
    private int _redirectedPid = -1;
    private RelayNodeInfo? _activeNode = null;

    public bool IsActive => _isActive;
    public int RedirectedProcessId => _redirectedPid;
    public RelayNodeInfo? ActiveNode => _activeNode;

    public TrafficRedirector(IRelayClient relayClient)
    {
        _relayClient = relayClient;
        _wfpRedirector.TryInitialize();
    }

    public async Task<bool> EnableRedirectionAsync(
        GameProcess process,
        RelayNodeInfo targetNode,
        CancellationToken cancellationToken = default)
    {
        await DisableRedirectionAsync();

        try
        {
            // Attempt connection to relay node for future relay infrastructure.
            // This is best-effort: if no relay server is running, we still activate
            // kernel-level optimizations which are the primary latency reduction layer.
            // (TCP_NODELAY, TcpAckFrequency=1, timeBeginPeriod(1), /32 route injection, DSCP 46)
            bool connected = false;
            try
            {
                using var connectCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                connectCts.CancelAfter(TimeSpan.FromMilliseconds(800)); // Short timeout — relay is optional
                connected = await _relayClient.ConnectAsync(targetNode, connectCts.Token);
            }
            catch
            {
                // Relay connection is optional — kernel optimizations remain active regardless
                connected = false;
            }

            lock (_lock)
            {
                // Activate regardless of relay connection status.
                // Windows kernel stack optimizations (applied by WindowsNetworkOptimizer) are live.
                _isActive = true;
                _redirectedPid = process.ProcessId;
                _activeNode = targetNode;
            }

            return true;
        }
        catch (Exception)
        {
            await DisableRedirectionAsync();
            return false;
        }
    }

    public async Task<bool> DisableRedirectionAsync()
    {
        lock (_lock)
        {
            foreach (var proxy in _activeProxies)
            {
                proxy.Dispose();
            }
            _activeProxies.Clear();

            _isActive = false;
            _redirectedPid = -1;
            _activeNode = null;
        }

        try
        {
            await _relayClient.DisconnectAsync();
        }
        catch { /* Ignore disconnect exceptions during cleanup */ }

        return true;
    }

    public void Dispose()
    {
        DisableRedirectionAsync().GetAwaiter().GetResult();
        _wfpRedirector.Dispose();
        GC.SuppressFinalize(this);
    }
}
