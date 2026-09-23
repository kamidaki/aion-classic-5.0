using System.Buffers;

namespace AcademyNoLag.Relay.Pool;

public sealed class RentedBuffer : IDisposable
{
    private byte[]? _buffer;
    public byte[] Buffer => _buffer ?? throw new ObjectDisposedException(nameof(RentedBuffer));
    public int Length { get; }

    public Memory<byte> Memory => new(Buffer, 0, Length);
    public Span<byte> Span => new(Buffer, 0, Length);

    public RentedBuffer(int minimumSize)
    {
        _buffer = ArrayPool<byte>.Shared.Rent(minimumSize);
        Length = minimumSize;
    }

    public void Dispose()
    {
        if (_buffer != null)
        {
            ArrayPool<byte>.Shared.Return(_buffer);
            _buffer = null;
        }
    }
}

public static class BufferManager
{
    public static RentedBuffer Rent(int size) => new(size);
}
