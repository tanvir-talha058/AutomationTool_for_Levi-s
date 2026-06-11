# 🤖 Web Automation Tool for Levi's

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.0+-43B02A?logo=selenium&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3+-black?logo=flask&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-purple)
![Version](https://img.shields.io/badge/Version-3.1-orange)
![License](https://img.shields.io/badge/License-MIT-green)

A modern, web-based automation tool for bulk data entry into websites using Selenium. Features a sleek dark/light themed UI with real-time progress tracking, multi-browser support, and intuitive click-to-select element identification.

---

## 🆕 What's New in v3.1

- 🚀 **Auto-opens browser** - App automatically launches in your default browser
- 📚 **Quick Start Guide** - Interactive tutorial for first-time users
- ⚡ **Speed Presets** - One-click Fast/Normal/Careful mode switching
- 📋 **Recent URLs** - Autocomplete with your last 10 URLs
- ⏱️ **Time Estimates** - See how long automation will take before starting
- ✅ **Confirmation Modal** - Review settings before starting
- 📊 **Success Rate** - Real-time success percentage tracking
- 🔴 **Failed Rows Panel** - View, copy, or export failed entries
- 🎉 **Completion UI** - Beautiful completion screen with quick actions
- 🌙 **Dark/Light Theme** - Follows system preference with manual toggle

---

## 📸 Preview

<div align="center">

```
╔══════════════════════════════════════════════════════════════╗
║  🤖 Web Automation Tool                              v2.0   ║
╠═════════════════════════════╦════════════════════════════════╣
║  ⚙️ Configuration            ║  📊 Progress                   ║
║  ───────────────────────    ║  ────────────────────────────  ║
║  URL: https://example.com   ║  42 / 100              42%     ║
║  Browser: [Chrome ▼]        ║  ██████████░░░░░░░░░░░░░░      ║
║  Delay:   [2.0] seconds     ║                                ║
║                             ║  ✓ 40   ✗ 2   ⏱ 01:45   🚀 24 ║
╠═════════════════════════════╬════════════════════════════════╣
║  📁 Excel File              ║  📝 Activity Log               ║
║  ───────────────────────    ║  ────────────────────────────  ║
║  ┌─────────────────────┐    ║  10:30:15 ✓ Row 42 submitted   ║
║  │   📤 Drop file here │    ║  10:30:12 ✓ Row 41 submitted   ║
║  │   or click to upload│    ║  10:30:09 ✓ Row 40 submitted   ║
║  └─────────────────────┘    ║  10:30:06 ✓ Row 39 submitted   ║
║                             ║  10:30:03 ✗ Row 38 failed      ║
║  🎮 Controls                ║  10:30:00 ✓ Row 37 submitted   ║
║  [▶ Start] [⏸ Pause] [⏹]   ║                                ║
╚═════════════════════════════╩════════════════════════════════╝
```

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Modern Web UI** | Clean, responsive dark/light themed interface built with HTML/CSS/JS |
| ⚡ **Real-time Updates** | Live progress tracking via WebSocket - no page refresh needed |
| 🖱️ **Click-to-Select** | Simply click on webpage elements to identify input fields and buttons |
| 🔄 **Pause/Resume** | Full control over automation - pause anytime and resume where you left off |
| 📈 **Live Statistics** | Track success/failure rates, speed (entries/min), ETA, and elapsed time |
| 🌐 **Multi-Browser** | Supports Chrome, Firefox, and Edge browsers |
| 📝 **Activity Log** | Color-coded real-time logging with search and filter |
| 📊 **Excel Support** | Import .xlsx and .xls files with column selection and preview |
| 🎯 **Row Range** | Process specific row ranges from your data |
| ⚡ **Speed Presets** | Quick switch between Fast, Normal, and Careful modes |
| 📋 **Recent URLs** | Auto-complete with history of your last 10 URLs |
| ⏱️ **Time Estimates** | See estimated completion time before starting |
| 🔴 **Failed Rows** | View, copy, or export failed entries as CSV |
| ⌨️ **Keyboard Shortcuts** | Space (pause), Escape (stop), T (theme), and more |
| 🔊 **Sound Notifications** | Audio alerts on completion or error (toggleable) |

---

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Chrome, Firefox, or Edge browser installed
- Git (for cloning)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/tanvir-talha058/AutomationTool_for_Levi-s.git

# 2. Navigate to the project
cd AutomationTool_for_Levi-s

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python automation.py
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | Web server framework |
| `flask-socketio` | Real-time WebSocket communication |
| `selenium` | Browser automation |
| `pandas` | Excel file processing |
| `openpyxl` | Excel file reading |
| `eventlet` | Async WebSocket support |

---

## 🚀 Usage

### 1️⃣ Start the Server
```bash
python automation.py
```
The server will start and automatically open your browser:
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🤖  WEB AUTOMATION TOOL  v3.1                             ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                           ║
║                                                              ║
║   🌐  URL: http://localhost:5000                            ║
║   📁  Upload Excel files to automate data entry             ║
║   ⌨️   Press Ctrl+C to stop the server                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 2️⃣ Open the Web Interface
The app **automatically opens** in your default browser. If not, navigate to **http://localhost:5000**.

### 3️⃣ First-Time Setup
On first visit, you'll see a **Quick Start Guide** with step-by-step instructions.

### 4️⃣ Configure Settings
| Setting | Description |
|---------|-------------|
| **Speed Preset** | Choose Fast (0.5s), Normal (2s), or Careful (5s) mode |
| **Target URL** | The website where data will be entered (with recent URL autocomplete) |
| **Browser** | Choose Chrome, Firefox, or Edge |
| **Delay** | Seconds to wait between each entry (0.5 - 30) |
| **Start/End Row** | Process specific rows (-1 = all) |
| **Headless Mode** | Run browser invisibly in background |
| **Retry Failed** | Automatically retry failed entries up to 3 times |

### 5️⃣ Upload Excel File
- Click the upload zone or drag & drop your `.xlsx`/`.xls` file
- Select the column containing the data to automate
- See **estimated completion time** based on your settings

### 6️⃣ Run Automation
1. Click **▶ Start** - Review the confirmation dialog with settings summary
2. Click **Start Automation** - A browser window will open
3. **Click on the input field** you want to automate (highlighted in blue)
4. **Click on the submit button** on the webpage
5. Watch the automation run with real-time progress! 🎉

### 7️⃣ Control Automation
| Control | Shortcut | Description |
|---------|----------|-------------|
| **⏸ Pause** | `Space` | Temporarily halt automation |
| **▶ Resume** | `Space` | Continue from where you paused |
| **⏹ Stop** | `Escape` | End automation completely |

### 8️⃣ After Completion
- View **completion summary** with success rate
- **Failed rows panel** shows any entries that failed
- **Export failed rows** as CSV for review
- Click **New Run** to start fresh

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Pause/Resume automation |
| `Escape` | Stop automation |
| `T` | Toggle dark/light theme |
| `M` | Toggle sound notifications |
| `/` | Focus log search |
| `?` | Show keyboard shortcuts |

---

## 📁 Project Structure

```
AutomationTool_for_Levi-s/
├── automation.py          # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── templates/
│   └── index.html        # Web UI (HTML/CSS/JS)
└── uploads/              # Temporary file storage (auto-created)
```

---

## ⚙️ Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| Target URL | `https://www.google.com` | Website to automate |
| Browser | Chrome | Browser to use (Chrome, Firefox, Edge) |
| Delay | 2 seconds | Wait time between entries |
| Start Row | 0 | First row to process |
| End Row | -1 | Last row (-1 = all rows) |
| Headless | Off | Run browser invisibly |
| Retry Failed | On | Retry failed entries (up to 3 times) |

### Speed Presets

| Preset | Delay | Retry | Best For |
|--------|-------|-------|----------|
| ⚡ **Fast** | 0.5s | Off | Fast, reliable websites |
| ▶️ **Normal** | 2s | On | Most websites |
| 🐢 **Careful** | 5s | On | Slow or unreliable websites |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser doesn't open | Ensure the browser is installed and up-to-date |
| WebDriver error | Selenium 4+ auto-manages drivers; update Selenium if issues persist |
| Port 5000 in use | Stop the conflicting process or change port in code |
| Excel file not loading | Ensure file is `.xlsx` or `.xls` format, max 16MB |
| Browser opens but no page | Check if URL is valid (must start with http:// or https://) |
| Elements not clickable | Increase delay time or use Careful mode |
| High failure rate | Enable "Retry Failed" option and use slower delay |

---

## 💡 Tips & Best Practices

1. **Test URL first** - Use the "Test URL" button to verify the website loads correctly
2. **Start small** - Test with 5-10 rows before processing large datasets
3. **Use Careful mode** - For slow or complex websites, use the Careful preset
4. **Check failed rows** - Export failed rows to analyze patterns and fix issues
5. **Save your settings** - Settings are auto-saved to your browser

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Tanvir Talha**

- GitHub: [@tanvir-talha058](https://github.com/tanvir-talha058)

---

<div align="center">

Made with ❤️ for automating repetitive tasks

⭐ **Star this repo if you found it helpful!** ⭐

**[Report Bug](https://github.com/tanvir-talha058/AutomationTool_for_Levi-s/issues) · [Request Feature](https://github.com/tanvir-talha058/AutomationTool_for_Levi-s/issues)**

</div>

