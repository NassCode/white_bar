import tkinter as tk
import ctypes
from ctypes import wintypes
import platform
import sys

# Constants for AppBar messages and styles
ABM_NEW = 0x00000000
ABM_REMOVE = 0x00000001
ABM_QUERYPOS = 0x00000002
ABM_SETPOS = 0x00000003
ABM_GETSTATE = 0x00000004
ABM_GETTASKBARPOS = 0x00000005
ABM_ACTIVATE = 0x00000006
ABM_GETAUTOHIDEBAR = 0x00000007
ABM_SETAUTOHIDEBAR = 0x00000008
ABM_WINDOWPOSCHANGED = 0x00000009
ABM_SETSTATE = 0x0000000A

ABS_AUTOHIDE = 0x0000001
ABS_ALWAYSONTOP = 0x0000002

ABE_LEFT = 0
ABE_TOP = 1
ABE_RIGHT = 2
ABE_BOTTOM = 3

def create_white_bar():
    root = tk.Tk()
    root.overrideredirect(True)  # Remove window borders
    root.attributes("-topmost", True)  # Keep the window on top
    root.configure(bg='white')  # Set background color to white

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()

    # Calculate initial height (3 cm)
    DPI = ctypes.windll.user32.GetDpiForSystem()
    pixels_per_cm = DPI / 2.54
    initial_height = int(3 * pixels_per_cm)

    # Get work area dimensions
    work_area = get_work_area()
    screen_height = work_area['bottom'] - work_area['top']

    # Position the bar just above the taskbar
    bar_y_position = work_area['bottom'] - initial_height

    # Set geometry to spawn the bar just above the taskbar
    root.geometry(f"{screen_width}x{initial_height}+0+{bar_y_position}")

    # Handle to resize the bar (at the top)
    handle = tk.Frame(root, cursor='sb_v_double_arrow', bg='grey', height=5)
    handle.pack(side='top', fill='x')

    def start_resize(event):
        root.y_start = event.y_root

    def perform_resize(event):
        delta = event.y_root - root.y_start
        new_height = root.winfo_height() - delta
        new_height = max(new_height, 10)  # Minimum height of 10 pixels
        bar_y_position = root.winfo_y() + delta
        root.geometry(f"{screen_width}x{new_height}+0+{bar_y_position}")
        root.y_start = event.y_root
        # Update AppBar position
        update_appbar_position(root)

    handle.bind("<ButtonPress-1>", start_resize)
    handle.bind("<B1-Motion>", perform_resize)

    # Close button inside the bar
    close_button = tk.Button(
        root, text="Close", command=lambda: on_close(root), bg='red', fg='white'
    )
    close_button.pack(side='right', padx=5, pady=5)

    # Adjust window behavior and register as AppBar
    root.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    adjust_window_behavior(root, hwnd)
    register_appbar(hwnd, root)

    root.mainloop()

def get_work_area():
    """Get the work area dimensions (area excluding the taskbar) on Windows."""
    SPI_GETWORKAREA = 0x0030
    rect = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    work_area = {
        'left': rect.left,
        'top': rect.top,
        'right': rect.right,
        'bottom': rect.bottom
    }
    return work_area

def adjust_window_behavior(root, hwnd):
    """Adjust the window to prevent interference with full-screen apps and keyboard."""
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOOLWINDOW = 0x00000080

    current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    new_style = current_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

    # On Linux, treat the window as a dock
    if platform.system() != "Windows":
        root.attributes('-type', 'dock')

def register_appbar(hwnd, root):
    """Register the window as an AppBar."""
    message = wintypes.MSG()
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd
    abd.uCallbackMessage = ctypes.windll.user32.RegisterWindowMessageW("AppBarMessage")
    abd.uEdge = ABE_BOTTOM
    ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))

    # Set AppBar position
    update_appbar_position(root)

def update_appbar_position(root):
    """Update AppBar position based on the window's current position and size."""
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd
    abd.uEdge = ABE_BOTTOM

    rect = wintypes.RECT()
    rect.left = 0
    rect.right = root.winfo_screenwidth()
    rect.bottom = root.winfo_y() + root.winfo_height()
    rect.top = root.winfo_y()

    abd.rc = rect
    ctypes.windll.shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))
    ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))

def on_close(root):
    """Clean up and exit."""
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    unregister_appbar(hwnd)
    root.destroy()
    sys.exit()

def unregister_appbar(hwnd):
    """Unregister the AppBar."""
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd
    ctypes.windll.shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(abd))

class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('hWnd', wintypes.HWND),
        ('uCallbackMessage', wintypes.UINT),
        ('uEdge', wintypes.UINT),
        ('rc', wintypes.RECT),
        ('lParam', wintypes.LPARAM),
    ]

if __name__ == "__main__":
    create_white_bar()
