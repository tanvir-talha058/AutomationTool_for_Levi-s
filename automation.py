import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class WebAutomationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Automation Tool")
        self.file_path = ""
        self.data = None
        self.driver = None
        self.input_box = None
        self.submit_button = None
        
        # UI Elements
        self.label = tk.Label(root, text="Select an Excel file:")
        self.label.pack()
        
        self.upload_btn = tk.Button(root, text="Upload Excel", command=self.upload_file)
        self.upload_btn.pack()
        
        self.start_btn = tk.Button(root, text="Start Automation", command=self.start_automation, state=tk.DISABLED)
        self.start_btn.pack()
        
        self.stop_btn = tk.Button(root, text="Stop Automation", command=self.stop_automation, state=tk.DISABLED)
        self.stop_btn.pack()
        
    def upload_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if self.file_path:
            self.data = pd.read_excel(self.file_path)
            messagebox.showinfo("Success", "Excel file loaded successfully!")
            self.start_btn.config(state=tk.NORMAL)
    
    def start_automation(self):
        if self.data is None:
            messagebox.showerror("Error", "Please upload an Excel file first.")
            return
        
        # Start WebDriver
        self.driver = webdriver.Chrome()
        self.driver.get("https://www.calculatorsoup.com/calculators/conversions/numberstowords.php")  # Replace with actual website
        
        messagebox.showinfo("Instructions", "Click on the input box and then press ENTER.")
        self.input_box = self.get_element()
        
        messagebox.showinfo("Instructions", "Click on the submit button and then press ENTER.")
        self.submit_button = self.get_element()
        
        self.process_data()
    
    def get_element(self):
        while True:
            element = self.driver.switch_to.active_element
            if element:
                return element
            time.sleep(1)
    
    def process_data(self):
        for index, row in self.data.iterrows():
            self.input_box.clear()
            self.input_box.send_keys(str(row[0]))  # Assuming first column has data
            self.submit_button.click()
            time.sleep(2)  # Adjust based on website response time
        
        messagebox.showinfo("Completed", "All data submitted successfully!")
        self.driver.quit()
    
    def stop_automation(self):
        if self.driver:
            self.driver.quit()
        messagebox.showinfo("Stopped", "Automation Stopped!")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = WebAutomationTool(root)
    root.mainloop()
