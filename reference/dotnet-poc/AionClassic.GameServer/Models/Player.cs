using AionClassic.Common.Models;

namespace AionClassic.GameServer.Models;

public class PlayerAppearance
{
    public byte Voice { get; set; }
    public byte SkinColor { get; set; }
    public byte HairColor { get; set; }
    public byte EyeColor { get; set; }
    public byte LipColor { get; set; }
    public byte Face { get; set; }
    public byte Hair { get; set; }
    public byte Deco { get; set; }
    public byte Tattoo { get; set; }
    public byte FaceContour { get; set; }
    public byte Expression { get; set; }
    public byte ShapeRatio { get; set; }
    public float Height { get; set; } = 1.0f;
    public byte[] CustomDetails { get; set; } = new byte[64];
}

public class Player
{
    public int Id { get; set; }
    public int AccountId { get; set; }
    public string Name { get; set; } = string.Empty;
    public PlayerClass PlayerClass { get; set; } = PlayerClass.Warrior;
    public Race Race { get; set; } = Race.Elyos;
    public Gender Gender { get; set; } = Gender.Male;
    public int Level { get; set; } = 1;
    public long Exp { get; set; } = 0;
    public int Hp { get; set; } = 1000;
    public int MaxHp { get; set; } = 1000;
    public int Mp { get; set; } = 1000;
    public int MaxMp { get; set; } = 1000;
    public int Dp { get; set; } = 0;
    public int MaxDp { get; set; } = 4000;

    // Posição no mundo
    public int WorldId { get; set; } = 210010000; // Poeta por padrão
    public float X { get; set; } = 2800.0f;
    public float Y { get; set; } = 1000.0f;
    public float Z { get; set; } = 200.0f;
    public byte Heading { get; set; } = 0;

    public PlayerAppearance Appearance { get; set; } = new();
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
