using System.Diagnostics;
using System.Net;
using System.Net.NetworkInformation;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using AcademyNoLag.Core.Models;
using Microsoft.Win32;

namespace AcademyNoLag.Network.Optimization;

[SupportedOSPlatform("windows")]
public class WindowsNetworkOptimizer : IDisposable
{
    [DllImport("winmm.dll", EntryPoint = "timeBeginPeriod", SetLastError = true)]
    private static extern uint TimeBeginPeriod(uint uMilliseconds);

    [DllImport("winmm.dll", EntryPoint = "timeEndPeriod", SetLastError = true)]
    private static extern uint TimeEndPeriod(uint uMilliseconds);

    private readonly Dictionary<string, object?> _originalRegistryValues = [];
    private readonly HashSet<string> _injectedHostRoutes = [];
    private static bool _globalTcpStackOptimized = false;
    private bool _isOptimized = false;
    private bool _timePeriodActive = false;
    private int _lastOptimizedPid = -1;
    private string? _lastOptimizedIp = null;
    private readonly object _lock = new();

    public bool IsOptimized
    {
        get { lock (_lock) return _isOptimized; }
    }

    public bool ApplyOptimizations(GameProcess? activeGame = null, IPAddress? targetServerIp = null)
    {
        lock (_lock)
        {
            int currentPid = activeGame?.ProcessId ?? -1;
            string? currentIp = targetServerIp?.ToString();

            // Prevent redundant re-execution if already optimized for this game session
            if (_isOptimized && _lastOptimizedPid == currentPid && _lastOptimizedIp == currentIp)
            {
                return true;
            }

            try
            {
                // Request 1.0 ms OS kernel multimedia timer resolution (down from default 15.6 ms)
                // This eliminates Winsock socket dispatch jitter and delayed ACK scheduling latency
                if (!_timePeriodActive)
                {
                    TimeBeginPeriod(1);
                    _timePeriodActive = true;
                }

                // 1. Disable Windows Multimedia Network Throttling & Tune MMCSS Game Scheduling
                OptimizeSystemProfile();

                // 2. Optimize TCP Parameters on Active Interfaces (TcpAckFrequency, TCPDelAckTicks, TcpNoDelay)
                OptimizeNetworkInterfaces();

                // 3. Remove Windows 20% Reserved Bandwidth (NonBestEffortLimit = 0)
                OptimizeQoSBandwidth();

                // 4. Kernel TCP Global Stack Tuning via netsh (ECN, RSS, Timestamps, TaskOffload)
                OptimizeTcpGlobalStack();

                // 5. Configure Gaming QoS Policy and boost Process Priority if game process is provided
                if (activeGame != null)
                {
                    ConfigureGamingQoS(activeGame.ProcessName);
                    BoostGameProcessPriority(activeGame.ProcessId);
                }

                // 6. Inject High-Priority Host Route (/32 metric 1) for the Game Server
                if (targetServerIp != null && !IPAddress.IsLoopback(targetServerIp))
                {
                    InjectHostRoute(targetServerIp);
                }

                // 7. Flush DNS resolver cache (WITHOUT deleting ARP cache, which causes game stutter)
                FlushNetworkCaches();

                _isOptimized = true;
                _lastOptimizedPid = currentPid;
                _lastOptimizedIp = currentIp;
                return true;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[NetworkOptimizer] Failed to apply optimizations: {ex.Message}");
                return false;
            }
        }
    }

