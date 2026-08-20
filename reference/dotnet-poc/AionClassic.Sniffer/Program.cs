using System.Buffers.Binary;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using AionClassic.Common.Models;
using AionClassic.Common.Utils;
using AionClassic.Network.Crypto;
using AionClassic.Network.Tests;

namespace AionClassic.Sniffer;

public class PacketLogEntry
{
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public string Direction { get; set; } = string.Empty;
    public int Port { get; set; }
    public string OpcodeHex { get; set; } = string.Empty;
    public int Opcode { get; set; }
    public int Length { get; set; }
    public string PayloadHex { get; set; } = string.Empty;
    public string AsciiPreview { get; set; } = string.Empty;
}

public static class Program
{
    private static readonly object _fileLock = new();
    private static string _logFilePath = string.Empty;

    public static async Task Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("==========================================================");
        Console.WriteLine("  Aion Classic (EU 4.5) - Real-Time Packet Sniffer & Proxy");
        Console.WriteLine("  C# .NET 9 Interceptor");
        Console.WriteLine("==========================================================");
        Console.ResetColor();

        // 1. Executa auto-validação criptográfica
        CryptoValidation.RunTests();

        string logDir = Path.Combine(AppContext.BaseDirectory, "captures");
        Directory.CreateDirectory(logDir);
        _logFilePath = Path.Combine(logDir, $"capture_{DateTime.Now:yyyyMMdd_HHmmss}.jsonl");
        Console.WriteLine($"[Sniffer] Arquivo de log: {_logFilePath}\n");

        // Configuração de portas
        int loginLocalPort = 2106;
        string loginTargetHost = "127.0.0.1";
        int loginTargetPort = 21060;

        int gameLocalPort = 7777;
        string gameTargetHost = "127.0.0.1";
        int gameTargetPort = 77770;

