using System.Net;
using System.Net.Sockets;
using System.Text;
using AionClassic.Data;
using AionClassic.GameServer.Network;

namespace AionClassic.GameServer;

public static class Program
{
    private static int _sessionCounter = 0;

    public static async Task Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.ForegroundColor = ConsoleColor.Magenta;
        Console.WriteLine("==========================================================");
        Console.WriteLine("        Aion Classic (EU 4.5) - Game Server (.NET 9)      ");
        Console.WriteLine("==========================================================");
        Console.ResetColor();

        // 1. Carrega dados estáticos
        string staticDataPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "legacy_java", "AL-Game", "data", "static_data");
        if (Directory.Exists(staticDataPath))
        {
            DataManager.Instance.LoadData(staticDataPath);
        }
        else
        {
            DataManager.Instance.LoadData(AppContext.BaseDirectory);
        }

        // 2. Inicia servidor TCP na porta 7777
        int port = 7777;
        if (args.Length > 0 && int.TryParse(args[0], out int customPort))
        {
            port = customPort;
        }

        var listener = new TcpListener(IPAddress.Any, port);
        try
        {
            listener.Start();
            Console.WriteLine($"[GameServer] Escutando em 0.0.0.0:{port} (Porta do Mundo Aion)");
            Console.WriteLine("[GameServer] Servidor pronto para receber conexões dos jogadores.");
            Console.WriteLine("Pressione Ctrl+C para encerrar o servidor.");
            Console.WriteLine("----------------------------------------------------------");

            var cts = new CancellationTokenSource();
            Console.CancelKeyPress += (s, e) =>
            {
                e.Cancel = true;
                cts.Cancel();
                listener.Stop();
            };

            while (!cts.IsCancellationRequested)
            {
                try
                {
                    var tcpClient = await listener.AcceptTcpClientAsync(cts.Token);
                    int sessionId = Interlocked.Increment(ref _sessionCounter);
                    var session = new GameSession(tcpClient, sessionId);
                    _ = Task.Run(() => session.RunAsync(cts.Token), cts.Token);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    if (!cts.IsCancellationRequested)
                    {
                        Console.WriteLine($"[GameServer] Erro ao aceitar conexão: {ex.Message}");
                    }
                }
            }
        }
        finally
        {
            listener.Stop();
            Console.WriteLine("[GameServer] Servidor finalizado.");
        }
    }
}