    public bool RestoreDefaults(bool force = false)
    {
        lock (_lock)
        {
            if (!_isOptimized) return true;

            try
            {
                // Check if the game is still running!
                // If the game is still running, NEVER delete the injected route or cut the connection!
                bool gameStillRunning = false;
                if (!force && _lastOptimizedPid > 0)
                {
                    try
                    {
                        var proc = Process.GetProcessById(_lastOptimizedPid);
                        gameStillRunning = !proc.HasExited;
                    }
                    catch { gameStillRunning = false; }
                }

                if (!gameStillRunning)
                {
                    // 1. Remove injected host routes only if game actually exited or force=true
                    foreach (var ip in _injectedHostRoutes)
                    {
                        RemoveHostRoute(ip);
                    }
                    _injectedHostRoutes.Clear();
                }

                // 2. Restore backed up registry keys
                foreach (var (keyPath, originalVal) in _originalRegistryValues)
                {
                    try
                    {
                        int lastSlash = keyPath.LastIndexOf('\\');
                        if (lastSlash > 0)
                        {
                            string subKey = keyPath[..lastSlash];
                            string valueName = keyPath[(lastSlash + 1)..];

                            using var regKey = Registry.LocalMachine.OpenSubKey(subKey, writable: true);
                            if (regKey != null)
                            {
                                if (originalVal != null)
                                {
                                    regKey.SetValue(valueName, originalVal);
                                }
                                else
                                {
                                    regKey.DeleteValue(valueName, throwOnMissingValue: false);
                                }
                            }
                        }
                    }
                    catch { /* Best effort restoration */ }
                }

                _originalRegistryValues.Clear();
                _injectedHostRoutes.Clear();

                if (_timePeriodActive)
                {
                    TimeEndPeriod(1);
                    _timePeriodActive = false;
                }

                _lastOptimizedPid = -1;
                _lastOptimizedIp = null;
                _isOptimized = false;
                return true;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[NetworkOptimizer] Failed to restore defaults: {ex.Message}");
                return false;
            }
        }
    }

