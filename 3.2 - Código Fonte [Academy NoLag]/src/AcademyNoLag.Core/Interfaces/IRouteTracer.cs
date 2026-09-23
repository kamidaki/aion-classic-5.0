using System.Net;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Interfaces;

public interface IRouteTracer
{
    event EventHandler<RouteHopInfo>? HopDiscovered;

    Task<RoutePath> TraceRouteAsync(
        IPAddress destination,
        int maxHops = 30,
        int timeoutMs = 1500,
        CancellationToken cancellationToken = default);
}
