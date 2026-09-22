using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;

namespace AcademyNoLag.App;

public partial class App : System.Windows.Application
{
    public const string ShowHudMessageName = "AcademyNoLag_ShowFloatingHud_Broadcast";
    public static int ShowHudMessageId { get; private set; }

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    private static extern int RegisterWindowMessage(string lpString);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool PostMessage(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam);

    protected override void OnStartup(StartupEventArgs e)
    {
        // 1. Setup Global Exception Logging so nothing ever silently crashes
        AppDomain.CurrentDomain.UnhandledException += (s, args) =>
        {
            try
            {
                var ex = args.ExceptionObject as Exception;
                string logPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log");
                System.IO.File.WriteAllText(logPath, $"[{DateTime.UtcNow}] UnhandledException: {ex}");
            }
            catch { }
        };

        DispatcherUnhandledException += (s, args) =>
        {
            try
            {
                string logPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log");
                System.IO.File.WriteAllText(logPath, $"[{DateTime.UtcNow}] DispatcherException: {args.Exception}");
            }
            catch { }
            args.Handled = true; // Prevent app termination!
        };

        // 2. Single-Instance Check using real running process list
        try
        {
            ShowHudMessageId = RegisterWindowMessage(ShowHudMessageName);

            var current = Process.GetCurrentProcess();
            var existingProcesses = Process.GetProcessesByName(current.ProcessName)
                .Where(p => p.Id != current.Id)
                .ToList();

            if (existingProcesses.Count > 0)
            {
                // Verify if any existing process is actually alive and responsive
                var active = existingProcesses.FirstOrDefault(p =>
                {
                    try { return !p.HasExited && p.Responding; }
                    catch { return false; }
                });

                if (active != null)
                {
                    // Existing instance is running and responsive!
                    // Tell it to show its Floating HUD
                    IntPtr HWND_BROADCAST = (IntPtr)0xffff;
                    PostMessage(HWND_BROADCAST, ShowHudMessageId, IntPtr.Zero, IntPtr.Zero);

                    // Exit this second instance
                    Shutdown(0);
                    return;
                }
                else
                {
                    // Existing process was hung/zombie, terminate it so this new one can take over
                    foreach (var dead in existingProcesses)
                    {
                        try { dead.Kill(); } catch { }
                    }
                }
            }
        }
        catch { }

        base.OnStartup(e);
    }

    protected override void OnExit(ExitEventArgs e)
    {
        try
        {
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
