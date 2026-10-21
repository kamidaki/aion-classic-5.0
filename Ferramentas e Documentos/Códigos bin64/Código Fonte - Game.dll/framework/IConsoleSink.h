#pragma once

// Interface canônica de sink de comandos do console CryEngine (.?AUIConsoleSink@@)
struct IConsoleSink {
    virtual ~IConsoleSink() {}
    virtual void OnConsoleCommand(const char* szCommand) = 0;
};

// Interface canônica de sink de variáveis do console CryEngine (.?AUIConsoleVarSink@@)
struct IConsoleVarSink {
    virtual ~IConsoleVarSink() {}
    virtual void OnConsoleVarChange(const char* szVarName) = 0;
};
