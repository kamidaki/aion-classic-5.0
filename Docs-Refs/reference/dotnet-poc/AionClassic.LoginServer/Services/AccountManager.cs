using System.Collections.Concurrent;
using AionClassic.LoginServer.Models;

namespace AionClassic.LoginServer.Services;

public class AccountManager
{
    private static readonly Lazy<AccountManager> _instance = new(() => new AccountManager());
    public static AccountManager Instance => _instance.Value;

    private readonly ConcurrentDictionary<string, Account> _accounts = new(StringComparer.OrdinalIgnoreCase);
    private readonly ConcurrentDictionary<int, Account> _accountsById = new();
    private int _nextAccountId = 1;

    public AccountManager()
    {
        // Cria uma conta de teste padrão GM/Admin
        CreateOrGetAccount("admin", "admin", 3);
    }

    public Account CreateOrGetAccount(string username, string password, byte accessLevel = 0)
    {
        return _accounts.GetOrAdd(username, (user) =>
        {
            int id = Interlocked.Increment(ref _nextAccountId);
            var acc = new Account
            {
                Id = id,
                Username = user,
                Password = password,
                AccessLevel = accessLevel,
                CreatedAt = DateTime.UtcNow,
                LastLogin = DateTime.UtcNow
            };
            _accountsById[id] = acc;
            return acc;
        });
    }

    public Account? Authenticate(string username, string password, bool autoCreate = true)
    {
        if (string.IsNullOrWhiteSpace(username)) return null;

        if (_accounts.TryGetValue(username, out var account))
        {
            if (account.Password == password || string.IsNullOrEmpty(account.Password))
            {
                account.LastLogin = DateTime.UtcNow;
                return account;
            }
            return null;
        }

        if (autoCreate)
        {
            var newAcc = CreateOrGetAccount(username, password, 0);
            return newAcc;
        }

        return null;
    }

    public Account? GetAccount(int accountId)
    {
        _accountsById.TryGetValue(accountId, out var acc);
        return acc;
    }
}
