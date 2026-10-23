#include "CPrefetchFile.h"
#include <cstdio>
#include <cstring>

CPrefetchFile::CPrefetchFile()
    : m_size(0),
      m_cursor(0),
      m_bPreloaded(false)
{
}

CPrefetchFile::~CPrefetchFile()
{
    Close();
}

bool CPrefetchFile::Open(const char* filePath)
{
    if (!filePath || !filePath[0]) return false;

    Close();
    m_path = filePath;

    FILE* fp = nullptr;
    fopen_s(&fp, filePath, "rb");
    if (!fp) return false;

    fseek(fp, 0, SEEK_END);
    m_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    fclose(fp);

    return true;
}

void CPrefetchFile::Close()
{
    m_buffer.clear();
    m_size = 0;
    m_cursor = 0;
    m_bPreloaded = false;
    m_path.clear();
}

size_t CPrefetchFile::Read(void* pBuffer, size_t size)
{
    if (!pBuffer || size == 0 || m_cursor >= m_size)
        return 0;

    if (!m_bPreloaded)
    {
        PreloadAll();
    }

    size_t toRead = size;
    if (m_cursor + toRead > m_size)
    {
        toRead = m_size - m_cursor;
    }

    if (toRead > 0 && !m_buffer.empty())
    {
        memcpy(pBuffer, &m_buffer[m_cursor], toRead);
        m_cursor += toRead;
        return toRead;
    }

    return 0;
}

bool CPrefetchFile::Seek(size_t offset)
{
    if (offset <= m_size)
    {
        m_cursor = offset;
        return true;
    }
    return false;
}

size_t CPrefetchFile::GetSize() const
{
    return m_size;
}

bool CPrefetchFile::PreloadAll()
{
    if (m_bPreloaded) return true;
    if (m_path.empty() || m_size == 0) return false;

    FILE* fp = nullptr;
    fopen_s(&fp, m_path.c_str(), "rb");
    if (!fp) return false;

    m_buffer.resize(m_size);
    size_t readBytes = fread(m_buffer.data(), 1, m_size, fp);
    fclose(fp);

    if (readBytes == m_size)
    {
        m_bPreloaded = true;
        return true;
    }

    return false;
}

bool CPrefetchFile::IsPreloaded() const
{
    return m_bPreloaded;
}

void CPrefetchFile::Slot7() {}
void CPrefetchFile::Slot8() {}
void CPrefetchFile::Slot9() {}
void CPrefetchFile::Slot10() {}
void CPrefetchFile::Slot11() {}
void CPrefetchFile::Slot12() {}
