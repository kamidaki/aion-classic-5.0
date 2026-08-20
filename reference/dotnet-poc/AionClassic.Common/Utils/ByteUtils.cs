using System.Text;

namespace AionClassic.Common.Utils;

public static class ByteUtils
{
    public static string ToHexString(ReadOnlySpan<byte> data, string separator = " ")
    {
        if (data.IsEmpty) return string.Empty;
        var sb = new StringBuilder(data.Length * (2 + separator.Length));
        for (int i = 0; i < data.Length; i++)
        {
            if (i > 0 && !string.IsNullOrEmpty(separator))
                sb.Append(separator);
            sb.Append(data[i].ToString("X2"));
        }
        return sb.ToString();
    }

    public static byte[] FromHexString(string hex)
    {
        hex = hex.Replace(" ", "").Replace("-", "").Replace(":", "");
        if (hex.Length % 2 != 0)
            throw new ArgumentException("Hex string must have an even length");

        byte[] bytes = new byte[hex.Length / 2];
        for (int i = 0; i < bytes.Length; i++)
        {
            bytes[i] = Convert.ToByte(hex.Substring(i * 2, 2), 16);
        }
        return bytes;
    }
}
