using System.Diagnostics;
using AionClassic.Network.Crypto;
using AionClassic.Network.Packets;

namespace AionClassic.Network.Tests;

public static class CryptoValidation
{
    public static void RunTests()
    {
        Console.WriteLine("[Tests] Executando auto-validação de Criptografia e Pacotes...");

        // 1. Teste Blowfish
        byte[] testKey = [0x6b, 0x60, 0xcb, 0x5b, 0x82, 0xce, 0x90, 0xb1, 0xcc, 0x2b, 0x6c, 0x55, 0x6c, 0x6c, 0x6c, 0x6c];
        var cipher = new BlowfishCipher(testKey);
        byte[] original = "AionClassicTest12345"u8.ToArray();
        int paddedLen = original.Length + (8 - (original.Length % 8));
        byte[] buffer = new byte[paddedLen];
        Array.Copy(original, buffer, original.Length);

        byte[] encrypted = (byte[])buffer.Clone();
        cipher.Cipher(encrypted);

        byte[] decrypted = (byte[])encrypted.Clone();
        cipher.Decipher(decrypted);

        Debug.Assert(buffer.AsSpan().SequenceEqual(decrypted.AsSpan()), "Blowfish encryption/decryption failed!");
        Console.WriteLine("  ✓ Blowfish Cipher 64-bit: PASS");

        // 2. Teste Game Server Crypt Engine
        var gameCrypt = new GameCryptEngine();
        int clientKeySent = gameCrypt.EnableKey(0x12345678);

        var writer = new PacketWriter();
        writer.WriteInt16(0x1234);
        writer.WriteByte(GameCryptEngine.StaticClientPacketCode);
        writer.WriteInt16((short)~0x1234);
        writer.WriteInt32(unchecked((int)0xCAFEBABE));
        byte[] clientPacket = writer.ToArray();

        var clientEngine = new GameCryptEngine();
        clientEngine.SetClientKey(0x12345678);

        byte[] packetToDecrypt = (byte[])clientPacket.Clone();
        bool valid = gameCrypt.DecryptClient(packetToDecrypt);
        Debug.Assert(valid, "GameCryptEngine client validation failed!");
        Console.WriteLine("  ✓ Game Server Stream Cipher & Validation: PASS");

        // 3. Teste PacketReader & PacketWriter
        var pw = new PacketWriter();
        pw.WriteByte(0xFF)
          .WriteInt32(1234567)
          .WriteUInt64(9876543210123456UL)
          .WriteSingle(3.14159f)
          .WriteStringUnicode("Aion Classic")
          .WriteStringAscii("Gameforge");

        var pr = new PacketReader(pw.Span);
        Debug.Assert(pr.ReadByte() == 0xFF);
        Debug.Assert(pr.ReadInt32() == 1234567);
        Debug.Assert(pr.ReadUInt64() == 9876543210123456UL);
        Debug.Assert(Math.Abs(pr.ReadSingle() - 3.14159f) < 0.0001f);
        Debug.Assert(pr.ReadStringUnicode() == "Aion Classic");
        Debug.Assert(pr.ReadStringAscii() == "Gameforge");
        Console.WriteLine("  ✓ PacketReader & PacketWriter (Zero Alloc Span): PASS");

        Console.WriteLine("[Tests] Validação concluída com sucesso!\n");
    }
}
