using System.Buffers;
using System.Net;
using System.Net.Sockets;

namespace AcademyNoLag.Redirection;

/// <summary>
/// High-throughput transparent socket proxy. Relays bidirectional TCP stream
/// between the local game socket and the selected optimization relay node.
/// </summary>
public class TransparentProxy : IDisposable
{
    private readonly Socket _clientSocket;
    private readonly Socket _remoteSocket;
    private readonly CancellationTokenSource _cts = new();
    private Task? _pipeTask1;
    private Task? _pipeTask2;
    private long _bytesRelayed = 0;

    public long BytesRelayed => Interlocked.Read(ref _bytesRelayed);
    public bool IsActive => _clientSocket.Connected && _remoteSocket.Connected;

    public TransparentProxy(Socket clientSocket, Socket remoteSocket)
    {
        _clientSocket = clientSocket;
        _remoteSocket = remoteSocket;

        _clientSocket.NoDelay = true;
        _remoteSocket.NoDelay = true;
    }

    public void Start()
    {
        _pipeTask1 = PipeStreamAsync(_clientSocket, _remoteSocket, _cts.Token);
        _pipeTask2 = PipeStreamAsync(_remoteSocket, _clientSocket, _cts.Token);
    }

    private async Task PipeStreamAsync(Socket source, Socket destination, CancellationToken cancellationToken)
    {
        byte[] buffer = ArrayPool<byte>.Shared.Rent(32768);

        try
        {
            while (!cancellationToken.IsCancellationRequested && source.Connected && destination.Connected)
            {
                int bytesRead = await source.ReceiveAsync(buffer, SocketFlags.None, cancellationToken);
                if (bytesRead == 0) break; // Graceful EOF

                await destination.SendAsync(buffer.AsMemory(0, bytesRead), SocketFlags.None, cancellationToken);
                Interlocked.Add(ref _bytesRelayed, bytesRead);
            }
        }
        catch (Exception)
        {
            // Socket error or disconnect
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);
            Close();
        }
    }

    public void Close()
    {
        _cts.Cancel();
        try
        {
            if (_clientSocket.Connected) _clientSocket.Shutdown(SocketShutdown.Both);
            _clientSocket.Close();
        }
        catch { }

        try
        {
            if (_remoteSocket.Connected) _remoteSocket.Shutdown(SocketShutdown.Both);
            _remoteSocket.Close();
        }
        catch { }
    }

    public void Dispose()
    {
        Close();
        _cts.Dispose();
        _clientSocket.Dispose();
        _remoteSocket.Dispose();
        GC.SuppressFinalize(this);
    }
}
