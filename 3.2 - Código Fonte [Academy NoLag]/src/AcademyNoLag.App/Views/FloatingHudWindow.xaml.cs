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
        InitializeComponent();
        _viewModel = viewModel;
        DataContext = _viewModel;

        Loaded += OnLoaded;
        Closing += OnWindowClosing;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        // 1. Position window at bottom-right above taskbar, ensuring safe screen bounds
        var workingArea = SystemParameters.WorkArea;
        double w = ActualWidth > 100 ? ActualWidth : (Width > 0 ? Width : 465);
        double h = ActualHeight > 100 ? ActualHeight : (Height > 0 ? Height : 545);
        Left = Math.Max(20, workingArea.Right - w - 24);
        Top = Math.Max(20, workingArea.Bottom - h - 24);

        // 2. Initialize Tray Manager
        try
        {
            if (_trayManager == null)
            {
                _trayManager = new SystemTrayManager(this, _viewModel);
            }
        }
        catch (Exception ex)
        {
            Logger.Instance.Error("TrayManager", $"Failed to initialize TrayManager: {ex.Message}");
        }

        // 3. Ensure window is visible and focused
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
