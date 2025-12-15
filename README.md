# Web Automation Tool

![Python](https://img.shields.io/badge/Python-3.x-blue) ![Selenium](https://img.shields.io/badge/Selenium-Automation-green) ![Flask](https://img.shields.io/badge/Flask-Web_UI-orange) ![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-purple)

A modern web-based automation tool for data entry into websites using Selenium. Upload an Excel sheet, click to select elements, and watch the automation run with real-time progress updates.

## ✨ Features

- 🌐 **Modern Web UI** - Clean, responsive HTML/CSS/JS interface
- 📊 **Real-time Progress** - Live updates via WebSocket
- 🖱️ **Click-to-Select** - Simply click on webpage elements to identify them
- 🌙 **Dark Theme** - Easy on the eyes
- 🔄 **Pause/Resume** - Full control over automation flow
- 📈 **Live Statistics** - Success rate, speed, elapsed time
- 🌐 **Multi-Browser** - Chrome, Firefox, Edge support
- 📝 **Activity Log** - Color-coded real-time logging

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/tanvir-talha058/AutomationTool_for_Levi-s.git
cd AutomationTool_for_Levi-s

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage

1. **Start the server:**
   ```bash
   python automation.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000`

3. **Configure:**
   - Enter the target URL
   - Select browser (Chrome/Firefox/Edge)
   - Set delay between entries

4. **Upload Excel file:**
   - Click the upload zone
   - Select your .xlsx or .xls file
   - Choose the data column

5. **Run automation:**
   - Click **Start**
   - Click on the **input field** in the new browser window
   - Click **Confirm Input Field**
   - Click on the **submit button**
   - Click **Confirm Submit Button**
   - Watch the automation run!

## 📋 Requirements

- Python 3.8+
- Chrome, Firefox, or Edge browser
- WebDriver (auto-managed by Selenium)

## 🖼️ Screenshot

```
┌──────────────────────────────────────────────────┐
│  🤖 Web Automation Tool                     v2.0 │
├─────────────────────┬────────────────────────────┤
│  ⚙️ Configuration   │  📊 Progress               │
│  ─────────────────  │  ──────────────────        │
│  URL: [input]       │  42 / 100    42%           │
│  Browser: [Chrome]  │  ████████░░░░░░░░          │
│  Delay: [2]         │                            │
│                     │  ✓ 40  ✗ 2  ⏱ 01:45       │
├─────────────────────┼────────────────────────────┤
│  📁 Excel File      │  📝 Activity Log           │
│  ─────────────────  │  ──────────────────        │
│  [Upload Zone]      │  10:30:15 Row 42 submitted │
│                     │  10:30:12 Row 41 submitted │
│  🎮 Controls        │  10:30:09 Row 40 submitted │
│  [▶ Start] [⏸] [⏹] │                            │
└─────────────────────┴────────────────────────────┘
```

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## 📜 License

[MIT License](LICENSE)

---
### 📩 Contact

For any issues, feel free to reach out!

