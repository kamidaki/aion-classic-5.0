using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Xml.Linq;

namespace spawn_parser;

public class Parser
{
	public static Thread thr;
	public bool ShowDialogOnFinish { get; set; } = true;
	private readonly FormMain.ChangeUI _ui;
	private volatile bool _stopRequested;

	private class SpotInfo
	{
		public string X { get; set; } = "0";
		public string Y { get; set; } = "0";
		public string Z { get; set; } = "0";
		public string H { get; set; } = "0";
	}

	private class NpcInfo
	{
		public string Id { get; set; } = "";
		public string Name { get; set; } = "";
		public string UiType { get; set; } = "";
		public string NpcType { get; set; } = "";
	}

	public Parser(FormMain.ChangeUI ui)
	{
		_ui = ui;
	}

	public void Stop()
	{
		_stopRequested = true;
	}

	public void Run(string mapID, string pathMission, string pathClientNpcs, string pathGather, string TypeSpawn)
	{
		_stopRequested = false;
		general.mapID = mapID;
		general.missionFile = pathMission;
		general.clientNpcs = pathClientNpcs;
		general.gathers = pathGather;
		general.TypeSpawn = TypeSpawn;

		thr = new Thread(parsing)
		{
			IsBackground = true
		};
		thr.Start();
	}

	private int WriteCategoryFile(
		string suffix,
		string categoryName,
		Func<string, (bool match, string id)> matcher,
		Dictionary<string, List<SpotInfo>> spawnGroups,
		string worldID)
	{
		string outputFileName = $"spawn_{worldID}{suffix}.xml";
		_ui($"\nWriting {categoryName} results to {outputFileName}...");

		int count = 0;
		using (var writer = new StreamWriter(outputFileName, false, Encoding.UTF8))
		{
			writer.WriteLine("<?xml version=\"1.0\" encoding=\"utf-8\"?>");
			writer.WriteLine("<spawns xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\">");
			writer.WriteLine($"<!--Parsed spawns {categoryName} by fieshu 2014 -->");
			writer.WriteLine($"\t<spawn_map map_id=\"{worldID}\">");

			foreach (var kvp in spawnGroups)
			{
				if (_stopRequested)
				{
					_ui($"Parsing cancelled while writing {outputFileName}.");
					break;
				}

				string npcName = kvp.Key;
				List<SpotInfo> spots = kvp.Value;

				var (match, id) = matcher(npcName);
				if (!match || string.IsNullOrEmpty(id))
				{
					continue;
				}

				writer.WriteLine($"        <!--\"{npcName}\"-->");
				writer.WriteLine($"        <spawn npcid=\"{id}\" respawn_time=\"295\">");
				foreach (SpotInfo spot in spots)
				{
					writer.WriteLine($"                <spot x=\"{spot.X}\" y=\"{spot.Y}\" z=\"{spot.Z}\" h=\"{spot.H}\"/>");
				}
				writer.WriteLine("        </spawn>");

				count++;
				_ui($"{id} parsed! <!-- {npcName} --> ({spots.Count} spots)");
			}

			writer.WriteLine("\t</spawn_map>");
			writer.WriteLine("</spawns>");
		}

		_ui($"Saved {count} spawns into {outputFileName}.");
		return count;
	}

