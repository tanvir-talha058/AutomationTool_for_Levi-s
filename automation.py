import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class WebAutomationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Automation Tool")
        self.root.geometry("300x400")
        self.root.configure(bg="#fdfefe")  
        self.file_path = ""
        self.data = None
        self.driver = None
        self.input_box = None
        self.submit_button = None

        # Header 
        self.header = tk.Label(root, text="Web Automation", bg="#3B7097", fg="white", font=("Arial", 14, "bold"), padx=10, pady=5)
        self.header.pack(fill=tk.X)
        
        # UI design
        self.label = tk.Label(root, text="Select an Excel file:", bg="#38BFA7", fg="#2C3E50", font=("Arial", 12))
        self.label.pack(pady=10)
        
        self.upload_btn = tk.Button(root, text="⬆ Upload", command=self.upload_file, bg="#524582", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10, relief=tk.FLAT)
        self.upload_btn.pack(pady=10)
        
        self.start_btn = tk.Button(root, text="▶ Start", command=self.start_automation, state=tk.DISABLED, bg="#3675C3", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10, relief=tk.FLAT)
        self.start_btn.pack(pady=10)
        
        self.stop_btn = tk.Button(root, text="⏹ Stop", command=self.stop_automation, state=tk.DISABLED, bg="#C14364", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10, relief=tk.FLAT)
        self.stop_btn.pack(pady=10)

    
    def upload_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if self.file_path:
            try:
                self.data = pd.read_excel(self.file_path)
                messagebox.showinfo("Success", "Excel file loaded successfully!")
                self.start_btn.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load Excel file: {e}")
    
    def start_automation(self):
        if self.data is None:
            messagebox.showerror("Error", "Please upload an Excel file first.")
            return

        
        try:
            self.driver = webdriver.Chrome()
            self.driver.get("https://www.youtube.com/")  
            
            messagebox.showinfo("Instructions", "Click on the input box and then press ENTER.")
            self.input_box = self.get_element()
            
            messagebox.showinfo("Instructions", "Click on the submit button and then press ENTER.")
            self.submit_button = self.get_element()

            self.process_data()
        except Exception as e:
            messagebox.showerror("Error", f"Automation failed: {e}")
    
    def get_element(self):
        while True:
            element = self.driver.switch_to.active_element
            if element:
                return element
            time.sleep(1)
    
    def process_data(self):
        try:
            for index, row in self.data.iterrows():
                self.input_box.clear()
                self.input_box.send_keys(str(row.iloc[0]))  
                self.submit_button.click()
                time.sleep(2) 
            
            messagebox.showinfo("Completed", "All data submitted successfully!")
            self.driver.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Data submission failed: {e}")
    
    def stop_automation(self):
        if self.driver:
            self.driver.quit()
        messagebox.showinfo("Stopped", "Automation Stopped!")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebAutomationTool(root)
    root.mainloop()
