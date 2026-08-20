using AionClassic.Common.Models;

namespace AionClassic.Data.Templates;

public class ItemTemplate
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string ItemType { get; set; } = string.Empty;
    public string ItemSlot { get; set; } = string.Empty;
    public int Level { get; set; }
    public int Quality { get; set; }
    public int Price { get; set; }
    public int MaxStack { get; set; } = 1;
}

public class NpcTemplate
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public int Level { get; set; }
    public int MaxHp { get; set; }
    public int MaxMp { get; set; }
    public string NpcType { get; set; } = string.Empty;
    public string Race { get; set; } = string.Empty;
    public string Faction { get; set; } = string.Empty;
    public int Exp { get; set; }
    public float WalkSpeed { get; set; } = 2.0f;
    public float RunSpeed { get; set; } = 6.0f;
}

public class SpawnTemplate
{
    public int NpcId { get; set; }
    public int WorldId { get; set; }
    public float X { get; set; }
    public float Y { get; set; }
    public float Z { get; set; }
    public byte Heading { get; set; }
    public int RespawnTime { get; set; }
    public string WalkerId { get; set; } = string.Empty;
}

public class WorldMapTemplate
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public int TwinCount { get; set; }
    public int MaxPlayers { get; set; }
    public bool Prison { get; set; }
    public string WorldType { get; set; } = string.Empty;
}

public class SkillTemplate
{
    public int SkillId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int SkillLevel { get; set; }
    public int RequiredLevel { get; set; }
    public PlayerClass PlayerClass { get; set; }
    public int Cooldown { get; set; }
    public int CastTime { get; set; }
    public int HpCost { get; set; }
    public int MpCost { get; set; }
    public int DpCost { get; set; }
}
