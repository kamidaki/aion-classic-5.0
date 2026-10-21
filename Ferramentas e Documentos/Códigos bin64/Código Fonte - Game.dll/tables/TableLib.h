#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <memory>
#include <functional>

// Motor Canônico de Tabelas e Templates do CryEngine / Aion Classic 5.0 (TableLib & BasicTable)

namespace TableLib {

    // .?AV?$Array@...@@
    template<typename T>
    class Array {
    public:
        Array() : m_pData(nullptr), m_size(0), m_capacity(0) {}
        Array(size_t initialCapacity) : m_size(0), m_capacity(initialCapacity) {
            m_pData = initialCapacity > 0 ? new T[initialCapacity] : nullptr;
        }
        virtual ~Array() {
            delete[] m_pData;
            m_pData = nullptr;
            m_size = 0;
            m_capacity = 0;
        }

        void PushBack(const T& item) {
            if (m_size >= m_capacity) {
                Reserve(m_capacity == 0 ? 8 : m_capacity * 2);
            }
            m_pData[m_size++] = item;
        }

        void Reserve(size_t newCap) {
            if (newCap <= m_capacity) return;
            T* pNew = new T[newCap];
            for (size_t i = 0; i < m_size; ++i) {
                pNew[i] = m_pData[i];
            }
            delete[] m_pData;
            m_pData = pNew;
            m_capacity = newCap;
        }

        size_t Size() const { return m_size; }
        size_t Capacity() const { return m_capacity; }
        bool Empty() const { return m_size == 0; }
        void Clear() { m_size = 0; }

        T& operator[](size_t index) { return m_pData[index]; }
        const T& operator[](size_t index) const { return m_pData[index]; }

        T* Data() { return m_pData; }
        const T* Data() const { return m_pData; }

    private:
        T* m_pData;
        size_t m_size;
        size_t m_capacity;
    };

    // .?AU?$Node@...@@
    template<typename K, typename V>
    struct Node {
        K key;
        V value;

        Node() : key(), value() {}
        Node(const K& k, const V& v) : key(k), value(v) {}
    };

    // .?AV?$TableCHeapCache@...@@ e .?AVCacheNode@?$TableCHeapCache@...@@
    template<typename KeyT, typename ValueT>
    class TableCHeapCache {
    public:
        class CacheNode {
        public:
            CacheNode() : key(), pValue(nullptr), lru(0) {}
            virtual ~CacheNode() {}

            KeyT key;
            ValueT* pValue;
            uint64_t lru;
        };

        TableCHeapCache() {}
        virtual ~TableCHeapCache() { Clear(); }

        void Clear() { m_cache.clear(); }
        size_t Size() const { return m_cache.size(); }

    private:
        std::unordered_map<KeyT, CacheNode> m_cache;
    };


} // namespace TableLib

// .?AV?$TableVector@...@@
template<typename T>
class TableVector {
public:
    TableVector() {}
    virtual ~TableVector() {}

    void Add(const T& val) { m_items.push_back(val); }
    size_t Size() const { return m_items.size(); }
    const T& Get(size_t i) const { return m_items[i]; }
    T& operator[](size_t i) { return m_items[i]; }
    const T& operator[](size_t i) const { return m_items[i]; }

private:
    std::vector<T> m_items;
};

// .?AV?$TableStringBase@...@@
template<typename CharT, typename Trait = std::char_traits<CharT>>
class TableStringBase {
public:
    TableStringBase() {}
    TableStringBase(const CharT* str) : m_str(str ? str : "") {}
    virtual ~TableStringBase() {}

    const std::basic_string<CharT, Trait>& Get() const { return m_str; }
    const CharT* CStr() const { return m_str.c_str(); }
    bool Empty() const { return m_str.empty(); }

    bool operator==(const TableStringBase& o) const { return m_str == o.m_str; }
    bool operator<(const TableStringBase& o) const { return m_str < o.m_str; }

private:
    std::basic_string<CharT, Trait> m_str;
};

// .?AV?$_TableIndexAlloc@...@@
template<typename KeyT, typename ValueT, typename LessT = std::less<KeyT>>
class _TableIndexAlloc {
public:
    _TableIndexAlloc() {}
    virtual ~_TableIndexAlloc() {}
};

// .?AV?$TableIndex@...@@
template<typename KeyT, typename ValueT, typename LessT = std::less<KeyT>, typename CompT = std::equal_to<KeyT>>
class TableIndex : public _TableIndexAlloc<KeyT, ValueT, LessT> {
public:
    TableIndex() {}
    virtual ~TableIndex() {}

    void Insert(const KeyT& key, const ValueT& val) {
        m_index[key] = val;
    }

    const ValueT* Find(const KeyT& key) const {
        auto it = m_index.find(key);
        return it != m_index.end() ? &it->second : nullptr;
    }

    size_t Size() const { return m_index.size(); }
    void Clear() { m_index.clear(); }

private:
    std::map<KeyT, ValueT, LessT> m_index;
};

// .?AV?$TableMultiIndex@...@@
template<typename KeyT, typename ValueT, typename LessT = std::less<KeyT>, typename CompT = std::equal_to<KeyT>>
class TableMultiIndex : public _TableIndexAlloc<KeyT, ValueT, LessT> {
public:
    TableMultiIndex() {}
    virtual ~TableMultiIndex() {}

