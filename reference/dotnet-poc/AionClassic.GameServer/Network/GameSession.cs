using System.Buffers.Binary;
using System.Net.Sockets;
using System.Text;
using AionClassic.Common.Models;
using AionClassic.GameServer.Models;
using AionClassic.GameServer.Services;
using AionClassic.GameServer.World;
using AionClassic.Network.Crypto;
using AionClassic.Network.Packets;

namespace AionClassic.GameServer.Network;

public class GameSession
{
    private readonly TcpClient _client;
    private readonly NetworkStream _stream;
    private readonly int _sessionId;
    private readonly GameCryptEngine _cryptEngine;

    public int AccountId { get; set; } = 1;
    public Player? ActivePlayer { get; set; }

    public GameSession(TcpClient client, int sessionId)
    {
        _client = client;
        _stream = client.GetStream();
        _sessionId = sessionId;
        _cryptEngine = new GameCryptEngine();
    }

    public async Task RunAsync(CancellationToken ct)
    {
        Console.WriteLine($"[GameServer] Nova conexão estabelecida. Session ID: {_sessionId}");

        try
        {
            // 1. Envia SM_KEY inicial (não criptografado)
            await SendSmKeyAsync(ct);

            // 2. Loop de leitura de pacotes
            byte[] headerBuf = new byte[2];

            while (!ct.IsCancellationRequested && _client.Connected)
            {
                int read = await _stream.ReadAsync(headerBuf.AsMemory(0, 2), ct);
                if (read < 2) break;

                int packetLength = BinaryPrimitives.ReadInt16LittleEndian(headerBuf);
                if (packetLength < 5 || packetLength > 65535) break;

                int payloadLen = packetLength - 2;
                byte[] payload = new byte[payloadLen];
                int totalRead = 0;

                while (totalRead < payloadLen)
                {
                    int r = await _stream.ReadAsync(payload.AsMemory(totalRead, payloadLen - totalRead), ct);
                    if (r <= 0) break;
                    totalRead += r;
                }

                if (totalRead < payloadLen) break;

                // Descriptografa pacote com cifra de fluxo dinâmica
                bool valid = _cryptEngine.DecryptClient(payload);
                if (!valid)
                {
                    Console.WriteLine($"[GameServer] Falha de validação/checksum de pacote do cliente {_sessionId}");
                    break;
                }

                await HandlePacketAsync(payload, ct);
            }
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            Console.WriteLine($"[GameServer] Erro na sessão {_sessionId}: {ex.Message}");
        }
        finally
        {
            WorldManager.Instance.UnregisterPlayer(this);
            _client.Dispose();
            Console.WriteLine($"[GameServer] Sessão encerrada. Session ID: {_sessionId}");
        }
    }

    private async Task SendSmKeyAsync(CancellationToken ct)
    {
        int key = _cryptEngine.EnableKey();

        var pw = new PacketWriter();
        pw.WriteByte(0x00)
          .WriteByte(GameCryptEngine.StaticServerPacketCode) // 0x40 no Classic
          .WriteInt32(key);

        byte[] raw = pw.ToArray();
        byte[] packet = new byte[raw.Length + 2];
        BinaryPrimitives.WriteInt16LittleEndian(packet.AsSpan(0, 2), (short)(raw.Length + 2));
        Array.Copy(raw, 0, packet, 2, raw.Length);

        await _stream.WriteAsync(packet.AsMemory(), ct);
        Console.WriteLine($"[GameServer] -> SM_KEY enviado (False Key=0x{key:X8})");
    }

