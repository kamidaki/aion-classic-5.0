using System.Buffers.Binary;

namespace AionClassic.Network.Crypto;

/// <summary>
/// Motor de criptografia para os pacotes do LoginServer (Aion Classic).
/// Cuida do handshake inicial, XOR pass, checksum e cipher Blowfish desmontados do Game.dll x64.
/// </summary>
public sealed class LoginCryptEngine
{
    private static readonly byte[] StaticKey =
    [
        0x6b, 0x60, 0xcb, 0x5b,
        0x82, 0xce, 0x90, 0xb1,
        0xcc, 0x2b, 0x6c, 0x55,
        0x6c, 0x6c, 0x6c, 0x6c
    ];

    private byte[] _currentKey;
    private bool _updatedKey;
    private readonly BlowfishCipher _cipher;

    public LoginCryptEngine()
    {
        _currentKey = (byte[])StaticKey.Clone();
        _cipher = new BlowfishCipher(_currentKey);
    }

    public void UpdateKey(byte[] newKey)
    {
        _currentKey = newKey;
    }

    public bool Decrypt(Span<byte> data, int offset, int length)
    {
        _cipher.Decipher(data, offset, length);
        return VerifyChecksum(data, offset, length);
    }

    public int Encrypt(Span<byte> data, int offset, int length, int xorSeed = 0)
    {
        if (!_updatedKey)
        {
            // Primeiro pacote (SM_INIT): precisa de padding para múltiplo de 8 e pelo menos 8 bytes no final
            int totalLen = 192; // Tamanho padrão exato do buffer de SM_INIT para Game.dll x64

            EncXorPass(data, offset, totalLen, xorSeed != 0 ? xorSeed : Random.Shared.Next());
            _cipher.Cipher(data, offset, totalLen);
            _cipher.UpdateKey(_currentKey);
            _updatedKey = true;
            return totalLen;
        }
        else
        {
            int pad = 8 - ((length + 4) % 8);
            int totalLen = length + 4 + (pad == 8 ? 0 : pad);
            AppendChecksum(data, offset, totalLen);
            _cipher.Cipher(data, offset, totalLen);
            return totalLen;
        }
    }

    public static bool VerifyChecksum(ReadOnlySpan<byte> data, int offset, int length)
    {
        if ((length & 3) != 0 || length <= 4)
            return false;

        uint chksum = 0;
        int count = length - 4;
        int i = offset;

        for (; i < count; i += 4)
        {
            uint check = data[i];
            check |= (uint)data[i + 1] << 8;
            check |= (uint)data[i + 2] << 16;
            check |= (uint)data[i + 3] << 24;
            chksum ^= check;
        }

        uint finalCheck = data[i];
        finalCheck |= (uint)data[i + 1] << 8;
        finalCheck |= (uint)data[i + 2] << 16;
        finalCheck |= (uint)data[i + 3] << 24;
        chksum ^= finalCheck;

        return chksum == 0;
    }

    public static void AppendChecksum(Span<byte> raw, int offset, int length)
    {
        uint chksum = 0;
        int count = length - 4;
        int i = offset;

        for (; i < count; i += 4)
        {
            uint ecx = raw[i];
            ecx |= (uint)raw[i + 1] << 8;
            ecx |= (uint)raw[i + 2] << 16;
            ecx |= (uint)raw[i + 3] << 24;
            chksum ^= ecx;
        }

        raw[i] = (byte)(chksum & 0xFF);
        raw[i + 1] = (byte)((chksum >> 8) & 0xFF);
        raw[i + 2] = (byte)((chksum >> 16) & 0xFF);
        raw[i + 3] = (byte)((chksum >> 24) & 0xFF);
    }

    private static void EncXorPass(Span<byte> data, int offset, int totalLen, int key)
    {
        int ecx = (totalLen - 8) / 4;
        uint currKey = (uint)key;

        for (int i = 1; i < ecx; i++)
        {
            int p = offset + i * 4;
            uint plain = BinaryPrimitives.ReadUInt32LittleEndian(data.Slice(p, 4));
            currKey += plain;
            uint cipher = plain ^ currKey;
            BinaryPrimitives.WriteUInt32LittleEndian(data.Slice(p, 4), cipher);
        }

        int keyOffset = offset + totalLen - 8;
        BinaryPrimitives.WriteUInt32LittleEndian(data.Slice(keyOffset, 4), currKey);
    }
}
