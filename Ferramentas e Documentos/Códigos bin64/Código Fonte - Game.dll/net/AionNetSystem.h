#pragma once
#include <string>

// Provedor canônico de recursos de rede do Aion (.?AVAionResourceProvider@@)
class AionResourceProvider {
public:
    AionResourceProvider() {}
    virtual ~AionResourceProvider() {}
    virtual bool RequestResource(const std::string& resourceUri) { (void)resourceUri; return true; }
};

// Informações de requisição HTTP (.?AVHttpRequestInfo@@)
class HttpRequestInfo {
public:
    HttpRequestInfo() : method(0), statusCode(200) {}
    virtual ~HttpRequestInfo() {}

    std::string url;
    int method;
    int statusCode;
    std::string responseBody;
};
