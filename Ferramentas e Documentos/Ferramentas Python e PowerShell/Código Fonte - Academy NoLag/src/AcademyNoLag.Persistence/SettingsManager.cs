using System.Text.Json;

namespace AcademyNoLag.Persistence;

public class AppSettings
{
    public bool AutoOptimize { get; set; } = true;
    public double MinImprovementPercent { get; set; } = 7.0;
    public double MinImprovementAbsoluteMs { get; set; } = 4.0;
    public string PreferredRegion { get; set; } = "Auto";
    public bool StartWithWindows { get; set; } = false;
    public bool MinimizeToTray { get; set; } = true;
    public string SelectedInterfaceName { get; set; } = "Auto";
    public bool EnableVerboseLogs { get; set; } = false;
    public int PingIntervalMs { get; set; } = 1000;
}

public class SettingsManager
{
    private readonly string _settingsFilePath;
    private AppSettings _currentSettings = new();
    private readonly object _lock = new();

    public AppSettings Current
    {
        get
        {
            lock (_lock) return _currentSettings;
        }
    }

    public SettingsManager(string? customPath = null)
    {
        if (!string.IsNullOrEmpty(customPath))
        {
            _settingsFilePath = customPath;
        }
        else
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string dir = Path.Combine(appData, "AcademyNoLag");
            _settingsFilePath = Path.Combine(dir, "settings.json");
        }

        Load();
    }

    public void Load()
    {
        lock (_lock)
        {
            try
            {
                if (File.Exists(_settingsFilePath))
                {
                    string json = File.ReadAllText(_settingsFilePath);
                    var loaded = JsonSerializer.Deserialize<AppSettings>(json);
                    if (loaded != null) _currentSettings = loaded;
                }
                else
                {
                    Save(); // Write default settings
                }
            }
            catch
            {
                _currentSettings = new AppSettings();
            }
        }
    }

    public void Save()
    {
        lock (_lock)
        {
            try
            {
                string? dir = Path.GetDirectoryName(_settingsFilePath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }

                string json = JsonSerializer.Serialize(_currentSettings, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(_settingsFilePath, json);
            }
            catch { /* Ignore IO errors */ }
        }
    }

    public void Update(Action<AppSettings> updateAction)
    {
        lock (_lock)
        {
            updateAction(_currentSettings);
            Save();
        }
    }
}
