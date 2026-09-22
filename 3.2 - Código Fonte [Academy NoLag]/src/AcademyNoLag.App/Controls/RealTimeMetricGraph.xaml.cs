using System.Collections.Specialized;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;

namespace AcademyNoLag.App.Controls;

public partial class RealTimeMetricGraph : System.Windows.Controls.UserControl
{
    public static readonly DependencyProperty DirectPointsProperty =
        DependencyProperty.Register(
            nameof(DirectPoints),
            typeof(INotifyCollectionChanged),
            typeof(RealTimeMetricGraph),
            new PropertyMetadata(null, OnPointsChanged));

    public static readonly DependencyProperty OptimizedPointsProperty =
        DependencyProperty.Register(
            nameof(OptimizedPoints),
            typeof(INotifyCollectionChanged),
            typeof(RealTimeMetricGraph),
            new PropertyMetadata(null, OnPointsChanged));

    public INotifyCollectionChanged? DirectPoints
    {
        get => (INotifyCollectionChanged?)GetValue(DirectPointsProperty);
        set => SetValue(DirectPointsProperty, value);
    }

    public INotifyCollectionChanged? OptimizedPoints
    {
        get => (INotifyCollectionChanged?)GetValue(OptimizedPointsProperty);
        set => SetValue(OptimizedPointsProperty, value);
    }

    private readonly Polyline _directLine;
    private readonly Polyline _optimizedLine;
    private double _maxScale = 100.0;

    public RealTimeMetricGraph()
    {
        InitializeComponent();

        _directLine = new Polyline
        {
            Stroke = new SolidColorBrush(Color.FromRgb(249, 115, 22)), // Orange
            StrokeThickness = 2,
            StrokeLineJoin = PenLineJoin.Round
        };

        _optimizedLine = new Polyline
        {
            Stroke = new SolidColorBrush(Color.FromRgb(0, 229, 255)), // Cyan
            StrokeThickness = 2.5,
            StrokeLineJoin = PenLineJoin.Round
        };

        SizeChanged += (_, _) => Redraw();
    }

    private static void OnPointsChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is RealTimeMetricGraph graph)
        {
            if (e.OldValue is INotifyCollectionChanged oldColl)
            {
                oldColl.CollectionChanged -= graph.OnCollectionChanged;
            }
            if (e.NewValue is INotifyCollectionChanged newColl)
            {
                newColl.CollectionChanged += graph.OnCollectionChanged;
            }
            graph.Redraw();
        }
    }

    private void OnCollectionChanged(object? sender, NotifyCollectionChangedEventArgs e)
    {
        Dispatcher.Invoke(Redraw);
    }

    private double _lastWidth = 0;
    private double _lastHeight = 0;

    private void Redraw()
    {
        double width = ActualWidth;
        double height = ActualHeight;
        if (width <= 10 || height <= 10) return;

        // Extract values
        var directList = (DirectPoints as IEnumerable<double>)?.ToList() ?? [];
        var optList = (OptimizedPoints as IEnumerable<double>)?.ToList() ?? [];

        double currentMax = 50.0;
        if (directList.Count > 0) currentMax = Math.Max(currentMax, directList.Max());
        if (optList.Count > 0) currentMax = Math.Max(currentMax, optList.Max());

        _maxScale = Math.Max(60.0, currentMax * 1.2);
        MaxScaleText.Text = $"{_maxScale:F0}ms";
        MidScaleText.Text = $"{_maxScale / 2.0:F0}ms";

        // Only clear and rebuild visual tree if size changed significantly to avoid layout loops
        bool sizeChanged = Math.Abs(_lastWidth - width) > 1.0 || Math.Abs(_lastHeight - height) > 1.0;
        if (sizeChanged || GraphCanvas.Children.Count == 0)
        {
            _lastWidth = width;
            _lastHeight = height;
            GraphCanvas.Children.Clear();

            // Draw horizontal gridlines (0%, 25%, 50%, 75%, 100%)
            var gridPen = new SolidColorBrush(Color.FromArgb(30, 255, 255, 255));
            for (int i = 0; i <= 4; i++)
            {
                double y = height * (i / 4.0);
                var gridLine = new Line
                {
                    X1 = 0,
                    X2 = width,
                    Y1 = y,
                    Y2 = y,
                    Stroke = gridPen,
                    StrokeDashArray = [4, 4],
                    StrokeThickness = 1
                };
                GraphCanvas.Children.Add(gridLine);
            }
            GraphCanvas.Children.Add(_directLine);
            GraphCanvas.Children.Add(_optimizedLine);
        }

        // Build polyline points
        _directLine.Points.Clear();
        if (directList.Count > 1)
        {
            double stepX = width / Math.Max(1, directList.Count - 1);
            for (int i = 0; i < directList.Count; i++)
            {
                double x = i * stepX;
                double normalizedY = Math.Clamp(directList[i] / _maxScale, 0.0, 1.0);
                double y = height - (normalizedY * (height - 20)) - 10;
                _directLine.Points.Add(new Point(x, y));
            }
        }

        _optimizedLine.Points.Clear();
        if (optList.Count > 1)
        {
            double stepX = width / Math.Max(1, optList.Count - 1);
            for (int i = 0; i < optList.Count; i++)
            {
                double x = i * stepX;
                double normalizedY = Math.Clamp(optList[i] / _maxScale, 0.0, 1.0);
                double y = height - (normalizedY * (height - 20)) - 10;
                _optimizedLine.Points.Add(new Point(x, y));
            }
        }
    }
}
