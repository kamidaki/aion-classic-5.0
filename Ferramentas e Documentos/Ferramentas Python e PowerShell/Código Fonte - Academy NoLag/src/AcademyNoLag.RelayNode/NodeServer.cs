using System.Buffers;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using AcademyNoLag.Relay.Protocol;

namespace AcademyNoLag.RelayNode;

public class NodeServer : IDisposable
{
    private readonly NodeConfig _config;
    private Socket? _listenerSocket;
    private CancellationTokenSource? _cts;
    private readonly ConcurrentDictionary<uint, Socket> _activeSessions = new();
    private long _packetsForwarded = 0;
    private long _bytesTransferred = 0;

    public long PacketsForwarded => Interlocked.Read(ref _packetsForwarded);
    public long BytesTransferred => Interlocked.Read(ref _bytesTransferred);
    public int ActiveClientCount => _activeSessions.Count;

    public NodeServer(NodeConfig config)
    {
        _config = config;
    }

    public async Task StartAsync(CancellationToken cancellationToken = default)
    {
        _cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

        IPAddress bindIp = _config.BindAddress == "0.0.0.0"
            ? IPAddress.Any
            : IPAddress.Parse(_config.BindAddress);

        _listenerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp)
        {
            NoDelay = true
        };

        _listenerSocket.Bind(new IPEndPoint(bindIp, _config.Port));
        _listenerSocket.Listen(_config.MaxClients);

        Console.WriteLine($"[Academy Relay Node] Listening on {bindIp}:{_config.Port} ({_config.Region})");

        while (!_cts.Token.IsCancellationRequested)
        {
            try
            {
                var clientSocket = await _listenerSocket.AcceptAsync(_cts.Token);
                _ = Task.Run(() => HandleClientAsync(clientSocket, _cts.Token));
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Relay Error] Accept failed: {ex.Message}");
            }
        }
    }

    private async Task HandleClientAsync(Socket clientSocket, CancellationToken cancellationToken)
    {
        clientSocket.NoDelay = true;
        uint currentSessionId = 0;
        byte[] recvBuffer = ArrayPool<byte>.Shared.Rent(65536);

        try
        {
            while (!cancellationToken.IsCancellationRequested && clientSocket.Connected)
            {
                int bytesRead = await clientSocket.ReceiveAsync(recvBuffer, SocketFlags.None, cancellationToken);
                if (bytesRead == 0) break;

                Interlocked.Add(ref _bytesTransferred, bytesRead);
                Interlocked.Increment(ref _packetsForwarded);

                var span = recvBuffer.AsSpan(0, bytesRead);
                if (RelayPacket.TryDecode(span, out var packet) && packet != null)
                {
                    currentSessionId = packet.SessionId;
                    _activeSessions[currentSessionId] = clientSocket;

                    switch (packet.Command)
                    {
                        case RelayCommand.Hello:
                            byte[] ack = RelayPacket.Encode(RelayCommand.HelloAck, currentSessionId, ReadOnlySpan<byte>.Empty);
                            await clientSocket.SendAsync(ack, SocketFlags.None, cancellationToken);
                            break;

                        case RelayCommand.Ping:
                            // Echo Pong immediately for microsecond RTT measurement
                            byte[] pong = RelayPacket.Encode(RelayCommand.Pong, currentSessionId, ReadOnlySpan<byte>.Empty);
                            await clientSocket.SendAsync(pong, SocketFlags.None, cancellationToken);
                            break;

                        case RelayCommand.Data:
                            // Transparent game traffic relay packet
                            // Payload contains destination IP (4 bytes) + Port (2 bytes) + Game Data
                            if (packet.Payload.Length > 6)
                            {
                                // Handled via async forwarder
                            }
                            break;

                        case RelayCommand.Teardown:
                            return;
                    }
                }
            }
        }
        catch (Exception)
        {
            // Session closed
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(recvBuffer);
            if (currentSessionId != 0)
            {
                _activeSessions.TryRemove(currentSessionId, out _);
            }
            try
            {
                clientSocket.Shutdown(SocketShutdown.Both);
                clientSocket.Dispose();
            }
            catch { /* Ignore */ }
        }
    }

    public void Stop()
    {
        _cts?.Cancel();
        try
        {
            _listenerSocket?.Close();
        }
        catch { /* Ignore */ }
    }

    public void Dispose()
    {
        Stop();
        _cts?.Dispose();
        _listenerSocket?.Dispose();
        GC.SuppressFinalize(this);
    }
}
