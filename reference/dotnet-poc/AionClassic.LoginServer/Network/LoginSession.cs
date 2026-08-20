using System.Buffers.Binary;
using System.Net.Sockets;
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using AionClassic.LoginServer.Models;
using AionClassic.LoginServer.Services;
using AionClassic.Network.Crypto;
using AionClassic.Network.Packets;

namespace AionClassic.LoginServer.Network;

public class LoginSession
{
    private static readonly object _logLock = new();
    private readonly TcpClient _client;
    private readonly NetworkStream _stream;
    private readonly int _sessionId;
    private readonly RSA _rsa;
    private readonly RSAParameters _rsaParams;
    private readonly byte[] _blowfishKey;
    private readonly LoginCryptEngine _cryptEngine;
    private Account? _account;

    public LoginSession(TcpClient client, int sessionId)
    {
        _client = client;
        _stream = client.GetStream();
        _sessionId = sessionId;
        _rsa = RSA.Create(1024);
        _rsaParams = _rsa.ExportParameters(true);
        _blowfishKey = RandomNumberGenerator.GetBytes(16);
        _cryptEngine = new LoginCryptEngine();
    }

    private void Log(string msg)
    {
        string formatted = $"[{DateTime.Now:HH:mm:ss.fff}] [Session {_sessionId}] {msg}";
        Console.WriteLine(formatted);
        lock (_logLock)
        {
            try
            {
                File.AppendAllText(Path.Combine(AppContext.BaseDirectory, "login_debug.log"), formatted + Environment.NewLine);
            }
            catch { }
        }
    }

    public async Task RunAsync(CancellationToken ct)
    {
        Log($"Nova conexao estabelecida de {_client.Client.RemoteEndPoint}");

        try
        {
            // 1. Envia SM_INIT (Handshake de criptografia com flag 0xFD)
            await SendInitAsync(ct);

            // 2. Envia SM_AUTH_GG
            await Task.Delay(80, ct);
            await SendAuthGgAsync(ct);

            // 3. Envia SM_LOGIN_OK (com flags 0xFF, 0xFE e 0x3F)
            await Task.Delay(100, ct);
            _account = AccountManager.Instance.CreateOrGetAccount("durak", "durak", 0);
            await SendLoginOkAsync(ct);

            // 4. Envia SM_SERVER_LIST abrangente (com servidores para Brackets 0, 1 e 2)
            await Task.Delay(120, ct);
            await SendServerListAsync(ct);

            Log($"-> Handshake inicial concluido com sucesso. Aguardando pacotes do cliente...");

            // 5. Loop de recebimento de pacotes (CM_PLAY, etc)
            byte[] headerBuf = new byte[2];

            while (!ct.IsCancellationRequested && _client.Connected)
            {
                int read = await _stream.ReadAsync(headerBuf.AsMemory(0, 2), ct);
                if (read < 2)
                {
                    Log($"Conexao encerrada pelo cliente (read={read})");
                    break;
                }

                int packetLength = BinaryPrimitives.ReadInt16LittleEndian(headerBuf);
                Log($"<- [TCP Header] packetLength={packetLength} bytes");

                if (packetLength < 2 || packetLength > 65535)
                {
                    Log($"[ERRO] Tamanho de pacote invalido: {packetLength}");
                    break;
                }

                int payloadLen = packetLength - 2;
                byte[] payload = new byte[payloadLen];
                int totalRead = 0;

                while (totalRead < payloadLen)
                {
                    int r = await _stream.ReadAsync(payload.AsMemory(totalRead, payloadLen - totalRead), ct);
                    if (r <= 0) break;
                    totalRead += r;
                }

                if (totalRead < payloadLen)
                {
                    Log($"[ERRO] Payload truncado (lido {totalRead}/{payloadLen})");
                    break;
                }

                Log($"<- [Bruto Hex]: {Convert.ToHexString(payload)}");

                // Se o pacote tem 168 bytes (CM_LOGIN nativo do cliente):
                if (payload.Length == 168 || (payload.Length >= 5 && payload[4] == 0x0B))
                {
                    Log($"<- [CM_LOGIN] Pacote de login recebido. Confirmando SM_LOGIN_OK...");
                    await SendLoginOkAsync(ct);
                    await Task.Delay(80, ct);
                    await SendServerListAsync(ct);
                    continue;
                }

                // Descriptografa com Blowfish para pacotes normais
                byte[] decPayload = new byte[payload.Length];
                Array.Copy(payload, decPayload, payload.Length);
                bool decrypted = _cryptEngine.Decrypt(decPayload, 0, decPayload.Length);
                if (!decrypted)
                {
                    Log($"[AVISO] Checksum Blowfish divergente, tentando processar...");
                }
                else
                {
                    Log($"<- [Decriptado Hex]: {Convert.ToHexString(decPayload)}");
                }

                await HandlePacketAsync(decrypted ? decPayload : payload, ct);
            }
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            Log($"Excecao na sessao: {ex.Message} -> {ex.StackTrace}");
        }
        finally
        {
            _client.Dispose();
            _rsa.Dispose();
            Log($"Sessao finalizada.");
        }
    }

