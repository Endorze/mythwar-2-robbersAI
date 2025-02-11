import cv2
import numpy as np
import pyautogui
import pytesseract
import pygetwindow as gw
import time
import keyboard
import win32api, win32con  # 🔹 Windows API för att simulera knapptryck

# 🔹 Ange sökvägen till Tesseract om det behövs (Windows-användare)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔹 Lista över felstavningar som ska accepteras
ROBBER_VARIANTS = ["robber", "rober", "r0bber", "r0ber", "robbr"]
paused = False  

def toggle_pause():
    """ Växlar mellan pausat och aktivt läge. """
    global paused
    paused = not paused
    print("⏸️ Skript pausat. Tryck F5 för att återuppta." if paused else "▶️ Skript återupptas.")

# 🔹 Lyssna på F5-knappen för att pausa/återuppta skriptet
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

def force_click(x, y, game_position):
    """ Simulerar ett hårdvaruklick med Windows API inom 75% av skärmområdet. """
    x, y = enforce_click_boundaries(x, y, game_position)
    smooth_move(x, y)  # Mjuk musrörelse först
    time.sleep(0.05)  # Kort paus
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)  # Håller ner musen en kort stund
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def enforce_click_boundaries(x, y, game_position):
    """ Justerar klicket så att det alltid är inom 75% av skärmen (15% marginal på kanterna). """
    game_x, game_y, game_w, game_h = game_position

    min_x = game_x + int(game_w * 0.15)
    max_x = game_x + int(game_w * 0.85)
    min_y = game_y + int(game_h * 0.15)
    max_y = game_y + int(game_h * 0.85)

    # Begränsa x och y så att de alltid är inom 75% av skärmen
    x = max(min_x, min(x, max_x))
    y = max(min_y, min(y, max_y))

    return x, y

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

def detect_robber_text(image, game_position):
    """ Identifiera 'Robber' och klicka på den om den hittas. """
    processed_image = filter_text_colors(image)
    data = pytesseract.image_to_data(processed_image, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)

    robber_found = False

    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        if any(variant in text for variant in ROBBER_VARIANTS):  
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 30

            print(f"✅ Klickade på '{text}' vid ({click_x}, {click_y})")
            force_click(click_x, click_y, game_position)

            robber_found = True
            break  

    if not robber_found:
        print("❌ OCR hittade ingen 'Robber'-text.")

    # Klicka alltid i mitten av skärmen efter att ha letat efter en Robber
    click_middle_screen(game_position)

def click_middle_screen(game_position):
    """ Klickar 55% ner på skärmen i mitten, alltid efter att ha letat efter en Robber. """
    _, _, game_w, game_h = game_position

    click_x = game_position[0] + game_w // 2
    click_y = game_position[1] + int(game_h * 0.52)

    print(f"✅ Klickade på mitten av skärmen vid ({click_x}, {click_y})")
    force_click(click_x, click_y, game_position)

# 🔹 Loop för att kontinuerligt söka och klicka
while True:
    if paused:
        print("⏸️  Pausat - Väntar på F5 för att återuppta...")
        time.sleep(0.5)
        continue

    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        print("🔍 Letar efter 'Robber'...")
        detect_robber_text(screenshot, game_position)

    time.sleep(0.05)
