using System.Buffers.Binary;
using System.Text;

namespace AionClassic.Network.Packets;

public sealed class PacketWriter
{
    private byte[] _buffer;
    private int _position;

    public PacketWriter(int initialCapacity = 256)
    {
        _buffer = new byte[initialCapacity];
        _position = 0;
    }

    public int Length => _position;
    public byte[] Buffer => _buffer;
    public Span<byte> Span => _buffer.AsSpan(0, _position);
    public ReadOnlyMemory<byte> Memory => _buffer.AsMemory(0, _position);

    private void EnsureCapacity(int additional)
    {
        if (_position + additional > _buffer.Length)
        {
            int newCap = Math.Max(_buffer.Length * 2, _position + additional + 64);
            Array.Resize(ref _buffer, newCap);
        }
    }

    public PacketWriter WriteByte(byte value)
    {
        EnsureCapacity(1);
        _buffer[_position++] = value;
        return this;
    }

    public PacketWriter WriteBoolean(bool value) => WriteByte((byte)(value ? 1 : 0));

    public PacketWriter WriteInt16(short value)
    {
        EnsureCapacity(2);
        BinaryPrimitives.WriteInt16LittleEndian(_buffer.AsSpan(_position, 2), value);
        _position += 2;
        return this;
    }

    public PacketWriter WriteUInt16(ushort value)
    {
        EnsureCapacity(2);
        BinaryPrimitives.WriteUInt16LittleEndian(_buffer.AsSpan(_position, 2), value);
        _position += 2;
        return this;
    }

    public PacketWriter WriteInt32(int value)
    {
        EnsureCapacity(4);
        BinaryPrimitives.WriteInt32LittleEndian(_buffer.AsSpan(_position, 4), value);
        _position += 4;
        return this;
    }

    public PacketWriter WriteUInt32(uint value)
    {
        EnsureCapacity(4);
        BinaryPrimitives.WriteUInt32LittleEndian(_buffer.AsSpan(_position, 4), value);
        _position += 4;
        return this;
    }

    public PacketWriter WriteInt64(long value)
    {
        EnsureCapacity(8);
        BinaryPrimitives.WriteInt64LittleEndian(_buffer.AsSpan(_position, 8), value);
        _position += 8;
        return this;
    }

    public PacketWriter WriteUInt64(ulong value)
    {
        EnsureCapacity(8);
        BinaryPrimitives.WriteUInt64LittleEndian(_buffer.AsSpan(_position, 8), value);
        _position += 8;
        return this;
    }

    public PacketWriter WriteSingle(float value)
    {
        EnsureCapacity(4);
        BinaryPrimitives.WriteSingleLittleEndian(_buffer.AsSpan(_position, 4), value);
        _position += 4;
        return this;
    }

    public PacketWriter WriteDouble(double value)
    {
        EnsureCapacity(8);
        BinaryPrimitives.WriteDoubleLittleEndian(_buffer.AsSpan(_position, 8), value);
        _position += 8;
        return this;
    }

    public PacketWriter WriteBytes(ReadOnlySpan<byte> bytes)
    {
        EnsureCapacity(bytes.Length);
        bytes.CopyTo(_buffer.AsSpan(_position));
        _position += bytes.Length;
        return this;
    }

    public PacketWriter WriteStringUnicode(string value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            int byteCount = Encoding.Unicode.GetByteCount(value);
            EnsureCapacity(byteCount + 2);
            Encoding.Unicode.GetBytes(value, _buffer.AsSpan(_position, byteCount));
            _position += byteCount;
        }
        else
        {
            EnsureCapacity(2);
        }
        _buffer[_position++] = 0;
        _buffer[_position++] = 0;
        return this;
    }

    public PacketWriter WriteStringAscii(string value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            int byteCount = Encoding.UTF8.GetByteCount(value);
            EnsureCapacity(byteCount + 1);
            Encoding.UTF8.GetBytes(value, _buffer.AsSpan(_position, byteCount));
            _position += byteCount;
        }
        else
        {
            EnsureCapacity(1);
        }
        _buffer[_position++] = 0;
        return this;
    }

    public PacketWriter WriteZeros(int count)
    {
        EnsureCapacity(count);
        _buffer.AsSpan(_position, count).Clear();
        _position += count;
        return this;
    }

    public byte[] ToArray()
    {
        byte[] copy = new byte[_position];
        Array.Copy(_buffer, copy, _position);
        return copy;
    }
}
