package com.aionemu.commons.utils;

import java.util.Arrays;

public class Base64 {
    private static final char[] CA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".toCharArray();
    private static final int[] IA = new int[256];

    public static char[] encodeToChar(byte[] sArr, boolean lineSep) {
        int sLen;
        int n = sLen = sArr != null ? sArr.length : 0;
        if (sLen == 0) {
            return new char[0];
        }
        int eLen = sLen / 3 * 3;
        int cCnt = (sLen - 1) / 3 + 1 << 2;
        int dLen = cCnt + (lineSep ? (cCnt - 1) / 76 << 1 : 0);
        char[] dArr = new char[dLen];
        int s = 0;
        int d = 0;
        int cc = 0;
        while (s < eLen) {
            int i = (sArr[s++] & 0xFF) << 16 | (sArr[s++] & 0xFF) << 8 | sArr[s++] & 0xFF;
            dArr[d++] = CA[i >>> 18 & 0x3F];
            dArr[d++] = CA[i >>> 12 & 0x3F];
            dArr[d++] = CA[i >>> 6 & 0x3F];
            dArr[d++] = CA[i & 0x3F];
            if (!lineSep || ++cc != 19 || d >= dLen - 2) continue;
            dArr[d++] = 13;
            dArr[d++] = 10;
            cc = 0;
        }
        int left = sLen - eLen;
        if (left > 0) {
            int i = (sArr[eLen] & 0xFF) << 10 | (left == 2 ? (sArr[sLen - 1] & 0xFF) << 2 : 0);
            dArr[dLen - 4] = CA[i >> 12];
            dArr[dLen - 3] = CA[i >>> 6 & 0x3F];
            dArr[dLen - 2] = left == 2 ? CA[i & 0x3F] : 61;
            dArr[dLen - 1] = 61;
        }
        return dArr;
    }

    public static byte[] decode(char[] sArr) {
        int sLen;
        int n = sLen = sArr != null ? sArr.length : 0;
        if (sLen == 0) {
            return new byte[0];
        }
        int sepCnt = 0;
        for (int i = 0; i < sLen; ++i) {
            if (IA[sArr[i]] >= 0) continue;
            ++sepCnt;
        }
        if ((sLen - sepCnt) % 4 != 0) {
            return null;
        }
        int pad = 0;
        int i = sLen;
        while (i > 1 && IA[sArr[--i]] <= 0) {
            if (sArr[i] != '=') continue;
            ++pad;
        }
        int len = ((sLen - sepCnt) * 6 >> 3) - pad;
        byte[] dArr = new byte[len];
        int s = 0;
        int d = 0;
        while (d < len) {
            int i2 = 0;
            for (int j = 0; j < 4; ++j) {
                int c;
                if ((c = IA[sArr[s++]]) >= 0) {
                    i2 |= c << 18 - j * 6;
                    continue;
                }
                --j;
            }
            dArr[d++] = (byte)(i2 >> 16);
            if (d >= len) continue;
            dArr[d++] = (byte)(i2 >> 8);
            if (d >= len) continue;
            dArr[d++] = (byte)i2;
        }
        return dArr;
    }

    public static byte[] decodeFast(char[] sArr) {
        int sIx;
        int sLen = sArr.length;
        if (sLen == 0) {
            return new byte[0];
        }
        int eIx = sLen - 1;
        for (sIx = 0; sIx < eIx && IA[sArr[sIx]] < 0; ++sIx) {
        }
        while (eIx > 0 && IA[sArr[eIx]] < 0) {
            --eIx;
        }
        int pad = sArr[eIx] == '=' ? (sArr[eIx - 1] == '=' ? 2 : 1) : 0;
        int cCnt = eIx - sIx + 1;
        int sepCnt = sLen > 76 ? (sArr[76] == '\r' ? cCnt / 78 : 0) << 1 : 0;
        int len = ((cCnt - sepCnt) * 6 >> 3) - pad;
        byte[] dArr = new byte[len];
        int d = 0;
        int cc = 0;
        int eLen = len / 3 * 3;
        while (d < eLen) {
            int i = IA[sArr[sIx++]] << 18 | IA[sArr[sIx++]] << 12 | IA[sArr[sIx++]] << 6 | IA[sArr[sIx++]];
            dArr[d++] = (byte)(i >> 16);
            dArr[d++] = (byte)(i >> 8);
            dArr[d++] = (byte)i;
            if (sepCnt <= 0 || ++cc != 19) continue;
            sIx += 2;
            cc = 0;
        }
        if (d < len) {
            int i = 0;
            int j = 0;
            while (sIx <= eIx - pad) {
                i |= IA[sArr[sIx++]] << 18 - j * 6;
                ++j;
            }
            int r = 16;
            while (d < len) {
                dArr[d++] = (byte)(i >> r);
                r -= 8;
            }
        }
        return dArr;
    }

