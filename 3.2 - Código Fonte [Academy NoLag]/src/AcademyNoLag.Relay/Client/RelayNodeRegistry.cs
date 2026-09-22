using System.Text.Json;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Relay.Client;

public class RelayNodeRegistry : IRelayNodeRegistry
{
    private readonly List<RelayNodeInfo> _nodes = [];
    private readonly object _lock = new();

    public RelayNodeRegistry(string? customNodesPath = null)
    {
        InitializeDefaultNodes();

        if (!string.IsNullOrEmpty(customNodesPath) && File.Exists(customNodesPath))
        {
            LoadCustomNodes(customNodesPath);
            return;
        }

        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string[] candidatePaths = [
            Path.Combine(baseDir, "data", "config", "nodes.json"),
            Path.Combine(baseDir, "config", "nodes.json"),
            Path.Combine(baseDir, "bin", "config", "nodes.json")
        ];

        foreach (var path in candidatePaths)
        {
            if (File.Exists(path))
            {
                LoadCustomNodes(path);
                break;
            }
        }
    }

    private void LoadCustomNodes(string filePath)
    {
        try
        {
            string json = File.ReadAllText(filePath);
            var loaded = JsonSerializer.Deserialize<List<RelayNodeInfo>>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (loaded != null && loaded.Count > 0)
            {
                lock (_lock)
                {
                    _nodes.Clear();
                    _nodes.AddRange(loaded);
                }
            }
        }
        catch { /* Fallback to defaults on corrupt json */ }
    }

    private void InitializeDefaultNodes()
    {
        lock (_lock)
        {
            _nodes.Clear();

            _nodes.Add(new RelayNodeInfo(
                Id: "node_local_test",
                Name: "Local Test Node (Low Overhead Loopback)",
                Region: "Localhost",
                CountryCode: "BR",
                Host: "127.0.0.1",
                Port: 42420
            ));

            _nodes.Add(new RelayNodeInfo(
                Id: "node_sa_sp1",
                Name: "São Paulo FastPath Node 01",
                Region: "São Paulo",
                CountryCode: "BR",
                Host: "127.0.0.1", // Defaults to local listener when server runs
                Port: 42421
            ));

            _nodes.Add(new RelayNodeInfo(
                Id: "node_na_mia",
                Name: "Miami Gaming Gateway",
                Region: "Miami",
                CountryCode: "US",
                Host: "1.1.1.1", // Cloudflare edge IP for real live reachability ping
                Port: 53
            ));

            _nodes.Add(new RelayNodeInfo(
                Id: "node_eu_fra",
                Name: "Frankfurt Core Transit (Aion EU)",
                Region: "Frankfurt",
                CountryCode: "DE",
                Host: "8.8.8.8", // Google DNS Anycast for real reachability probe
                Port: 53
            ));

            _nodes.Add(new RelayNodeInfo(
                Id: "node_na_va",
                Name: "Virginia East Hub",
                Region: "North Virginia",
                CountryCode: "US",
                Host: "9.9.9.9", // Quad9 Anycast for real reachability probe
                Port: 53
            ));
        }
    }

    public IReadOnlyList<RelayNodeInfo> GetNodes()
    {
        lock (_lock)
        {
            return _nodes.ToList();
        }
    }

    public void RegisterNode(RelayNodeInfo node)
    {
        lock (_lock)
        {
            int index = _nodes.FindIndex(n => n.Id == node.Id);
            if (index >= 0)
            {
                _nodes[index] = node;
            }
            else
            {
                _nodes.Add(node);
            }
        }
    }

    public void RemoveNode(string nodeId)
    {
        lock (_lock)
        {
            _nodes.RemoveAll(n => n.Id == nodeId);
        }
    }

    public async Task RefreshAllNodesHealthAsync(CancellationToken cancellationToken = default)
    {
        using var client = new RelayClient();
        var tasks = new List<Task>();

        foreach (var node in GetNodes())
        {
            tasks.Add(Task.Run(async () =>
            {
                await client.MeasureNodeLatencyAsync(node, cancellationToken);
            }, cancellationToken));
        }

        await Task.WhenAll(tasks);
    }
}
