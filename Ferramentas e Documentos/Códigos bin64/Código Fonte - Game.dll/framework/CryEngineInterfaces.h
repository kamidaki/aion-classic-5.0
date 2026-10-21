#pragma once
#include <cstdint>
#include <vector>

// Interface canônica CryEngine para usuários de movie/cutscene (.?AUIMovieUser@@)
struct IMovieUser {
    virtual ~IMovieUser() {}
    virtual void OnMovieEvent(int eventId) { (void)eventId; }
};

// Interface canônica CryEngine para eventos de som (.?AUISoundEventListener@@)
struct ISoundEventListener {
    virtual ~ISoundEventListener() {}
    virtual void OnSoundEvent(int eventId) { (void)eventId; }
};

// Interface canônica CryEngine para pontos de tag (.?AUITagPoint@@)
struct ITagPoint {
    virtual ~ITagPoint() {}
    virtual void GetPos(float& x, float& y, float& z) = 0;
    virtual void SetPos(float x, float y, float z) = 0;
};

// Interface canônica CryEngine para gerenciador de tag points (.?AUITagPointManager@@)
struct ITagPointManager {
    virtual ~ITagPointManager() {}
    virtual ITagPoint* CreateTagPoint(const char* name) = 0;
    virtual ITagPoint* GetTagPoint(const char* name) = 0;
    virtual void RemoveTagPoint(ITagPoint* point) = 0;
};

// Interface canônica CryEngine para áreas de gatilho e som (.?AUIXArea@@)
struct IXArea {
    virtual ~IXArea() {}
    virtual int GetAreaId() const = 0;
};

// Interface canônica CryEngine para gerenciador de áreas (.?AUIXAreaMgr@@)
struct IXAreaMgr {
    virtual ~IXAreaMgr() {}
    virtual IXArea* CreateArea() = 0;
    virtual void DeleteArea(IXArea* area) = 0;
};

// Interface canônica CryEngine de condição lógica (.?AUIcond@@)
struct Icond {
    virtual ~Icond() {}
    virtual bool Evaluate() = 0;
};

// Interface canônica CryEngine de job/tarefa (.?AUIjob@@)
struct Ijob {
    virtual ~Ijob() {}
    virtual void Execute() = 0;
};

// Interface canônica CryEngine de cálculo unitário (.?AUICalcUnit@@)
struct ICalcUnit {
    virtual ~ICalcUnit() {}
    virtual void Calculate() = 0;
};

// Interface de callback MX Wrapper (.?AUIMXWrapperCallback@@)
struct IMXWrapperCallback {
    virtual ~IMXWrapperCallback() {}
    virtual void OnWrapperCallback(int code) { (void)code; }
};

// Interface para operações pendentes (.?AUIPending@@)
struct IPending {
    virtual ~IPending() {}
    virtual bool IsPending() const = 0;
};

// Classe canônica de estado pendente (.?AVPending@@)
class Pending : public IPending {
public:
    Pending() : m_bPending(true) {}
    virtual ~Pending() {}
    virtual bool IsPending() const override { return m_bPending; }
    void SetPending(bool p) { m_bPending = p; }
private:
    bool m_bPending;
};

// Callback de prefetch assíncrono (.?AUIPrefetchCallback@@)
struct IPrefetchCallback {
    virtual ~IPrefetchCallback() {}
    virtual void OnPrefetchComplete(int result) { (void)result; }
};

// Parâmetros de pré-efeito de impacto (.?AUSFxcHitFxPreParams@@)
struct SFxcHitFxPreParams {
    virtual ~SFxcHitFxPreParams() {}
    int fxId;
    float posX, posY, posZ;
};

// Parâmetros de pré-efeito de status (.?AUSFxcStatusFxPreParams@@)
struct SFxcStatusFxPreParams {
    virtual ~SFxcStatusFxPreParams() {}
    int statusId;
    float duration;
};

// Lista de pontos de forma (.?AVShapePointList@@)
class ShapePointList {
public:
    ShapePointList() {}
    virtual ~ShapePointList() {}
    std::vector<float> points;
};
