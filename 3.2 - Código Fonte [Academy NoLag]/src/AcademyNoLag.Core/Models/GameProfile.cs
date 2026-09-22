namespace AcademyNoLag.Core.Models;

public class GameProfile
{
    public required string Id { get; set; }
    public required string DisplayName { get; set; }
    public required List<string> ProcessNames { get; set; } = [];
    public List<string> ExecutablePatterns { get; set; } = [];
    public List<int> KnownPorts { get; set; } = [];
    public NetworkTransportProtocol DefaultProtocol { get; set; } = NetworkTransportProtocol.Tcp;
    public List<string> PreferredRegions { get; set; } = [];
    public bool AutoOptimize { get; set; } = true;
    public bool IsAionClassic { get; set; } = false;
    public string Category { get; set; } = "MMORPG";
    public string IconKey { get; set; } = "game_default";
    public string Description { get; set; } = "";

    public bool MatchesProcess(string processName, string? executablePath = null)
    {
        if (ProcessNames.Any(p => string.Equals(p, processName, StringComparison.OrdinalIgnoreCase)))
            return true;

        if (ProcessNames.Any(p => string.Equals(System.IO.Path.GetFileNameWithoutExtension(p), processName, StringComparison.OrdinalIgnoreCase)))
            return true;

        if (ProcessNames.Any(p => string.Equals(p + ".exe", processName, StringComparison.OrdinalIgnoreCase)))
            return true;

        if (!string.IsNullOrEmpty(executablePath))
        {
            string fileName = System.IO.Path.GetFileName(executablePath);
            if (ProcessNames.Any(p => string.Equals(p, fileName, StringComparison.OrdinalIgnoreCase)))
                return true;

            if (ExecutablePatterns.Any(pattern =>
                executablePath.Contains(pattern, StringComparison.OrdinalIgnoreCase)))
                return true;
        }

        return false;
    }
}
