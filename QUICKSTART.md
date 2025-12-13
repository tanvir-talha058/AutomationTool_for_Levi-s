# Quick Start Guide - Web Automation Tool

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install pandas openpyxl selenium
```

### 2. Install ChromeDriver

**Option A: Using Chrome for Testing**
```bash
pip install webdriver-manager
```
Then modify automation.py line 76 to:
```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Replace line 76 with:
self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

**Option B: Manual Installation**
1. Check your Chrome browser version (Chrome menu → Help → About Google Chrome)
2. Download matching ChromeDriver from: https://chromedriver.chromium.org/
3. Add ChromeDriver to your system PATH

### 3. Run the Application
```bash
python automation.py
```

## Usage Flow

1. Launch the application
2. Enter target website URL (e.g., https://www.google.com)
3. Set delay between submissions (default: 2 seconds)
4. Click "Upload Excel File" and select your data file
5. Choose which column contains the data to submit
6. Click "Start Automation"
7. Click on the input field on the webpage (when prompted)
8. Click on the submit button on the webpage (when prompted)
9. Watch the automation run!

## Excel File Example

Create an Excel file with your data:

| Product Name | SKU | Quantity |
|--------------|-----|----------|
| Levi's 501   | L501| 10       |
| Levi's 511   | L511| 15       |
| Levi's 721   | L721| 8        |

Save as `data.xlsx` and upload through the tool.

## Troubleshooting

**Issue**: "ChromeDriver not found"
- **Solution**: Install ChromeDriver and add to PATH, or use webdriver-manager

**Issue**: "Excel file won't load"
- **Solution**: Ensure file is .xlsx or .xls format and not corrupted

**Issue**: "Element not found"
- **Solution**: Increase delay time or ensure webpage loads completely

**Issue**: Automation stops unexpectedly
- **Solution**: Check activity log for errors, verify internet connection

## Tips

- Test with a small Excel file (3-5 rows) first
- Use longer delays (3-5 seconds) for slow websites
- Ensure popup blockers are disabled
- Some websites may block automation - respect their terms of service

## Support

For issues or questions, check the activity log in the application for detailed error messages.
