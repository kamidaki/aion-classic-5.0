using System.Diagnostics;
using System.Net;

namespace AcademyNoLag.Network.Probing;

public record DnsBenchmarkResult(
    string ResolverName,
    string Hostname,
    double ResponseTimeMs,
    IPAddress? ResolvedIp,
    bool IsSuccess,
    string? ErrorMessage = null
);

public class DnsBenchmarkProber
{
    public async Task<DnsBenchmarkResult> BenchmarkResolverAsync(
        string hostname,
        string resolverName = "System",
        CancellationToken cancellationToken = default)
    {
        long startTimestamp = Stopwatch.GetTimestamp();

        try
        {
            var addresses = await Dns.GetHostAddressesAsync(hostname, cancellationToken);
            double elapsedMs = Stopwatch.GetElapsedTime(startTimestamp).TotalMilliseconds;

            var primary = addresses.FirstOrDefault(a => a.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);

            return new DnsBenchmarkResult(
                resolverName,
                hostname,
                Math.Max(0.1, elapsedMs),
                primary,
                primary != null
            );
        }
        catch (Exception ex)
        {
            double elapsedMs = Stopwatch.GetElapsedTime(startTimestamp).TotalMilliseconds;
            return new DnsBenchmarkResult(
                resolverName,
                hostname,
                elapsedMs,
                null,
                false,
                ex.Message
            );
        }
    }
}