    void Insert(const KeyT& key, const ValueT& val) {
        m_multimap.insert(std::make_pair(key, val));
    }

    std::vector<ValueT> FindAll(const KeyT& key) const {
        std::vector<ValueT> res;
        auto range = m_multimap.equal_range(key);
        for (auto it = range.first; it != range.second; ++it) {
            res.push_back(it->second);
        }
        return res;
    }

    size_t Size() const { return m_multimap.size(); }
    void Clear() { m_multimap.clear(); }

private:
    std::multimap<KeyT, ValueT, LessT> m_multimap;
};

// .?AVITableContainer@@
class ITableContainer {
public:
    ITableContainer() {}
    virtual ~ITableContainer() {}
    virtual bool LoadFromBuffer(const uint8_t* pData, size_t size) = 0;
    virtual void Unload() = 0;
    virtual size_t GetRecordCount() const = 0;
    virtual const char* GetContainerName() const = 0;
};

// .?AV?$BasicInIDAttribute@...@@
template<typename DataT>
class BasicInIDAttribute {
public:
    BasicInIDAttribute() : m_id(0) {}
    virtual ~BasicInIDAttribute() {}

    uint32_t GetId() const { return m_id; }
    void SetId(uint32_t id) { m_id = id; }

protected:
    uint32_t m_id;
};

// .?AV?$BasicTable@...@@
template<typename DataT, typename KeyT = uint32_t, typename LessT = std::less<KeyT>>
class BasicTable : public ITableContainer {
public:
    BasicTable() : m_bLoaded(false) {}
    virtual ~BasicTable() { Unload(); }

    virtual bool LoadFromBuffer(const uint8_t* pData, size_t size) override {
        if (!pData || size == 0) return false;
        m_bLoaded = true;
        return true;
    }

    virtual void Unload() override {
        m_records.clear();
        m_bLoaded = false;
    }

    virtual size_t GetRecordCount() const override {
        return m_records.size();
    }

    virtual const char* GetContainerName() const override {
        return "BasicTable";
    }

    void InsertRecord(const KeyT& key, const DataT& data) {
        m_records[key] = data;
    }

    const DataT* GetRecord(const KeyT& key) const {
        auto it = m_records.find(key);
        return it != m_records.end() ? &it->second : nullptr;
    }

    bool HasRecord(const KeyT& key) const {
        return m_records.find(key) != m_records.end();
    }

    bool IsLoaded() const { return m_bLoaded; }

protected:
    bool m_bLoaded;
    std::unordered_map<KeyT, DataT> m_records;
};

// .?AV?$CompressedTable@...@@
template<typename DataT, typename KeyT = uint32_t>
class CompressedTable : public BasicTable<DataT, KeyT> {
public:
    CompressedTable() : m_uncompressedSize(0) {}
    virtual ~CompressedTable() {}

    virtual bool LoadCompressed(const uint8_t* pCompressedData, size_t compSize, size_t origSize) {
        if (!pCompressedData || compSize == 0) return false;
        m_uncompressedSize = origSize;
        this->m_bLoaded = true;
        return true;
    }

    size_t GetUncompressedSize() const { return m_uncompressedSize; }

private:
    size_t m_uncompressedSize;
};

// .?AV?$PriorityQueueNode@...@@
template<typename T>
class PriorityQueueNode {
public:
    PriorityQueueNode() : priority(0), value() {}
    PriorityQueueNode(int p, const T& v) : priority(p), value(v) {}
    virtual ~PriorityQueueNode() {}

    int priority;
    T value;

    bool operator<(const PriorityQueueNode& o) const {
        return priority < o.priority;
    }
};

// .?AV?$TLinkedListMember@...@@
template<typename T>
class TLinkedListMember {
public:
    TLinkedListMember() : m_pNext(nullptr), m_pPrev(nullptr) {}
    virtual ~TLinkedListMember() {}

    T* m_pNext;
    T* m_pPrev;
};

// .?AV?$TLinkedList@...@@
template<typename T>
class TLinkedList {
public:
    TLinkedList() : m_pHead(nullptr), m_pTail(nullptr), m_count(0) {}
    virtual ~TLinkedList() { Clear(); }

    void PushBack(T* item) {
        if (!item) return;
        item->m_pNext = nullptr;
        item->m_pPrev = m_pTail;
        if (m_pTail) m_pTail->m_pNext = item;
        else m_pHead = item;
        m_pTail = item;
        m_count++;
    }

    void Clear() {
        m_pHead = nullptr;
        m_pTail = nullptr;
        m_count = 0;
    }

    size_t Size() const { return m_count; }
    bool Empty() const { return m_count == 0; }

private:
    T* m_pHead;
    T* m_pTail;
    size_t m_count;
};

// .?AVRBTreeNode@@
class RBTreeNode {
public:
    RBTreeNode() : m_pLeft(nullptr), m_pRight(nullptr), m_pParent(nullptr), m_color(0), m_key(0) {}
    virtual ~RBTreeNode() {}

    RBTreeNode* m_pLeft;
    RBTreeNode* m_pRight;
    RBTreeNode* m_pParent;
    uint8_t m_color; // 0 = Black, 1 = Red
    uint32_t m_key;
};
