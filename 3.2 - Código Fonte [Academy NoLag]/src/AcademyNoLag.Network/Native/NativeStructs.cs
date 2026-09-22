using System.Net;
using System.Runtime.InteropServices;

namespace AcademyNoLag.Network.Native;

public enum TCP_TABLE_CLASS
{
    TCP_TABLE_BASIC_LISTENER,
    TCP_TABLE_BASIC_CONNECTIONS,
    TCP_TABLE_BASIC_ALL,
    TCP_TABLE_OWNER_PID_LISTENER,
    TCP_TABLE_OWNER_PID_CONNECTIONS,
    TCP_TABLE_OWNER_PID_ALL,
    TCP_TABLE_OWNER_MODULE_LISTENER,
    TCP_TABLE_OWNER_MODULE_CONNECTIONS,
    TCP_TABLE_OWNER_MODULE_ALL
}

public enum UDP_TABLE_CLASS
{
    UDP_TABLE_BASIC,
    UDP_TABLE_OWNER_PID,
    UDP_TABLE_OWNER_MODULE
}

public enum MIB_TCP_STATE
{
    CLOSED = 1,
    LISTEN = 2,
    SYN_SENT = 3,
    SYN_RCVD = 4,
    ESTAB = 5,
    FIN_WAIT1 = 6,
    FIN_WAIT2 = 7,
    CLOSE_WAIT = 8,
    CLOSING = 9,
    LAST_ACK = 10,
    TIME_WAIT = 11,
    DELETE_TCB = 12
}

[StructLayout(LayoutKind.Sequential)]
public struct MIB_TCPROW_OWNER_PID
{
    public uint state;
    public uint localAddr;
    public byte localPort1;
    public byte localPort2;
    public byte localPort3;
    public byte localPort4;
    public uint remoteAddr;
    public byte remotePort1;
    public byte remotePort2;
    public byte remotePort3;
    public byte remotePort4;
    public uint owningPid;

    public ushort LocalPort => (ushort)((localPort1 << 8) | localPort2);
    public ushort RemotePort => (ushort)((remotePort1 << 8) | remotePort2);

    public IPAddress LocalAddress => new IPAddress(localAddr);
    public IPAddress RemoteAddress => new IPAddress(remoteAddr);

    public MIB_TCP_STATE State => (MIB_TCP_STATE)state;
    public int ProcessId => (int)owningPid;
}

[StructLayout(LayoutKind.Sequential)]
public struct MIB_UDPROW_OWNER_PID
{
    public uint localAddr;
    public byte localPort1;
    public byte localPort2;
    public byte localPort3;
    public byte localPort4;
    public uint owningPid;

    public ushort LocalPort => (ushort)((localPort1 << 8) | localPort2);
    public IPAddress LocalAddress => new IPAddress(localAddr);
    public int ProcessId => (int)owningPid;
}

[StructLayout(LayoutKind.Sequential)]
public struct IP_OPTION_INFORMATION
{
    public byte Ttl;
    public byte Tos;
    public byte Flags;
    public byte OptionsSize;
    public IntPtr OptionsData;
}

[StructLayout(LayoutKind.Sequential)]
public struct ICMP_ECHO_REPLY
{
    public uint Address;
    public uint Status;
    public uint RoundTripTime;
    public ushort DataSize;
    public ushort Reserved;
    public IntPtr Data;
    public IP_OPTION_INFORMATION Options;
}