    private async Task SendInitAsync(CancellationToken ct)
    {
        byte[] scrambledModulus = ScrambleModulus(_rsaParams.Modulus!);

        var pw = new PacketWriter();
        pw.WriteByte(0x00) // Opcode SM_INIT (offset 0)
          .WriteInt32(_sessionId) // offset 1..4
          .WriteInt32(0x0000C621) // Protocol Revision (offset 5..8)
          .WriteBytes(scrambledModulus) // 128 bytes (offset 0x09 a 0x88)
          .WriteInt32(0) // offset 0x89..0x8C (4 bytes)
          .WriteInt32(0) // offset 0x8D..0x90 (4 bytes)
          .WriteInt32(0) // offset 0x91..0x94 (4 bytes)
          .WriteBytes(_blowfishKey) // 16 bytes (offset 0x95..0xA4)
          .WriteByte(0x00) // offset 0xA5
          .WriteByte(0x00) // offset 0xA6
          .WriteByte(0x00) // offset 0xA7
          .WriteByte(0xFD) // offset 0xA8 (0xFD exigido pelo Game.dll x64!)
          .WriteByte(0x04) // offset 0xA9 (Major version = 4)
          .WriteByte(0x05) // offset 0xAA (Minor version = 5)
          .WriteByte(0x00) // offset 0xAB (Patch = 0)
          .WriteByte(0x00); // offset 0xAC

        byte[] raw = pw.ToArray();

        int maxLen = 192;
        byte[] buffer = new byte[maxLen];
        Array.Copy(raw, buffer, raw.Length);

        // Atualiza a nova chave Blowfish que valerá após o SM_INIT
        _cryptEngine.UpdateKey(_blowfishKey);
        int encLength = _cryptEngine.Encrypt(buffer, 0, raw.Length);

        byte[] packet = new byte[encLength + 2];
        BinaryPrimitives.WriteInt16LittleEndian(packet.AsSpan(0, 2), (short)(encLength + 2));
        Array.Copy(buffer, 0, packet, 2, encLength);

        await _stream.WriteAsync(packet.AsMemory(), ct);
        Log($"-> SM_INIT enviado ({packet.Length} bytes) com flag 0xFD no offset 0xA8.");
    }

    private async Task HandlePacketAsync(byte[] payload, CancellationToken ct)
    {
        byte opcode = payload[0];
        Log($"<- Processando Opcode=0x{opcode:X2} (Len={payload.Length})");

        switch (opcode)
        {
            case 0x07: // CM_AUTH_GG
                await SendAuthGgAsync(ct);
                break;

            case 0x0B: // CM_LOGIN
            case 0x08: // CM_LOGIN alternate
                await HandleLoginAsync(payload, ct);
                break;

            case 0x05: // CM_SERVER_LIST (SendServerListExt)
                await SendServerListAsync(ct);
                break;

            case 0x02: // CM_PLAY
                await HandlePlayAsync(payload, ct);
                break;

            default:
                Log($"[AVISO] Opcode 0x{opcode:X2} recebido.");
                break;
        }
    }

    private async Task SendAuthGgAsync(CancellationToken ct)
    {
        var pw = new PacketWriter();
        pw.WriteByte(0x0B) // Opcode SM_AUTH_GG
          .WriteInt32(_sessionId)
          .WriteInt32(0).WriteInt32(0).WriteInt32(0).WriteInt32(0)
          .WriteBytes(new byte[0x19]);

        await SendEncryptedPacketAsync(pw.ToArray(), ct);
        Log($"-> SM_AUTH_GG enviado (SessionId={_sessionId})");
    }

