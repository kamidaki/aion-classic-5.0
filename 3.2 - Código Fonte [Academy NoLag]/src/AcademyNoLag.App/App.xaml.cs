using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using System.Windows;
using AcademyNoLag.Diagnostics;

namespace AcademyNoLag.App;

public partial class App : System.Windows.Application
{
    private const string SingleInstanceMutexName = @"Local\AcademyNoLag_SingleInstance_Mutex2";
    private const string SingleInstanceEventName = @"Local\AcademyNoLag_SingleInstance_Signal2";
    private static EventWaitHandle? _singleInstanceEvent;
    private static Mutex? _singleInstanceMutex;

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    private static extern IntPtr FindWindow(string? lpClassName, string lpWindowName);

    protected override void OnStartup(StartupEventArgs e)
    {
        // 1. Normalize working directory immediately (UAC elevation can change CWD to System32)
        try
        {
            Directory.SetCurrentDirectory(AppDomain.CurrentDomain.BaseDirectory);
        }
        catch { }

        // 2. Setup Global Exception Logging
        AppDomain.CurrentDomain.UnhandledException += (s, args) =>
        {
            Logger.Instance.Error("AppDomain", $"UnhandledException: {args.ExceptionObject}");
        };

        DispatcherUnhandledException += (s, args) =>
        {
            Console.Error.WriteLine($"DispatcherException: {args.Exception}");
            Logger.Instance.Error("Dispatcher", $"DispatcherException: {args.Exception}");
            args.Handled = false;
        };

        // 3. Structured [BOOT] Logging
        var currentProcess = Process.GetCurrentProcess();
        bool isAdmin = IsRunningAsAdmin();
        Logger.Instance.Info("BOOT", "=== Academy NoLag Boot Initialization ===");
        Logger.Instance.Info("BOOT", $"Process started: PID={currentProcess.Id}, SessionID={currentProcess.SessionId}");
        Logger.Instance.Info("BOOT", $"Running as Administrator: {(isAdmin ? "YES" : "NO")}");
        Logger.Instance.Info("BOOT", $"Executable path: {currentProcess.MainModule?.FileName ?? "Unknown"}");
        Logger.Instance.Info("BOOT", $"Working directory: {Environment.CurrentDirectory}");
        Logger.Instance.Info("BOOT", $"Base directory: {AppDomain.CurrentDomain.BaseDirectory}");

        // 4. Single-Instance Check using Mutex & EventWaitHandle with Cross-Integrity DACL
        bool isOnlyInstance = false;
        try
        {
            var mutexSecurity = new MutexSecurity();
            var mutexRule = new MutexAccessRule(
                new SecurityIdentifier(WellKnownSidType.AuthenticatedUserSid, null),
                MutexRights.FullControl,
                AccessControlType.Allow);
            mutexSecurity.AddAccessRule(mutexRule);

            _singleInstanceMutex = MutexAcl.Create(true, SingleInstanceMutexName, out isOnlyInstance, mutexSecurity);
        }
        catch (UnauthorizedAccessException)
        {
            Logger.Instance.Info("BOOT", "Mutex access denied — existing instance is active with higher/different token.");
            isOnlyInstance = false;
        }
        catch (AbandonedMutexException)
        {
            Logger.Instance.Info("BOOT", "Abandoned mutex detected from terminated previous instance. Taking ownership.");
            isOnlyInstance = true;
        }
        catch (Exception ex)
        {
            Logger.Instance.Warn("BOOT", $"Mutex check fallback: {ex.Message}");
            try
            {
                Mutex.OpenExisting(SingleInstanceMutexName);
                isOnlyInstance = false;
            }
            catch
            {
                isOnlyInstance = true;
            }
        }

        try
        {
            var eventSecurity = new EventWaitHandleSecurity();
            var eventRule = new EventWaitHandleAccessRule(
                new SecurityIdentifier(WellKnownSidType.AuthenticatedUserSid, null),
                EventWaitHandleRights.FullControl,
                AccessControlType.Allow);
            eventSecurity.AddAccessRule(eventRule);

            _singleInstanceEvent = EventWaitHandleAcl.Create(false, EventResetMode.AutoReset, SingleInstanceEventName, out _, eventSecurity);
        }
        catch (Exception ex)
        {
            try
            {
                _singleInstanceEvent = new EventWaitHandle(false, EventResetMode.AutoReset, SingleInstanceEventName);
            }
            catch { }
            Logger.Instance.Info("BOOT", $"EventWaitHandle fallback note: {ex.Message}");
        }

        if (!isOnlyInstance)
        {
            Logger.Instance.Info("BOOT", "Existing instance detected. Signaling existing instance and exiting.");
            try
            {
                if (EventWaitHandle.TryOpenExisting(SingleInstanceEventName, out var signalEvent))
                {
                    signalEvent.Set();
                    signalEvent.Dispose();
                }
                else
                {
                    _singleInstanceEvent?.Set();
                }

                IntPtr existingHwnd = FindWindow(null, "Academy NoLag — Gaming HUD");
                if (existingHwnd != IntPtr.Zero)
                {
                    ShowWindowAsync(existingHwnd, 9); // SW_RESTORE
                    SetForegroundWindow(existingHwnd);
                }
            }
            catch { }

            Shutdown(0);
            return;
        }

        Logger.Instance.Info("BOOT", "Mutex acquired: primary application instance confirmed.");

        // 5. Listen for wake-up signals from secondary launches
        Task.Run(() =>
        {
            while (_singleInstanceEvent != null)
            {
                try
                {
                    if (_singleInstanceEvent.WaitOne())
                    {
                        Logger.Instance.Info("App", "Wake-up signal received from secondary launch attempt.");
                        Current?.Dispatcher.Invoke(() =>
                        {
                            if (Current.MainWindow is Views.FloatingHudWindow hud)
                            {
                                hud.ShowFloatingHud();
                            }
                        });
                    }
                }
                catch { break; }
            }
        });

        base.OnStartup(e);

        // 6. Explicitly instantiate and show the Floating HUD window
        try
        {
            Logger.Instance.Info("BOOT", "UI subsystem initialized: creating FloatingHudWindow...");
            var hud = new Views.FloatingHudWindow();
            MainWindow = hud;

            Logger.Instance.Info("BOOT", "Displaying FloatingHudWindow...");
            hud.Show();
            hud.Activate();
            Logger.Instance.Info("BOOT", "Academy NoLag startup completed successfully!");
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"FATAL: {ex}");
            Logger.Instance.Error("BOOT", $"FATAL: Failed to initialize/show FloatingHudWindow: {ex}");
        }
    }

    private static bool IsRunningAsAdmin()
    {
        try
        {
            using var identity = WindowsIdentity.GetCurrent();
            var principal = new WindowsPrincipal(identity);
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }
        catch
        {
            return false;
        }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        try
        {
            _singleInstanceEvent?.Dispose();
            _singleInstanceEvent = null;

            _singleInstanceMutex?.ReleaseMutex();
            _singleInstanceMutex?.Dispose();
            _singleInstanceMutex = null;

            if (MainWindow is Views.FloatingHudWindow hud)
            {
                hud.ShutdownApp();
            }
            else
            {
                KillRemainingProcesses();
            }
        }
        catch { }

        base.OnExit(e);
    }

    private static void KillRemainingProcesses()
    {
        string[] targetProcesses = ["AcademyNoLag.RelayNode", "AcademyNoLag.Service"];
        foreach (var name in targetProcesses)
        {
            try
            {
                foreach (var p in Process.GetProcessesByName(name))
                {
                    try { p.Kill(); }
                    catch { }
                }
            }
            catch { }
        }
    }
}
