import subprocess
import tkinter as tk
from tkinter import messagebox

# Function to check if a VM exists and get its details
def check_vm(vm_name):
    try:
        # Run the govc command to get VM info
        result = subprocess.run(
            ['govc', 'vm.info', vm_name],
            capture_output=True, text=True
        )
        
        # If the command returns output, VM exists
        if result.returncode == 0:
            return result.stdout
        else:
            # Retry with the fully qualified domain name
            result = subprocess.run(
                ['govc', 'vm.info', f'{vm_name}.corp.pvt'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return "VM does not exist"
    except Exception as e:
        return f"Error checking VM: {str(e)}"

# Function to display the output in a pop-up window
def show_vm_info(vm_info):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo("VM Information", vm_info)

# Example usage
vm_name = "st1lntmk7193"
vm_info = check_vm(vm_name)

# Show the information in a pop-up window
show_vm_info(vm_info)

