using System.IO.Pipes;
using System.Text.Json;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Service;

public class IpcServer : IDisposable
{
    public const string PipeName = "AcademyNoLag_IPC";
    private readonly ITrafficRedirector _redirector;
    private readonly Watchdog _watchdog;
    private CancellationTokenSource? _cts;
    private Task? _serverTask;

    public IpcServer(ITrafficRedirector redirector, Watchdog watchdog)
    {
        _redirector = redirector;
        _watchdog = watchdog;
    }

    public Task StartAsync(CancellationToken cancellationToken = default)
    {
        _cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        _serverTask = RunServerLoopAsync(_cts.Token);
        return Task.CompletedTask;
    }

    private async Task RunServerLoopAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            try
            {
                using var pipe = new NamedPipeServerStream(
                    PipeName,
                    PipeDirection.InOut,
                    NamedPipeServerStream.MaxAllowedServerInstances,
                    PipeTransmissionMode.Byte,
                    PipeOptions.Asynchronous);

                await pipe.WaitForConnectionAsync(cancellationToken);
                await HandleClientPipeAsync(pipe, cancellationToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[IPC Server Error] {ex.Message}");
            }
        }
    }

    private async Task HandleClientPipeAsync(NamedPipeServerStream pipe, CancellationToken cancellationToken)
    {
        using var reader = new StreamReader(pipe);
        using var writer = new StreamWriter(pipe) { AutoFlush = true };

        string? requestLine = await reader.ReadLineAsync(cancellationToken);
        if (string.IsNullOrEmpty(requestLine)) return;

        _watchdog.Heartbeat();

        try
        {
            var req = JsonSerializer.Deserialize<IpcRequest>(requestLine);
            if (req == null) return;

            IpcResponse resp = req.Command switch
            {
                "Ping" => new IpcResponse(true, "Pong"),
                "GetStatus" => new IpcResponse(true, "OK", _redirector.IsActive ? "Optimized" : "Direct"),
                "Stop" => await HandleStopAsync(),
                _ => new IpcResponse(false, $"Unknown command: {req.Command}")
            };

            string responseJson = JsonSerializer.Serialize(resp);
            await writer.WriteLineAsync(responseJson.AsMemory(), cancellationToken);
        }
        catch (Exception ex)
        {
            var errResp = new IpcResponse(false, ex.Message);
            await writer.WriteLineAsync(JsonSerializer.Serialize(errResp).AsMemory(), cancellationToken);
        }
    }

    private async Task<IpcResponse> HandleStopAsync()
    {
        await _redirector.DisableRedirectionAsync();
        return new IpcResponse(true, "Redirection disabled, network restored to default.");
    }

    public void Dispose()
    {
        _cts?.Cancel();
        _cts?.Dispose();
        GC.SuppressFinalize(this);
    }
}
