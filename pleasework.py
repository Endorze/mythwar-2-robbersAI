import cv2
import numpy as np
import pyautogui
import pytesseract
import pygetwindow as gw
import time
import keyboard
import win32api, win32con  

# 🔹 Ange sökvägen till Tesseract om det behövs (Windows-användare)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔹 Lista över felstavningar som ska accepteras
ROBBER_VARIANTS = ["robber", "rober", "r0bber", "r0ber", "robbr"]
BLOCKED_NPCS = ["elven witch", "cupid"]  # 🔹 NPC:er som ska ignoreras

paused = False  
previous_position = None  # Håller koll på senaste klickets position

def toggle_pause():
    """ Växlar mellan pausat och aktivt läge. """
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

def filter_text_colors(image):
    """ Behåller endast gul text, gör allt annat svart. """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([22, 150, 150])
    upper_yellow = np.array([35, 255, 255])

    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    result = cv2.bitwise_and(image, image, mask=mask_yellow)
    result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    result = cv2.bitwise_not(result)

    return result

def smooth_move(x, y, duration=0.3):
    """ Flyttar musen mjukt till positionen istället för att teleportera. """
    pyautogui.moveTo(x, y, duration=duration)

def force_click(x, y, game_position):
    """ Simulerar ett hårdvaruklick med Windows API inom 75% av skärmområdet. """
    global previous_position

    x, y = enforce_click_boundaries(x, y, game_position)
    
    if detect_light_blue_near_center(game_position):
        print("🔵 Ljusblå färg nära mitten! Kontrollerar om det är ett problem...")
        if is_large_blue_area(game_position):
            print("🚨 Stor blå yta upptäckt! Justerar klick.")
            x, y = adjust_click_away_from_blue(x, y, game_position)

    smooth_move(x, y)  
    time.sleep(0.05)  
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)  
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    previous_position = (x, y)  # Uppdatera senaste klicket

def enforce_click_boundaries(x, y, game_position):
    """ Justerar klicket så att det alltid är inom 75% av skärmen (15% marginal på kanterna). """
    game_x, game_y, game_w, game_h = game_position

    min_x = game_x + int(game_w * 0.15)
    max_x = game_x + int(game_w * 0.85)
    min_y = game_y + int(game_h * 0.15)
    max_y = game_y + int(game_h * 0.85)

    x = max(min_x, min(x, max_x))
    y = max(min_y, min(y, max_y))

    return x, y

def detect_light_blue_near_center(game_position):
    """ Kontrollerar om ljusblå färg finns nära mitten av skärmen. """
    screenshot, _ = capture_game_screen()
    if screenshot is None:
        return False

    hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

    lower_light_blue = np.array([90, 150, 150])
    upper_light_blue = np.array([110, 255, 255])

    mask_light_blue = cv2.inRange(hsv, lower_light_blue, upper_light_blue)

    return np.any(mask_light_blue)

def is_large_blue_area(game_position):
    """ Kollar om det blå området är stort och blockar skärmen. """
    screenshot, _ = capture_game_screen()
    if screenshot is None:
        return False

    hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
    lower_light_blue = np.array([90, 150, 150])
    upper_light_blue = np.array([110, 255, 255])
    mask_light_blue = cv2.inRange(hsv, lower_light_blue, upper_light_blue)

    return np.count_nonzero(mask_light_blue) > 2000  

def adjust_click_away_from_blue(x, y, game_position):
    """ Om ljusblått är framför, klicka åt sidan istället för motsatt håll. """
    global previous_position
    if not previous_position:
        return enforce_click_boundaries(x + 50, y, game_position)  # Standard justering

    prev_x, prev_y = previous_position

    dx = x - prev_x
    dy = y - prev_y

    if abs(dx) > abs(dy):  
        new_x = x + (-50 if dx > 0 else 50)  
        new_y = y
    else:  
        new_x = x
        new_y = y + (-50 if dy > 0 else 50)  

    return enforce_click_boundaries(new_x, new_y, game_position)

while True:
    if paused:
        print("⏸️  Pausat - Väntar på F5 för att återuppta...")
        time.sleep(0.5)
        continue

    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        force_click(game_position[0] + game_position[2] // 2, game_position[1] + int(game_position[3] * 0.52), game_position)

    time.sleep(0.05)
