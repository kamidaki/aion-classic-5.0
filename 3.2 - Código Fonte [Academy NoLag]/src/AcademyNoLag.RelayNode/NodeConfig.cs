namespace AcademyNoLag.RelayNode;

public record NodeConfig(
    int Port = 42420,
    string BindAddress = "0.0.0.0",
    string NodeName = "Academy NoLag Relay Node",
    string Region = "BR-Local",
    int MaxClients = 1000
);
