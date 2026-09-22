using System.Buffers.Binary;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Network.Probing;

public class UdpProber : INetworkProber
{
    public string ProtocolName => "UDP";
    private uint _sequence = 0;

    public async Task<NetworkMetricSample> ProbeAsync(
        IPEndPoint target,
        TimeSpan timeout,
        CancellationToken cancellationToken = default)
    {
        using var client = new UdpClient();
        client.Client.ReceiveTimeout = (int)timeout.TotalMilliseconds;
        client.Client.SendTimeout = (int)timeout.TotalMilliseconds;

        // Build probe packet: [0..3] Magic 'ACNL', [4..7] Sequence, [8..15] Timestamp
        byte[] buffer = new byte[16];
        buffer[0] = (byte)'A';
        buffer[1] = (byte)'C';
        buffer[2] = (byte)'N';
        buffer[3] = (byte)'L';

        uint seq = Interlocked.Increment(ref _sequence);
        BinaryPrimitives.WriteUInt32BigEndian(buffer.AsSpan(4, 4), seq);

        long sendTimestamp = Stopwatch.GetTimestamp();
        BinaryPrimitives.WriteInt64BigEndian(buffer.AsSpan(8, 8), sendTimestamp);

        try
        {
            await client.SendAsync(buffer, buffer.Length, target);

            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(timeout);

            var receiveTask = client.ReceiveAsync(cts.Token).AsTask();
            var result = await receiveTask;

            double rttMs = Stopwatch.GetElapsedTime(sendTimestamp).TotalMilliseconds;
            return NetworkMetricSample.Success(target, ProtocolName, Math.Max(0.1, rttMs));
        }
        catch (OperationCanceledException)
        {
            return NetworkMetricSample.Failure(target, ProtocolName, "UDP Probe Timeout");
        }
        catch (SocketException sex)
        {
            // Port unreachable ICMP error received back
            if (sex.SocketErrorCode == SocketError.ConnectionReset)
            {
                double elapsedMs = Stopwatch.GetElapsedTime(sendTimestamp).TotalMilliseconds;
                return NetworkMetricSample.Success(target, ProtocolName, Math.Max(0.1, elapsedMs));
            }
            return NetworkMetricSample.Failure(target, ProtocolName, $"Socket Error: {sex.SocketErrorCode}");
        }
        catch (Exception ex)
        {
            return NetworkMetricSample.Failure(target, ProtocolName, ex.Message);
        }
    }

    public void Dispose()
    {
        GC.SuppressFinalize(this);
    }
}