    private async Task HandlePacketAsync(byte[] payload, CancellationToken ct)
    {
        // O payload descriptografado do cliente tem formato:
        // [0..1] short s0, [2] StaticClientPacketCode (0x6F), [3..4] ~s0, [5..6] opcode
        if (payload.Length < 7) return;

        ushort rawOpcode = BinaryPrimitives.ReadUInt16LittleEndian(payload.AsSpan(5, 2));
        int opcode = GameCryptEngine.DecryptClientOpcode(rawOpcode);

        Console.WriteLine($"[GameServer] <- Pacote recebido: Opcode=0x{opcode:X4} (Raw=0x{rawOpcode:X4}, Len={payload.Length})");

        switch (opcode)
        {
            case 0x0014: // CM_VERSION_CHECK
            case 0x001F:
                await SendVersionCheckAsync(ct);
                break;

            case 0x002B: // CM_CHARACTER_LIST
            case 0x0001:
                await SendCharacterListAsync(ct);
                break;

            case 0x002C: // CM_CREATE_CHARACTER
                await HandleCreateCharacterAsync(payload, ct);
                break;

            case 0x002E: // CM_ENTER_WORLD
                await HandleEnterWorldAsync(payload, ct);
                break;

            case 0x003A: // CM_MOVE
                await HandleMoveAsync(payload, ct);
                break;

            case 0x004F: // CM_CHAT
                await HandleChatAsync(payload, ct);
                break;

            default:
                Console.WriteLine($"[GameServer] Opcode de jogo 0x{opcode:X4} recebido");
                break;
        }
    }

    private async Task SendVersionCheckAsync(CancellationToken ct)
    {
        var pw = new PacketWriter();
        pw.WriteInt16((short)GameCryptEngine.EncodeServerOpcode(0x0014)) // SM_VERSION_CHECK
          .WriteByte(0)    // Status OK
          .WriteByte(2)    // Country Code (EU = 2)
          .WriteInt32(0)
          .WriteInt32(0)
          .WriteInt32((int)DateTimeOffset.UtcNow.ToUnixTimeSeconds());

        await SendPacketAsync(pw.ToArray(), ct);
        Console.WriteLine("[GameServer] -> SM_VERSION_CHECK enviado");
    }

    private async Task SendCharacterListAsync(CancellationToken ct)
    {
        var players = PlayerService.Instance.GetPlayersByAccountId(AccountId);

        var pw = new PacketWriter();
        pw.WriteInt16((short)GameCryptEngine.EncodeServerOpcode(0x002B)) // SM_CHARACTER_LIST
          .WriteByte((byte)players.Count); // Contagem de personagens

        foreach (var player in players)
        {
            pw.WriteInt32(player.Id)
              .WriteStringUnicode(player.Name)
              .WriteByte((byte)player.Gender)
              .WriteByte((byte)player.Race)
              .WriteByte((byte)player.PlayerClass)
              .WriteInt32(player.Level)
              .WriteInt32(player.WorldId)
              .WriteSingle(player.X)
              .WriteSingle(player.Y)
              .WriteSingle(player.Z)
              .WriteInt32(player.Hp)
              .WriteInt32(player.MaxHp)
              .WriteInt32(player.Mp)
              .WriteInt32(player.MaxMp);
        }

        await SendPacketAsync(pw.ToArray(), ct);
        Console.WriteLine($"[GameServer] -> SM_CHARACTER_LIST enviado ({players.Count} personagens)");
    }

    private async Task HandleCreateCharacterAsync(byte[] payload, CancellationToken ct)
    {
        var pr = new PacketReader(payload);
        pr.ReadInt16(); // s0
        pr.ReadByte();  // code
        pr.ReadInt16(); // ~s0
        pr.ReadInt16(); // opcode

        string name = pr.ReadStringUnicode();
        byte genderByte = pr.ReadByte();
        byte raceByte = pr.ReadByte();
        byte classByte = pr.ReadByte();

        var appearance = new PlayerAppearance
        {
            Voice = pr.ReadByte(),
            SkinColor = pr.ReadByte(),
            HairColor = pr.ReadByte(),
            EyeColor = pr.ReadByte(),
            Face = pr.ReadByte(),
            Hair = pr.ReadByte(),
            Height = pr.ReadSingle()
        };

        var created = PlayerService.Instance.CreateCharacter(
            AccountId,
            name,
            (Race)raceByte,
            (PlayerClass)classByte,
            (Gender)genderByte,
            appearance
        );

        var pw = new PacketWriter();
        pw.WriteInt16((short)GameCryptEngine.EncodeServerOpcode(0x002C)) // SM_CREATE_CHARACTER
          .WriteByte((byte)(created != null ? 0 : 1)); // 0 = Sucesso

        await SendPacketAsync(pw.ToArray(), ct);
    }