    private void OptimizeSystemProfile()
    {
        const string profileKeyPath = @"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile";
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(profileKeyPath, writable: true);
            if (key != null)
            {
                // Disable network throttling (default is 10 packets/ms)
                BackupAndSetDword(key, profileKeyPath, "NetworkThrottlingIndex", unchecked((int)0xFFFFFFFF));
                // Dedicate 100% network scheduler time to real-time packets
                BackupAndSetDword(key, profileKeyPath, "SystemResponsiveness", 0);
            }

            // Tune MMCSS Game Priority
            const string gamesTaskPath = @"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games";
            using var gamesKey = Registry.LocalMachine.OpenSubKey(gamesTaskPath, writable: true);
            if (gamesKey != null)
            {
                BackupAndSetDword(gamesKey, gamesTaskPath, "GPU Priority", 8);
                BackupAndSetDword(gamesKey, gamesTaskPath, "Priority", 6);
                BackupAndSetString(gamesKey, gamesTaskPath, "Scheduling Category", "High");
                BackupAndSetString(gamesKey, gamesTaskPath, "SFIO Priority", "High");
            }
        }
        catch (UnauthorizedAccessException)
        {
            // Requires elevation; handled gracefully
        }
        catch { }
    }

    private void OptimizeNetworkInterfaces()
    {
        const string baseInterfacesPath = @"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces";
        const string tcpParametersPath = @"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters";
        try
        {
            // Global TCP Stack Parameters
            using var tcpParamsKey = Registry.LocalMachine.OpenSubKey(tcpParametersPath, writable: true);
            if (tcpParamsKey != null)
            {
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "DisableTaskOffload", 0);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "EnableTCPA", 1);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "SackOpts", 1);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "Tcp1323Opts", 1);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "DefaultTTL", 64);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "MaxUserPort", 65534);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "TcpTimedWaitDelay", 30);
                BackupAndSetDword(tcpParamsKey, tcpParametersPath, "SynAttackProtect", 1);
            }

            // Winsock AFD Fast Path Tuning
            const string afdParametersPath = @"SYSTEM\CurrentControlSet\Services\AFD\Parameters";
            using var afdKey = Registry.LocalMachine.CreateSubKey(afdParametersPath, writable: true);
            if (afdKey != null)
            {
                BackupAndSetDword(afdKey, afdParametersPath, "FastSendDatagramThreshold", 1024);
                BackupAndSetDword(afdKey, afdParametersPath, "FastCopyReceiveThreshold", 1024);
                BackupAndSetDword(afdKey, afdParametersPath, "DynamicBacklog", 1);
                BackupAndSetDword(afdKey, afdParametersPath, "MinimumDynamicBacklog", 20);
                BackupAndSetDword(afdKey, afdParametersPath, "MaximumDynamicBacklog", 1000);
            }

            using var interfacesKey = Registry.LocalMachine.OpenSubKey(baseInterfacesPath, writable: true);
            if (interfacesKey == null) return;

            var activeGuids = NetworkInterface.GetAllNetworkInterfaces()
                .Where(n => n.OperationalStatus == OperationalStatus.Up &&
                            n.NetworkInterfaceType != NetworkInterfaceType.Loopback)
                .Select(n => n.Id.Trim('{', '}'))
                .ToHashSet(StringComparer.OrdinalIgnoreCase);

            foreach (var subKeyName in interfacesKey.GetSubKeyNames())
            {
                string cleanSubKey = subKeyName.Trim('{', '}');
                // Apply to active interfaces or if fewer than 5 interfaces exist, apply to all non-loopback
                if (activeGuids.Contains(cleanSubKey) || activeGuids.Count == 0)
                {
                    string interfacePath = $@"{baseInterfacesPath}\{subKeyName}";
                    using var ifaceKey = Registry.LocalMachine.OpenSubKey(interfacePath, writable: true);
                    if (ifaceKey != null)
                    {
                        // 1. Immediate ACK: ACK every packet instantly without waiting 200ms
                        BackupAndSetDword(ifaceKey, interfacePath, "TcpAckFrequency", 1);
                        BackupAndSetDword(ifaceKey, interfacePath, "TCPDelAckTicks", 0);
                        // 2. Disable Nagle's packet coalescing algorithm on this interface
                        BackupAndSetDword(ifaceKey, interfacePath, "TcpNoDelay", 1);
                        BackupAndSetDword(ifaceKey, interfacePath, "TcpInitialRTT", 2);
                    }
                }
            }
        }
        catch (UnauthorizedAccessException) { }
        catch { }
    }

    private void OptimizeQoSBandwidth()
    {
        const string pschedKeyPath = @"SOFTWARE\Policies\Microsoft\Windows\Psched";
        try
        {
            using var key = Registry.LocalMachine.CreateSubKey(pschedKeyPath, writable: true);
            if (key != null)
            {
                // Remove Windows default 20% reserved bandwidth limit
                BackupAndSetDword(key, pschedKeyPath, "NonBestEffortLimit", 0);
            }
        }
        catch { }
    }

    private static void OptimizeTcpGlobalStack()
    {
        if (_globalTcpStackOptimized) return;
        _globalTcpStackOptimized = true;

        Task.Run(() =>
        {
            try
            {
                // Run netsh commands silently in background for lowest possible gaming latency
                string[] commands = [
                    "int tcp set global autotuninglevel=normal",
                    "int tcp set global ecncapability=enabled",
                    "int tcp set global timestamps=disabled",
                    "int tcp set global rss=enabled",
                    "int tcp set global rsc=disabled", // Disable RSC to eliminate NIC packet buffering
                    "int tcp set global initialRto=1000",
                    "int tcp set heuristics disabled",
                    "int ip set global taskoffload=enabled",
                ];

                foreach (var cmd in commands)
                {
                    RunSilentProcess("netsh.exe", cmd);
                }

                // BBR2 congestion control requires Windows 11 22H2+ (build 22621+).
                // CTCP is the best fallback for Windows 10 and reduces bufferbloat significantly.
                // Run only one — running both causes CTCP to overwrite BBR2 on the same supplemental template.
                bool isBbr2Supported = Environment.OSVersion.Version.Build >= 22621;
                if (isBbr2Supported)
                {
                    RunSilentProcess("netsh.exe", "int tcp set supplemental template=internet congestionprovider=bbr2");
                }
                else
                {
                    RunSilentProcess("netsh.exe", "int tcp set supplemental template=internet congestionprovider=ctcp");
                }
            }
            catch { }
        });
    }

    private static void BoostGameProcessPriority(int processId)
    {
        try
        {
            var proc = Process.GetProcessById(processId);
            if (!proc.HasExited && proc.PriorityClass < ProcessPriorityClass.AboveNormal)
            {
                // AboveNormal is optimal: prioritizes game packets & engine threads
                // without starving graphics driver or audio threads (which caused freeze with High).
                proc.PriorityClass = ProcessPriorityClass.AboveNormal;
            }
        }
        catch { }
    }

    private static void ConfigureGamingQoS(string gameProcessName)
    {
        try
        {
            using var qosKey = Registry.LocalMachine.OpenSubKey(
                @"SOFTWARE\Policies\Microsoft\Windows\QoS", writable: true);
            if (qosKey != null)
            {
                string ruleName = $"AcademyNoLag_{gameProcessName}";
                using var ruleKey = qosKey.CreateSubKey(ruleName, writable: true);
                if (ruleKey != null)
                {
                    ruleKey.SetValue("Version", "1.0", RegistryValueKind.String);
                    ruleKey.SetValue("Application Name", $"{gameProcessName}.exe", RegistryValueKind.String);
                    ruleKey.SetValue("Protocol", "*", RegistryValueKind.String);
                    ruleKey.SetValue("Local Port", "*", RegistryValueKind.String);
                    ruleKey.SetValue("Remote Port", "*", RegistryValueKind.String);
                    ruleKey.SetValue("DSCP Value", "46", RegistryValueKind.String); // 46 = Expedited Forwarding (Voice/Gaming VIP)
                    ruleKey.SetValue("Throttle Rate", "-1", RegistryValueKind.String);
                }
            }
        }
        catch { }
    }

    public void InjectHostRoute(IPAddress targetIp)
    {
        string ipStr = targetIp.ToString();
        lock (_lock)
        {
            if (_injectedHostRoutes.Contains(ipStr)) return;

            try
            {
                var defaultGateway = NetworkInterface.GetAllNetworkInterfaces()
                    .Where(n => n.OperationalStatus == OperationalStatus.Up &&
                                n.NetworkInterfaceType != NetworkInterfaceType.Loopback)
                    .SelectMany(n => n.GetIPProperties().GatewayAddresses)
                    .Select(g => g.Address)
                    .FirstOrDefault(a => a.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork &&
                                        !IPAddress.IsLoopback(a) &&
                                        !a.Equals(IPAddress.Any));

                if (defaultGateway != null)
                {
                    // Inject /32 host route with metric 1 via real active gateway
                    RunSilentProcess("route.exe", $"ADD {ipStr} MASK 255.255.255.255 {defaultGateway} METRIC 1");
                    _injectedHostRoutes.Add(ipStr);
                }
                else
                {
                    var activeNic = NetworkInterface.GetAllNetworkInterfaces()
                        .FirstOrDefault(n => n.OperationalStatus == OperationalStatus.Up &&
                                             n.NetworkInterfaceType != NetworkInterfaceType.Loopback &&
                                             n.GetIPProperties().GetIPv4Properties() != null);
                    if (activeNic != null)
                    {
                        int ifIndex = activeNic.GetIPProperties().GetIPv4Properties()!.Index;
                        RunSilentProcess("route.exe", $"ADD {ipStr} MASK 255.255.255.255 0.0.0.0 IF {ifIndex} METRIC 1");
                        _injectedHostRoutes.Add(ipStr);
                    }
                }
            }
            catch { }
        }
    }

    public void RemoveHostRoute(string ipStr)
    {
        try
        {
            RunSilentProcess("route.exe", $"DELETE {ipStr}");
        }
        catch { }
    }

    private static void FlushNetworkCaches()
    {
        Task.Run(() =>
        {
            try
            {
                // Flush DNS resolver cache only. NEVER delete ARP cache during gameplay.
                RunSilentProcess("ipconfig.exe", "/flushdns");
            }
            catch { }
        });
    }

    private static void RunSilentProcess(string fileName, string arguments)
    {
        try
        {
            var psi = new ProcessStartInfo(fileName, arguments)
            {
                CreateNoWindow = true,
                UseShellExecute = false,
                WindowStyle = ProcessWindowStyle.Hidden
            };
            using var p = Process.Start(psi);
            // 150ms max wait — netsh/route commands apply kernel-side immediately;
            // waiting 1000ms × 10 commands = 10s total block that freezes game during app restart.
            p?.WaitForExit(150);
        }
        catch { }
    }

    private void BackupAndSetDword(RegistryKey key, string keyPath, string valueName, int newValue)
    {
        string fullValKey = $@"{keyPath}\{valueName}";
        if (!_originalRegistryValues.ContainsKey(fullValKey))
        {
            _originalRegistryValues[fullValKey] = key.GetValue(valueName);
        }

        key.SetValue(valueName, newValue, RegistryValueKind.DWord);
    }

    private void BackupAndSetString(RegistryKey key, string keyPath, string valueName, string newValue)
    {
        string fullValKey = $@"{keyPath}\{valueName}";
        if (!_originalRegistryValues.ContainsKey(fullValKey))
        {
            _originalRegistryValues[fullValKey] = key.GetValue(valueName);
        }

        key.SetValue(valueName, newValue, RegistryValueKind.String);
    }

    public void Dispose()
    {
        RestoreDefaults();
        GC.SuppressFinalize(this);
    }
}
