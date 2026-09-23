using System.Text.Json;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Detection;

public class ProfileManager
{
    private readonly List<GameProfile> _profiles = [];
    private readonly string? _customProfilesPath;
    private readonly object _lock = new();

    public IReadOnlyList<GameProfile> Profiles
    {
        get
        {
            lock (_lock)
            {
                return _profiles.ToList();
            }
        }
    }

    public ProfileManager(string? customProfilesPath = null)
    {
        _customProfilesPath = customProfilesPath;
        LoadDefaultProfiles();

        if (!string.IsNullOrEmpty(customProfilesPath) && File.Exists(customProfilesPath))
        {
            LoadCustomProfiles(customProfilesPath);
            return;
        }

        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string[] candidatePaths = [
            Path.Combine(baseDir, "data", "config", "profiles.json"),
            Path.Combine(baseDir, "config", "profiles.json"),
            Path.Combine(baseDir, "modules", "config", "profiles.json"),
            Path.Combine(baseDir, "bin", "config", "profiles.json")
        ];

        foreach (var path in candidatePaths)
        {
            if (File.Exists(path))
            {
                _customProfilesPath = path;
                LoadCustomProfiles(path);
                break;
            }
        }
    }

    private void LoadDefaultProfiles()
    {
        lock (_lock)
        {
            _profiles.Clear();

            // 1. Aion Classic 5.0 (Target #1)
            // BUG FIX: Windows reports process name WITHOUT extension (.bin/.exe stripped).
            // "Aion.bin" runs as ProcessName="Aion". MainModule is inaccessible without
            // admin rights on 64-bit processes, so we must include bare names for detection.
            _profiles.Add(new GameProfile
            {
                Id = "aion_classic_50",
                DisplayName = "Aion Classic 5.0 (EU / Private)",
                ProcessNames = [
                    // Bare names (what Windows actually reports via GetProcessesByName):
                    "Aion", "aion", "AionClassic", "aionclassic", "aion_x64",
                    // Full filenames (for MainModule path matching when accessible):
                    "Aion.bin", "aion.bin", "aionclassic.bin", "Aion.exe", "aion_x64.bin"
                ],
                // Aion Classic 5.0 — all known window titles and exe patterns
                // Window title matching is the universal fallback for emulator clients
                // that may rename the executable. The AION window title is standardized:
                // "AION Client (64bit)", "AION Classic", "AION", "Aion Classic 5.0"
                ExecutablePatterns = [
                    "Aion", "AION", "AionClassic", "Aion Classic", "AION Classic",
                    "Aion EU", "Aion 5.0", "AION Client", "Aion Client"
                ],
                KnownPorts = [2106, 6600, 7777, 10241],
                DefaultProtocol = NetworkTransportProtocol.Tcp,
                PreferredRegions = ["EU-Frankfurt", "SA-SaoPaulo", "NA-Virginia"],
                AutoOptimize = true,
                IsAionClassic = true,
                Category = "MMORPG",
                IconKey = "aion",
                Description = "Aion Classic 5.0 EU / Emulator Client. Dynamic game server and login endpoint routing."
            });

            // 2. League of Legends
            _profiles.Add(new GameProfile
            {
                Id = "league_of_legends",
                DisplayName = "League of Legends",
                ProcessNames = ["League of Legends.exe", "LeagueClient.exe"],
                ExecutablePatterns = ["League of Legends", "Riot Games"],
                KnownPorts = [2099, 5222, 5223, 5000, 5001, 5002],
                DefaultProtocol = NetworkTransportProtocol.Udp,
                PreferredRegions = ["SA-SaoPaulo", "NA-Chicago", "EU-Frankfurt"],
                AutoOptimize = true,
                Category = "MOBA",
                IconKey = "lol",
                Description = "League of Legends MOBA client."
            });

            // 3. Valorant
            _profiles.Add(new GameProfile
            {
                Id = "valorant",
                DisplayName = "Valorant",
                ProcessNames = ["VALORANT-Win64-Shipping.exe", "VALORANT.exe"],
                ExecutablePatterns = ["VALORANT", "Riot Games"],
                KnownPorts = [7000, 7001, 7002, 7003, 7004, 7005],
                DefaultProtocol = NetworkTransportProtocol.Udp,
                PreferredRegions = ["SA-SaoPaulo", "NA-Virginia"],
                AutoOptimize = true,
                Category = "FPS",
                IconKey = "valorant",
                Description = "Valorant Tactical Shooter."
            });

            // 4. Counter-Strike 2
            _profiles.Add(new GameProfile
            {
                Id = "cs2",
                DisplayName = "Counter-Strike 2",
                ProcessNames = ["cs2.exe"],
                ExecutablePatterns = ["Counter-Strike Global Offensive", "cs2"],
                KnownPorts = [27015, 27016, 27017, 27018, 27019, 27020],
                DefaultProtocol = NetworkTransportProtocol.Udp,
                PreferredRegions = ["SA-SaoPaulo", "NA-Virginia", "EU-Frankfurt"],
                AutoOptimize = true,
                Category = "FPS",
                IconKey = "cs2",
                Description = "Counter-Strike 2 Valve Matchmaking."
            });

            // 5. World of Warcraft
            _profiles.Add(new GameProfile
            {
                Id = "wow",
                DisplayName = "World of Warcraft",
                ProcessNames = ["Wow.exe", "WowClassic.exe", "Wow_x64.exe"],
                ExecutablePatterns = ["World of Warcraft"],
                KnownPorts = [3724, 1119],
                DefaultProtocol = NetworkTransportProtocol.Tcp,
                PreferredRegions = ["NA-Chicago", "EU-Frankfurt", "SA-SaoPaulo"],
                AutoOptimize = true,
                Category = "MMORPG",
                IconKey = "wow",
                Description = "World of Warcraft Retail and Classic."
            });

            // 6. Final Fantasy XIV
            _profiles.Add(new GameProfile
            {
                Id = "ffxiv",
                DisplayName = "Final Fantasy XIV",
                ProcessNames = ["ffxiv_dx11.exe", "ffxiv.exe"],
                ExecutablePatterns = ["SquareEnix", "FINAL FANTASY XIV"],
                KnownPorts = [54992, 54993, 54994, 55006, 55007],
                DefaultProtocol = NetworkTransportProtocol.Tcp,
                PreferredRegions = ["NA-Sacramento", "EU-Frankfurt", "JP-Tokyo"],
                AutoOptimize = true,
                Category = "MMORPG",
                IconKey = "ffxiv",
                Description = "Final Fantasy XIV Online."
            });

            // 7. Path of Exile
            _profiles.Add(new GameProfile
            {
                Id = "poe",
                DisplayName = "Path of Exile",
                ProcessNames = ["PathOfExile.exe", "PathOfExile_x64.exe", "PathOfExileSteam.exe"],
                ExecutablePatterns = ["Path of Exile", "GrindingGearGames"],
                KnownPorts = [20481, 6112],
                DefaultProtocol = NetworkTransportProtocol.Tcp,
                PreferredRegions = ["SA-SaoPaulo", "NA-Texas", "EU-Amsterdam"],
                AutoOptimize = true,
                Category = "ARPG",
                IconKey = "poe",
                Description = "Path of Exile Action RPG."
            });
        }
    }

