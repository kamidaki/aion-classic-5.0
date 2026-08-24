using System.Collections.Concurrent;
using AionClassic.GameServer.Models;
using AionClassic.GameServer.Network;

namespace AionClassic.GameServer.World;

public class WorldManager
{
    private static readonly Lazy<WorldManager> _instance = new(() => new WorldManager());
    public static WorldManager Instance => _instance.Value;

    private readonly ConcurrentDictionary<int, ConcurrentDictionary<int, GameSession>> _worldSessions = new();

    public void RegisterPlayer(GameSession session)
    {
        if (session.ActivePlayer == null) return;
        int worldId = session.ActivePlayer.WorldId;

        var mapSessions = _worldSessions.GetOrAdd(worldId, _ => new ConcurrentDictionary<int, GameSession>());
        mapSessions[session.ActivePlayer.Id] = session;

        Console.WriteLine($"[WorldManager] Jogador '{session.ActivePlayer.Name}' entrou no mapa {worldId}. Total no mapa: {mapSessions.Count}");
    }

    public void UnregisterPlayer(GameSession session)
    {
        if (session.ActivePlayer == null) return;
        int worldId = session.ActivePlayer.WorldId;

        if (_worldSessions.TryGetValue(worldId, out var mapSessions))
        {
            mapSessions.TryRemove(session.ActivePlayer.Id, out _);
            Console.WriteLine($"[WorldManager] Jogador '{session.ActivePlayer.Name}' saiu do mapa {worldId}.");
        }
    }

    public async Task BroadcastToMapAsync(int worldId, byte[] packet, int exceptPlayerId = 0)
    {
        if (_worldSessions.TryGetValue(worldId, out var mapSessions))
        {
            foreach (var session in mapSessions.Values)
            {
                if (session.ActivePlayer?.Id != exceptPlayerId)
                {
                    await session.SendRawPacketAsync(packet);
                }
            }
        }
    }
}
