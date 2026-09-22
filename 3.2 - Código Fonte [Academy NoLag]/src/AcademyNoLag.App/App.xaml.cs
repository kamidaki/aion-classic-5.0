using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Windows;

namespace AcademyNoLag.App;

public partial class App : System.Windows.Application
{
    private const string SingleInstanceEventName = "AcademyNoLag_SingleInstance_Signal";
    private static EventWaitHandle? _singleInstanceEvent;

    protected override void OnStartup(StartupEventArgs e)
    {
        // 1. Setup Global Exception Logging so nothing ever silently crashes
        AppDomain.CurrentDomain.UnhandledException += (s, args) =>
        {
            try
            {
                var ex = args.ExceptionObject as Exception;
                string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log");
                File.WriteAllText(logPath, $"[{DateTime.UtcNow}] UnhandledException: {ex}");
            }
            catch { }
        };

        DispatcherUnhandledException += (s, args) =>
        {
            try
            {
                string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log");
                File.WriteAllText(logPath, $"[{DateTime.UtcNow}] DispatcherException: {args.Exception}");
            }
            catch { }
            args.Handled = true;
        };

        // 2. Single-Instance Check using EventWaitHandle (cross-process signal, UIPI-immune)
        bool createdNew;
        try
        {
            _singleInstanceEvent = new EventWaitHandle(false, EventResetMode.AutoReset, SingleInstanceEventName, out createdNew);
        }
        catch
        {
            createdNew = true;
        }

        if (!createdNew)
        {
            // Another instance is already running!
            // Signal the running instance to bring its Floating HUD to foreground
            try
            {
                _singleInstanceEvent?.Set();
            }
            catch { }

            Shutdown(0);
            return;
        }

        // 3. Listen for wake-up signals from secondary launches in a background thread
        Task.Run(() =>
        {
            while (_singleInstanceEvent != null)
            {
                try
                {
                    if (_singleInstanceEvent.WaitOne())
                    {
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
    }

    protected override void OnExit(ExitEventArgs e)
    {
        try
        {
            _singleInstanceEvent?.Dispose();
            _singleInstanceEvent = null;

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
