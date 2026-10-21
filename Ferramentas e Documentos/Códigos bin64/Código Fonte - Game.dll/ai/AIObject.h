#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <memory>
#include "AiCharContext.h"

struct Vec3F {
    float x, y, z;
    Vec3F(float _x = 0.0f, float _y = 0.0f, float _z = 0.0f) : x(_x), y(_y), z(_z) {}
};

// Objeto base de IA e entidades do mundo extraído do RTTI do game.dll (.?AVAIObject@@)
class AIObject {
public:
    AIObject(uint32_t objectId, const std::string& name);
    virtual ~AIObject();

    virtual void Update();

    uint32_t GetObjectId() const { return m_objectId; }
    const std::string& GetName() const { return m_name; }

    void SetPosition(const Vec3F& pos) { m_position = pos; }
    const Vec3F& GetPosition() const { return m_position; }

    AiCharContext* GetAiContext() { return m_pAiContext.get(); }

private:
    uint32_t m_objectId;
    std::string m_name;
    Vec3F m_position;
    std::unique_ptr<AiCharContext> m_pAiContext;
};