    private async Task HandleEnterWorldAsync(byte[] payload, CancellationToken ct)
    {
        var pr = new PacketReader(payload);
        pr.ReadInt16(); // s0
        pr.ReadByte();  // code
        pr.ReadInt16(); // ~s0
        pr.ReadInt16(); // opcode
        int playerId = pr.ReadInt32();

        ActivePlayer = PlayerService.Instance.GetPlayerById(playerId);

        if (ActivePlayer != null)
        {
            WorldManager.Instance.RegisterPlayer(this);

            var pw = new PacketWriter();
            pw.WriteInt16((short)GameCryptEngine.EncodeServerOpcode(0x002E)) // SM_ENTER_WORLD_CHECK
              .WriteInt32(ActivePlayer.WorldId)
              .WriteSingle(ActivePlayer.X)
              .WriteSingle(ActivePlayer.Y)
              .WriteSingle(ActivePlayer.Z)
              .WriteByte(ActivePlayer.Heading);

            await SendPacketAsync(pw.ToArray(), ct);
            Console.WriteLine($"[GameServer] -> SM_ENTER_WORLD_CHECK enviado para '{ActivePlayer.Name}' no mapa {ActivePlayer.WorldId}");
        }
    }

    private async Task HandleMoveAsync(byte[] payload, CancellationToken ct)
    {
        if (ActivePlayer == null) return;

        var pr = new PacketReader(payload);
        pr.ReadInt16(); // s0
        pr.ReadByte();  // code
        pr.ReadInt16(); // ~s0
        pr.ReadInt16(); // opcode

        float x = pr.ReadSingle();
        float y = pr.ReadSingle();
        float z = pr.ReadSingle();
        byte heading = pr.ReadByte();

        ActivePlayer.X = x;
        ActivePlayer.Y = y;
        ActivePlayer.Z = z;
        ActivePlayer.Heading = heading;

        // Broadcast de movimento para os demais jogadores no mapa
        var pw = new PacketWriter();
        pw.WriteInt16((short)GameCryptEngine.EncodeServerOpcode(0x003A)) // SM_MOVE
          .WriteInt32(ActivePlayer.Id)
          .WriteSingle(x)
          .WriteSingle(y)
          .WriteSingle(z)
          .WriteByte(heading);

        await WorldManager.Instance.BroadcastToMapAsync(ActivePlayer.WorldId, pw.ToArray(), exceptPlayerId: ActivePlayer.Id);
    }

    private async Task HandleChatAsync(byte[] payload, CancellationToken ct)
    {
        if (ActivePlayer == null) return;

        var pr = new PacketReader(payload);
        pr.ReadInt16(); // s0
        pr.ReadByte();  // code
        pr.ReadInt16(); // ~s0
        pr.ReadInt16(); // opcode
        string message = pr.ReadStringUnicode();

        Console.WriteLine($"[Chat] [{ActivePlayer.Name}]: {message}");

        var pw = new PacketWriter();
        pw.WriteInt16((short)GameCryptEngine.EncodeServerOpcode(0x004F)) // SM_MESSAGE
          .WriteInt32(ActivePlayer.Id)
          .WriteStringUnicode(ActivePlayer.Name)
          .WriteStringUnicode(message);

        await WorldManager.Instance.BroadcastToMapAsync(ActivePlayer.WorldId, pw.ToArray());
    }

    public async Task SendPacketAsync(byte[] raw, CancellationToken ct)
    {
        byte[] buffer = new byte[raw.Length + 4];
        BinaryPrimitives.WriteInt16LittleEndian(buffer.AsSpan(0, 2), 0x1234);
        buffer[2] = GameCryptEngine.StaticServerPacketCode;
        BinaryPrimitives.WriteInt16LittleEndian(buffer.AsSpan(3, 2), (short)~0x1234);
        Array.Copy(raw, 0, buffer, 5, raw.Length);

        _cryptEngine.EncryptServer(buffer);

        byte[] packet = new byte[buffer.Length + 2];
        BinaryPrimitives.WriteInt16LittleEndian(packet.AsSpan(0, 2), (short)(buffer.Length + 2));
        Array.Copy(buffer, 0, packet, 2, buffer.Length);

        await _stream.WriteAsync(packet.AsMemory(), ct);
    }

    public async Task SendRawPacketAsync(byte[] raw)
    {
        try
        {
            await SendPacketAsync(raw, CancellationToken.None);
        }
        catch { }
    }
}
