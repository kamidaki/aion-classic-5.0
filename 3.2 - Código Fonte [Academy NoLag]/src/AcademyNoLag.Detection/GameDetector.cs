using System.Diagnostics;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Detection;

public class GameDetector : IGameDetector
{
    public event EventHandler<GameProcess>? GameDetected;
    public event EventHandler<GameProcess>? GameExited;

    private readonly ProfileManager _profileManager;
    private readonly TimeSpan _scanInterval;
    private CancellationTokenSource? _scanCts;
    private Task? _scanTask;
    private readonly object _lock = new();

    private GameProcess? _activeGame;
    private GameProfile? _activeProfile;

    public GameProcess? ActiveGame
    {
        get { lock (_lock) return _activeGame; }
        private set { lock (_lock) _activeGame = value; }
    }

    public GameProfile? ActiveProfile
    {
        get { lock (_lock) return _activeProfile; }
        private set { lock (_lock) _activeProfile = value; }
    }

    public bool IsMonitoring => _scanTask != null && !_scanTask.IsCompleted;

    public GameDetector(ProfileManager profileManager, TimeSpan? scanInterval = null)
    {
        _profileManager = profileManager;
        _scanInterval = scanInterval ?? TimeSpan.FromSeconds(2);
    }

    public Task StartMonitoringAsync(CancellationToken cancellationToken = default)
    {
        if (IsMonitoring) return Task.CompletedTask;

        _scanCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        _scanTask = RunMonitoringLoopAsync(_scanCts.Token);
        return Task.CompletedTask;
    }

    public async Task StopMonitoringAsync()
    {
        if (_scanCts != null)
        {
            _scanCts.Cancel();
            if (_scanTask != null)
            {
                try { await _scanTask; }
                catch (OperationCanceledException) { }
            }
            _scanCts.Dispose();
            _scanCts = null;
            _scanTask = null;
        }
    }

    private async Task RunMonitoringLoopAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            try
            {
                CheckForRunningGames();
            }
            catch (Exception)
            {
                // Continue scanning loop despite transient OS errors
            }

            try
            {
                await Task.Delay(_scanInterval, cancellationToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    public void CheckForRunningGames()
    {
        var currentActive = ActiveGame;

        // Verify if currently tracked game is still alive
        if (currentActive != null)
        {
            bool isStillAlive = false;
            try
            {
                var proc = Process.GetProcessById(currentActive.ProcessId);
                isStillAlive = !proc.HasExited;
            }
            catch
            {
                isStillAlive = false;
            }

            if (!isStillAlive)
            {
                var exited = currentActive;
                ActiveGame = null;
                ActiveProfile = null;
                GameExited?.Invoke(this, exited);
            }
            else
            {
                // Game still running, nothing more needed
                return;
            }
        }

        // Scan for new running games matching profiles
        var runningGames = ScanRunningProcesses();
        if (runningGames.Count > 0)
        {
            var detected = runningGames[0];
            var profile = _profileManager.FindMatchingProfile(detected.ProcessName, detected.ExecutablePath);

            ActiveGame = detected;
            ActiveProfile = profile;

            GameDetected?.Invoke(this, detected);
        }
    }

    public IReadOnlyList<GameProcess> ScanRunningProcesses()
    {
        var matched = new List<GameProcess>();

        // 1. Fast targeted check for known profile processes (0% CPU impact)
        try
        {
            var searchNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var p in _profileManager.Profiles)
            {
                foreach (var name in p.ProcessNames)
                {
                    string noExt = Path.GetFileNameWithoutExtension(name);
                    if (!string.IsNullOrEmpty(noExt)) searchNames.Add(noExt);
                    string withExt = Path.GetFileName(name);
                    if (!string.IsNullOrEmpty(withExt)) searchNames.Add(withExt);
                }
            }

            foreach (var baseName in searchNames)
            {
                if (string.IsNullOrEmpty(baseName)) continue;
                Process[] foundProcs;
                try { foundProcs = Process.GetProcessesByName(baseName); }
                catch { continue; }

                foreach (var proc in foundProcs)
                {
                    try
                    {
                        string procName = proc.ProcessName;
                        string? mainModulePath = null;
                        string? windowTitle = null;

                        try
                        {
                            windowTitle = proc.MainWindowTitle;
                            mainModulePath = proc.MainModule?.FileName;
                        }
                        catch { /* System/protected process */ }

                        var profile = _profileManager.FindMatchingProfile(procName, mainModulePath);
                        if (profile != null)
                        {
                            matched.Add(new GameProcess(
                                ProcessId: proc.Id,
                                ProcessName: procName,
                                ExecutablePath: mainModulePath ?? procName,
                                CommandLine: null,
                                StartTime: null,
                                MainWindowTitle: windowTitle
                            ));
                        }
                    }
                    catch { /* Skip */ }
                    finally
                    {
                        // Dispose Win32 process handle to prevent handle leak across polling cycles
                        proc.Dispose();
                    }
                }
            }
        }
        catch { /* Resilient targeted lookup */ }

        if (matched.Count > 0)
        {
            return matched;
        }

        // 2. Fallback full scan only if targeted didn't match (e.g. for custom profile patterns)
        Process[] processes;
        try
        {
            processes = Process.GetProcesses();
        }
        catch
        {
            return matched;
        }

        foreach (var proc in processes)
        {
            try
            {
                string procName = proc.ProcessName;
                string? mainModulePath = null;
                string? windowTitle = null;

                try
                {
                    windowTitle = proc.MainWindowTitle;
                    mainModulePath = proc.MainModule?.FileName;
                }
                catch { /* Privilege access denied on system processes */ }

                var profile = _profileManager.FindMatchingProfile(procName, mainModulePath);
                if (profile != null)
                {
                    matched.Add(new GameProcess(
                        ProcessId: proc.Id,
                        ProcessName: procName,
                        ExecutablePath: mainModulePath ?? procName,
                        CommandLine: null,
                        StartTime: null,
                        MainWindowTitle: windowTitle
                    ));
                }
            }
            catch { /* Skip unreadable processes */ }
            finally
            {
                // Dispose Win32 process handle to prevent handle leak during full-scan fallback
                proc.Dispose();
            }
        }

        return matched;
    }

    public void SetManualGame(GameProcess game, GameProfile? profile = null)
    {
        ActiveGame = game;
        ActiveProfile = profile ?? _profileManager.FindMatchingProfile(game.ProcessName, game.ExecutablePath);
        GameDetected?.Invoke(this, game);
    }

    public void ClearActiveGame()
    {
        var active = ActiveGame;
        if (active != null)
        {
            ActiveGame = null;
            ActiveProfile = null;
            GameExited?.Invoke(this, active);
        }
    }

    public void Dispose()
    {
        _scanCts?.Cancel();
        _scanCts?.Dispose();
        GC.SuppressFinalize(this);
    }
}
