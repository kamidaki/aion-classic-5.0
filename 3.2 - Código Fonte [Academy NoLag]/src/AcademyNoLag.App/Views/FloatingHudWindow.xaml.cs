using System.ComponentModel;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using AcademyNoLag.App.Tray;
using AcademyNoLag.App.ViewModels;
using AcademyNoLag.Diagnostics;

namespace AcademyNoLag.App.Views;

public partial class FloatingHudWindow : Window
{
    private readonly MainViewModel _viewModel;
    private SystemTrayManager? _trayManager;
    private bool _isPinned = true;
    private bool _isExplicitExit = false;

    public SystemTrayManager? TrayManager => _trayManager;

    public FloatingHudWindow() : this(new MainViewModel())
    {
    }

    public FloatingHudWindow(MainViewModel viewModel)
    {
        Logger.Instance.Info("UI", "FloatingHudWindow constructor starting...");
        _viewModel = viewModel;
        DataContext = _viewModel;

        InitializeComponent();
        Logger.Instance.Info("UI", "FloatingHudWindow InitializeComponent completed.");

        // Create SystemTrayManager in constructor so tray icon is active immediately
        try
        {
            _trayManager = new SystemTrayManager(this, _viewModel);
            Logger.Instance.Info("UI", "SystemTrayManager created in constructor.");
        }
        catch (Exception ex)
        {
            Logger.Instance.Error("UI", $"Failed to create SystemTrayManager in constructor: {ex}");
        }

        Loaded += OnLoaded;
        Closing += OnWindowClosing;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        Logger.Instance.Info("UI", $"FloatingHudWindow OnLoaded triggered! Screen WorkArea: {SystemParameters.WorkArea.Width}x{SystemParameters.WorkArea.Height}");

        // If tray manager was not yet created, create it now as fallback
        if (_trayManager == null)
        {
            try
            {
                _trayManager = new SystemTrayManager(this, _viewModel);
            }
            catch (Exception ex)
            {
                Logger.Instance.Error("UI", $"Failed to initialize fallback TrayManager: {ex.Message}");
            }
        }

        // Center on screen initially for prominent visibility
        if (double.IsNaN(Left) || Left <= 0 || Left > SystemParameters.WorkArea.Right - 50)
        {
            Left = Math.Max(20, (SystemParameters.WorkArea.Width - Width) / 2);
        }
        if (double.IsNaN(Top) || Top <= 0 || Top > SystemParameters.WorkArea.Bottom - 50)
        {
            Top = Math.Max(20, (SystemParameters.WorkArea.Height - Height) / 2);
        }

        ShowFloatingHud();
    }

    public void ShowFloatingHud()
    {
        if (WindowState == WindowState.Minimized)
        {
            WindowState = WindowState.Normal;
        }
        Show();
        Visibility = Visibility.Visible;
        Activate();
        Topmost = _isPinned;
        Focus();
    }

    private void OnWindowClosing(object? sender, CancelEventArgs e)
    {
        if (!_isExplicitExit)
        {
            e.Cancel = true;
            Hide();
        }
    }

    private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ButtonState == MouseButtonState.Pressed)
        {
            DragMove();
        }
    }

    private void PinButton_Click(object sender, RoutedEventArgs e)
    {
        _isPinned = !_isPinned;
        Topmost = _isPinned;
        PinButton.Opacity = _isPinned ? 1.0 : 0.45;
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        Hide();
    }

    private void NavButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string tag && int.TryParse(tag, out int idx))
        {
            _viewModel.SelectedTabIndex = idx;
        }
    }

    public void ShutdownApp()
    {
        _isExplicitExit = true;

        try
        {
            // 1. Hide UI immediately
            Hide();

            // 2. Dispose tray manager (removes tray icon instantly)
            _trayManager?.Dispose();
            _trayManager = null;

            // 3. Dispose ViewModel (stops engine, restores network settings)
            _viewModel?.Dispose();

            // 4. Terminate helper processes
            KillRemainingProcesses();
        }
        catch { /* Ensure exit proceeds regardless */ }
        finally
        {
            Application.Current?.Shutdown();
            Environment.Exit(0);
        }
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
