using System.Net;
using System.Net.Sockets;
using System.Text;
using AionClassic.LoginServer.Network;

namespace AionClassic.LoginServer;

public static class Program
{
    private static int _sessionCounter = 0;

    public static async Task Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine("==========================================================");
        Console.WriteLine("        Aion Classic (EU 4.5) - Login Server (.NET 9)     ");
        Console.WriteLine("==========================================================");
        Console.ResetColor();

        int port = 2106;
        if (args.Length > 0 && int.TryParse(args[0], out int customPort))
        {
            port = customPort;
        }

        var listener = new TcpListener(IPAddress.Any, port);
        try
        {
            listener.Start();
            Console.WriteLine($"[LoginServer] Escutando em 0.0.0.0:{port} (Porta de Autenticação Aion)");
            Console.WriteLine("[LoginServer] Servidor pronto para conexões do cliente x64.");
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
                    var session = new LoginSession(tcpClient, sessionId);
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
                        Console.WriteLine($"[LoginServer] Erro ao aceitar conexão: {ex.Message}");
                    }
                }
            }
        }
        finally
        {
            listener.Stop();
            Console.WriteLine("[LoginServer] Servidor finalizado.");
        }
    }
}
