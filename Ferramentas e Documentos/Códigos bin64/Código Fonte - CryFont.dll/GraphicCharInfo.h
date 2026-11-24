#ifndef GRAPHIC_CHAR_INFO_H
#define GRAPHIC_CHAR_INFO_H

#pragma once
#include <string.h>

class GraphicCharInfo {
public:
    int m_nCharCount;
    int m_nFlags;
    unsigned char m_data[0x1630 - 16];

    GraphicCharInfo() {
        m_nCharCount = 0;
        m_nFlags = 0;
        memset(m_data, 0, sizeof(m_data));
    }

    virtual ~GraphicCharInfo() {}
    virtual void Render(void* pRenderer = nullptr, void* pFont = nullptr) {
        (void)pRenderer;
        (void)pFont;
    }
};

class GraphicCharInfo_billboard : public GraphicCharInfo {
public:
    GraphicCharInfo_billboard() : GraphicCharInfo() {}
    virtual ~GraphicCharInfo_billboard() override {}
    virtual void Render(void* pRenderer = nullptr, void* pFont = nullptr) override {
        (void)pRenderer;
        (void)pFont;
    }
};

#endif // GRAPHIC_CHAR_INFO_H
