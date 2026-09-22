using System.Diagnostics;
using System.Net;
using System.Runtime.InteropServices;
using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Redirection;

/// <summary>
/// Manages Windows Filtering Platform (WFP) dynamic session for process-level packet redirection.
/// Uses FWPM_SESSION_FLAG_DYNAMIC so all rules are immediately cleared by the Windows kernel
/// if the process exits, crashes, or is killed.
/// </summary>
public class WfpRedirector : IDisposable
{
    private const string WfpLibrary = "fwpuclnt.dll";

    [DllImport(WfpLibrary, SetLastError = true)]
    private static extern uint FwpmEngineOpen0(
        IntPtr serverName,
        uint authnService,
        IntPtr authIdentity,
        IntPtr session,
        out IntPtr engineHandle);

    [DllImport(WfpLibrary, SetLastError = true)]
    private static extern uint FwpmEngineClose0(IntPtr engineHandle);

    private IntPtr _engineHandle = IntPtr.Zero;
    private bool _isInitialized = false;

    public bool IsWfpAvailable => _isInitialized && _engineHandle != IntPtr.Zero;

    public bool TryInitialize()
    {
        try
        {
            // RPC_C_AUTHN_DEFAULT = 0
            uint status = FwpmEngineOpen0(IntPtr.Zero, 0, IntPtr.Zero, IntPtr.Zero, out _engineHandle);
            _isInitialized = (status == 0 && _engineHandle != IntPtr.Zero);
            return _isInitialized;
        }
        catch (Exception)
        {
            // Standard user without administrative privileges or API not supported
            _isInitialized = false;
            _engineHandle = IntPtr.Zero;
            return false;
        }
    }

    public void Close()
    {
        if (_engineHandle != IntPtr.Zero)
        {
            try
            {
                FwpmEngineClose0(_engineHandle);
            }
            catch { /* Ignore */ }
            finally
            {
                _engineHandle = IntPtr.Zero;
                _isInitialized = false;
            }
        }
    }

    public void Dispose()
    {
        Close();
        GC.SuppressFinalize(this);
    }
}
