package com.aionemu.commons.network;

import java.util.Arrays;

public class IPRange {
    private final long min;
    private final long max;
    private final byte[] address;

    public IPRange(String min, String max, String address) {
        this.min = IPRange.toLong(IPRange.toByteArray(min));
        this.max = IPRange.toLong(IPRange.toByteArray(max));
        this.address = IPRange.toByteArray(address);
    }

    public IPRange(byte[] min, byte[] max, byte[] address) {
        this.min = IPRange.toLong(min);
        this.max = IPRange.toLong(max);
        this.address = address;
    }

    public boolean isInRange(String address) {
        long addr = IPRange.toLong(IPRange.toByteArray(address));
        return addr >= this.min && addr <= this.max;
    }

    public byte[] getAddress() {
        return this.address;
    }

    public byte[] getMinAsByteArray() {
        return IPRange.toBytes(this.min);
    }

    public byte[] getMaxAsByteArray() {
        return IPRange.toBytes(this.max);
    }

    private static long toLong(byte[] bytes) {
        long result = 0L;
        result += (long)(bytes[3] & 0xFF);
        result += (long)((bytes[2] & 0xFF) << 8);
        result += (long)((bytes[1] & 0xFF) << 16);
        return (result += (long)(bytes[0] << 24)) & 0xFFFFFFFFL;
    }

    private static byte[] toBytes(long val) {
        byte[] result = new byte[4];
        result[3] = (byte)(val & 0xFFL);
        result[2] = (byte)(val >> 8 & 0xFFL);
        result[1] = (byte)(val >> 16 & 0xFFL);
        result[0] = (byte)(val >> 24 & 0xFFL);
        return result;
    }

    public static byte[] toByteArray(String address) {
        byte[] result = new byte[4];
        String[] strings = address.split("\\.");
        int n = strings.length;
        for (int i = 0; i < n; ++i) {
            result[i] = (byte)Integer.parseInt(strings[i]);
        }
        return result;
    }

    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof IPRange)) {
            return false;
        }
        IPRange ipRange = (IPRange)o;
        return this.max == ipRange.max && this.min == ipRange.min && Arrays.equals(this.address, ipRange.address);
    }

    public int hashCode() {
        int result = (int)(this.min ^ this.min >>> 32);
        result = 31 * result + (int)(this.max ^ this.max >>> 32);
        result = 31 * result + Arrays.hashCode(this.address);
        return result;
    }
}

