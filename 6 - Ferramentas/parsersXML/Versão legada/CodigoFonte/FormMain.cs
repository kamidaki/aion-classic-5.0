using System;
using System.ComponentModel;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace spawn_parser;

public class FormMain : Form
{
	public delegate void ChangeUI(string data);

	private ChangeUI myUI;
	private Parser _parser;
	private IContainer components = null;

	private TextBox pathMission;
	private Label labelPathMission;
	private Button buttonSelectMission;
	private Button buttonSelectNpcs;
	private Label labelPathClientNpcs;
	private TextBox pathClientNpcs;
	private ListBox listLog;
	private Button buttonStart;
	private Button buttonStop;
	private Label labelWorldId;
	private TextBox worldID;
	private Label labelCategory;
	private ComboBox comboBox1;
	private Button button1;
	private Label label1;
	private TextBox textBox1;
	private Button button2;
	private Button button3;
	private Button button4;

	public FormMain()
	{
		InitializeComponent();
	}

	public void Changed(string data)
	{
		if (IsDisposed || Disposing)
		{
			return;
		}

		if (InvokeRequired)
		{
			try
			{
				BeginInvoke(new Action(() => Changed(data)));
			}
			catch
			{
			}
			return;
		}

		// Prevent listbox from overflowing memory / GDI limits
		if (listLog.Items.Count > 3000)
		{
			listLog.Items.RemoveAt(0);
		}

		listLog.Items.Add(data);
		listLog.TopIndex = listLog.Items.Count - 1;
	}

	private void SetUiRunning(bool running)
	{
		if (IsDisposed || Disposing)
		{
			return;
		}

		if (InvokeRequired)
		{
			try
			{
				BeginInvoke(new Action(() => SetUiRunning(running)));
			}
			catch
			{
			}
			return;
		}

		buttonStart.Enabled = !running;
		buttonStop.Enabled = running;
	}

	private void buttonStart_Click(object sender, EventArgs e)
	{
		SetUiRunning(true);
		myUI = (data) =>
		{
			Changed(data);
			if (data.StartsWith("Finished!") || data.StartsWith("FATAL ERROR:") || data.StartsWith("Parsing stopped") || data.StartsWith("Error:"))
			{
				SetUiRunning(false);
			}
		};

		_parser = new Parser(myUI);
		_parser.Run(worldID.Text, pathMission.Text, pathClientNpcs.Text, textBox1.Text, comboBox1.Text);
	}

	private void buttonStop_Click(object sender, EventArgs e)
	{
		_parser?.Stop();
		SetUiRunning(false);
	}

	private void button2_Click(object sender, EventArgs e)
	{
		Close();
	}

	private void buttonSelectMission_Click(object sender, EventArgs e)
	{
		OpenFileDialog openFileDialog = new OpenFileDialog();
		openFileDialog.Title = "Open mission_mission0.xml file";
		if (openFileDialog.ShowDialog() == DialogResult.OK)
		{
			pathMission.Text = openFileDialog.FileName;
		}
	}

	private void buttonSelectNpcs_Click(object sender, EventArgs e)
	{
		OpenFileDialog openFileDialog = new OpenFileDialog();
		openFileDialog.Title = "Open client_npcs.xml file";
		if (openFileDialog.ShowDialog() == DialogResult.OK)
		{
			pathClientNpcs.Text = openFileDialog.FileName;
		}
	}

	private void button1_Click(object sender, EventArgs e)
	{
		OpenFileDialog openFileDialog = new OpenFileDialog();
		openFileDialog.Title = "Open gather_src.xml file";
		if (openFileDialog.ShowDialog() == DialogResult.OK)
		{
			textBox1.Text = openFileDialog.FileName;
		}
	}

	private void button3_Click(object sender, EventArgs e)
	{
		OpenFileDialog openFileDialog = new OpenFileDialog();
		openFileDialog.Title = "Open WorldId.xml file";
		if (openFileDialog.ShowDialog() == DialogResult.OK)
		{
			worldID.Text = openFileDialog.FileName;
		}
	}

