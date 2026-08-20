using System.Collections.Concurrent;
using System.Xml.Linq;
using AionClassic.Common.Models;
using AionClassic.Data.Templates;

namespace AionClassic.Data;

public class DataManager
{
    private static readonly Lazy<DataManager> _instance = new(() => new DataManager());
    public static DataManager Instance => _instance.Value;

    public ConcurrentDictionary<int, ItemTemplate> Items { get; } = new();
    public ConcurrentDictionary<int, NpcTemplate> Npcs { get; } = new();
    public ConcurrentDictionary<int, WorldMapTemplate> WorldMaps { get; } = new();
    public ConcurrentDictionary<int, List<SpawnTemplate>> Spawns { get; } = new();
    public ConcurrentDictionary<int, List<SkillTemplate>> Skills { get; } = new();

    public bool IsLoaded { get; private set; }

    public void LoadData(string basePath)
    {
        Console.WriteLine($"[DataManager] Carregando templates estáticos de: {basePath}");

        // 1. Carrega Mapas
        string mapsPath = Path.Combine(basePath, "world_maps.xml");
        if (File.Exists(mapsPath))
        {
            try
            {
                var doc = XDocument.Load(mapsPath);
                foreach (var el in doc.Descendants("map"))
                {
                    int id = int.Parse(el.Attribute("id")?.Value ?? "0");
                    string name = el.Attribute("name")?.Value ?? string.Empty;
                    int twin = int.Parse(el.Attribute("twin_count")?.Value ?? "0");
                    int maxPlayers = int.Parse(el.Attribute("max_players")?.Value ?? "0");
                    bool prison = bool.Parse(el.Attribute("prison")?.Value ?? "false");
                    string worldType = el.Attribute("world_type")?.Value ?? string.Empty;

                    WorldMaps[id] = new WorldMapTemplate
                    {
                        Id = id,
                        Name = name,
                        TwinCount = twin,
                        MaxPlayers = maxPlayers,
                        Prison = prison,
                        WorldType = worldType
                    };
                }
                Console.WriteLine($"  ✓ Mapas carregados: {WorldMaps.Count}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  [!] Erro ao carregar world_maps.xml: {ex.Message}");
            }
        }

        // 2. Carrega Dados Iniciais padrão (Poeta = 210010000, Ishalgen = 220010000, etc.)
        EnsureDefaultMaps();

        IsLoaded = true;
        Console.WriteLine("[DataManager] Carregamento de dados concluído com sucesso.");
    }

    private void EnsureDefaultMaps()
    {
        if (!WorldMaps.ContainsKey(210010000))
        {
            WorldMaps[210010000] = new WorldMapTemplate { Id = 210010000, Name = "Poeta", WorldType = "ASSONLY" };
        }
        if (!WorldMaps.ContainsKey(220010000))
        {
            WorldMaps[220010000] = new WorldMapTemplate { Id = 220010000, Name = "Ishalgen", WorldType = "ASSONLY" };
        }
        if (!WorldMaps.ContainsKey(110010000))
        {
            WorldMaps[110010000] = new WorldMapTemplate { Id = 110010000, Name = "Sanctum", WorldType = "CITY" };
        }
        if (!WorldMaps.ContainsKey(120010000))
        {
            WorldMaps[120010000] = new WorldMapTemplate { Id = 120010000, Name = "Pandaemonium", WorldType = "CITY" };
        }
    }
}
