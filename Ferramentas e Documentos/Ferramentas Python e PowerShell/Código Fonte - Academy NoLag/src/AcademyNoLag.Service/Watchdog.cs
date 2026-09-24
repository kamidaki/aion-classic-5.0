using AcademyNoLag.Core.Interfaces;

namespace AcademyNoLag.Service;

public class Watchdog : IDisposable
{
    private readonly ITrafficRedirector _redirector;
    private readonly Timer _watchdogTimer;
    private DateTime _lastHeartbeat = DateTime.UtcNow;
    private readonly TimeSpan _timeout = TimeSpan.FromSeconds(5);

    public Watchdog(ITrafficRedirector redirector)
    {
        _redirector = redirector;
        _watchdogTimer = new Timer(CheckLiveness, null, TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(2));
    }

    public void Heartbeat()
    {
        _lastHeartbeat = DateTime.UtcNow;
    }

    private void CheckLiveness(object? state)
    {
        if (_redirector.IsActive && DateTime.UtcNow - _lastHeartbeat > _timeout)
        {
            Console.WriteLine("[Watchdog] Client UI heartbeat timed out! Restoring default network route safely...");
            _redirector.DisableRedirectionAsync().GetAwaiter().GetResult();
        }
    }

    public void Dispose()
    {
        _watchdogTimer.Dispose();
        GC.SuppressFinalize(this);
    }
}