    public static byte[] encodeToByte(byte[] sArr, boolean lineSep) {
        int sLen;
        int n = sLen = sArr != null ? sArr.length : 0;
        if (sLen == 0) {
            return new byte[0];
        }
        int eLen = sLen / 3 * 3;
        int cCnt = (sLen - 1) / 3 + 1 << 2;
        int dLen = cCnt + (lineSep ? (cCnt - 1) / 76 << 1 : 0);
        byte[] dArr = new byte[dLen];
        int s = 0;
        int d = 0;
        int cc = 0;
        while (s < eLen) {
            int i = (sArr[s++] & 0xFF) << 16 | (sArr[s++] & 0xFF) << 8 | sArr[s++] & 0xFF;
            dArr[d++] = (byte)CA[i >>> 18 & 0x3F];
            dArr[d++] = (byte)CA[i >>> 12 & 0x3F];
            dArr[d++] = (byte)CA[i >>> 6 & 0x3F];
            dArr[d++] = (byte)CA[i & 0x3F];
            if (!lineSep || ++cc != 19 || d >= dLen - 2) continue;
            dArr[d++] = 13;
            dArr[d++] = 10;
            cc = 0;
        }
        int left = sLen - eLen;
        if (left > 0) {
            int i = (sArr[eLen] & 0xFF) << 10 | (left == 2 ? (sArr[sLen - 1] & 0xFF) << 2 : 0);
            dArr[dLen - 4] = (byte)CA[i >> 12];
            dArr[dLen - 3] = (byte)CA[i >>> 6 & 0x3F];
            dArr[dLen - 2] = (byte) (left == 2 ? CA[i & 0x3F] : 61);
            dArr[dLen - 1] = 61;
        }
        return dArr;
    }

    public static byte[] decode(byte[] sArr) {
        int sLen = sArr.length;
        int sepCnt = 0;
        for (int i = 0; i < sLen; ++i) {
            if (IA[sArr[i] & 0xFF] >= 0) continue;
            ++sepCnt;
        }
        if ((sLen - sepCnt) % 4 != 0) {
            return null;
        }
        int pad = 0;
        int i = sLen;
        while (i > 1 && IA[sArr[--i] & 0xFF] <= 0) {
            if (sArr[i] != 61) continue;
            ++pad;
        }
        int len = ((sLen - sepCnt) * 6 >> 3) - pad;
        byte[] dArr = new byte[len];
        int s = 0;
        int d = 0;
        while (d < len) {
            int i2 = 0;
            for (int j = 0; j < 4; ++j) {
                int c;
                if ((c = IA[sArr[s++] & 0xFF]) >= 0) {
                    i2 |= c << 18 - j * 6;
                    continue;
                }
                --j;
            }
            dArr[d++] = (byte)(i2 >> 16);
            if (d >= len) continue;
            dArr[d++] = (byte)(i2 >> 8);
            if (d >= len) continue;
            dArr[d++] = (byte)i2;
        }
        return dArr;
    }

    public static byte[] decodeFast(byte[] sArr) {
        int sIx;
        int sLen = sArr.length;
        if (sLen == 0) {
            return new byte[0];
        }
        int eIx = sLen - 1;
        for (sIx = 0; sIx < eIx && IA[sArr[sIx] & 0xFF] < 0; ++sIx) {
        }
        while (eIx > 0 && IA[sArr[eIx] & 0xFF] < 0) {
            --eIx;
        }
        int pad = sArr[eIx] == 61 ? (sArr[eIx - 1] == 61 ? 2 : 1) : 0;
        int cCnt = eIx - sIx + 1;
        int sepCnt = sLen > 76 ? (sArr[76] == 13 ? cCnt / 78 : 0) << 1 : 0;
        int len = ((cCnt - sepCnt) * 6 >> 3) - pad;
        byte[] dArr = new byte[len];
        int d = 0;
        int cc = 0;
        int eLen = len / 3 * 3;
        while (d < eLen) {
            int i = IA[sArr[sIx++]] << 18 | IA[sArr[sIx++]] << 12 | IA[sArr[sIx++]] << 6 | IA[sArr[sIx++]];
            dArr[d++] = (byte)(i >> 16);
            dArr[d++] = (byte)(i >> 8);
            dArr[d++] = (byte)i;
            if (sepCnt <= 0 || ++cc != 19) continue;
            sIx += 2;
            cc = 0;
        }
        if (d < len) {
            int i = 0;
            int j = 0;
            while (sIx <= eIx - pad) {
                i |= IA[sArr[sIx++]] << 18 - j * 6;
                ++j;
            }
            int r = 16;
            while (d < len) {
                dArr[d++] = (byte)(i >> r);
                r -= 8;
            }
        }
        return dArr;
    }

