# 🤖 Web Automation Tool for Levi's

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.0+-43B02A?logo=selenium&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3+-black?logo=flask&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-purple)
![License](https://img.shields.io/badge/License-MIT-green)

A modern, web-based automation tool for bulk data entry into websites using Selenium. Features a sleek dark-themed UI with real-time progress tracking, multi-browser support, and intuitive click-to-select element identification.

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
| 🌐 **Modern Web UI** | Clean, responsive dark-themed interface built with HTML/CSS/JS |
| ⚡ **Real-time Updates** | Live progress tracking via WebSocket - no page refresh needed |
| 🖱️ **Click-to-Select** | Simply click on webpage elements to identify input fields and buttons |
| 🔄 **Pause/Resume** | Full control over automation - pause anytime and resume where you left off |
| 📈 **Live Statistics** | Track success/failure rates, speed (entries/min), and elapsed time |
| 🌐 **Multi-Browser** | Supports Chrome, Firefox, and Edge browsers |
| 📝 **Activity Log** | Color-coded real-time logging with timestamps |
| 📊 **Excel Support** | Import .xlsx and .xls files with column selection |
| 🎯 **Row Range** | Process specific row ranges from your data |

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
The server will start and display:
```
==================================================
🤖 Web Automation Tool - Modern UI
==================================================
Open your browser and go to: http://localhost:5000
==================================================
```

### 2️⃣ Open the Web Interface
Navigate to **http://localhost:5000** in your browser.

### 3️⃣ Configure Settings
| Setting | Description |
|---------|-------------|
| **Target URL** | The website where data will be entered |
| **Browser** | Choose Chrome, Firefox, or Edge |
| **Delay** | Seconds to wait between each entry (0.5 - 30) |
| **Start/End Row** | Process specific rows (-1 = all) |

### 4️⃣ Upload Excel File
- Click the upload zone or drag & drop your `.xlsx`/`.xls` file
- Select the column containing the data to automate

### 5️⃣ Run Automation
1. Click **▶ Start** - A browser window will open
2. **Click on the input field** you want to automate
3. Click **✓ Confirm Input Field** in the web UI
4. **Click on the submit button** on the webpage
5. Click **✓ Confirm Submit Button** in the web UI
6. Watch the automation run! 🎉

### 6️⃣ Control Automation
- **⏸ Pause** - Temporarily halt automation
- **▶ Resume** - Continue from where you paused
- **⏹ Stop** - End automation completely

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
| Browser | Chrome | Browser to use |
| Delay | 2 seconds | Wait time between entries |
| Start Row | 0 | First row to process |
| End Row | -1 | Last row (-1 = all rows) |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser doesn't open | Ensure the browser is installed and up-to-date |
| WebDriver error | Selenium 4+ auto-manages drivers; update Selenium if issues persist |
| Port 5000 in use | The app will try 5001, or stop the conflicting process |
| Excel file not loading | Ensure file is `.xlsx` or `.xls` format |

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

</div>

