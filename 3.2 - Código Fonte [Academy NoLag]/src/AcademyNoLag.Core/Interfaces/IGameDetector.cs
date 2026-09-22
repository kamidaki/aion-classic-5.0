using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Interfaces;

public interface IGameDetector : IDisposable
{
    event EventHandler<GameProcess>? GameDetected;
    event EventHandler<GameProcess>? GameExited;

    GameProcess? ActiveGame { get; }
    GameProfile? ActiveProfile { get; }
    bool IsMonitoring { get; }

    Task StartMonitoringAsync(CancellationToken cancellationToken = default);
    Task StopMonitoringAsync();
    IReadOnlyList<GameProcess> ScanRunningProcesses();
}
