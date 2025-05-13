import os
import winshell
from win32com.client import Dispatch
from create_icon import create_bakery_icon

def create_shortcut():
    # Get the desktop path
    desktop = winshell.desktop()
    
    # Get the current directory (where the batch file is)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    batch_path = os.path.join(current_dir, "launch_bakery.bat")
    
    # Create the shortcut path
    shortcut_path = os.path.join(desktop, "Bakery Management.lnk")
    
    # Create the icon if it doesn't exist
    icon_path = os.path.join(current_dir, "bakery_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = create_bakery_icon()
    
    # Create the shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = batch_path
    shortcut.WorkingDirectory = current_dir
    shortcut.IconLocation = icon_path
    shortcut.save()
    
    print(f"Shortcut created on desktop: {shortcut_path}")

if __name__ == "__main__":
    create_shortcut() 