	private void FormMain_Load(object sender, EventArgs e)
	{
		comboBox1.Text = "Npc";
		buttonStop.Enabled = false;

		if (!File.Exists(pathMission.Text))
		{
			if (File.Exists(@"Arquivos_teste\Level\mission_mission0.xml"))
				pathMission.Text = @"Arquivos_teste\Level\mission_mission0.xml";
			else if (File.Exists(@"Arquivos_teste\mission_mission0.xml"))
				pathMission.Text = @"Arquivos_teste\mission_mission0.xml";
		}

		if (!File.Exists(pathClientNpcs.Text))
		{
			if (File.Exists(@"Arquivos_teste\npcs\client_npcs.xml"))
				pathClientNpcs.Text = @"Arquivos_teste\npcs\client_npcs.xml";
			else if (File.Exists(@"Arquivos_teste\client_npcs.xml"))
				pathClientNpcs.Text = @"Arquivos_teste\client_npcs.xml";
		}

		if (!File.Exists(textBox1.Text))
		{
			if (File.Exists(@"Arquivos_teste\Gather\gather_src.xml"))
				textBox1.Text = @"Arquivos_teste\Gather\gather_src.xml";
			else if (File.Exists(@"Arquivos_teste\gather_src.xml"))
				textBox1.Text = @"Arquivos_teste\gather_src.xml";
		}

		if (!File.Exists(worldID.Text))
		{
			if (File.Exists(@"Arquivos_teste\world\WorldId.xml"))
				worldID.Text = @"Arquivos_teste\world\WorldId.xml";
			else if (File.Exists(@"Arquivos_teste\WorldId.xml"))
				worldID.Text = @"Arquivos_teste\WorldId.xml";
		}
	}

	private void button4_Click(object sender, EventArgs e)
	{
		listLog.Items.Clear();
	}

	protected override void Dispose(bool disposing)
	{
		if (disposing && components != null)
		{
			components.Dispose();
		}
		base.Dispose(disposing);
	}

