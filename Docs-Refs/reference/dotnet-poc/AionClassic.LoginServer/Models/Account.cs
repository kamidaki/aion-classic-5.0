namespace AionClassic.LoginServer.Models;

public class Account
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public byte AccessLevel { get; set; } = 0;
    public byte Membership { get; set; } = 0;
    public byte LastServer { get; set; } = 1;
    public int SessionKey1 { get; set; }
    public int SessionKey2 { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime LastLogin { get; set; } = DateTime.UtcNow;
}
