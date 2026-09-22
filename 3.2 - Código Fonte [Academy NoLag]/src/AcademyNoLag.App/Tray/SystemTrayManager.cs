using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Threading;
using AcademyNoLag.App.ViewModels;
using AcademyNoLag.App.Views;

namespace AcademyNoLag.App.Tray;

public class SystemTrayManager : IDisposable
{
    private const int NIM_ADD = 0x00000000;
    private const int NIM_MODIFY = 0x00000001;
    private const int NIM_DELETE = 0x00000002;

    private const int NIF_MESSAGE = 0x00000001;
    private const int NIF_ICON = 0x00000002;
    private const int NIF_TIP = 0x00000004;

    private const int WM_USER = 0x0400;
    private const int WM_TRAYICON = WM_USER + 101;
    private const int WM_LBUTTONUP = 0x0202;
    private const int WM_LBUTTONDBLCLK = 0x0203;
    private const int WM_RBUTTONUP = 0x0205;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct NOTIFYICONDATA
    {
        public int cbSize;
        public IntPtr hWnd;
        public int uID;
        public int uFlags;
        public int uCallbackMessage;
        public IntPtr hIcon;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)]
        public string szTip;
        public int dwState;
        public int dwStateMask;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 256)]
        public string szInfo;
        public int uTimeoutOrVersion;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)]
        public string szInfoTitle;
        public int dwInfoFlags;
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern bool Shell_NotifyIcon(int dwMessage, ref NOTIFYICONDATA lpData);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr LoadImage(IntPtr hinst, string lpszName, uint uType, int cxDesired, int cyDesired, uint fuLoad);

    [DllImport("user32.dll")]
    private static extern IntPtr LoadIcon(IntPtr hInstance, IntPtr lpIconName);

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr ExtractIcon(IntPtr hInst, string lpszExeFileName, int nIconIndex);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    private static extern int RegisterWindowMessage(string lpString);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool DestroyIcon(IntPtr hIcon);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    private static readonly int WM_TASKBARCREATED = RegisterWindowMessage("TaskbarCreated");

    private readonly FloatingHudWindow _floatingHud;
    private readonly MainViewModel _viewModel;
    private readonly ContextMenu _contextMenu;
    private readonly DispatcherTimer _tooltipTimer;

    private HwndSource? _hwndSource;
    private NOTIFYICONDATA _nid;
    private bool _isAdded = false;

    public FloatingHudWindow FloatingHud => _floatingHud;

    public SystemTrayManager(FloatingHudWindow floatingHud, MainViewModel viewModel)
    {
        _floatingHud = floatingHud;
        _viewModel = viewModel;

        // Build stylish dark gaming context menu
        _contextMenu = BuildContextMenu();

        // Use the genuine HWND of the Floating HUD window
        var helper = new WindowInteropHelper(_floatingHud);
        IntPtr hwnd = helper.EnsureHandle();
        _hwndSource = HwndSource.FromHwnd(hwnd);
        _hwndSource?.AddHook(WndProc);

        IntPtr hIcon = ResolveTrayIcon();

        _nid = new NOTIFYICONDATA
        {
            cbSize = Marshal.SizeOf<NOTIFYICONDATA>(),
            hWnd = hwnd,
            uID = 1001,
            uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP,
            uCallbackMessage = WM_TRAYICON,
            hIcon = hIcon,
            szTip = "Academy NoLag • Otimizador Ativo\nAguardando Aion Classic..."
        };

        _isAdded = Shell_NotifyIcon(NIM_ADD, ref _nid);

        // Setup periodic tooltip updater (every 1.5s, virtually 0% CPU)
        _tooltipTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromMilliseconds(1500)
        };
        _tooltipTimer.Tick += (_, _) => UpdateTooltip();
        _tooltipTimer.Start();
    }

    private static IntPtr ResolveTrayIcon()
    {
        try
        {
            // 1. Try loading app.ico from application directory with Unicode support
            string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app.ico");
            if (File.Exists(iconPath))
            {
                // IMAGE_ICON = 1, LR_LOADFROMFILE = 0x00000010
                IntPtr hIcon = LoadImage(IntPtr.Zero, iconPath, 1, 16, 16, 0x00000010);
                if (hIcon != IntPtr.Zero) return hIcon;
            }

            // 2. Try extracting icon from own executable
            string exePath = Process.GetCurrentProcess().MainModule?.FileName ?? "";
            if (!string.IsNullOrEmpty(exePath) && File.Exists(exePath))
            {
                IntPtr hIcon = ExtractIcon(IntPtr.Zero, exePath, 0);
                if (hIcon != IntPtr.Zero) return hIcon;
            }

            // 3. Fallback to standard application icon so Shell_NotifyIcon NEVER fails
            return LoadIcon(IntPtr.Zero, (IntPtr)32512); // IDI_APPLICATION
        }
        catch
        {
            return LoadIcon(IntPtr.Zero, (IntPtr)32512);
        }
    }

    private ContextMenu BuildContextMenu()
    {
        var menu = new ContextMenu
        {
            Background = new SolidColorBrush(Color.FromRgb(15, 23, 42)),
            BorderBrush = new SolidColorBrush(Color.FromRgb(0, 229, 255)),
            BorderThickness = new Thickness(1.2),
            Padding = new Thickness(4),
            SnapsToDevicePixels = true,
            HasDropShadow = true
        };

        // Header item
        var headerItem = CreateCustomMenuItem("⚡ ACADEMY NOLAG", new SolidColorBrush(Color.FromRgb(0, 229, 255)), null, isBold: true, isEnabled: false);
        menu.Items.Add(headerItem);
        menu.Items.Add(new Separator());

        // Abrir Painel Flutuante
        var itemFloating = CreateCustomMenuItem("Abrir Academy NoLag", new SolidColorBrush(Color.FromRgb(248, 250, 252)), () => ShowFloatingHud(), isBold: true);
        menu.Items.Add(itemFloating);

        menu.Items.Add(new Separator());

        // Otimização Automática toggle
        var itemAuto = CreateCustomMenuItem(
            _viewModel.AutoOptimize ? "✓ Otimização Automática: ATIVA" : "○ Otimização Automática: MANUAL", 
            new SolidColorBrush(Color.FromRgb(16, 185, 129)), 
            () =>
            {
                _viewModel.AutoOptimize = !_viewModel.AutoOptimize;
            });
        menu.Items.Add(itemAuto);

        menu.Items.Add(new Separator());

        // Encerrar
        var itemExit = CreateCustomMenuItem("Encerrar", new SolidColorBrush(Color.FromRgb(239, 68, 68)), () => _floatingHud.ShutdownApp(), isBold: true);
        menu.Items.Add(itemExit);

        return menu;
    }

    private static MenuItem CreateCustomMenuItem(string header, Brush foreground, Action? onClick, bool isBold = false, bool isEnabled = true)
    {
        var item = new MenuItem
        {
            Header = header,
            Foreground = foreground,
            FontWeight = isBold ? FontWeights.Bold : FontWeights.SemiBold,
            FontSize = 12,
            IsEnabled = isEnabled,
            Padding = new Thickness(12, 7, 12, 7),
            Background = Brushes.Transparent,
            Cursor = isEnabled ? System.Windows.Input.Cursors.Hand : System.Windows.Input.Cursors.Arrow
        };

        if (isEnabled)
        {
            item.MouseEnter += (s, _) =>
            {
                if (s is MenuItem mi) mi.Background = new SolidColorBrush(Color.FromRgb(30, 41, 59));
            };
            item.MouseLeave += (s, _) =>
            {
                if (s is MenuItem mi) mi.Background = Brushes.Transparent;
            };
        }

        if (onClick != null)
        {
            item.Click += (_, _) => onClick();
        }
        return item;
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg == WM_TASKBARCREATED)
        {
            // Windows Explorer restarted or tray was refreshed — re-register icon
            _isAdded = Shell_NotifyIcon(NIM_ADD, ref _nid);
            return IntPtr.Zero;
        }

        if (msg == WM_TRAYICON)
        {
            int eventId = lParam.ToInt32();
            if (eventId == WM_LBUTTONUP || eventId == WM_LBUTTONDBLCLK)
            {
                // Left click or double click toggles the stylish Floating HUD
                ToggleFloatingHud();
                handled = true;
            }
            else if (eventId == WM_RBUTTONUP)
            {
                // Right click shows stylish context menu
                ShowContextMenu();
                handled = true;
            }
        }

        return IntPtr.Zero;
    }

    private void ShowContextMenu()
    {
        if (_hwndSource != null)
        {
            SetForegroundWindow(_hwndSource.Handle);
        }

        _contextMenu.Placement = System.Windows.Controls.Primitives.PlacementMode.MousePoint;
        _contextMenu.IsOpen = true;
    }

    public void ToggleFloatingHud()
    {
        if (_floatingHud.IsVisible)
        {
            _floatingHud.Hide();
        }
        else
        {
            ShowFloatingHud();
        }
    }

    public void ShowFloatingHud()
    {
        _floatingHud.ShowFloatingHud();
    }

    public void MinimizeToTray()
    {
        _floatingHud.Hide();
    }

    public void UpdateTooltip()
    {
        if (!_isAdded) return;

        try
        {
            string tip;
            if (_viewModel.HasActiveGame)
            {
                string ping = _viewModel.OptimizedPing > 0 
                    ? $"{_viewModel.OptimizedPing:F0}ms" 
                    : $"{_viewModel.DirectPing:F0}ms";

                string imp = _viewModel.PingImprovementPercent > 0 
                    ? $" (-{_viewModel.PingImprovementPercent:F0}%)" 
                    : "";

                string game = _viewModel.ActiveGameName;
                if (game.Length > 20) game = game[..20];

                string endpoint = _viewModel.PrimaryEndpointDisplay;
                if (endpoint.Length > 22) endpoint = endpoint[..22];

                tip = $"Academy NoLag [Otimizado]\n{game}\nIP: {endpoint}\nPing: {ping}{imp}";
            }
            else
            {
                tip = "Academy NoLag • Monitorando\nNenhum jogo em execução\nAguardando Aion Classic...";
            }

            // Win32 NOTIFYICONDATA.szTip limit is 128 characters including null terminator
            if (tip.Length >= 128) tip = tip[..127];

            _nid.szTip = tip;
            _nid.uFlags = NIF_TIP;
            Shell_NotifyIcon(NIM_MODIFY, ref _nid);
        }
        catch { /* Gracefully handle Win32 update */ }
    }

    public void Dispose()
    {
        _tooltipTimer.Stop();

        if (_isAdded)
        {
            Shell_NotifyIcon(NIM_DELETE, ref _nid);
            _isAdded = false;
        }

        if (_nid.hIcon != IntPtr.Zero)
        {
            DestroyIcon(_nid.hIcon);
            _nid.hIcon = IntPtr.Zero;
        }

        _hwndSource?.RemoveHook(WndProc);
        GC.SuppressFinalize(this);
    }
}
