namespace AcademyNoLag.RelayNode;

internal class Program
{
    private static async Task Main(string[] args)
    {
        Console.Title = "Academy NoLag — Edge Optimization Relay Server";
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine(@"
╔══════════════════════════════════════════════════════════════════════╗
║                   ACADEMY NOLAG RELAY NODE SERVER                   ║
║         Enterprise Game Routing Optimization Gateway (v1.0)          ║
╚══════════════════════════════════════════════════════════════════════╝
");
        Console.ResetColor();

        int port = 42420;
        string region = "BR-Local";

        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--port" && i + 1 < args.Length && int.TryParse(args[i + 1], out int p))
            {
                port = p;
            }
            if (args[i] == "--region" && i + 1 < args.Length)
            {
                region = args[i + 1];
            }
        }

        var config = new NodeConfig(Port: port, Region: region);
        using var server = new NodeServer(config);
        using var cts = new CancellationTokenSource();

        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        var serverTask = server.StartAsync(cts.Token);

        // Status update loop
        _ = Task.Run(async () =>
        {
            while (!cts.Token.IsCancellationRequested)
            {
                await Task.Delay(5000, cts.Token);
                Console.WriteLine($"[Telemetry] Active Clients: {server.ActiveClientCount} | Total Packets: {server.PacketsForwarded} | Bytes: {server.BytesTransferred / 1024} KB");
            }
        }, cts.Token);

        try
        {
            await serverTask;
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("[Relay Node] Shutting down cleanly...");
        }
    }
}
