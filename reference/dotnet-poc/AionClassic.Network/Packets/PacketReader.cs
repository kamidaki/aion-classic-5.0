using System.Buffers.Binary;
using System.Text;

namespace AionClassic.Network.Packets;

public ref struct PacketReader
{
    private readonly ReadOnlySpan<byte> _data;
    private int _position;

    public PacketReader(ReadOnlySpan<byte> data)
    {
        _data = data;
        _position = 0;
    }

    public int Position => _position;
    public int Remaining => _data.Length - _position;
    public int Length => _data.Length;

    public byte ReadByte()
    {
        if (_position >= _data.Length) return 0;
        return _data[_position++];
    }

    public bool ReadBoolean() => ReadByte() != 0;

    public short ReadInt16()
    {
        if (Remaining < 2) return 0;
        var val = BinaryPrimitives.ReadInt16LittleEndian(_data.Slice(_position, 2));
        _position += 2;
        return val;
    }

    public ushort ReadUInt16()
    {
        if (Remaining < 2) return 0;
        var val = BinaryPrimitives.ReadUInt16LittleEndian(_data.Slice(_position, 2));
        _position += 2;
        return val;
    }

    public int ReadInt32()
    {
        if (Remaining < 4) return 0;
        var val = BinaryPrimitives.ReadInt32LittleEndian(_data.Slice(_position, 4));
        _position += 4;
        return val;
    }

    public uint ReadUInt32()
    {
        if (Remaining < 4) return 0;
        var val = BinaryPrimitives.ReadUInt32LittleEndian(_data.Slice(_position, 4));
        _position += 4;
        return val;
    }

    public long ReadInt64()
    {
        if (Remaining < 8) return 0;
        var val = BinaryPrimitives.ReadInt64LittleEndian(_data.Slice(_position, 8));
        _position += 8;
        return val;
    }

    public ulong ReadUInt64()
    {
        if (Remaining < 8) return 0;
        var val = BinaryPrimitives.ReadUInt64LittleEndian(_data.Slice(_position, 8));
        _position += 8;
        return val;
    }

    public float ReadSingle()
    {
        if (Remaining < 4) return 0f;
        var val = BinaryPrimitives.ReadSingleLittleEndian(_data.Slice(_position, 4));
        _position += 4;
        return val;
    }

    public double ReadDouble()
    {
        if (Remaining < 8) return 0.0;
        var val = BinaryPrimitives.ReadDoubleLittleEndian(_data.Slice(_position, 8));
        _position += 8;
        return val;
    }

    public ReadOnlySpan<byte> ReadBytes(int count)
    {
        if (count > Remaining) count = Remaining;
        var slice = _data.Slice(_position, count);
        _position += count;
        return slice;
    }

    public string ReadStringUnicode()
    {
        int start = _position;
        while (_position + 1 < _data.Length)
        {
            if (_data[_position] == 0 && _data[_position + 1] == 0)
            {
                int len = _position - start;
                _position += 2;
                return Encoding.Unicode.GetString(_data.Slice(start, len));
            }
            _position += 2;
        }
        int remainingLen = _data.Length - start;
        _position = _data.Length;
        return Encoding.Unicode.GetString(_data.Slice(start, remainingLen));
    }

    public string ReadStringAscii()
    {
        int start = _position;
        while (_position < _data.Length)
        {
            if (_data[_position] == 0)
            {
                int len = _position - start;
                _position++;
                return Encoding.UTF8.GetString(_data.Slice(start, len));
            }
            _position++;
        }
        int remainingLen = _data.Length - start;
        _position = _data.Length;
        return Encoding.UTF8.GetString(_data.Slice(start, remainingLen));
    }
}