    private async Task HandleLoginAsync(byte[] payload, CancellationToken ct)
    {
        try
        {
            string user = "durak";
            string pass = "durak";

            _account = AccountManager.Instance.Authenticate(user, pass, autoCreate: true);
            _account ??= AccountManager.Instance.CreateOrGetAccount("durak", "durak", 0);

            Log($"Login autenticado com sucesso para '{_account.Username}' (ID={_account.Id})");
            
            // 1. Envia SM_LOGIN_OK
            await SendLoginOkAsync(ct);

            // 2. Aguarda 80ms para a transição de estado e envia SM_SERVER_LIST
            await Task.Delay(80, ct);
            await SendServerListAsync(ct);
        }
        catch (Exception ex)
        {
            Log($"Erro ao processar CM_LOGIN: {ex.Message}");
            _account = AccountManager.Instance.CreateOrGetAccount("durak", "durak", 0);
            await SendLoginOkAsync(ct);
            await Task.Delay(80, ct);
            await SendServerListAsync(ct);
        }
    }

    private async Task SendLoginOkAsync(CancellationToken ct)
    {
        _account ??= AccountManager.Instance.CreateOrGetAccount("durak", "durak", 0);
        _account.SessionKey1 = Random.Shared.Next();
        _account.SessionKey2 = Random.Shared.Next();

        var pw = new PacketWriter();
        pw.WriteByte(0x03) // SM_LOGIN_OK
          .WriteInt32(_account.Id) // offset 0x00
          .WriteInt32(_account.SessionKey1) // offset 0x04
          .WriteInt32(0) // offset 0x08
          .WriteInt32(0) // offset 0x0C
          .WriteInt32(0x0000003F) // offset 0x10 (Flag 0x3F: Termos Aceitos bit 0x10 + Adulto + Ativo!)
          .WriteInt32(0x0000003F) // offset 0x14 (Flag 0x3F)
          .WriteInt32(0x0000003F) // offset 0x18 (Flag 0x3F)
          .WriteInt32(0x0000003F) // offset 0x1C (Flag 0x3F)
          .WriteByte(0xFF) // offset 0x20 (0xFF exigido pelo Game.dll no offset 0x717B40!)
          .WriteByte(0xFE) // offset 0x21 (0xFE exigido pelo Game.dll no offset 0x717B46!)
          .WriteByte(0x00) // offset 0x22
          .WriteByte(0x00) // offset 0x23
          .WriteInt32(0) // offset 0x24
          .WriteInt32(0) // offset 0x28
          .WriteInt32(0) // offset 0x2C
          .WriteInt32(0x00000001) // offset 0x30 (TOS Agreement = 1)
          .WriteBytes(new byte[0x19]);

        await SendEncryptedPacketAsync(pw.ToArray(), ct);
        Log($"-> SM_LOGIN_OK enviado com flags 0xFF/0xFE e Termos de Servico Aceitos (0x3F)!");
    }

    private async Task SendLoginFailAsync(CancellationToken ct)
    {
        var pw = new PacketWriter();
        pw.WriteByte(0x01) // SM_LOGIN_FAIL
          .WriteInt32(1); // Invalid password or user

        await SendEncryptedPacketAsync(pw.ToArray(), ct);
        Log($"-> SM_LOGIN_FAIL enviado");
    }

    private async Task SendServerListAsync(CancellationToken ct)
    {
        var pw = new PacketWriter();
        pw.WriteByte(0x04) // SM_SERVER_LIST (Opcode)
          .WriteByte(3)    // Server count = 3 servidores universais
          .WriteByte(1);   // Last server id = 1

        // Servidor 1: Bracket = 2 (EU Gameforge), ServerBits = 0x401
        WriteServerEntry(pw, serverId: 1, bracket: 2, serverBits: 0x00000401);

        // Servidor 2: Bracket = 1 (NA / Global), ServerBits = 0x00000401
        WriteServerEntry(pw, serverId: 2, bracket: 1, serverBits: 0x00000401);

        // Servidor 3: Bracket = 0 (Universal), ServerBits = 0x00000401
        WriteServerEntry(pw, serverId: 3, bracket: 0, serverBits: 0x00000401);

        // Character counts section (3 servidores)
        pw.WriteInt16(3)  // Total de servidores na lista de contagem = 3
          .WriteByte(0)   // Server 1 char count = 0
          .WriteByte(0)   // Server 2 char count = 0
          .WriteByte(0);  // Server 3 char count = 0

        await SendEncryptedPacketAsync(pw.ToArray(), ct);
        Log($"-> SM_SERVER_LIST enviado (3 servidores para Brackets 0, 1 e 2 em 127.0.0.1:7777)");
    }

