#pragma once

#ifndef _CCVARSAVEDUMP_H_
#define _CCVARSAVEDUMP_H_

#include <vector>
#include <string>

class CCVarSaveDump
{
public:
    CCVarSaveDump();
    virtual ~CCVarSaveDump();

    void AddCVar(const char* name, const char* value);
    bool DumpToFile(const char* filePath);
    void Clear();

private:
    struct CVarEntry
    {
        std::string name;
        std::string value;
    };
    std::vector<CVarEntry> m_cvars;
};

#endif // _CCVARSAVEDUMP_H_
