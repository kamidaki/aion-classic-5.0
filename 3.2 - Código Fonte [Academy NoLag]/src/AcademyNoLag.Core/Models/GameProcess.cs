using System.Net;

namespace AcademyNoLag.Core.Models;

public record GameProcess(
    int ProcessId,
    string ProcessName,
    string ExecutablePath,
    string? CommandLine = null,
    DateTime? StartTime = null,
    string? MainWindowTitle = null
)
{
    public override string ToString() => $"{ProcessName} (PID: {ProcessId}) - {ExecutablePath}";
}
