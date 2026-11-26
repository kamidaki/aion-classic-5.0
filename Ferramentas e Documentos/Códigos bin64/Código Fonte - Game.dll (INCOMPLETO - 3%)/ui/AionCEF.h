#pragma once
#include <cstdint>
#include <string>

// ============================================================================
// Estruturas Canônicas CEF (Chromium Embedded Framework) extraídas do RTTI
// ============================================================================

// .?AU_cef_browser_settings_t@@
struct _cef_browser_settings_t {
    virtual ~_cef_browser_settings_t() {}
    size_t size;
    int windowless_frame_rate;
};

// .?AU_cef_cookie_t@@
struct _cef_cookie_t {
    virtual ~_cef_cookie_t() {}
    size_t size;
};

// .?AU_cef_key_event_t@@
struct _cef_key_event_t {
    virtual ~_cef_key_event_t() {}
    size_t size;
    int type;
    uint32_t modifiers;
    int windows_key_code;
};

// .?AU_cef_main_args_t@@
struct _cef_main_args_t {
    virtual ~_cef_main_args_t() {}
    void* instance;
};

// .?AU_cef_mouse_event_t@@
struct _cef_mouse_event_t {
    virtual ~_cef_mouse_event_t() {}
    int x;
    int y;
    uint32_t modifiers;
};

// .?AU_cef_point_t@@
struct _cef_point_t {
    virtual ~_cef_point_t() {}
    int x;
    int y;
};

// .?AU_cef_range_t@@
struct _cef_range_t {
    virtual ~_cef_range_t() {}
    int from;
    int to;
};

// .?AU_cef_rect_t@@
struct _cef_rect_t {
    virtual ~_cef_rect_t() {}
    int x;
    int y;
    int width;
    int height;
};

// .?AU_cef_settings_t@@
struct _cef_settings_t {
    virtual ~_cef_settings_t() {}
    size_t size;
    int single_process;
    int no_sandbox;
};

// .?AU_cef_urlparts_t@@
struct _cef_urlparts_t {
    virtual ~_cef_urlparts_t() {}
    size_t size;
};

// .?AU_cef_window_info_t@@
struct _cef_window_info_t {
    virtual ~_cef_window_info_t() {}
    void* parent_window;
    int windowless_rendering_enabled;
};

// Template base canônica para invólucro de structs CEF (.?AV?$CefStructBase@...@@)
template<typename Traits>
class CefStructBase : public Traits {
public:
    CefStructBase() {}
    virtual ~CefStructBase() {}
};

// Template base canônica para strings CEF (.?AV?$CefStringBase@...@@)
template<typename Traits>
class CefStringBase {
public:
    CefStringBase() {}
    virtual ~CefStringBase() {}
    std::wstring str;
};

// Manipulador canônico de esquema de URI customizado Aion CEF (.?AVAionCEFSchemeHandler@@)
class AionCEFSchemeHandler {
public:
    AionCEFSchemeHandler() {}
    virtual ~AionCEFSchemeHandler() {}
    virtual bool ProcessRequest(const char* url) { (void)url; return true; }
};

// Fábrica canônica do manipulador de esquema Aion CEF (.?AVAionCEFSchemeHandlerFactory@@)
class AionCEFSchemeHandlerFactory {
public:
    AionCEFSchemeHandlerFactory() {}
    virtual ~AionCEFSchemeHandlerFactory() {}
    virtual AionCEFSchemeHandler* Create() { return new AionCEFSchemeHandler(); }
};