	private void InitializeComponent()
	{
		this.pathMission = new System.Windows.Forms.TextBox();
		this.labelPathMission = new System.Windows.Forms.Label();
		this.buttonSelectMission = new System.Windows.Forms.Button();
		this.buttonSelectNpcs = new System.Windows.Forms.Button();
		this.labelPathClientNpcs = new System.Windows.Forms.Label();
		this.pathClientNpcs = new System.Windows.Forms.TextBox();
		this.listLog = new System.Windows.Forms.ListBox();
		this.buttonStart = new System.Windows.Forms.Button();
		this.buttonStop = new System.Windows.Forms.Button();
		this.labelWorldId = new System.Windows.Forms.Label();
		this.worldID = new System.Windows.Forms.TextBox();
		this.labelCategory = new System.Windows.Forms.Label();
		this.comboBox1 = new System.Windows.Forms.ComboBox();
		this.button1 = new System.Windows.Forms.Button();
		this.label1 = new System.Windows.Forms.Label();
		this.textBox1 = new System.Windows.Forms.TextBox();
		this.button2 = new System.Windows.Forms.Button();
		this.button3 = new System.Windows.Forms.Button();
		this.button4 = new System.Windows.Forms.Button();
		base.SuspendLayout();
		this.pathMission.BackColor = System.Drawing.Color.Gainsboro;
		this.pathMission.Location = new System.Drawing.Point(163, 6);
		this.pathMission.Name = "pathMission";
		this.pathMission.Size = new System.Drawing.Size(359, 20);
		this.pathMission.TabIndex = 0;
		this.pathMission.Text = "mission_mission0.xml";
		this.labelPathMission.AutoSize = true;
		this.labelPathMission.Location = new System.Drawing.Point(12, 9);
		this.labelPathMission.Name = "labelPathMission";
		this.labelPathMission.Size = new System.Drawing.Size(145, 13);
		this.labelPathMission.TabIndex = 1;
		this.labelPathMission.Text = "Path to mission_mission0.xml:";
		this.buttonSelectMission.Location = new System.Drawing.Point(528, 4);
		this.buttonSelectMission.Name = "buttonSelectMission";
		this.buttonSelectMission.Size = new System.Drawing.Size(31, 23);
		this.buttonSelectMission.TabIndex = 2;
		this.buttonSelectMission.Text = "...";
		this.buttonSelectMission.UseVisualStyleBackColor = true;
		this.buttonSelectMission.Click += new System.EventHandler(buttonSelectMission_Click);
		this.buttonSelectNpcs.Location = new System.Drawing.Point(528, 30);
		this.buttonSelectNpcs.Name = "buttonSelectNpcs";
		this.buttonSelectNpcs.Size = new System.Drawing.Size(31, 23);
		this.buttonSelectNpcs.TabIndex = 5;
		this.buttonSelectNpcs.Text = "...";
		this.buttonSelectNpcs.UseVisualStyleBackColor = true;
		this.buttonSelectNpcs.Click += new System.EventHandler(buttonSelectNpcs_Click);
		this.labelPathClientNpcs.AutoSize = true;
		this.labelPathClientNpcs.Location = new System.Drawing.Point(12, 35);
		this.labelPathClientNpcs.Name = "labelPathClientNpcs";
		this.labelPathClientNpcs.Size = new System.Drawing.Size(119, 13);
		this.labelPathClientNpcs.TabIndex = 4;
		this.labelPathClientNpcs.Text = "Path to client_npcs.xml:";
		this.pathClientNpcs.BackColor = System.Drawing.Color.Gainsboro;
		this.pathClientNpcs.Location = new System.Drawing.Point(163, 32);
		this.pathClientNpcs.Name = "pathClientNpcs";
		this.pathClientNpcs.Size = new System.Drawing.Size(359, 20);
		this.pathClientNpcs.TabIndex = 3;
		this.pathClientNpcs.Text = "client_npcs.xml";
		this.listLog.BackColor = System.Drawing.Color.Gainsboro;
		this.listLog.FormattingEnabled = true;
		this.listLog.Location = new System.Drawing.Point(11, 138);
		this.listLog.Name = "listLog";
		this.listLog.Size = new System.Drawing.Size(548, 186);
		this.listLog.TabIndex = 6;
		this.buttonStart.Location = new System.Drawing.Point(214, 330);
		this.buttonStart.Name = "buttonStart";
		this.buttonStart.Size = new System.Drawing.Size(75, 23);
		this.buttonStart.TabIndex = 7;
		this.buttonStart.Text = "Start";
		this.buttonStart.UseVisualStyleBackColor = true;
		this.buttonStart.Click += new System.EventHandler(buttonStart_Click);
		this.buttonStop.Location = new System.Drawing.Point(295, 330);
		this.buttonStop.Name = "buttonStop";
		this.buttonStop.Size = new System.Drawing.Size(75, 23);
		this.buttonStop.TabIndex = 8;
		this.buttonStop.Text = "Stop";
		this.buttonStop.UseVisualStyleBackColor = true;
		this.buttonStop.Click += new System.EventHandler(buttonStop_Click);
		this.labelWorldId.AutoSize = true;
		this.labelWorldId.Location = new System.Drawing.Point(12, 88);
		this.labelWorldId.Name = "labelWorldId";
		this.labelWorldId.Size = new System.Drawing.Size(102, 13);
		this.labelWorldId.TabIndex = 10;
		this.labelWorldId.Text = "Path to WorldId.xml:";
		this.worldID.BackColor = System.Drawing.Color.Gainsboro;
		this.worldID.Location = new System.Drawing.Point(163, 85);
		this.worldID.Name = "worldID";
		this.worldID.Size = new System.Drawing.Size(359, 20);
		this.worldID.TabIndex = 9;
		this.worldID.Text = "WorldId.xml";
		this.labelCategory.AutoSize = true;
		this.labelCategory.Location = new System.Drawing.Point(12, 114);
		this.labelCategory.Name = "labelCategory";
		this.labelCategory.Size = new System.Drawing.Size(52, 13);
		this.labelCategory.TabIndex = 11;
		this.labelCategory.Text = "Category:";
		this.comboBox1.BackColor = System.Drawing.Color.Gainsboro;
		this.comboBox1.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
		this.comboBox1.FormattingEnabled = true;
		this.comboBox1.Items.AddRange(new object[4] { "Npc", "Monster", "Gather", "All" });
		this.comboBox1.Location = new System.Drawing.Point(163, 111);
		this.comboBox1.Name = "comboBox1";
		this.comboBox1.Size = new System.Drawing.Size(396, 21);
		this.comboBox1.TabIndex = 12;
		this.button1.Location = new System.Drawing.Point(528, 56);
		this.button1.Name = "button1";
		this.button1.Size = new System.Drawing.Size(31, 23);
		this.button1.TabIndex = 15;
		this.button1.Text = "...";
		this.button1.UseVisualStyleBackColor = true;
		this.button1.Click += new System.EventHandler(button1_Click);
		this.label1.AutoSize = true;
		this.label1.Location = new System.Drawing.Point(12, 61);
		this.label1.Name = "label1";
		this.label1.Size = new System.Drawing.Size(119, 13);
		this.label1.TabIndex = 14;
		this.label1.Text = "Path to client_npcs.xml:";
		this.textBox1.BackColor = System.Drawing.Color.Gainsboro;
		this.textBox1.Location = new System.Drawing.Point(163, 58);
		this.textBox1.Name = "textBox1";
		this.textBox1.Size = new System.Drawing.Size(359, 20);
		this.textBox1.TabIndex = 13;
		this.textBox1.Text = "gather_src.xml";
		this.button2.Location = new System.Drawing.Point(484, 330);
		this.button2.Name = "button2";
		this.button2.Size = new System.Drawing.Size(75, 23);
		this.button2.TabIndex = 16;
		this.button2.Text = "Close";
		this.button2.UseVisualStyleBackColor = true;
		this.button2.Click += new System.EventHandler(button2_Click);
		this.button3.Location = new System.Drawing.Point(528, 83);
		this.button3.Name = "button3";
		this.button3.Size = new System.Drawing.Size(31, 23);
		this.button3.TabIndex = 17;
		this.button3.Text = "...";
		this.button3.UseVisualStyleBackColor = true;
		this.button3.Click += new System.EventHandler(button3_Click);
		this.button4.Location = new System.Drawing.Point(403, 330);
		this.button4.Name = "button4";
		this.button4.Size = new System.Drawing.Size(75, 23);
		this.button4.TabIndex = 18;
		this.button4.Text = "Clear log";
		this.button4.UseVisualStyleBackColor = true;
		this.button4.Click += new System.EventHandler(button4_Click);
		base.AutoScaleDimensions = new System.Drawing.SizeF(6f, 13f);
		base.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
		base.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
		this.BackColor = System.Drawing.Color.White;
		base.ClientSize = new System.Drawing.Size(571, 361);
		base.Controls.Add(this.button4);
		base.Controls.Add(this.button3);
		base.Controls.Add(this.button2);
		base.Controls.Add(this.button1);
		base.Controls.Add(this.label1);
		base.Controls.Add(this.textBox1);
		base.Controls.Add(this.comboBox1);
		base.Controls.Add(this.labelCategory);
		base.Controls.Add(this.labelWorldId);
		base.Controls.Add(this.worldID);
		base.Controls.Add(this.buttonStop);
		base.Controls.Add(this.buttonStart);
		base.Controls.Add(this.listLog);
		base.Controls.Add(this.buttonSelectNpcs);
		base.Controls.Add(this.labelPathClientNpcs);
		base.Controls.Add(this.pathClientNpcs);
		base.Controls.Add(this.buttonSelectMission);
		base.Controls.Add(this.labelPathMission);
		base.Controls.Add(this.pathMission);
		this.ForeColor = System.Drawing.Color.Black;
		try
		{
			string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app.ico");
			if (File.Exists(iconPath))
			{
				base.Icon = new Icon(iconPath);
			}
			else if (File.Exists("app.ico"))
			{
				base.Icon = new Icon("app.ico");
			}
			else
			{
				base.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
			}
		}
		catch
		{
		}
		base.MaximizeBox = false;
		base.Name = "FormMain";
		base.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
		this.Text = "Spawn Parser [by fieshu]";
		base.Load += new System.EventHandler(FormMain_Load);
		base.ResumeLayout(false);
		base.PerformLayout();
	}
}
