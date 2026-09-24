using AcademyNoLag.Core.Models;

namespace AcademyNoLag.Core.Interfaces;

public interface ITrafficRedirector : IDisposable
{
    bool IsActive { get; }
    int RedirectedProcessId { get; }
    RelayNodeInfo? ActiveNode { get; }

    Task<bool> EnableRedirectionAsync(GameProcess process, RelayNodeInfo targetNode, CancellationToken cancellationToken = default);
    Task<bool> DisableRedirectionAsync();
}
