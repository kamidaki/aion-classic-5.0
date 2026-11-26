#pragma once
#include <cstdint>
#include <vector>
#include <unordered_map>

// Tabela canônica de rotas de voo e teleporte de voo extraída do RTTI (.?AVFlyPathTable@@)
class FlyPathTable {
public:
    FlyPathTable();
    virtual ~FlyPathTable();

    virtual bool LoadTable();
    virtual const char* GetTableName() const { return "FlyPathTable"; }
    bool HasFlyPath(uint32_t id) const;

private:
    bool m_bLoaded;
    std::unordered_map<uint32_t, uint32_t> m_paths;
};
