import pyautogui
from PIL import Image
import io
import base64
import time
import json
import os

class ComputerControl:
    def __init__(self):
        # Get the selected screen from config
        self.screen_index = 0  # Default to primary screen
        self.load_screen_config()
        
        # Get screen info
        self.screens = pyautogui.screenshot().size  # Fallback to full desktop size
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window
            
            # Get all screens
            screens = root.winfo_screenwidth(), root.winfo_screenheight()
            if hasattr(root, 'winfo_screens'):  # Check if multiple screen info is available
                screen_names = root.winfo_screens()
                if self.screen_index < len(screen_names):
                    screen = root.winfo_screen(screen_names[self.screen_index])
                    self.screen_x = screen.winfo_x()
                    self.screen_y = screen.winfo_y()
                    self.screen_width = screen.winfo_width()
                    self.screen_height = screen.winfo_height()
            else:
                # Fallback to primary screen
                self.screen_x = 0
                self.screen_y = 0
                self.screen_width = root.winfo_screenwidth()
                self.screen_height = root.winfo_screenheight()
            
            root.destroy()
        except Exception as e:
            # Fallback to full desktop size if tkinter fails
            self.screen_x = 0
            self.screen_y = 0
            self.screen_width, self.screen_height = self.screens
            
        pyautogui.PAUSE = 0.5  # Add a small delay between actions for stability
        
    def load_screen_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    self.screen_index = config.get('screen_index', 0)
        except Exception as e:
            print(f"Error loading screen config: {e}")
            self.screen_index = 0
        
    def perform_action(self, action):
        action_type = action['type']
        
        if action_type == 'mouse_move':
            x, y = self.map_from_ai_space(action['x'], action['y'])
            pyautogui.moveTo(x, y)
        elif action_type == 'left_click':
            pyautogui.click()
            time.sleep(0.1)  # Add a small delay after clicking
        elif action_type == 'right_click':
            pyautogui.rightClick()
            time.sleep(0.1)
        elif action_type == 'middle_click':
            pyautogui.middleClick()
            time.sleep(0.1)
        elif action_type == 'double_click':
            pyautogui.doubleClick()
            time.sleep(0.1)
        elif action_type == 'left_click_drag':
            start_x, start_y = pyautogui.position()
            end_x, end_y = self.map_from_ai_space(action['x'], action['y'])
            pyautogui.dragTo(end_x, end_y, button='left', duration=0.5)
        elif action_type == 'type':
            pyautogui.write(action['text'], interval=0.1)  # Add a small delay between keystrokes
        elif action_type == 'key':
            pyautogui.press(action['text'])
            time.sleep(0.1)
        elif action_type == 'screenshot':
            return self.take_screenshot()
        elif action_type == 'cursor_position':
            x, y = pyautogui.position()
            return self.map_to_ai_space(x, y)
        else:
            raise ValueError(f"Unsupported action: {action_type}")
        
    def take_screenshot(self):
        """Take screenshot of the selected screen"""
        try:
            import mss
            with mss.mss() as sct:
                # Get all monitors
                monitors = sct.monitors[1:]  # Skip the "all monitors" monitor
                if self.screen_index < len(monitors):
                    monitor = monitors[self.screen_index]
                    # Take screenshot of just this monitor
                    screenshot = sct.grab(monitor)
                    # Convert to PIL Image
                    from PIL import Image
                    screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                else:
                    # Fallback to primary monitor if index is invalid
                    screenshot = pyautogui.screenshot()
        except ImportError:
            # Fallback to pyautogui if mss is not available
            screenshot = pyautogui.screenshot()

        ai_screenshot = self.resize_for_ai(screenshot)
        buffered = io.BytesIO()
        ai_screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
        
    def map_from_ai_space(self, x, y):
        """Map coordinates from AI space (1280x800) to screen space"""
        ai_width, ai_height = 1280, 800
        screen_x = (x * self.screen_width / ai_width) + self.screen_x
        screen_y = (y * self.screen_height / ai_height) + self.screen_y
        return (screen_x, screen_y)
        
    def map_to_ai_space(self, x, y):
        """Map coordinates from screen space to AI space (1280x800)"""
        ai_width, ai_height = 1280, 800
        # First subtract screen offset
        x = x - self.screen_x
        y = y - self.screen_y
        # Then map to AI space
        ai_x = x * ai_width / self.screen_width
        ai_y = y * ai_height / self.screen_height
        return (ai_x, ai_y)
        
    def resize_for_ai(self, screenshot):
        """Resize screenshot to AI space dimensions"""
        return screenshot.resize((1280, 800), Image.Resampling.LANCZOS)
