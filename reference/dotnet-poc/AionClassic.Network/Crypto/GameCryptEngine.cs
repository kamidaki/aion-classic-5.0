using System.Buffers.Binary;
using System.Text;

namespace AionClassic.Network.Crypto;

/// <summary>
/// Motor de criptografia para pacotes do GameServer (Aion Classic).
/// Utiliza a cifra de fluxo dinâmica com tabela estática XOR de 64 bytes
/// e ofuscação de opcodes.
/// </summary>
public sealed class GameCryptEngine
{
    private static readonly byte[] StaticKey = "nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"u8.ToArray();

    public const byte StaticServerPacketCode = 0x40;
    public const byte StaticClientPacketCode = 0x6F;

    private readonly byte[] _serverKey = new byte[8];
    private readonly byte[] _clientKey = new byte[8];

    public bool IsEnabled { get; set; }
    public int BaseKey { get; private set; }

    public int EnableKey(int? customKey = null)
    {
        int key = customKey ?? Random.Shared.Next();
        BaseKey = key;

        _serverKey[0] = (byte)(key & 0xFF);
        _serverKey[1] = (byte)((key >> 8) & 0xFF);
        _serverKey[2] = (byte)((key >> 16) & 0xFF);
        _serverKey[3] = (byte)((key >> 24) & 0xFF);
        _serverKey[4] = 0xA1;
        _serverKey[5] = 0x6C;
        _serverKey[6] = 0x54;
        _serverKey[7] = 0x87;

        Array.Copy(_serverKey, _clientKey, 8);

        // Retorna a "false key" enviada para o cliente no pacote SM_KEY
        return (int)(((uint)key ^ 0xCD92E451u) + 0x3FF2CC87u);
    }

    public void SetClientKey(int key)
    {
        BaseKey = key;
        _serverKey[0] = (byte)(key & 0xFF);
        _serverKey[1] = (byte)((key >> 8) & 0xFF);
        _serverKey[2] = (byte)((key >> 16) & 0xFF);
        _serverKey[3] = (byte)((key >> 24) & 0xFF);
        _serverKey[4] = 0xA1;
        _serverKey[5] = 0x6C;
        _serverKey[6] = 0x54;
        _serverKey[7] = 0x87;

        Array.Copy(_serverKey, _clientKey, 8);
        IsEnabled = true;
    }

    public bool DecryptClient(Span<byte> data)
    {
        if (!IsEnabled)
            return true;

        int size = data.Length;
        int prev = data[0];
        data[0] ^= _clientKey[0];

        for (int i = 1; i < size; i++)
        {
            int curr = data[i];
            data[i] ^= (byte)(StaticKey[i & 63] ^ _clientKey[i & 7] ^ prev);
            prev = curr;
        }

        ulong oldKey = BinaryPrimitives.ReadUInt64LittleEndian(_clientKey);
        oldKey += (ulong)size;

        if (ValidateClientPacket(data))
        {
            BinaryPrimitives.WriteUInt64LittleEndian(_clientKey, oldKey);
            return true;
        }

        return false;
    }

    public void EncryptServer(Span<byte> data)
    {
        if (!IsEnabled)
        {
            IsEnabled = true;
            return;
        }

        int size = data.Length;
        data[0] ^= _serverKey[0];
        int prev = data[0];

        for (int i = 1; i < size; i++)
        {
            data[i] ^= (byte)(StaticKey[i & 63] ^ _serverKey[i & 7] ^ prev);
            prev = data[i];
        }

        ulong oldKey = BinaryPrimitives.ReadUInt64LittleEndian(_serverKey);
        oldKey += (ulong)size;
        BinaryPrimitives.WriteUInt64LittleEndian(_serverKey, oldKey);
    }

    public static bool ValidateClientPacket(ReadOnlySpan<byte> buf)
    {
        if (buf.Length < 5) return false;
        short s0 = BinaryPrimitives.ReadInt16LittleEndian(buf[0..2]);
        short s3 = BinaryPrimitives.ReadInt16LittleEndian(buf[3..5]);
        byte b2 = buf[2];
        return (s0 == (short)~s3) && (b2 == StaticClientPacketCode);
    }

    public static int EncodeServerOpcode(int op) => (op + 0xC0) ^ 0xCF;
    public static int DecodeServerOpcode(int op) => (op ^ 0xCF) - 0xC0;
    public static int DecryptClientOpcode(int op) => ((op ^ 0x20) - 0xB4) ^ 0x1E;
}
