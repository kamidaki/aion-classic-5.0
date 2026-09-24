using System.Buffers.Binary;

namespace AcademyNoLag.Relay.Protocol;

public enum RelayCommand : byte
{
    Hello = 1,
    HelloAck = 2,
    Data = 3,
    Ping = 4,
    Pong = 5,
    KeepAlive = 6,
    Teardown = 7
}

public class RelayPacket
{
    public const uint MagicHeader = 0x41434E4C; // "ACNL" in ASCII
    public const byte CurrentVersion = 1;
    public const int HeaderSize = 26;

    public RelayCommand Command { get; set; }
    public uint SessionId { get; set; }
    public long TimestampTicks { get; set; }
    public byte[] Payload { get; set; } = [];

    public static byte[] Encode(RelayCommand cmd, uint sessionId, ReadOnlySpan<byte> payload)
    {
        int totalSize = HeaderSize + payload.Length;
        byte[] buffer = new byte[totalSize];
        var span = buffer.AsSpan();

        // [0..3] Magic
        BinaryPrimitives.WriteUInt32BigEndian(span[..4], MagicHeader);
        // [4] Version
        span[4] = CurrentVersion;
        // [5] Command
        span[5] = (byte)cmd;
        // [6..9] SessionId
        BinaryPrimitives.WriteUInt32BigEndian(span.Slice(6, 4), sessionId);
        // [10..17] Timestamp
        BinaryPrimitives.WriteInt64BigEndian(span.Slice(10, 8), DateTime.UtcNow.Ticks);
        // [18..21] Payload Length
        BinaryPrimitives.WriteInt32BigEndian(span.Slice(18, 4), payload.Length);

        // [26..N] Copy Payload
        if (payload.Length > 0)
        {
            payload.CopyTo(span[HeaderSize..]);
        }

        // [22..25] Compute CRC32 over Header (excluding CRC field) + Payload
        uint crc = Crc32.Compute(payload);
        BinaryPrimitives.WriteUInt32BigEndian(span.Slice(22, 4), crc);

        return buffer;
    }

    public static bool TryDecode(ReadOnlySpan<byte> data, out RelayPacket? packet)
    {
        packet = null;
        if (data.Length < HeaderSize) return false;

        uint magic = BinaryPrimitives.ReadUInt32BigEndian(data[..4]);
        if (magic != MagicHeader) return false;

        byte version = data[4];
        if (version != CurrentVersion) return false;

        var cmd = (RelayCommand)data[5];
        uint sessionId = BinaryPrimitives.ReadUInt32BigEndian(data.Slice(6, 4));
        long ticks = BinaryPrimitives.ReadInt64BigEndian(data.Slice(10, 8));
        int payloadLen = BinaryPrimitives.ReadInt32BigEndian(data.Slice(18, 4));
        uint expectedCrc = BinaryPrimitives.ReadUInt32BigEndian(data.Slice(22, 4));

        if (data.Length < HeaderSize + payloadLen) return false;

        var payloadSpan = data.Slice(HeaderSize, payloadLen);
        uint actualCrc = Crc32.Compute(payloadSpan);
        if (expectedCrc != actualCrc) return false; // CRC integrity check failed

        packet = new RelayPacket
        {
            Command = cmd,
            SessionId = sessionId,
            TimestampTicks = ticks,
            Payload = payloadSpan.ToArray()
        };

        return true;
    }
}
