using System.IO;
using System.Text;

namespace spawn_parser;

internal static class save
{
	public static void SaveResult(string filename, string result)
	{
		using StreamWriter streamWriter = new StreamWriter(filename + ".xml", append: true, Encoding.UTF8);
		streamWriter.WriteLine(result);
	}

	public static void SaveFile(string filename, string content)
	{
		File.WriteAllText(filename + ".xml", content, Encoding.UTF8);
	}
}
