using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using AcademyNoLag.Core.Algorithms;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;
using AcademyNoLag.Relay.Protocol;

namespace AcademyNoLag.Relay.Client;

public class RelayClient : IRelayClient
{
    private Socket? _socket;
    private RelayNodeInfo? _currentNode;
    private readonly JitterCalculator _jitterCalculator = new();
    private readonly RollingStatistics _rollingStats = new(50);
    private CancellationTokenSource? _heartbeatCts;
    private Task? _heartbeatTask;
    private uint _sessionId;
    private double _currentTunnelPingMs = -1;

    public bool IsConnected => _socket != null && _socket.Connected;
    public RelayNodeInfo? CurrentNode => _currentNode;
    public double CurrentTunnelPingMs => _currentTunnelPingMs;
    public double CurrentJitterMs => _jitterCalculator.CurrentJitterMs;
    public NetworkAggregateStats AggregateStats => _rollingStats.ComputeStats();

    public async Task<bool> ConnectAsync(RelayNodeInfo node, CancellationToken cancellationToken = default)
    {
        await DisconnectAsync();

        try
        {
            var socket = new Socket(SocketType.Stream, ProtocolType.Tcp)
            {
                NoDelay = true,
                Blocking = false
            };

            using var connectCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            connectCts.CancelAfter(TimeSpan.FromSeconds(3));

            await socket.ConnectAsync(node.Host, node.Port, connectCts.Token);

            _socket = socket;
            _currentNode = node;
            _sessionId = (uint)Random.Shared.Next(1, int.MaxValue);

            // Send Hello
            byte[] helloPacket = RelayPacket.Encode(RelayCommand.Hello, _sessionId, ReadOnlySpan<byte>.Empty);
            await _socket.SendAsync(helloPacket, SocketFlags.None, connectCts.Token);

            // Start background heartbeat
            _heartbeatCts = new CancellationTokenSource();
            _heartbeatTask = RunHeartbeatLoopAsync(_heartbeatCts.Token);

            return true;
        }
        catch (Exception)
        {
            await DisconnectAsync();
            return false;
        }
    }

    public async Task DisconnectAsync()
    {
        if (_heartbeatCts != null)
        {
            _heartbeatCts.Cancel();
            if (_heartbeatTask != null)
            {
                try { await _heartbeatTask; }
                catch (OperationCanceledException) { }
            }
            _heartbeatCts.Dispose();
            _heartbeatCts = null;
            _heartbeatTask = null;
        }

        if (_socket != null)
        {
            try
            {
                if (_socket.Connected)
                {
                    byte[] teardown = RelayPacket.Encode(RelayCommand.Teardown, _sessionId, ReadOnlySpan<byte>.Empty);
                    await _socket.SendAsync(teardown, SocketFlags.None);
                    _socket.Shutdown(SocketShutdown.Both);
                }
            }
            catch { /* Ignore */ }
            finally
            {
                _socket.Dispose();
                _socket = null;
            }
        }

        _currentNode = null;
        _currentTunnelPingMs = -1;
    }

    public async Task<double> MeasureNodeLatencyAsync(RelayNodeInfo node, CancellationToken cancellationToken = default)
    {
        using var probeSocket = new Socket(SocketType.Stream, ProtocolType.Tcp)
        {
            NoDelay = true,
            Blocking = false,
            LingerState = new LingerOption(true, 0)
        };

        using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        cts.CancelAfter(TimeSpan.FromSeconds(2));

        long startTimestamp = Stopwatch.GetTimestamp();
        try
        {
            await probeSocket.ConnectAsync(node.Host, node.Port, cts.Token);
            double rttMs = Stopwatch.GetElapsedTime(startTimestamp).TotalMilliseconds;

            node.PingMs = Math.Round(rttMs, 1);
            node.IsOnline = true;
            node.LastChecked = DateTime.UtcNow;

            return rttMs;
        }
        catch
        {
            node.IsOnline = false;
            node.PingMs = -1;
            node.LastChecked = DateTime.UtcNow;
            return -1;
        }
    }

    private async Task RunHeartbeatLoopAsync(CancellationToken cancellationToken)
    {
        byte[] recvBuffer = new byte[1024];

        while (!cancellationToken.IsCancellationRequested && IsConnected)
        {
            long startTimestamp = Stopwatch.GetTimestamp();

            try
            {
                byte[] pingPacket = RelayPacket.Encode(RelayCommand.Ping, _sessionId, ReadOnlySpan<byte>.Empty);
                if (_socket != null)
                {
                    await _socket.SendAsync(pingPacket, SocketFlags.None, cancellationToken);

                    using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                    timeoutCts.CancelAfter(TimeSpan.FromSeconds(1.5));

                    int bytesRead = await _socket.ReceiveAsync(recvBuffer, SocketFlags.None, timeoutCts.Token);
                    if (bytesRead > 0 && RelayPacket.TryDecode(recvBuffer.AsSpan(0, bytesRead), out var packet))
                    {
                        if (packet?.Command == RelayCommand.Pong)
                        {
                            double rttMs = Stopwatch.GetElapsedTime(startTimestamp).TotalMilliseconds;
                            _currentTunnelPingMs = Math.Round(rttMs, 1);
                            _jitterCalculator.UpdateRtt(rttMs);
                            _rollingStats.AddSample(rttMs, true);
                        }
                    }
                }
            }
            catch (Exception)
            {
                _rollingStats.AddSample(-1, false);
            }

            try
            {
                await Task.Delay(1000, cancellationToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    public void Dispose()
    {
        DisconnectAsync().GetAwaiter().GetResult();
        GC.SuppressFinalize(this);
    }
}
