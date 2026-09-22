using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Threading;
using AcademyNoLag.App.ViewModels;
using AcademyNoLag.App.Views;
using WinForms = System.Windows.Forms;

namespace AcademyNoLag.App.Tray;

public class SystemTrayManager : IDisposable
{
    private readonly FloatingHudWindow _floatingHud;
    private readonly MainViewModel _viewModel;
    private readonly WinForms.NotifyIcon _notifyIcon;
    private readonly WinForms.ContextMenuStrip _contextMenu;
    private readonly DispatcherTimer _tooltipTimer;
    private WinForms.ToolStripMenuItem? _autoOptimizeMenuItem;
    private bool _isDisposed = false;

    public FloatingHudWindow FloatingHud => _floatingHud;
    public WinForms.NotifyIcon NotifyIcon => _notifyIcon;

    public SystemTrayManager(FloatingHudWindow floatingHud, MainViewModel viewModel)
    {
        _floatingHud = floatingHud;
        _viewModel = viewModel;

        Diagnostics.Logger.Instance.Info("Tray", "SystemTrayManager constructor started.");

        // 1. Build Dark Gaming ContextMenuStrip with Custom Renderer (Zero White Margins)
        _contextMenu = BuildContextMenu();
        Diagnostics.Logger.Instance.Info("Tray", "ContextMenu built.");

        // 2. Resolve Icon
        Icon icon = ResolveTrayIcon();
        Diagnostics.Logger.Instance.Info("Tray", $"Icon resolved: {icon.Width}x{icon.Height}");

        // 3. Initialize NotifyIcon
        _notifyIcon = new WinForms.NotifyIcon
        {
            Icon = icon,
            Text = "Academy NoLag • Otimizador Ativo",
            ContextMenuStrip = _contextMenu,
            Visible = true
        };
        Diagnostics.Logger.Instance.Info("Tray", $"NotifyIcon initialized with Visible={_notifyIcon.Visible}");

        // Click handlers
        _notifyIcon.MouseClick += (s, e) =>
        {
            if (e.Button == WinForms.MouseButtons.Left)
            {
                _floatingHud.Dispatcher.Invoke(ToggleFloatingHud);
            }
        };

        _notifyIcon.DoubleClick += (s, e) =>
        {
            _floatingHud.Dispatcher.Invoke(ShowFloatingHud);
        };

        // Listen for ViewModel changes to update the auto-optimize menu checkmark
        _viewModel.PropertyChanged += (s, e) =>
        {
            if (e.PropertyName == nameof(MainViewModel.AutoOptimize) && _autoOptimizeMenuItem != null)
            {
                _floatingHud.Dispatcher.Invoke(() =>
                {
                    _autoOptimizeMenuItem.Checked = _viewModel.AutoOptimize;
                    _autoOptimizeMenuItem.Text = _viewModel.AutoOptimize
                        ? "✓ Otimização Automática: ATIVA"
                        : "○ Otimização Automática: MANUAL";
                });
            }
        };

        // 4. Periodic tooltip update (1.5s interval, virtually 0% CPU)
        _tooltipTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromMilliseconds(1500)
        };
        _tooltipTimer.Tick += (_, _) => UpdateTooltip();
        _tooltipTimer.Start();

