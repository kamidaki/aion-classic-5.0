namespace AcademyNoLag.Diagnostics;

public enum LogLevel
{
    Debug,
    Info,
    Warning,
    Error,
    Metric
}

public record LogMessage(
    DateTime Timestamp,
    LogLevel Level,
    string Component,
    string Message
)
{
    public string Formatted => $"[{Timestamp:HH:mm:ss.fff}] [{Level.ToString().ToUpper()}] [{Component}] {Message}";
}

public class Logger
{
    private static readonly Lazy<Logger> _instance = new(() => new Logger());
    public static Logger Instance => _instance.Value;

    private readonly List<LogMessage> _memoryLogs = [];
    private readonly object _lock = new();
    private readonly string? _logFilePath;
    private const int MaxMemoryLogCount = 1000;

    public event EventHandler<LogMessage>? LogAppended;

    public IReadOnlyList<LogMessage> RecentLogs
    {
        get
        {
            lock (_lock) return _memoryLogs.ToList();
        }
    }

    public Logger(string? customLogPath = null)
    {
        if (customLogPath != null)
        {
            _logFilePath = customLogPath;
        }
        else
        {
            try
            {
                string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                string dir = Path.Combine(appData, "AcademyNoLag", "logs");
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);
                _logFilePath = Path.Combine(dir, $"academy_nolag_{DateTime.Now:yyyyMMdd}.log");
            }
            catch { }
        }
    }

    public void Log(LogLevel level, string component, string message)
    {
        var log = new LogMessage(DateTime.Now, level, component, message);

        lock (_lock)
        {
            _memoryLogs.Add(log);
            if (_memoryLogs.Count > MaxMemoryLogCount)
            {
                _memoryLogs.RemoveAt(0);
            }

            if (!string.IsNullOrEmpty(_logFilePath))
            {
                try
                {
                    File.AppendAllText(_logFilePath, log.Formatted + Environment.NewLine);
                }
                catch { }
            }
        }

        LogAppended?.Invoke(this, log);
    }

    public void Info(string component, string message) => Log(LogLevel.Info, component, message);
    public void Warn(string component, string message) => Log(LogLevel.Warning, component, message);
    public void Error(string component, string message) => Log(LogLevel.Error, component, message);
    public void Metric(string component, string message) => Log(LogLevel.Metric, component, message);
    public void Debug(string component, string message) => Log(LogLevel.Debug, component, message);
}
