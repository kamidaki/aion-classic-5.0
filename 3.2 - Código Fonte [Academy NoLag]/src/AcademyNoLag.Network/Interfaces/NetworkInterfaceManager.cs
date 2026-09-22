using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Network.Interfaces;

public class NetworkInterfaceManager
{
    public IReadOnlyList<NetworkInterfaceInfo> GetAllInterfaces()
    {
        var result = new List<NetworkInterfaceInfo>();

        try
        {
            var interfaces = NetworkInterface.GetAllNetworkInterfaces();

            foreach (var nic in interfaces)
            {
                if (nic.NetworkInterfaceType == NetworkInterfaceType.Loopback)
                    continue;

                var ipProps = nic.GetIPProperties();

                var ipv4List = ipProps.UnicastAddresses
                    .Where(u => u.Address.AddressFamily == AddressFamily.InterNetwork)
                    .Select(u => u.Address)
                    .ToList();

                var ipv6List = ipProps.UnicastAddresses
                    .Where(u => u.Address.AddressFamily == AddressFamily.InterNetworkV6)
                    .Select(u => u.Address)
                    .ToList();

                var gatewayIpv4 = ipProps.GatewayAddresses
                    .FirstOrDefault(g => g.Address.AddressFamily == AddressFamily.InterNetwork)?.Address;

                var gatewayIpv6 = ipProps.GatewayAddresses
                    .FirstOrDefault(g => g.Address.AddressFamily == AddressFamily.InterNetworkV6)?.Address;

                var dnsList = ipProps.DnsAddresses.ToList();

                int mtu = 1500;
                try
                {
                    var ipv4Props = ipProps.GetIPv4Properties();
                    if (ipv4Props != null) mtu = ipv4Props.Mtu;
                }
                catch { /* Ignore */ }

                bool isDefault = gatewayIpv4 != null && nic.OperationalStatus == OperationalStatus.Up;

                var info = new NetworkInterfaceInfo(
                    Id: nic.Id,
                    Name: nic.Name,
                    Description: nic.Description,
                    InterfaceType: nic.NetworkInterfaceType.ToString(),
                    IPv4Addresses: ipv4List,
                    IPv6Addresses: ipv6List,
                    GatewayIPv4: gatewayIpv4,
                    GatewayIPv6: gatewayIpv6,
                    DnsServers: dnsList,
                    SpeedBitsPerSec: nic.Speed,
                    OperationalStatus: nic.OperationalStatus.ToString(),
                    Mtu: mtu,
                    IsDefaultGateway: isDefault
                );

                result.Add(info);
            }
        }
        catch (Exception)
        {
            // Fallback empty list on error
        }

        return result;
    }

    public NetworkInterfaceInfo? GetPrimaryInterface()
    {
        var interfaces = GetAllInterfaces();
        return interfaces.FirstOrDefault(i => i.IsDefaultGateway && i.OperationalStatus == "Up")
               ?? interfaces.FirstOrDefault(i => i.OperationalStatus == "Up");
    }
}
