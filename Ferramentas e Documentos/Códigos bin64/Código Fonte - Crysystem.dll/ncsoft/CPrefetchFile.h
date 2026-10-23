#pragma once

#ifndef _CPREFETCHFILE_H_
#define _CPREFETCHFILE_H_

#include <string>
#include <vector>

class CPrefetchFile
{
public:
    CPrefetchFile();
    virtual ~CPrefetchFile();

    // 14 virtual slots matching binary VTable at 0x1801e4c00
    virtual bool Open(const char* filePath);
    virtual void Close();
    virtual size_t Read(void* pBuffer, size_t size);
    virtual bool Seek(size_t offset);
    virtual size_t GetSize() const;
    virtual bool PreloadAll();
    virtual bool IsPreloaded() const;
    virtual void Slot7();
    virtual void Slot8();
    virtual void Slot9();
    virtual void Slot10();
    virtual void Slot11();
    virtual void Slot12();

private:
    std::string m_path;
    size_t      m_size;
    size_t      m_cursor;
    bool        m_bPreloaded;
    std::vector<unsigned char> m_buffer;
};

#endif // _CPREFETCHFILE_H_
