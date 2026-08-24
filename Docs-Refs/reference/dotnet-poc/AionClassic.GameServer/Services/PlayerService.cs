using System.Collections.Concurrent;
using AionClassic.Common.Models;
using AionClassic.GameServer.Models;

namespace AionClassic.GameServer.Services;

public class PlayerService
{
    private static readonly Lazy<PlayerService> _instance = new(() => new PlayerService());
    public static PlayerService Instance => _instance.Value;

    private readonly ConcurrentDictionary<int, Player> _players = new();
    private readonly ConcurrentDictionary<string, Player> _playersByName = new(StringComparer.OrdinalIgnoreCase);
    private int _nextPlayerId = 10000;

    public List<Player> GetPlayersByAccountId(int accountId)
    {
        return _players.Values.Where(p => p.AccountId == accountId).ToList();
    }

    public Player? GetPlayerById(int playerId)
    {
        _players.TryGetValue(playerId, out var player);
        return player;
    }

    public bool IsNameAvailable(string name)
    {
        return !_playersByName.ContainsKey(name);
    }

    public Player? CreateCharacter(int accountId, string name, Race race, PlayerClass playerClass, Gender gender, PlayerAppearance appearance)
    {
        if (!IsNameAvailable(name)) return null;

        int playerId = Interlocked.Increment(ref _nextPlayerId);

        // Define mapa inicial baseado na raça
        int initialWorldId = race == Race.Elyos ? 210010000 : 220010000; // Poeta / Ishalgen
        float startX = race == Race.Elyos ? 2800.0f : 590.0f;
        float startY = race == Race.Elyos ? 1000.0f : 2470.0f;
        float startZ = race == Race.Elyos ? 200.0f : 280.0f;

        var player = new Player
        {
            Id = playerId,
            AccountId = accountId,
            Name = name,
            Race = race,
            PlayerClass = playerClass,
            Gender = gender,
            Appearance = appearance,
            WorldId = initialWorldId,
            X = startX,
            Y = startY,
            Z = startZ,
            Level = 1,
            Exp = 0,
            Hp = 1000,
            MaxHp = 1000,
            Mp = 1000,
            MaxMp = 1000
        };

        _players[playerId] = player;
        _playersByName[name] = player;

        Console.WriteLine($"[PlayerService] Personagem criado: '{player.Name}' (ID={playerId}, Classe={playerClass}, Raça={race})");
        return player;
    }
}
