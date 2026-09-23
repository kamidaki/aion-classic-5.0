using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace AcademyNoLag.Core.Models;

public class GameProfile : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    public required string Id { get; set; }
    public required string DisplayName { get; set; }
    public required List<string> ProcessNames { get; set; } = [];
    public List<string> ExecutablePatterns { get; set; } = [];
    public List<int> KnownPorts { get; set; } = [];
    public NetworkTransportProtocol DefaultProtocol { get; set; } = NetworkTransportProtocol.Tcp;
    public List<string> PreferredRegions { get; set; } = [];
    
    private bool _autoOptimize = true;
    public bool AutoOptimize
    {
        get => _autoOptimize;
        set
        {
            if (_autoOptimize != value)
            {
                _autoOptimize = value;
                OnPropertyChanged();
            }
        }
    }
    
    public bool IsAionClassic { get; set; } = false;
    public string Category { get; set; } = "MMORPG";
    public string IconKey { get; set; } = "game_default";
    public string Description { get; set; } = "";

    public bool MatchesProcess(string processName, string? executablePath = null)
    {
        if (string.IsNullOrWhiteSpace(processName)) return false;

        string cleanName = processName.Trim();
        string processNoExt = System.IO.Path.GetFileNameWithoutExtension(cleanName);

        // 1. Direct match on ProcessNames (exact or stripped extension)
        if (ProcessNames.Any(p =>
            string.Equals(p, cleanName, StringComparison.OrdinalIgnoreCase) ||
            string.Equals(p, processNoExt, StringComparison.OrdinalIgnoreCase) ||
            string.Equals(System.IO.Path.GetFileNameWithoutExtension(p), cleanName, StringComparison.OrdinalIgnoreCase) ||
            string.Equals(System.IO.Path.GetFileNameWithoutExtension(p), processNoExt, StringComparison.OrdinalIgnoreCase)))
            return true;

        // 2. Suffix match (.exe, .bin)
        if (ProcessNames.Any(p =>
            string.Equals(p + ".exe", cleanName, StringComparison.OrdinalIgnoreCase) ||
            string.Equals(p + ".bin", cleanName, StringComparison.OrdinalIgnoreCase)))
            return true;

        // 3. ExecutablePatterns match against processName
        if (ExecutablePatterns.Any(pattern =>
            string.Equals(cleanName, pattern, StringComparison.OrdinalIgnoreCase) ||
            string.Equals(processNoExt, pattern, StringComparison.OrdinalIgnoreCase) ||
            cleanName.StartsWith(pattern, StringComparison.OrdinalIgnoreCase) ||
            processNoExt.StartsWith(pattern, StringComparison.OrdinalIgnoreCase)))
            return true;

        // 4. ExecutablePath matching when accessible (with elevation)
        if (!string.IsNullOrEmpty(executablePath))
        {
            string fileName = System.IO.Path.GetFileName(executablePath);
            string fileNameNoExt = System.IO.Path.GetFileNameWithoutExtension(fileName);

            if (ProcessNames.Any(p =>
                string.Equals(p, fileName, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(System.IO.Path.GetFileNameWithoutExtension(p), fileNameNoExt, StringComparison.OrdinalIgnoreCase)))
                return true;

            // Match ExecutablePatterns ONLY against the executable filename, never against parent directories
            if (ExecutablePatterns.Any(pattern =>
                string.Equals(fileName, pattern, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(fileNameNoExt, pattern, StringComparison.OrdinalIgnoreCase) ||
                fileName.StartsWith(pattern, StringComparison.OrdinalIgnoreCase)))
                return true;
        }

        return false;
    }
}
