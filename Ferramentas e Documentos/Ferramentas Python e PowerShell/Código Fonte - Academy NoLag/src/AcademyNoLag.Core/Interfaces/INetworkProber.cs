using System.Net;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Interfaces;

public interface INetworkProber : IDisposable
{
    string ProtocolName { get; }
    Task<NetworkMetricSample> ProbeAsync(IPEndPoint target, TimeSpan timeout, CancellationToken cancellationToken = default);
}

public interface IMultiProtocolProber : IDisposable
{
    Task<NetworkMetricSample> ProbeBestAsync(IPEndPoint target, TimeSpan timeout, CancellationToken cancellationToken = default);
    Task<NetworkMetricSample> ProbeIcmpAsync(IPAddress target, TimeSpan timeout, CancellationToken cancellationToken = default);
    Task<NetworkMetricSample> ProbeTcpAsync(IPEndPoint target, TimeSpan timeout, CancellationToken cancellationToken = default);
    Task<NetworkMetricSample> ProbeUdpAsync(IPEndPoint target, TimeSpan timeout, CancellationToken cancellationToken = default);
}
