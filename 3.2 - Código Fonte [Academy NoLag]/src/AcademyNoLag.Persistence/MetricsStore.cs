using System.Text.Json;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Persistence;

public record SessionHistoryEntry(
    DateTime Timestamp,
    string GameName,
    string ServerEndpoint,
    string SelectedNode,
    double DirectAvgPingMs,
    double OptimizedAvgPingMs,
    double ImprovementMs,
    double ImprovementPercent,
    double PacketLossPercentage
);

public class MetricsStore
{
    private readonly string _historyFilePath;
    private readonly List<SessionHistoryEntry> _entries = [];
    private readonly object _lock = new();

    public IReadOnlyList<SessionHistoryEntry> History
    {
        get
        {
            lock (_lock) return _entries.ToList();
        }
    }

    public MetricsStore(string? customPath = null)
    {
        if (!string.IsNullOrEmpty(customPath))
        {
            _historyFilePath = customPath;
        }
        else
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string dir = Path.Combine(appData, "AcademyNoLag");
            _historyFilePath = Path.Combine(dir, "history.json");
        }

        Load();
    }

    public void Load()
    {
        lock (_lock)
        {
            try
            {
                if (File.Exists(_historyFilePath))
                {
                    string json = File.ReadAllText(_historyFilePath);
                    var loaded = JsonSerializer.Deserialize<List<SessionHistoryEntry>>(json);
                    if (loaded != null)
                    {
                        _entries.Clear();
                        _entries.AddRange(loaded);
                    }
                }
            }
            catch { }
        }
    }

    public void RecordSession(SessionHistoryEntry entry)
    {
        lock (_lock)
        {
            _entries.Add(entry);
            // Limit history to last 500 records
            if (_entries.Count > 500)
            {
                _entries.RemoveAt(0);
            }

            try
            {
                string? dir = Path.GetDirectoryName(_historyFilePath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }

                string json = JsonSerializer.Serialize(_entries, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(_historyFilePath, json);
            }
            catch { }
        }
    }
}
