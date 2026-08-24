namespace AionClassic.Common.Models;

public enum Race : byte
{
    Elyos = 0,
    Asmodians = 1,
    Lycan = 2,
    Krall = 3,
    Naga = 4,
    Dragon = 5,
    None = 6
}

public enum PlayerClass : byte
{
    Warrior = 0,
    Gladiator = 1,
    Templar = 2,
    Scout = 3,
    Assassin = 4,
    Ranger = 5,
    Mage = 6,
    Sorcerer = 7,
    SpiritMaster = 8,
    Priest = 9,
    Cleric = 10,
    Chanter = 11,
    Technist = 12,
    Aethertech = 13,
    Gunner = 14,
    Muse = 15,
    Songweaver = 16,
    Painter = 17,
    Monk = 18,
    Vanguard = 19
}

public enum Gender : byte
{
    Male = 0,
    Female = 1
}

public enum StorageType : byte
{
    Cube = 0,
    RegularWarehouse = 1,
    AccountWarehouse = 2,
    LegionWarehouse = 3
}

public enum PacketDirection : byte
{
    ClientToServer,
    ServerToClient
}
