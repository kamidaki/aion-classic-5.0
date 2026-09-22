using System.Net;
using AcademyNoLag.Core.Interfaces;
using AcademyNoLag.Core.Models;
using AcademyNoLag.Network.Tracing;

namespace AcademyNoLag.Routing;

public class RouteAnalyzer
{
    private readonly IRouteTracer _tracer;

    public RouteAnalyzer(IRouteTracer? tracer = null)
    {
        _tracer = tracer ?? new RouteTracer();
    }

    public async Task<RoutePath> AnalyzeRouteAsync(
        IPAddress destination,
        CancellationToken cancellationToken = default)
    {
        return await _tracer.TraceRouteAsync(destination, maxHops: 25, timeoutMs: 1200, cancellationToken);
    }
}