        // Permite passar argumentos via CLI: --login-target 127.0.0.1:21060 --game-target 127.0.0.1:77770
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--login-target" && i + 1 < args.Length)
            {
                var parts = args[i + 1].Split(':');
                loginTargetHost = parts[0];
                if (parts.Length > 1) loginTargetPort = int.Parse(parts[1]);
            }
            else if (args[i] == "--game-target" && i + 1 < args.Length)
            {
                var parts = args[i + 1].Split(':');
                gameTargetHost = parts[0];
                if (parts.Length > 1) gameTargetPort = int.Parse(parts[1]);
            }
        }

        Console.WriteLine($"[Config] Login Proxy: 0.0.0.0:{loginLocalPort} -> {loginTargetHost}:{loginTargetPort}");
        Console.WriteLine($"[Config] Game  Proxy: 0.0.0.0:{gameLocalPort}  -> {gameTargetHost}:{gameTargetPort}");
        Console.WriteLine("----------------------------------------------------------");
        Console.WriteLine("Status: ESCUTANDO. Abra o cliente do Aion para capturar...");
        Console.WriteLine("Pressione Ctrl+C para encerrar a captura a qualquer momento.");
        Console.WriteLine("----------------------------------------------------------\n");

        var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (s, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        var loginTask = StartLoginProxyAsync(loginLocalPort, loginTargetHost, loginTargetPort, cts.Token);
        var gameTask = StartGameProxyAsync(gameLocalPort, gameTargetHost, gameTargetPort, cts.Token);

        await Task.WhenAll(loginTask, gameTask);
    }

    private static async Task StartLoginProxyAsync(int localPort, string targetHost, int targetPort, CancellationToken ct)
    {
        var listener = new TcpListener(IPAddress.Any, localPort);
        listener.Start();

        while (!ct.IsCancellationRequested)
        {
            try
            {
                var clientSocket = await listener.AcceptTcpClientAsync(ct);
                _ = Task.Run(() => HandleLoginSessionAsync(clientSocket, targetHost, targetPort, ct), ct);
            }
            catch (OperationCanceledException) { break; }
            catch (Exception ex)
            {
                Console.WriteLine($"[Login Proxy Error] {ex.Message}");
            }
        }
    }

    private static async Task HandleLoginSessionAsync(TcpClient client, string targetHost, int targetPort, CancellationToken ct)
    {
        using (client)
        using (var target = new TcpClient())
        {
            try
            {
                await target.ConnectAsync(targetHost, targetPort, ct);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine($"\n[Login] Conexão ativa! Cliente: {client.Client.RemoteEndPoint} -> Servidor: {targetHost}:{targetPort}");
                Console.ResetColor();

                var cryptEngine = new LoginCryptEngine();

                var clientStream = client.GetStream();
                var targetStream = target.GetStream();

                var c2s = ForwardLoginStreamAsync(clientStream, targetStream, cryptEngine, PacketDirection.ClientToServer, 2106, ct);
                var s2c = ForwardLoginStreamAsync(targetStream, clientStream, cryptEngine, PacketDirection.ServerToClient, 2106, ct);

                await Task.WhenAny(c2s, s2c);
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.DarkYellow;
                Console.WriteLine($"[Login Session Closed] {ex.Message}");
                Console.ResetColor();
            }
        }
    }

    private static async Task ForwardLoginStreamAsync(NetworkStream source, NetworkStream dest, LoginCryptEngine crypt, PacketDirection dir, int port, CancellationToken ct)
    {
        byte[] buffer = new byte[8192];
        while (!ct.IsCancellationRequested)
        {
            int read = await ReadExactAsync(source, buffer.AsMemory(0, 2), ct);
            if (read == 0) break;

            ushort packetLength = BinaryPrimitives.ReadUInt16LittleEndian(buffer.AsSpan(0, 2));
            if (packetLength < 2 || packetLength > 8192) break;

            int payloadLength = packetLength - 2;
            if (payloadLength > 0)
            {
                read = await ReadExactAsync(source, buffer.AsMemory(2, payloadLength), ct);
                if (read == 0) break;
            }

            await dest.WriteAsync(buffer.AsMemory(0, packetLength), ct);

            byte[] copy = new byte[packetLength];
            Array.Copy(buffer, copy, packetLength);

            int opcode = payloadLength > 0 ? copy[2] : 0;
            LogPacket(dir, port, opcode, copy.AsSpan(2, payloadLength));
        }
    }

    private static async Task StartGameProxyAsync(int localPort, string targetHost, int targetPort, CancellationToken ct)
    {
        var listener = new TcpListener(IPAddress.Any, localPort);
        listener.Start();

        while (!ct.IsCancellationRequested)
        {
            try
            {
                var clientSocket = await listener.AcceptTcpClientAsync(ct);
                _ = Task.Run(() => HandleGameSessionAsync(clientSocket, targetHost, targetPort, ct), ct);
            }
            catch (OperationCanceledException) { break; }
            catch (Exception ex)
            {
                Console.WriteLine($"[Game Proxy Error] {ex.Message}");
            }
        }
    }

    private static async Task HandleGameSessionAsync(TcpClient client, string targetHost, int targetPort, CancellationToken ct)
    {
        using (client)
        using (var target = new TcpClient())
        {
            try
            {
                await target.ConnectAsync(targetHost, targetPort, ct);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine($"\n[Game] Conexão ativa! Cliente: {client.Client.RemoteEndPoint} -> Servidor: {targetHost}:{targetPort}");
                Console.ResetColor();

                var cryptEngine = new GameCryptEngine();

                var clientStream = client.GetStream();
                var targetStream = target.GetStream();

                var c2s = ForwardGameStreamAsync(clientStream, targetStream, cryptEngine, PacketDirection.ClientToServer, 7777, ct);
                var s2c = ForwardGameStreamAsync(targetStream, clientStream, cryptEngine, PacketDirection.ServerToClient, 7777, ct);

                await Task.WhenAny(c2s, s2c);
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.DarkYellow;
                Console.WriteLine($"[Game Session Closed] {ex.Message}");
                Console.ResetColor();
            }
        }
    }

    private static async Task ForwardGameStreamAsync(NetworkStream source, NetworkStream dest, GameCryptEngine crypt, PacketDirection dir, int port, CancellationToken ct)
    {
        byte[] buffer = new byte[65536];
        while (!ct.IsCancellationRequested)
        {
            int read = await ReadExactAsync(source, buffer.AsMemory(0, 2), ct);
            if (read == 0) break;

            ushort packetLength = BinaryPrimitives.ReadUInt16LittleEndian(buffer.AsSpan(0, 2));
            if (packetLength < 2) break;

            int payloadLength = packetLength - 2;
            if (payloadLength > 0)
            {
                read = await ReadExactAsync(source, buffer.AsMemory(2, payloadLength), ct);
                if (read == 0) break;
            }

            await dest.WriteAsync(buffer.AsMemory(0, packetLength), ct);

            byte[] packetPayload = new byte[payloadLength];
            Array.Copy(buffer, 2, packetPayload, 0, payloadLength);

            if (dir == PacketDirection.ClientToServer)
            {
                crypt.DecryptClient(packetPayload);
            }

            int rawOpcode = packetPayload.Length > 0 ? packetPayload[0] : 0;
            int decodedOpcode = dir == PacketDirection.ServerToClient
                ? GameCryptEngine.DecodeServerOpcode(rawOpcode)
                : rawOpcode;

            LogPacket(dir, port, decodedOpcode, packetPayload);
        }
    }

    private static async Task<int> ReadExactAsync(NetworkStream stream, Memory<byte> target, CancellationToken ct)
    {
        int totalRead = 0;
        while (totalRead < target.Length)
        {
            int read = await stream.ReadAsync(target.Slice(totalRead), ct);
            if (read == 0) return 0;
            totalRead += read;
        }
        return totalRead;
    }

    private static void LogPacket(PacketDirection dir, int port, int opcode, ReadOnlySpan<byte> payload)
    {
        string dirStr = dir == PacketDirection.ClientToServer ? "C2S" : "S2C";
        string opHex = $"0x{opcode:X2}";
        string payloadHex = ByteUtils.ToHexString(payload);

        var previewSb = new StringBuilder();
        foreach (byte b in payload)
        {
            previewSb.Append(b >= 32 && b <= 126 ? (char)b : '.');
        }

        var entry = new PacketLogEntry
        {
            Timestamp = DateTime.UtcNow,
            Direction = dirStr,
            Port = port,
            OpcodeHex = opHex,
            Opcode = opcode,
            Length = payload.Length,
            PayloadHex = payloadHex,
            AsciiPreview = previewSb.ToString()
        };

        var origColor = Console.ForegroundColor;
        Console.ForegroundColor = dir == PacketDirection.ClientToServer ? ConsoleColor.Yellow : ConsoleColor.Magenta;
        string previewPart = payloadHex.Length > 48 ? payloadHex[..48] + "..." : payloadHex;
        Console.WriteLine($"[{DateTime.Now:HH:mm:ss.fff}] [{dirStr}] [Porta {port}] Opcode: {opHex} (len: {payload.Length}) | {previewPart}");
        Console.ResetColor();

        string json = JsonSerializer.Serialize(entry);
        lock (_fileLock)
        {
            File.AppendAllText(_logFilePath, json + Environment.NewLine);
        }
    }
}
