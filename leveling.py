import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import keyboard
import win32api, win32con  

# Pausfunktion
paused = False  

def toggle_pause():
    global paused
    paused = not paused
    print("⏸️ Skript pausat. Tryck F5 för att återuppta." if paused else "▶️ Skript återupptas.")

keyboard.add_hotkey("f5", toggle_pause)

def get_game_window():
    """ Hitta spelrutans position och storlek på skärmen. """
    for window in gw.getWindowsWithTitle("[mountasi3] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):  
        if window.isActive:
            return window.left, window.top, window.width, window.height
    return None

def capture_game_screen():
    """ Tar en skärmbild av spelrutan. """
    game_window = get_game_window()
    if not game_window:
        print("❌ Spelet hittades inte! Kontrollera fönsternamnet.")
        return None, None

    x, y, w, h = game_window
    screenshot = pyautogui.screenshot(region=(x, y, w, h))  
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return screenshot, (x, y, w, h)

def smooth_move(x, y, duration=0.3):
    """ Flyttar musen mjukt till positionen istället för att teleportera. """
    pyautogui.moveTo(x, y, duration=duration)

def force_click(x, y):
    """ Simulerar ett hårdvaruklick med Windows API. """
    smooth_move(x, y)  
    time.sleep(0.05)  
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)  
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def detect_light_blue_areas(image):
    """ Detekterar ljusblå områden i skärmbilden. """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_light_blue = np.array([90, 150, 150])  
    upper_light_blue = np.array([110, 255, 255])
    mask = cv2.inRange(hsv, lower_light_blue, upper_light_blue)
    return mask

def get_random_click_position(game_position, mask):
    """ Hittar en slumpmässig klickposition inom spelområdet som inte innehåller ljusblå färg. """
    game_x, game_y, game_w, game_h = game_position

    for _ in range(50):  # Max 50 försök att hitta en bra position
        click_x = np.random.randint(game_x + int(game_w * 0.15), game_x + int(game_w * 0.85))
        click_y = np.random.randint(game_y + int(game_h * 0.15), game_y + int(game_h * 0.85))
        
        if mask[click_y - game_y, click_x - game_x] == 0:  # Endast klicka på mörka områden (inte ljusblå)
            return click_x, click_y

    return None, None  # Om ingen säker position hittas

while True:
    if paused:
        print("⏸️  Pausat - Väntar på F5 för att återuppta...")
        time.sleep(0.5)
        continue

    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        light_blue_mask = detect_light_blue_areas(screenshot)
        click_x, click_y = get_random_click_position(game_position, light_blue_mask)
        
        if click_x and click_y:
            print(f"✅ Klickar på ({click_x}, {click_y})")
            force_click(click_x, click_y)
        else:
            print("❌ Ingen säker klickposition hittades!")
    
    time.sleep(0.5)  # Vänta lite innan nästa klick
