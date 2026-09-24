using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Redirection;
using AcademyNoLag.Relay.Client;

namespace AcademyNoLag.Service;

internal class Program
{
    private static async Task Main(string[] args)
    {
        Console.Title = "Academy NoLag — Privileged Network Service";
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine(@"
╔══════════════════════════════════════════════════════════════════════╗
║              ACADEMY NOLAG PRIVILEGED NETWORK SERVICE                ║
║           Dynamic Windows Filtering Platform (WFP) Driver           ║
╚══════════════════════════════════════════════════════════════════════╝
");
        Console.ResetColor();

        using var relayClient = new RelayClient();
        using var redirector = new TrafficRedirector(relayClient);
        using var watchdog = new Watchdog(redirector);
        using var ipcServer = new IpcServer(redirector, watchdog);
        using var cts = new CancellationTokenSource();

        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        Console.WriteLine("[Service] Starting IPC Server on \\\\.\\pipe\\AcademyNoLag_IPC...");
        await ipcServer.StartAsync(cts.Token);

        Console.WriteLine("[Service] Service is running. Press Ctrl+C to stop.");

        try
        {
            await Task.Delay(Timeout.Infinite, cts.Token);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("[Service] Stopping and cleaning up WFP rules...");
            await redirector.DisableRedirectionAsync();
        }
    }
}
