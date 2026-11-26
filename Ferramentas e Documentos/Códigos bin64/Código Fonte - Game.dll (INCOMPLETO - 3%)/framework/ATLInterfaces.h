#pragma once
#include <windows.h>

// ============================================================================
// Interfaces Canônicas COM / Active Accessibility / ATL do RTTI
// ============================================================================

namespace AionATL {

// Interface canônica IUnknown (.?AUIUnknown@@)
struct IUnknown {
    virtual ~IUnknown() {}
    virtual long QueryInterface(const void* riid, void** ppvObject) { (void)riid; (void)ppvObject; return 0; }
    virtual unsigned long AddRef() { return 1; }
    virtual unsigned long Release() { return 0; }
};

// Interface canônica IDispatch (.?AUIDispatch@@)
struct IDispatch : public IUnknown {
    virtual ~IDispatch() {}
};

// Interface canônica IOleWindow (.?AUIOleWindow@@)
struct IOleWindow : public IUnknown {
    virtual ~IOleWindow() {}
};

// Interface canônica IOleClientSite (.?AUIOleClientSite@@)
struct IOleClientSite : public IUnknown {
    virtual ~IOleClientSite() {}
};

// Interface canônica IOleContainer (.?AUIOleContainer@@)
struct IOleContainer : public IUnknown {
    virtual ~IOleContainer() {}
};

// Interface canônica IOleControlSite (.?AUIOleControlSite@@)
struct IOleControlSite : public IUnknown {
    virtual ~IOleControlSite() {}
};

// Interface canônica IOleInPlaceFrame (.?AUIOleInPlaceFrame@@)
struct IOleInPlaceFrame : public IOleWindow {
    virtual ~IOleInPlaceFrame() {}
};

// Interface canônica IOleInPlaceSite (.?AUIOleInPlaceSite@@)
struct IOleInPlaceSite : public IOleWindow {
    virtual ~IOleInPlaceSite() {}
};

// Interface canônica IOleInPlaceSiteEx (.?AUIOleInPlaceSiteEx@@)
struct IOleInPlaceSiteEx : public IOleInPlaceSite {
    virtual ~IOleInPlaceSiteEx() {}
};

// Interface canônica IOleInPlaceSiteWindowless (.?AUIOleInPlaceSiteWindowless@@)
struct IOleInPlaceSiteWindowless : public IOleInPlaceSiteEx {
    virtual ~IOleInPlaceSiteWindowless() {}
};

// Interface canônica IOleInPlaceUIWindow (.?AUIOleInPlaceUIWindow@@)
struct IOleInPlaceUIWindow : public IOleWindow {
    virtual ~IOleInPlaceUIWindow() {}
};

// Interface canônica IAdviseSink (.?AUIAdviseSink@@)
struct IAdviseSink : public IUnknown {
    virtual ~IAdviseSink() {}
};

// Interface canônica IServiceProvider (.?AUIServiceProvider@@)
struct IServiceProvider : public IUnknown {
    virtual ~IServiceProvider() {}
};

// Interface canônica IParseDisplayName (.?AUIParseDisplayName@@)
struct IParseDisplayName : public IUnknown {
    virtual ~IParseDisplayName() {}
};

// Interface canônica IEnumUnknown (.?AUIEnumUnknown@@)
struct IEnumUnknown : public IUnknown {
    virtual ~IEnumUnknown() {}
};

// Interface canônica IObjectWithSite (.?AUIObjectWithSite@@)
struct IObjectWithSite : public IUnknown {
    virtual ~IObjectWithSite() {}
};

// Interface canônica IDocHostUIHandler (.?AUIDocHostUIHandler@@)
struct IDocHostUIHandler : public IUnknown {
    virtual ~IDocHostUIHandler() {}
};

// Interface canônica ITfInputProcessorProfileActivationSink (.?AUITfInputProcessorProfileActivationSink@@)
struct ITfInputProcessorProfileActivationSink : public IUnknown {
    virtual ~ITfInputProcessorProfileActivationSink() {}
};

// Interface canônica ITfUIElementSink (.?AUITfUIElementSink@@)
struct ITfUIElementSink : public IUnknown {
    virtual ~ITfUIElementSink() {}
};

// Interface canônica IAxWinAmbientDispatch (.?AUIAxWinAmbientDispatch@@)
struct IAxWinAmbientDispatch : public IDispatch {
    virtual ~IAxWinAmbientDispatch() {}
};

// Interface canônica IAxWinAmbientDispatchEx (.?AUIAxWinAmbientDispatchEx@@)
struct IAxWinAmbientDispatchEx : public IAxWinAmbientDispatch {
    virtual ~IAxWinAmbientDispatchEx() {}
};

// Interface canônica IAxWinHostWindow (.?AUIAxWinHostWindow@@)
struct IAxWinHostWindow : public IUnknown {
    virtual ~IAxWinHostWindow() {}
};

// Interface canônica IAxWinHostWindowLic (.?AUIAxWinHostWindowLic@@)
struct IAxWinHostWindowLic : public IAxWinHostWindow {
    virtual ~IAxWinHostWindowLic() {}
};

// Templates Canônicos ATL (Active Template Library) extraídos do RTTI

// .?AV?$CComObjectRootEx@...@@
template<typename ThreadModel>
class CComObjectRootEx {
public:
    CComObjectRootEx() {}
    virtual ~CComObjectRootEx() {}
};

// .?AV?$CComObject@...@@
template<typename Base>
class CComObject : public Base {
public:
    CComObject() {}
    virtual ~CComObject() {}
};

// .?AV?$CComCoClass@...@@
template<typename T, const void* pclsid = nullptr>
class CComCoClass {
public:
    CComCoClass() {}
    virtual ~CComCoClass() {}
};

// .?AV?$CComContainedObject@...@@
template<typename Base>
class CComContainedObject : public Base {
public:
    CComContainedObject() {}
    virtual ~CComContainedObject() {}
};

// .?AV?$CComEnum@...@@
template<typename ItemType>
class CComEnum {
public:
    CComEnum() {}
    virtual ~CComEnum() {}
};

// .?AV?$CComEnumImpl@...@@
template<typename ItemType>
class CComEnumImpl {
public:
    CComEnumImpl() {}
    virtual ~CComEnumImpl() {}
};

// .?AV?$CComPolyObject@...@@
template<typename Base>
class CComPolyObject : public Base {
public:
    CComPolyObject() {}
    virtual ~CComPolyObject() {}
};

// .?AV?$CWindowImplRoot@...@@
template<typename TBase>
class CWindowImplRoot {
public:
    CWindowImplRoot() {}
    virtual ~CWindowImplRoot() {}
};

// .?AV?$CWindowImplBaseT@...@@
template<typename TBase>
class CWindowImplBaseT : public CWindowImplRoot<TBase> {
public:
    CWindowImplBaseT() {}
    virtual ~CWindowImplBaseT() {}
};

// .?AV?$CWindowImpl@...@@
template<typename T, typename TBase = int>
class CWindowImpl : public CWindowImplBaseT<TBase> {
public:
    CWindowImpl() {}
    virtual ~CWindowImpl() {}
};

// .?AV?$IDispatchImpl@...@@
template<typename T>
class IDispatchImpl : public T {
public:
    IDispatchImpl() {}
    virtual ~IDispatchImpl() {}
};

// .?AV?$IObjectWithSiteImpl@...@@
template<typename T>
class IObjectWithSiteImpl : public T {
public:
    IObjectWithSiteImpl() {}
    virtual ~IObjectWithSiteImpl() {}
};

} // namespace AionATL
