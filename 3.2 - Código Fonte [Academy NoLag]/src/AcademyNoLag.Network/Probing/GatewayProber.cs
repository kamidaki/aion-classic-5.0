using System.Net;
using System.Net.NetworkInformation;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Network.Probing;

/// <summary>
/// Probes the local network default gateway (LAN / ISP Access point).
/// Distinguishes local router congestion or Wi-Fi jitter from WAN internet transit issues.
/// </summary>
public class GatewayProber : IDisposable
{
    private readonly IcmpProber _icmpProber = new();
    private IPAddress? _gatewayAddress;

    public IPAddress? GatewayAddress => _gatewayAddress;

    public GatewayProber()
    {
        DiscoverDefaultGateway();
    }

    public void DiscoverDefaultGateway()
    {
        try
        {
            var card = NetworkInterface.GetAllNetworkInterfaces()
                .FirstOrDefault(nic =>
                    nic.OperationalStatus == OperationalStatus.Up &&
                    nic.NetworkInterfaceType != NetworkInterfaceType.Loopback &&
                    nic.GetIPProperties().GatewayAddresses.Any(g => g.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork));

            if (card != null)
            {
                var gateway = card.GetIPProperties().GatewayAddresses
                    .FirstOrDefault(g => g.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);

                _gatewayAddress = gateway?.Address;
            }
        }
        catch
        {
            _gatewayAddress = null;
        }
    }

    public async Task<NetworkMetricSample> ProbeGatewayAsync(
        TimeSpan timeout,
        CancellationToken cancellationToken = default)
    {
        if (_gatewayAddress == null)
        {
            DiscoverDefaultGateway();
            if (_gatewayAddress == null)
            {
                return NetworkMetricSample.Failure(
                    new IPEndPoint(IPAddress.Loopback, 0),
                    "Gateway",
                    "No active default gateway found");
            }
        }

        return await _icmpProber.ProbeAddressAsync(_gatewayAddress, timeout, cancellationToken);
    }

    public void Dispose()
    {
        _icmpProber.Dispose();
        GC.SuppressFinalize(this);
    }
}
