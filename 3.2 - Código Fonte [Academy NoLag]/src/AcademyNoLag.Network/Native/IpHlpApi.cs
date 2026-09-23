using System.Net;
using System.Runtime.InteropServices;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Network.Native;

public static class IpHlpApi
{
    private const string LibraryName = "iphlpapi.dll";

    [DllImport(LibraryName, SetLastError = true)]
    public static extern uint GetExtendedTcpTable(
        IntPtr pTcpTable,
        ref int pdwSize,
        bool bOrder,
        uint ulAf,
        TCP_TABLE_CLASS tableClass,
        uint reserved = 0);

    [DllImport(LibraryName, SetLastError = true)]
    public static extern uint GetExtendedUdpTable(
        IntPtr pUdpTable,
        ref int pdwSize,
        bool bOrder,
        uint ulAf,
        UDP_TABLE_CLASS tableClass,
        uint reserved = 0);

    [DllImport(LibraryName, SetLastError = true)]
    public static extern IntPtr IcmpCreateFile();

    [DllImport(LibraryName, SetLastError = true)]
    public static extern bool IcmpCloseHandle(IntPtr icmpHandle);

    [DllImport(LibraryName, SetLastError = true)]
    public static extern uint IcmpSendEcho(
        IntPtr icmpHandle,
        uint destinationAddress,
        byte[] requestData,
        short requestSize,
        ref IP_OPTION_INFORMATION requestOptions,
        IntPtr replyBuffer,
        int replySize,
        int timeout);

    public const uint AF_INET = 2;
    public const uint AF_INET6 = 23;
    public const uint NO_ERROR = 0;
    public const uint ERROR_INSUFFICIENT_BUFFER = 122;

    public static List<MIB_TCPROW_OWNER_PID> GetAllTcpConnections()
    {
        var result = new List<MIB_TCPROW_OWNER_PID>();
        int bufferSize = 0;

        // First call to get required buffer size
        GetExtendedTcpTable(IntPtr.Zero, ref bufferSize, true, AF_INET, TCP_TABLE_CLASS.TCP_TABLE_OWNER_PID_ALL);

        if (bufferSize <= 0) return result;

        IntPtr tcpTablePtr = Marshal.AllocHGlobal(bufferSize);
        try
        {
            uint ret = GetExtendedTcpTable(tcpTablePtr, ref bufferSize, true, AF_INET, TCP_TABLE_CLASS.TCP_TABLE_OWNER_PID_ALL);
            if (ret != NO_ERROR) return result;

            int numEntries = Marshal.ReadInt32(tcpTablePtr);
            IntPtr rowPtr = IntPtr.Add(tcpTablePtr, sizeof(int));
            int rowSize = Marshal.SizeOf<MIB_TCPROW_OWNER_PID>();

            for (int i = 0; i < numEntries; i++)
            {
                var row = Marshal.PtrToStructure<MIB_TCPROW_OWNER_PID>(rowPtr);
                result.Add(row);
                rowPtr = IntPtr.Add(rowPtr, rowSize);
            }
        }
        finally
        {
            Marshal.FreeHGlobal(tcpTablePtr);
        }

        return result;
    }

    public static List<MIB_UDPROW_OWNER_PID> GetAllUdpEndpoints()
    {
        var result = new List<MIB_UDPROW_OWNER_PID>();
        int bufferSize = 0;

        GetExtendedUdpTable(IntPtr.Zero, ref bufferSize, true, AF_INET, UDP_TABLE_CLASS.UDP_TABLE_OWNER_PID);

        if (bufferSize <= 0) return result;

        IntPtr udpTablePtr = Marshal.AllocHGlobal(bufferSize);
        try
        {
            uint ret = GetExtendedUdpTable(udpTablePtr, ref bufferSize, true, AF_INET, UDP_TABLE_CLASS.UDP_TABLE_OWNER_PID);
            if (ret != NO_ERROR) return result;

            int numEntries = Marshal.ReadInt32(udpTablePtr);
            IntPtr rowPtr = IntPtr.Add(udpTablePtr, sizeof(int));
            int rowSize = Marshal.SizeOf<MIB_UDPROW_OWNER_PID>();

            for (int i = 0; i < numEntries; i++)
            {
                var row = Marshal.PtrToStructure<MIB_UDPROW_OWNER_PID>(rowPtr);
                result.Add(row);
                rowPtr = IntPtr.Add(rowPtr, rowSize);
            }
        }
        finally
        {
            Marshal.FreeHGlobal(udpTablePtr);
        }

        return result;
    }
}
