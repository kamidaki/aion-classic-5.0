using System.ComponentModel;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using AcademyNoLag.App.Tray;
using AcademyNoLag.App.ViewModels;

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
        try
        {
            if (_trayManager == null)
            {
                _trayManager = new SystemTrayManager(this, _viewModel);
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[TrayManager] Initialization warning: {ex.Message}");
        }

        // Hook window message loop to capture single-instance ShowHud broadcast
        var hwnd = new WindowInteropHelper(this).Handle;
        var source = HwndSource.FromHwnd(hwnd);
        source?.AddHook(WndProc);

        // Position window at bottom-right above taskbar
        var workingArea = SystemParameters.WorkArea;
        Left = workingArea.Right - ActualWidth - 24;
        Top = workingArea.Bottom - ActualHeight - 24;
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg == App.ShowHudMessageId && App.ShowHudMessageId != 0)
        {
            ShowFloatingHud();
            handled = true;
        }
        return IntPtr.Zero;
    }

    public void ShowFloatingHud()
    {
        Show();
        WindowState = WindowState.Normal;
        Activate();
        Topmost = _isPinned;
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

            // 2. Dispose tray manager
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