	public void parsing()
	{
		try
		{
			_ui("Checking files...");
			if (!File.Exists(general.missionFile))
			{
				_ui($"Error: Mission file not found: {general.missionFile}");
				MessageBox.Show($"Mission file not found: {general.missionFile}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
				return;
			}

			bool needClientNpcs = string.Equals(general.TypeSpawn, "Npc", StringComparison.OrdinalIgnoreCase) ||
			                      string.Equals(general.TypeSpawn, "Monster", StringComparison.OrdinalIgnoreCase) ||
			                      string.Equals(general.TypeSpawn, "All", StringComparison.OrdinalIgnoreCase);

			bool needGathers = string.Equals(general.TypeSpawn, "Gather", StringComparison.OrdinalIgnoreCase) ||
			                   string.Equals(general.TypeSpawn, "All", StringComparison.OrdinalIgnoreCase);

			if (needClientNpcs && !File.Exists(general.clientNpcs))
			{
				_ui($"Error: Client NPCs file not found: {general.clientNpcs}");
				MessageBox.Show($"Client NPCs file not found: {general.clientNpcs}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
				return;
			}

			if (needGathers && !File.Exists(general.gathers))
			{
				_ui($"Error: Gather file not found: {general.gathers}");
				MessageBox.Show($"Gather file not found: {general.gathers}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
				return;
			}

			if (!File.Exists(general.mapID))
			{
				_ui($"Warning: WorldId file not found: {general.mapID}. WorldID will default to 0.");
			}

			_ui("Loading XML files into memory...");
			XDocument xMission = XDocument.Load(general.missionFile);
			XDocument xWorldId = File.Exists(general.mapID) ? XDocument.Load(general.mapID) : null;

			if (_stopRequested)
			{
				_ui("Parsing stopped by user.");
				return;
			}

			// 1. Discover worldID from subzone and WorldId.xml
			general.worldID = null;
			if (xWorldId != null)
			{
				var worldDataMap = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
				foreach (XElement elem in xWorldId.Descendants("data"))
				{
					string val = elem?.Value?.Trim();
					string idAttr = elem?.Attribute("id")?.Value;
					if (!string.IsNullOrEmpty(val) && !string.IsNullOrEmpty(idAttr) && !worldDataMap.ContainsKey(val))
					{
						worldDataMap[val] = idAttr;
					}
				}

				foreach (XElement item in xMission.Descendants("subzone"))
				{
					string subzoneName = item?.Attribute("name")?.Value;
					if (string.IsNullOrEmpty(subzoneName))
					{
						continue;
					}

					string[] array = subzoneName.Split('_');
					if (array.Length > 0 && worldDataMap.TryGetValue(array[0], out string matchedId))
					{
						general.worldID = matchedId;
						break;
					}
				}
			}

			if (string.IsNullOrEmpty(general.worldID))
			{
				general.worldID = "0";
				_ui("WorldID not detected from subzones; defaulting to map_id=\"0\".");
			}
			else
			{
				_ui($"Detected WorldID: {general.worldID}");
			}

			if (_stopRequested)
			{
				_ui("Parsing stopped by user.");
				return;
			}

			// 2. Index NPC / Gather lookup table
			var npcLookup = new Dictionary<string, NpcInfo>(StringComparer.OrdinalIgnoreCase);
			var gatherLookup = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

			if (needClientNpcs)
			{
				_ui("Indexing Client NPC definitions...");
				XDocument xClientNpcs = XDocument.Load(general.clientNpcs);
				foreach (XElement item in xClientNpcs.Descendants("npc_client"))
				{
					string name = item?.Element("name")?.Value?.Trim();
					string id = item?.Element("id")?.Value?.Trim();
					if (string.IsNullOrEmpty(name) || string.IsNullOrEmpty(id))
					{
						continue;
					}

					string uiType = item?.Element("ui_type")?.Value?.Trim() ?? "";
					string npcType = item?.Element("npc_type")?.Value?.Trim() ?? "";

					if (!npcLookup.ContainsKey(name))
					{
						npcLookup[name] = new NpcInfo
						{
							Id = id,
							Name = name,
							UiType = uiType,
							NpcType = npcType
						};
					}
				}
				_ui($"Indexed {npcLookup.Count} client NPC definitions.");
			}

			if (needGathers)
			{
				_ui("Indexing Gather definitions...");
				XDocument xGathers = XDocument.Load(general.gathers);
				foreach (XElement item in xGathers.Descendants("gather_src"))
				{
					string name = item?.Element("name")?.Value?.Trim();
					string id = item?.Element("id")?.Value?.Trim();
					if (!string.IsNullOrEmpty(name) && !string.IsNullOrEmpty(id) && !gatherLookup.ContainsKey(name))
					{
						gatherLookup[name] = id;
					}
				}
				_ui($"Indexed {gatherLookup.Count} gather resources.");
			}

			if (_stopRequested)
			{
				_ui("Parsing stopped by user.");
				return;
			}

			// 3. Scan mission objects and group spawn spots by NPC name (O(N))
			_ui("Grouping spawn points from mission...");
			var spawnGroups = new Dictionary<string, List<SpotInfo>>(StringComparer.OrdinalIgnoreCase);
			int totalObjects = 0;
			int totalSpawns = 0;

			foreach (XElement item in xMission.Descendants("Object"))
			{
				totalObjects++;
				string objType = item?.Attribute("Type")?.Value;
				if (!string.Equals(objType, "SP", StringComparison.OrdinalIgnoreCase))
				{
					continue;
				}

				string npcName = item?.Attribute("npc")?.Value?.Trim();
				if (string.IsNullOrEmpty(npcName))
				{
					continue;
				}

				string posStr = item?.Attribute("Pos")?.Value;
				if (string.IsNullOrEmpty(posStr))
				{
					continue;
				}

				string[] coords = posStr.Split(',');
				if (coords.Length < 3)
				{
					continue;
				}

				string anglesStr = item?.Attribute("Angles")?.Value;
				string h = helper.h_coordinat(anglesStr);

				if (!spawnGroups.TryGetValue(npcName, out List<SpotInfo> spots))
				{
					spots = new List<SpotInfo>();
					spawnGroups[npcName] = spots;
				}

				spots.Add(new SpotInfo
				{
					X = coords[0].Trim(),
					Y = coords[1].Trim(),
					Z = coords[2].Trim(),
					H = h
				});
				totalSpawns++;
			}

			_ui($"Found {totalSpawns} spawn points for {spawnGroups.Count} unique NPC names (scanned {totalObjects} objects).");

			if (_stopRequested)
			{
				_ui("Parsing stopped by user.");
				return;
			}

			// 4. Output results to XML according to selected category
			(bool match, string id) MatchMonster(string npcName)
			{
				if (npcLookup.TryGetValue(npcName, out NpcInfo info))
				{
					bool isMonster = info.UiType.IndexOf("monster", StringComparison.OrdinalIgnoreCase) >= 0 ||
					                 info.NpcType.IndexOf("Monster", StringComparison.OrdinalIgnoreCase) >= 0;
					if (isMonster)
					{
						return (true, info.Id);
					}
				}
				return (false, null);
			}

			(bool match, string id) MatchNpc(string npcName)
			{
				if (npcLookup.TryGetValue(npcName, out NpcInfo info))
				{
					bool isMonster = info.UiType.IndexOf("monster", StringComparison.OrdinalIgnoreCase) >= 0 ||
					                 info.NpcType.IndexOf("Monster", StringComparison.OrdinalIgnoreCase) >= 0;
					if (!isMonster)
					{
						return (true, info.Id);
					}
				}
				return (false, null);
			}

			(bool match, string id) MatchGather(string npcName)
			{
				if (gatherLookup.TryGetValue(npcName, out string id))
				{
					return (true, id);
				}
				return (false, null);
			}

			string selected = general.TypeSpawn ?? "All";
			if (string.Equals(selected, "Npc", StringComparison.OrdinalIgnoreCase))
			{
				int count = WriteCategoryFile("_NPC", "NPC", MatchNpc, spawnGroups, general.worldID);
				string fileName = $"spawn_{general.worldID}_NPC.xml";
				_ui($"\nFinished! Successfully parsed {count} spawns into {fileName}.");
				if (ShowDialogOnFinish)
				{
					MessageBox.Show($"Parsed spawns finished successfully!\nTotal spawns written: {count}\nFile: {fileName}", "Spawn Parser", MessageBoxButtons.OK, MessageBoxIcon.Information);
				}
			}
			else if (string.Equals(selected, "Monster", StringComparison.OrdinalIgnoreCase))
			{
				int count = WriteCategoryFile("_Monster", "Monster", MatchMonster, spawnGroups, general.worldID);
				string fileName = $"spawn_{general.worldID}_Monster.xml";
				_ui($"\nFinished! Successfully parsed {count} spawns into {fileName}.");
				if (ShowDialogOnFinish)
				{
					MessageBox.Show($"Parsed spawns finished successfully!\nTotal spawns written: {count}\nFile: {fileName}", "Spawn Parser", MessageBoxButtons.OK, MessageBoxIcon.Information);
				}
			}
			else if (string.Equals(selected, "Gather", StringComparison.OrdinalIgnoreCase))
			{
				int count = WriteCategoryFile("_Gather", "Gather", MatchGather, spawnGroups, general.worldID);
				string fileName = $"spawn_{general.worldID}_Gather.xml";
				_ui($"\nFinished! Successfully parsed {count} spawns into {fileName}.");
				if (ShowDialogOnFinish)
				{
					MessageBox.Show($"Parsed spawns finished successfully!\nTotal spawns written: {count}\nFile: {fileName}", "Spawn Parser", MessageBoxButtons.OK, MessageBoxIcon.Information);
				}
			}
			else // "All" - Saves separate files for each one of them!
			{
				int npcCount = WriteCategoryFile("_NPC", "NPC", MatchNpc, spawnGroups, general.worldID);
				int monsterCount = WriteCategoryFile("_Monster", "Monster", MatchMonster, spawnGroups, general.worldID);
				int gatherCount = WriteCategoryFile("_Gather", "Gather", MatchGather, spawnGroups, general.worldID);

				string msg = $"Finished! Successfully generated separate spawn files:\n" +
				             $"  - spawn_{general.worldID}_NPC.xml: {npcCount} spawns\n" +
				             $"  - spawn_{general.worldID}_Monster.xml: {monsterCount} spawns\n" +
				             $"  - spawn_{general.worldID}_Gather.xml: {gatherCount} spawns";
				_ui($"\n{msg}");
				if (ShowDialogOnFinish)
				{
					MessageBox.Show(msg, "Spawn Parser", MessageBoxButtons.OK, MessageBoxIcon.Information);
				}
			}
		}
		catch (Exception ex)
		{
			_ui($"FATAL ERROR: {ex.Message}");
			MessageBox.Show($"An error occurred during parsing:\n{ex.Message}\n\nStack Trace:\n{ex.StackTrace}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
		}
	}
}
