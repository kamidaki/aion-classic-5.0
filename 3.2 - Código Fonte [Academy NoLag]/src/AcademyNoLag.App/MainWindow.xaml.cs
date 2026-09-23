using System.ComponentModel;
using System.Diagnostics;
using System.Windows;
using AcademyNoLag.App.Tray;
using AcademyNoLag.App.ViewModels;

namespace AcademyNoLag.App;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    public void ShutdownApp()
    {
        try
        {
            // 1. Hide UI immediately
            Hide();

            // 2. Dispose ViewModel and stop all routing/probers/network tweaks
            if (DataContext is MainViewModel vm)
            {
                vm.Dispose();
            }

            // 4. Terminate helper processes (RelayNode, Service)
            KillHelperProcesses();
        }
        catch { /* Ensure exit proceeds regardless */ }
        finally
        {
            // 5. Hard exit to guarantee zero zombie threads
            Application.Current?.Shutdown();
            Environment.Exit(0);
        }
    }

    private static void KillHelperProcesses()
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