        // Display brief introductory balloon notification
        try
        {
            _notifyIcon.ShowBalloonTip(
                2000,
                "Academy NoLag",
                "Otimizador de latência ativo e monitorando tráfego do jogo.",
                WinForms.ToolTipIcon.Info
            );
        }
        catch { }
    }

    private static Icon ResolveTrayIcon()
    {
        try
        {
            // 1. Look for app.ico in BaseDirectory
            string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app.ico");
            if (File.Exists(iconPath))
            {
                return new Icon(iconPath);
            }

            // 2. Look in data folder
            string altPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "app.ico");
            if (File.Exists(altPath))
            {
                return new Icon(altPath);
            }

            // 3. Extract associated icon from running executable
            string exePath = Process.GetCurrentProcess().MainModule?.FileName ?? "";
            if (!string.IsNullOrEmpty(exePath) && File.Exists(exePath))
            {
                var extracted = Icon.ExtractAssociatedIcon(exePath);
                if (extracted != null) return extracted;
            }

            // 4. Fallback to standard application icon
            return SystemIcons.Application;
        }
        catch
        {
            return SystemIcons.Application;
        }
    }

    private WinForms.ContextMenuStrip BuildContextMenu()
    {
        var menu = new WinForms.ContextMenuStrip
        {
            Renderer = new WinForms.ToolStripProfessionalRenderer(new DarkGamingColorTable()),
            ShowImageMargin = false, // Completely eliminates the white/gray left gutter column!
            BackColor = Color.FromArgb(15, 23, 42),
            ForeColor = Color.FromArgb(248, 250, 252),
            Font = new Font("Segoe UI", 9f, FontStyle.Regular)
        };

        // Header: ACADEMY NOLAG
        var header = new WinForms.ToolStripMenuItem("⚡ ACADEMY NOLAG")
        {
            Enabled = false,
            Font = new Font("Segoe UI", 9.5f, FontStyle.Bold),
            ForeColor = Color.FromArgb(0, 229, 255)
        };
        menu.Items.Add(header);

        menu.Items.Add(new WinForms.ToolStripSeparator());

        // Abrir Painel HUD
        var openItem = new WinForms.ToolStripMenuItem("🖥️ Abrir Painel HUD", null, (s, e) =>
        {
            _floatingHud.Dispatcher.Invoke(ShowFloatingHud);
        })
        {
            Font = new Font("Segoe UI", 9f, FontStyle.Bold),
            ForeColor = Color.FromArgb(248, 250, 252)
        };
        menu.Items.Add(openItem);

        menu.Items.Add(new WinForms.ToolStripSeparator());

        // Otimização Automática
        _autoOptimizeMenuItem = new WinForms.ToolStripMenuItem(
            _viewModel.AutoOptimize ? "✓ Otimização Automática: ATIVA" : "○ Otimização Automática: MANUAL",
            null,
            (s, e) =>
            {
                _floatingHud.Dispatcher.Invoke(() =>
                {
                    _viewModel.AutoOptimize = !_viewModel.AutoOptimize;
                });
            }
        )
        {
            Checked = _viewModel.AutoOptimize,
            ForeColor = Color.FromArgb(16, 185, 129),
            Font = new Font("Segoe UI", 9f, FontStyle.Regular)
        };
        menu.Items.Add(_autoOptimizeMenuItem);

        // Limpar Cache DNS
        var dnsItem = new WinForms.ToolStripMenuItem("🌐 Limpar Cache DNS", null, (s, e) =>
        {
            _floatingHud.Dispatcher.Invoke(() =>
            {
                if (_viewModel.FlushDnsCommand.CanExecute(null))
                {
                    _viewModel.FlushDnsCommand.Execute(null);
                }
            });
        })
        {
            ForeColor = Color.FromArgb(148, 163, 184),
            Font = new Font("Segoe UI", 9f, FontStyle.Regular)
        };
        menu.Items.Add(dnsItem);

        menu.Items.Add(new WinForms.ToolStripSeparator());

        // Encerrar
        var exitItem = new WinForms.ToolStripMenuItem("❌ Encerrar", null, (s, e) =>
        {
            _floatingHud.Dispatcher.Invoke(() => _floatingHud.ShutdownApp());
        })
        {
            Font = new Font("Segoe UI", 9f, FontStyle.Bold),
            ForeColor = Color.FromArgb(239, 68, 68)
        };
        menu.Items.Add(exitItem);

        return menu;
    }

    private void ToggleFloatingHud()
    {
        if (_floatingHud.IsVisible && _floatingHud.WindowState != System.Windows.WindowState.Minimized)
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

    private void UpdateTooltip()
    {
        try
        {
            if (_isDisposed || _notifyIcon == null) return;

            string tip;
            if (_viewModel.HasActiveGame)
            {
                string game = _viewModel.ActiveGameName;
                double ping = _viewModel.OptimizedPing > 0 ? _viewModel.OptimizedPing : _viewModel.DirectPing;
                tip = $"Academy NoLag • {game} ({ping:F0}ms)";
            }
            else
            {
                tip = "Academy NoLag • Monitorando jogos";
            }

            if (tip.Length > 63)
            {
                tip = tip.Substring(0, 60) + "...";
            }

            _notifyIcon.Text = tip;
        }
        catch { }
    }

    public void Dispose()
    {
        if (_isDisposed) return;
        _isDisposed = true;

        try
        {
            _tooltipTimer.Stop();
        }
        catch { }

        try
        {
            _notifyIcon.Visible = false;
            _notifyIcon.Dispose();
        }
        catch { }

        try
        {
            _contextMenu.Dispose();
        }
        catch { }

        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Custom ColorTable that enforces a modern gaming dark theme and eliminates all white borders/gutters.
    /// </summary>
    private class DarkGamingColorTable : WinForms.ProfessionalColorTable
    {
        public override Color MenuStripGradientBegin => Color.FromArgb(15, 23, 42);
        public override Color MenuStripGradientEnd => Color.FromArgb(15, 23, 42);
        public override Color ToolStripDropDownBackground => Color.FromArgb(15, 23, 42);

        // Eliminates left icon margin white/gray gutter
        public override Color ImageMarginGradientBegin => Color.FromArgb(15, 23, 42);
        public override Color ImageMarginGradientMiddle => Color.FromArgb(15, 23, 42);
        public override Color ImageMarginGradientEnd => Color.FromArgb(15, 23, 42);

        // Item selection & hover
        public override Color MenuItemSelected => Color.FromArgb(30, 41, 59);
        public override Color MenuItemSelectedGradientBegin => Color.FromArgb(30, 41, 59);
        public override Color MenuItemSelectedGradientEnd => Color.FromArgb(30, 41, 59);
        public override Color MenuItemPressedGradientBegin => Color.FromArgb(30, 41, 59);
        public override Color MenuItemPressedGradientEnd => Color.FromArgb(30, 41, 59);

        // Borders
        public override Color MenuBorder => Color.FromArgb(0, 229, 255);
        public override Color MenuItemBorder => Color.FromArgb(0, 229, 255);

        // Separator
        public override Color SeparatorDark => Color.FromArgb(30, 41, 59);
        public override Color SeparatorLight => Color.FromArgb(30, 41, 59);
    }
}
