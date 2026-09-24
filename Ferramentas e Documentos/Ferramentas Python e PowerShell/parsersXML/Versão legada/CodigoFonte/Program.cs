using System;
using System.Windows.Forms;

namespace spawn_parser;

internal static class Program
{
	[STAThread]
	private static void Main()
	{
		Application.EnableVisualStyles();
		Application.SetCompatibleTextRenderingDefault(defaultValue: false);
		Application.Run(new FormMain());
	}
}
