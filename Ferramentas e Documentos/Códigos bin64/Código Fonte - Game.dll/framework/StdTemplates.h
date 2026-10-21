#pragma once
#include <cstdint>

// ============================================================================
// Templates Canônicos CRT / STL (Microsoft Visual C++ Runtime) do RTTI
// ============================================================================

namespace AionStdTemplates {

// std::_Func_base (.?AV?$_Func_base@...@@)
template<typename Ret, typename... Args>
class _Func_base {
public:
    virtual ~_Func_base() {}
    virtual Ret operator()(Args... args) = 0;
};

// std::_Func_impl_no_alloc (.?AV?$_Func_impl_no_alloc@...@@)
template<typename Callable, typename Ret, typename... Args>
class _Func_impl_no_alloc : public _Func_base<Ret, Args...> {
public:
    virtual ~_Func_impl_no_alloc() {}
    virtual Ret operator()(Args... args) override {
        (void)sizeof...(args);
        return Ret();
    }
};

// std::_Binder (.?AV?$_Binder@...@@)
template<typename Func, typename... BoundArgs>
class _Binder {
public:
    virtual ~_Binder() {}
};

// std::function (.?AV?$function@...@@)
template<typename F>
class function {
public:
    virtual ~function() {}
};

// std::_Ref_count_base (.?AV_Ref_count_base@std@@)
class _Ref_count_base {
public:
    virtual ~_Ref_count_base() {}
};

// std::_Ref_count_obj (.?AV?$_Ref_count_obj@...@@)
template<typename T>
class _Ref_count_obj : public _Ref_count_base {
public:
    virtual ~_Ref_count_obj() {}
};

// std::_Node_base (.?AV_Node_base@std@@)
class _Node_base {
public:
    virtual ~_Node_base() {}
};

// std::_Node_assert (.?AV_Node_assert@std@@)
class _Node_assert : public _Node_base {
public:
    virtual ~_Node_assert() {}
};

// std::_Node_back (.?AV_Node_back@std@@)
class _Node_back : public _Node_base {
public:
    virtual ~_Node_back() {}
};

// std::_Node_capture (.?AV_Node_capture@std@@)
class _Node_capture : public _Node_base {
public:
    virtual ~_Node_capture() {}
};

// std::_Node_class (.?AV_Node_class@std@@)
class _Node_class : public _Node_base {
public:
    virtual ~_Node_class() {}
};

// std::_Node_end_group (.?AV_Node_end_group@std@@)
class _Node_end_group : public _Node_base {
public:
    virtual ~_Node_end_group() {}
};

// std::_Node_end_rep (.?AV_Node_end_rep@std@@)
class _Node_end_rep : public _Node_base {
public:
    virtual ~_Node_end_rep() {}
};

// std::_Node_endif (.?AV_Node_endif@std@@)
class _Node_endif : public _Node_base {
public:
    virtual ~_Node_endif() {}
};

// std::_Node_if (.?AV_Node_if@std@@)
class _Node_if : public _Node_base {
public:
    virtual ~_Node_if() {}
};

// std::_Node_rep (.?AV_Node_rep@std@@)
class _Node_rep : public _Node_base {
public:
    virtual ~_Node_rep() {}
};

// std::_Node_str (.?AV_Node_str@std@@)
class _Node_str : public _Node_base {
public:
    virtual ~_Node_str() {}
};

// std::_Root_node (.?AV_Root_node@std@@)
class _Root_node : public _Node_base {
public:
    virtual ~_Root_node() {}
};

// std::_Crt_new_delete (.?AU_Crt_new_delete@std@@)
struct _Crt_new_delete {
    virtual ~_Crt_new_delete() {}
};

// std::_Facet_base (.?AV_Facet_base@std@@)
class _Facet_base {
public:
    virtual ~_Facet_base() {}
};

// std::facet (.?AVfacet@locale@std@@)
class facet : public _Facet_base {
public:
    virtual ~facet() {}
};

// std::collate (.?AV?$collate@...@@)
template<typename CharT>
class collate : public facet {
public:
    virtual ~collate() {}
};

// std::_Iosb (.?AV?$_Iosb@...@@)
class _Iosb {
public:
    virtual ~_Iosb() {}
};

// std::ios_base (.?AVios_base@std@@)
class ios_base : public _Iosb {
public:
    virtual ~ios_base() {}
};

// std::basic_ios (.?AV?$basic_ios@...@@)
template<typename CharT>
class basic_ios : public ios_base {
public:
    virtual ~basic_ios() {}
};

// std::basic_streambuf (.?AV?$basic_streambuf@...@@)
template<typename CharT>
class basic_streambuf {
public:
    virtual ~basic_streambuf() {}
};

// std::basic_istream (.?AV?$basic_istream@...@@)
template<typename CharT>
class basic_istream : virtual public basic_ios<CharT> {
public:
    virtual ~basic_istream() {}
};

// std::basic_ostream (.?AV?$basic_ostream@...@@)
template<typename CharT>
class basic_ostream : virtual public basic_ios<CharT> {
public:
    virtual ~basic_ostream() {}
};

// std::basic_iostream (.?AV?$basic_iostream@...@@)
template<typename CharT>
class basic_iostream : public basic_istream<CharT>, public basic_ostream<CharT> {
public:
    virtual ~basic_iostream() {}
};

// std::basic_stringbuf (.?AV?$basic_stringbuf@...@@)
template<typename CharT>
class basic_stringbuf : public basic_streambuf<CharT> {
public:
    virtual ~basic_stringbuf() {}
};

// std::basic_stringstream (.?AV?$basic_stringstream@...@@)
template<typename CharT>
class basic_stringstream : public basic_iostream<CharT> {
public:
    virtual ~basic_stringstream() {}
};

// std::basic_ostringstream (.?AV?$basic_ostringstream@...@@)
template<typename CharT>
class basic_ostringstream : public basic_ostream<CharT> {
public:
    virtual ~basic_ostringstream() {}
};

// std::exception (.?AVexception@std@@)
class exception {
public:
    exception() {}
    virtual ~exception() {}
};

// std::bad_cast (.?AVbad_cast@std@@)
class bad_cast : public exception {
public:
    bad_cast() {}
    virtual ~bad_cast() {}
};

// std::runtime_error (.?AVruntime_error@std@@)
class runtime_error : public exception {
public:
    runtime_error() {}
    virtual ~runtime_error() {}
};

// type_info (.?AVtype_info@@)
class type_info {
public:
    type_info() {}
    virtual ~type_info() {}
};

} // namespace AionStdTemplates
