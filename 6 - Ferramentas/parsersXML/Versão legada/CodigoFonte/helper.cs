using System;
using System.Globalization;

namespace spawn_parser;

internal static class helper
{
	public static string h_coordinat(string hh)
	{
		if (string.IsNullOrWhiteSpace(hh))
		{
			return "0";
		}

		try
		{
			string[] array = hh.Split(',');
			if (array.Length < 3)
			{
				return "0";
			}

			if (!double.TryParse(array[2], NumberStyles.Float, CultureInfo.InvariantCulture, out double val))
			{
				return "0";
			}

			int num = ((int)Math.Round(val)) / 3;
			if (num < 0)
			{
				num = 120 + num;
			}
			num -= 30;
			if (num < 0)
			{
				num += 120;
			}
			return ((sbyte)num).ToString();
		}
		catch
		{
			return "0";
		}
	}
}
