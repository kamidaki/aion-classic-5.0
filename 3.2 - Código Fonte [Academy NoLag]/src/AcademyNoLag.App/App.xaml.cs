using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using AcademyNoLag.Diagnostics;

namespace AcademyNoLag.App;

public partial class App : System.Windows.Application
{
    private const string SingleInstanceEventName = @"Local\AcademyNoLag_SingleInstance_Signal";
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
        Logger.Instance.Info("App", "=== Academy NoLag Launching ===");

        // 1. Setup Global Exception Logging
        AppDomain.CurrentDomain.UnhandledException += (s, args) =>
        {
            Logger.Instance.Error("AppDomain", $"UnhandledException: {args.ExceptionObject}");
        };

        DispatcherUnhandledException += (s, args) =>
        {
            Logger.Instance.Error("Dispatcher", $"DispatcherException: {args.Exception}");
            args.Handled = true;
        };

        // 2. Single-Instance Check using Mutex & EventWaitHandle
        bool isOnlyInstance = false;
        try
        {
            _singleInstanceMutex = new Mutex(true, @"Local\AcademyNoLag_SingleInstance_Mutex", out isOnlyInstance);
        }
        catch (Exception ex)
        {
            Logger.Instance.Info("App", $"Mutex check note: {ex.Message}");
            isOnlyInstance = true;
        }

        try
        {
            _singleInstanceEvent = new EventWaitHandle(false, EventResetMode.AutoReset, SingleInstanceEventName);
        }
        catch { }

        if (!isOnlyInstance)
        {
            Logger.Instance.Info("App", "Existing instance detected. Signaling existing instance and exiting.");
            try
            {
                _singleInstanceEvent?.Set();

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

        // 3. Listen for wake-up signals from secondary launches
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

        // 4. Explicitly instantiate and show the Floating HUD window
        try
        {
            Logger.Instance.Info("App", "Instantiating FloatingHudWindow...");
            var hud = new Views.FloatingHudWindow();
            MainWindow = hud;

            Logger.Instance.Info("App", "Displaying FloatingHudWindow...");
            hud.Show();
            hud.Activate();
            Logger.Instance.Info("App", "FloatingHudWindow displayed successfully!");
        }
        catch (Exception ex)
        {
            Logger.Instance.Error("App", $"FATAL: Failed to initialize/show FloatingHudWindow: {ex}");
            MessageBox.Show($"Erro fatal ao iniciar a interface:\n\n{ex.Message}\n\nStack:\n{ex.StackTrace}", 
                            "Academy NoLag - Erro de Inicialização", 
                            MessageBoxButton.OK, 
                            MessageBoxImage.Error);
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