    private static void WriteServerEntry(PacketWriter pw, byte serverId, byte bracket, int serverBits)
    {
        pw.WriteByte(serverId) // Server ID (offset 0)
          .WriteByte(127).WriteByte(0).WriteByte(0).WriteByte(1) // Server IP = 127.0.0.1 (offset 1..4)
          .WriteInt32(7777) // GameServer Port = 7777 (offset 5..8)
          .WriteByte(0)     // Age limit = 0 (offset 9)
          .WriteByte(1)     // PvP = 1 (offset 10)
          .WriteInt16(0)    // Current players (offset 11..12)
          .WriteInt16(1000) // Max players (offset 13..14)
          .WriteByte(1)     // Status: Online = 1 (offset 15)
          .WriteInt32(serverBits) // Server Bits (offset 16..19)
          .WriteByte(bracket);    // Bracket / Country Code (offset 20)
    }

    private async Task HandlePlayAsync(byte[] payload, CancellationToken ct)
    {
        byte serverId = (payload.Length > 1 && payload[1] > 0) ? payload[1] : (byte)1;
        Log($"<- [CM_PLAY] Pedido de entrada no servidor {serverId} recebido.");
        await SendPlayOkAsync(serverId, ct);
    }

    private async Task SendPlayOkAsync(byte serverId, CancellationToken ct)
    {
        _account ??= AccountManager.Instance.CreateOrGetAccount("durak", "durak", 0);
        _account.SessionKey1 = _account.SessionKey1 == 0 ? Random.Shared.Next() : _account.SessionKey1;
        _account.SessionKey2 = _account.SessionKey2 == 0 ? Random.Shared.Next() : _account.SessionKey2;

        var pw = new PacketWriter();
        pw.WriteByte(0x07) // SM_PLAY_OK (Opcode)
          .WriteInt32(_account.SessionKey1)
          .WriteInt32(_account.SessionKey2)
          .WriteByte(serverId);

        await SendEncryptedPacketAsync(pw.ToArray(), ct);
        Log($"-> SM_PLAY_OK enviado com sucesso para o servidor {serverId}! (SessionKey1={_account.SessionKey1}, SessionKey2={_account.SessionKey2})");
    }

    private async Task SendEncryptedPacketAsync(byte[] raw, CancellationToken ct)
    {
        int maxLen = raw.Length + 32;
        byte[] buffer = new byte[maxLen];
        Array.Copy(raw, buffer, raw.Length);

        int encLength = _cryptEngine.Encrypt(buffer, 0, raw.Length);

        byte[] packet = new byte[encLength + 2];
        BinaryPrimitives.WriteInt16LittleEndian(packet.AsSpan(0, 2), (short)(encLength + 2));
        Array.Copy(buffer, 0, packet, 2, encLength);

        await _stream.WriteAsync(packet.AsMemory(), ct);
    }

    private static byte[] DecryptRawRsa(byte[] data, RSAParameters rsaParams)
    {
        var c = new BigInteger(data, isUnsigned: true, isBigEndian: true);
        var d = new BigInteger(rsaParams.D!, isUnsigned: true, isBigEndian: true);
        var n = new BigInteger(rsaParams.Modulus!, isUnsigned: true, isBigEndian: true);
        var m = BigInteger.ModPow(c, d, n);
        byte[] result = m.ToByteArray(isUnsigned: true, isBigEndian: true);
        if (result.Length < 128)
        {
            byte[] padded = new byte[128];
            Array.Copy(result, 0, padded, 128 - result.Length, result.Length);
            return padded;
        }
        return result;
    }

    private static byte[] ScrambleModulus(byte[] modulus)
    {
        byte[] encryptedModulus = new byte[0x80];
        if (modulus.Length == 0x81 && modulus[0] == 0x00)
        {
            Array.Copy(modulus, 1, encryptedModulus, 0, 0x80);
        }
        else if (modulus.Length == 0x80)
        {
            Array.Copy(modulus, 0, encryptedModulus, 0, 0x80);
        }
        else
        {
            Array.Copy(modulus, 0, encryptedModulus, 0x80 - modulus.Length, modulus.Length);
        }

        for (int i = 0; i < 4; i++)
        {
            byte temp = encryptedModulus[i];
            encryptedModulus[i] = encryptedModulus[0x4D + i];
            encryptedModulus[0x4D + i] = temp;
        }

        for (int i = 0; i < 0x40; i++)
        {
            encryptedModulus[i] = (byte)(encryptedModulus[i] ^ encryptedModulus[0x40 + i]);
        }

        for (int i = 0; i < 4; i++)
        {
            encryptedModulus[0x0D + i] = (byte)(encryptedModulus[0x0D + i] ^ encryptedModulus[0x34 + i]);
        }

        for (int i = 0; i < 0x40; i++)
        {
            encryptedModulus[0x40 + i] = (byte)(encryptedModulus[0x40 + i] ^ encryptedModulus[i]);
        }

        return encryptedModulus;
    }
}
