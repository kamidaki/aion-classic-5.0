namespace AcademyNoLag.Service;

public record IpcRequest(
    string Command,
    string? Payload = null
);

public record IpcResponse(
    bool Success,
    string Message,
    string? Data = null
);