    public void LoadCustomProfiles(string filePath)
    {
        try
        {
            string json = File.ReadAllText(filePath);
            var loaded = JsonSerializer.Deserialize<List<GameProfile>>(json);
            if (loaded != null)
            {
                lock (_lock)
                {
                    foreach (var profile in loaded)
                    {
                        var existing = _profiles.FindIndex(p => p.Id == profile.Id);
                        if (existing >= 0)
                        {
                            _profiles[existing] = profile;
                        }
                        else
                        {
                            _profiles.Add(profile);
                        }
                    }
                }
            }
        }
        catch { /* Fallback gracefully to default profiles */ }
    }

    public void SaveCustomProfiles(string filePath)
    {
        try
        {
            lock (_lock)
            {
                string json = JsonSerializer.Serialize(_profiles, new JsonSerializerOptions { WriteIndented = true });
                string? dir = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }
                File.WriteAllText(filePath, json);
            }
        }
        catch { /* Ignore save errors */ }
    }

    public GameProfile? FindMatchingProfile(string processName, string? executablePath = null)
    {
        lock (_lock)
        {
            return _profiles.FirstOrDefault(p => p.MatchesProcess(processName, executablePath));
        }
    }

    /// <summary>
    /// Matches a profile by window title — used as universal fallback for
    /// processes with unpredictable names (emulators, private servers, wrappers).
    /// </summary>
    public GameProfile? FindMatchingProfileByWindowTitle(string windowTitle)
    {
        if (string.IsNullOrWhiteSpace(windowTitle)) return null;
        lock (_lock)
        {
            // Check ExecutablePatterns, DisplayName, and ProcessNames keywords against the window title
            return _profiles.FirstOrDefault(p =>
                p.ExecutablePatterns.Any(pat =>
                    windowTitle.IndexOf(pat, StringComparison.OrdinalIgnoreCase) >= 0)
                || windowTitle.IndexOf(p.Id.Replace("_", " "), StringComparison.OrdinalIgnoreCase) >= 0
                || p.ProcessNames.Any(pname =>
                    windowTitle.IndexOf(System.IO.Path.GetFileNameWithoutExtension(pname), StringComparison.OrdinalIgnoreCase) >= 0));
        }
    }

    public void AddOrUpdateProfile(GameProfile profile)
    {
        lock (_lock)
        {
            int index = _profiles.FindIndex(p => p.Id == profile.Id);
            if (index >= 0)
            {
                _profiles[index] = profile;
            }
            else
            {
                _profiles.Add(profile);
            }
        }

        if (!string.IsNullOrEmpty(_customProfilesPath))
        {
            SaveCustomProfiles(_customProfilesPath);
        }
    }

    public void SetProfileAutoOptimize(string profileId, bool enable)
    {
        lock (_lock)
        {
            var profile = _profiles.FirstOrDefault(p => p.Id == profileId);
            if (profile != null)
            {
                profile.AutoOptimize = enable;
            }
        }

        if (!string.IsNullOrEmpty(_customProfilesPath))
        {
            SaveCustomProfiles(_customProfilesPath);
        }
    }
}
