#include "CCVarSaveDump.h"
#include <cstdio>

CCVarSaveDump::CCVarSaveDump()
{
}

CCVarSaveDump::~CCVarSaveDump()
{
}

void CCVarSaveDump::AddCVar(const char* name, const char* value)
{
    if (name && value)
    {
        m_cvars.push_back({name, value});
    }
}

bool CCVarSaveDump::DumpToFile(const char* filePath)
{
    if (!filePath || !filePath[0]) return false;

    FILE* fp = nullptr;
    fopen_s(&fp, filePath, "w");
    if (!fp) return false;

    fprintf(fp, "-- CrySystem CVar Save Dump (Aion Classic 5.0)\n");
    for (const auto& cv : m_cvars)
    {
        fprintf(fp, "%s = \"%s\"\n", cv.name.c_str(), cv.value.c_str());
    }
    fclose(fp);
    return true;
}

void CCVarSaveDump::Clear()
{
    m_cvars.clear();
}
