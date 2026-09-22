using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
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
                using var proc = Process.GetProcessById(currentActive.ProcessId);
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
        int currentPid = Environment.ProcessId;

        // 1. Fast targeted check for known profile processes
        try
        {
            var searchNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var p in _profileManager.Profiles)
            {
                foreach (var name in p.ProcessNames)
                {
                    if (string.IsNullOrWhiteSpace(name)) continue;
                    searchNames.Add(name); // e.g. "Aion.bin"
                    string noExt = Path.GetFileNameWithoutExtension(name);
                    if (!string.IsNullOrWhiteSpace(noExt)) searchNames.Add(noExt); // e.g. "Aion"
                }
                foreach (var pattern in p.ExecutablePatterns)
                {
                    if (string.IsNullOrWhiteSpace(pattern)) continue;
                    searchNames.Add(pattern);
                    string noExt = Path.GetFileNameWithoutExtension(pattern);
                    if (!string.IsNullOrWhiteSpace(noExt)) searchNames.Add(noExt);
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
                        if (proc.Id == currentPid) continue;
                        string procName = proc.ProcessName;
                        if (procName.StartsWith("Academy", StringComparison.OrdinalIgnoreCase)) continue;

                        string? mainModulePath = null;
                        string? windowTitle = null;

                        try { windowTitle = proc.MainWindowTitle; } catch { }
                        if (string.IsNullOrWhiteSpace(windowTitle))
                        {
                            windowTitle = GetProcessVisibleWindowTitle(proc.Id);
                        }

                        try
                        {
                            mainModulePath = proc.MainModule?.FileName;
                        }
                        catch { /* 64-bit or unprivileged access */ }

                        // Match by processName (+ exe path when available)
                        var profile = _profileManager.FindMatchingProfile(procName, mainModulePath);

                        // FALLBACK: if no match by name, try window title
                        if (profile == null && !string.IsNullOrEmpty(windowTitle))
                            profile = _profileManager.FindMatchingProfileByWindowTitle(windowTitle);

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

        // Phase 2: Fallback scan across all active processes
        // Matches by ProcessName, ExecutablePath, or WindowTitle (essential for emulators / private servers)
        Process[] processes;
        try { processes = Process.GetProcesses(); }
        catch { return matched; }

        foreach (var proc in processes)
        {
            try
            {
                if (proc.Id == currentPid) continue;
                string procName = proc.ProcessName;
                if (procName.StartsWith("Academy", StringComparison.OrdinalIgnoreCase)) continue;

                string? mainModulePath = null;
                string? windowTitle = null;

                try { windowTitle = proc.MainWindowTitle; } catch { }
                if (string.IsNullOrWhiteSpace(windowTitle))
                {
                    windowTitle = GetProcessVisibleWindowTitle(proc.Id);
                }

                try { mainModulePath = proc.MainModule?.FileName; } catch { }

                var profile = _profileManager.FindMatchingProfile(procName, mainModulePath);
                if (profile == null && !string.IsNullOrEmpty(windowTitle))
                {
                    profile = _profileManager.FindMatchingProfileByWindowTitle(windowTitle);
                }

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
                    break;
                }
            }
            catch { }
            finally { proc.Dispose(); }
        }

        if (matched.Count > 0) return matched;

        // Phase 3: Universal window-title scan
        var titleMatched = ScanByWindowTitle();
        if (titleMatched.Count > 0) return titleMatched;

        return matched;
    }

    /// <summary>
    /// Phase 3 scan: enumerate all processes with a visible window and match by window title.
    /// Works even when the process has a custom/unexpected name.
    /// </summary>
    private List<GameProcess> ScanByWindowTitle()
    {
        var matched = new List<GameProcess>();
        int currentPid = Environment.ProcessId;

        Process[] processes;
        try { processes = Process.GetProcesses(); }
        catch { return matched; }

        foreach (var proc in processes)
        {
            try
            {
                if (proc.Id == currentPid) continue;

                string procName = proc.ProcessName;
                if (procName.StartsWith("Academy", StringComparison.OrdinalIgnoreCase)) continue;

                string? windowTitle = null;
                try { windowTitle = proc.MainWindowTitle; } catch { }
                if (string.IsNullOrWhiteSpace(windowTitle))
                {
                    windowTitle = GetProcessVisibleWindowTitle(proc.Id);
                }

                if (string.IsNullOrWhiteSpace(windowTitle)) continue;

                var profile = _profileManager.FindMatchingProfileByWindowTitle(windowTitle);
                if (profile != null)
                {
                    string? mainModulePath = null;
                    try { mainModulePath = proc.MainModule?.FileName; } catch { }

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
            catch { }
            finally { proc.Dispose(); }
        }

        return matched;
    }

    #region Win32 Window Title Resolver
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    private static string? GetProcessVisibleWindowTitle(int pid)
    {
        string? result = null;
        try
        {
            EnumWindows((hWnd, lParam) =>
            {
                if (IsWindowVisible(hWnd))
                {
                    GetWindowThreadProcessId(hWnd, out uint windowPid);
                    if (windowPid == pid)
                    {
                        var sb = new StringBuilder(256);
                        int len = GetWindowText(hWnd, sb, sb.Capacity);
                        if (len > 0)
                        {
                            string title = sb.ToString();
                            if (!string.IsNullOrWhiteSpace(title))
                            {
                                result = title;
                                return false; // Found visible title, terminate search
                            }
                        }
                    }
                }
                return true;
            }, IntPtr.Zero);
        }
        catch { }
        return result;
    }
    #endregion

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