    public static String encodeToString(byte[] sArr, boolean lineSep) {
        return new String(Base64.encodeToChar(sArr, lineSep));
    }

    public static byte[] decode(String str) {
        int sLen;
        int n = sLen = str != null ? str.length() : 0;
        if (sLen == 0) {
            return new byte[0];
        }
        int sepCnt = 0;
        for (int i = 0; i < sLen; ++i) {
            if (IA[str.charAt(i)] >= 0) continue;
            ++sepCnt;
        }
        if ((sLen - sepCnt) % 4 != 0) {
            return null;
        }
        int pad = 0;
        int i = sLen;
        while (i > 1 && IA[str.charAt(--i)] <= 0) {
            if (str.charAt(i) != '=') continue;
            ++pad;
        }
        int len = ((sLen - sepCnt) * 6 >> 3) - pad;
        byte[] dArr = new byte[len];
        int s = 0;
        int d = 0;
        while (d < len) {
            int i2 = 0;
            for (int j = 0; j < 4; ++j) {
                int c;
                if ((c = IA[str.charAt(s++)]) >= 0) {
                    i2 |= c << 18 - j * 6;
                    continue;
                }
                --j;
            }
            dArr[d++] = (byte)(i2 >> 16);
            if (d >= len) continue;
            dArr[d++] = (byte)(i2 >> 8);
            if (d >= len) continue;
            dArr[d++] = (byte)i2;
        }
        return dArr;
    }

    public static byte[] decodeFast(String s) {
        int sIx;
        int sLen = s.length();
        if (sLen == 0) {
            return new byte[0];
        }
        int eIx = sLen - 1;
        for (sIx = 0; sIx < eIx && IA[s.charAt(sIx) & 0xFF] < 0; ++sIx) {
        }
        while (eIx > 0 && IA[s.charAt(eIx) & 0xFF] < 0) {
            --eIx;
        }
        int pad = s.charAt(eIx) == '=' ? (s.charAt(eIx - 1) == '=' ? 2 : 1) : 0;
        int cCnt = eIx - sIx + 1;
        int sepCnt = sLen > 76 ? (s.charAt(76) == '\r' ? cCnt / 78 : 0) << 1 : 0;
        int len = ((cCnt - sepCnt) * 6 >> 3) - pad;
        byte[] dArr = new byte[len];
        int d = 0;
        int cc = 0;
        int eLen = len / 3 * 3;
        while (d < eLen) {
            int i = IA[s.charAt(sIx++)] << 18 | IA[s.charAt(sIx++)] << 12 | IA[s.charAt(sIx++)] << 6 | IA[s.charAt(sIx++)];
            dArr[d++] = (byte)(i >> 16);
            dArr[d++] = (byte)(i >> 8);
            dArr[d++] = (byte)i;
            if (sepCnt <= 0 || ++cc != 19) continue;
            sIx += 2;
            cc = 0;
        }
        if (d < len) {
            int i = 0;
            int j = 0;
            while (sIx <= eIx - pad) {
                i |= IA[s.charAt(sIx++)] << 18 - j * 6;
                ++j;
            }
            int r = 16;
            while (d < len) {
                dArr[d++] = (byte)(i >> r);
                r -= 8;
            }
        }
        return dArr;
    }

    static {
        Arrays.fill(IA, -1);
        int iS = CA.length;
        for (int i = 0; i < iS; ++i) {
            Base64.IA[Base64.CA[i]] = i;
        }
        Base64.IA[61] = 0;
    }
}

