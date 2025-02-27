import cv2
import numpy as np
import pyautogui
import pytesseract
import pygetwindow as gw
import time
import keyboard
import sys
import win32api
import win32con

# 🔹 Ange sökvägen till Tesseract om det behövs (Windows-användare)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

paused = False

def toggle_pause():
    global paused
    paused = not paused
    if paused:
        print("⏸️ Skript pausat. Tryck F5 för att avsluta.")
    else:
        print("▶️ Skript återupptas.")

def terminate_script():
    print("❌ Skriptet avslutas.")
    sys.exit()

keyboard.add_hotkey("f5", terminate_script)

def press_alt_g():
    keyboard.press('alt+g')
    time.sleep(0.5)

def get_game_window():
    for window in gw.getWindowsWithTitle("[mountasi1] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):
        if window.isActive:
            return window.left, window.top, window.width, window.height
    return None

def smooth_click(x, y):
    pyautogui.moveTo(x, y, duration=0.4)
    time.sleep(0.1)
    pyautogui.click()

def capture_game_screen():
    game_window = get_game_window()
    if not game_window:
        print("❌ Spelet hittades inte! Kontrollera fönsternamnet.")
        return None, None
    x, y, w, h = game_window
    screenshot = pyautogui.screenshot(region=(x, y, w, h))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return screenshot, (x, y, w, h)

def detect_drowcrusher_text(image, game_position):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([20, 150, 150])
    upper_yellow = np.array([35, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    result = cv2.bitwise_and(image, image, mask=mask_yellow)
    result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    result = cv2.bitwise_not(result)
    
    # OCR-konfiguration
    data = pytesseract.image_to_data(result, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)
    
    # Lista med möjliga feltolkningar av "Drowcrusher"
    possible_variants = [
        "drowcrusher", "+drowcrusher+", "drowcrusber", "drowcrush3r", "drowcrushe", "drowcrusl1er", "drowcrushr", "drowcruhser"
    ]
    
    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        
        # Kontrollera om texten matchar någon av variationerna
        if any(variant in text for variant in possible_variants):
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 70
            print(f"✅ Klickar på '{text}' vid ({click_x}, {click_y})")
            smooth_click(click_x, click_y)
            return True
    
    print("❌ OCR hittade ingen 'Drowcrusher'-text eller den försvann.")
    return False


def force_hover_and_click(x, y):
    """ Flyttar bort musen, hovrar igen och gör ett kraftigt klick """
    pyautogui.moveTo(x + 0, y + 25, duration=0.3)  # Flytta bort musen
    time.sleep(0.2)
    pyautogui.moveTo(x, y, duration=0.3)  # Hovra tillbaka
    time.sleep(0.2)

    # Force-click med win32api
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.2)  # Håll nere klicket längre
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)


def find_and_click_item(item_image_path, force_hover=False):
    screenshot = pyautogui.screenshot()
    screenshot.save("inventory_screenshot.png")
    inventory_img = cv2.imread("inventory_screenshot.png", cv2.IMREAD_UNCHANGED)
    template = cv2.imread(item_image_path, cv2.IMREAD_UNCHANGED)
    result = cv2.matchTemplate(inventory_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    if max_val > 0.7:
        x, y = max_loc
        x_click = x + template.shape[1] // 2
        y_click = y + template.shape[0] // 2
        
        if force_hover:
            force_hover_and_click(x_click, y_click)  # 🔹 Endast om force_hover=True (dvs. för bag)
        else:
            smooth_click(x_click, y_click)  # 🔹 Vanlig smooth click för alla andra

        return True
    
    print(f"❌ Item {item_image_path} hittades inte, pausar skriptet.")
    toggle_pause()
    return False


def find_and_click_offset_item(item_image_path, retries=3):
    if paused:
        return False
    for attempt in range(retries):
        screenshot = pyautogui.screenshot()
        screenshot.save("offset_screenshot.png")
        inventory_img = cv2.imread("offset_screenshot.png", cv2.IMREAD_UNCHANGED)
        template = cv2.imread(item_image_path, cv2.IMREAD_UNCHANGED)
        result = cv2.matchTemplate(inventory_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.7:
            x, y = max_loc
            x_offset = x + template.shape[1] + 30
            y_offset = y + template.shape[0] // 2
            smooth_click(x_offset, y_offset)
            return True
        print(f"❌ Försök {attempt + 1}: Offset item hittades inte, försöker igen...")
        time.sleep(0.5)
    print("❌ Offset item hittades inte efter flera försök.")
    return False


def click_at_percentage(x_percent, y_percent):
    game_window = get_game_window()
    if not game_window:
        print("❌ Spelet hittades inte! Kontrollera fönsternamnet.")
        return
    game_x, game_y, game_w, game_h = game_window
    x = game_x + int(game_w * x_percent)
    y = game_y + int(game_h * y_percent)
    smooth_click(x, y)

def press_physical_pause_key():
    win32api.keybd_event(win32con.VK_PAUSE, 0, 0, 0)
    time.sleep(0.1)
    win32api.keybd_event(win32con.VK_PAUSE, 0, win32con.KEYEVENTF_KEYUP, 0)

def type_23():
    time.sleep(2)
    keyboard.press('backspace')
    time.sleep(2)
    keyboard.write("23")

if __name__ == "__main__":
    iteration_count = 0
    time.sleep(3)

    while True:  # Oändlig loop
        print(f"🔄 Iteration: {iteration_count + 1}")

        # ✅ **Steg 1: Klicka på bag** 
        press_alt_g()
        time.sleep(0.5)

        # ✅ **Steg 2: Ta en skärmdump och leta efter Drowcrusher**
        screenshot, game_position = capture_game_screen()
        if screenshot is None or not detect_drowcrusher_text(screenshot, game_position):
            print("⚠️ Drowcrusher hittades inte, hoppar över iterationen.")
            continue  # 🔄 Hoppa över resten av iterationen och börja om från början

        # ✅ **Om vi kommit hit: Bag är öppen och Drowcrusher hittades**
        pyautogui.moveTo(game_position[0] + int(game_position[2] * 0.8), game_position[1] + int(game_position[3] * 0.2))
        time.sleep(1)

        # ✅ **Steg 3: Klicka på item i inventory**
        item_clicked = find_and_click_item("cent.png")
        if not item_clicked:
            print("⚠️ Item hittades inte, hoppar över iterationen.")
            continue  # 🔄 Hoppa över resten av iterationen och börja om från början

        time.sleep(1)
        click_at_percentage(0.75, 0.765)  # Steg 4: Klicka 70% från vänster, 70% ned
        time.sleep(0.5)
        click_at_percentage(0.5, 0.5)  # Klicka i mitten av skärmen
        time.sleep(8)
        click_at_percentage(0.5, 0.5)

        # ✅ **Nu ökar iteration_count bara om ALLA steg lyckades!**
        iteration_count += 1

        # ✅ **Efter 23 lyckade iterationer, kör extrasteg**
        if iteration_count % 23 == 0:
            print("🎉 23 lyckade iterationer! Kör extrastegen.")
            sleep(1)
            press_physical_pause_key()
            time.sleep(1)

            if not find_and_click_item("cent.png"):
                print("⚠️ Item för extrasteg hittades inte, hoppar över.")
                continue

            time.sleep(2)
            find_and_click_offset_item("quantity.png", retries=10)
            time.sleep(2)
            type_23()
            time.sleep(2)
            find_and_click_item("continue.png")
            press_physical_pause_key()

            iteration_count = 0  # Återställ räknaren efter 23 lyckade iterationer
            time.sleep(2)