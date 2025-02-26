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

def get_game_window():
    for window in gw.getWindowsWithTitle("[mountasi1] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):
        if window.isActive:
            return window.left, window.top, window.width, window.height
    return None

def smooth_click(x, y):
    pyautogui.moveTo(x, y, duration=0.3)
    time.sleep(0.1)
    pyautogui.click()
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
    data = pytesseract.image_to_data(result, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)
    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        if "drowcrusher" in text:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 70
            print(f"✅ Klickar på '{text}' vid ({click_x}, {click_y})")
            smooth_click(click_x, click_y)
            return True
    print("❌ OCR hittade ingen 'Drowcrusher'-text eller den försvann.")
    return False

def find_and_click_item(item_image_path):
    screenshot = pyautogui.screenshot()
    screenshot.save("inventory_screenshot.png")
    inventory_img = cv2.imread("inventory_screenshot.png", cv2.IMREAD_UNCHANGED)
    template = cv2.imread(item_image_path, cv2.IMREAD_UNCHANGED)
    result = cv2.matchTemplate(inventory_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val > 0.7:
        x, y = max_loc
        smooth_click(x + template.shape[1] // 2, y + template.shape[0] // 2)
        return True
    print("❌ Item hittades inte, pausar skriptet.")
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

# if __name__ == "__main__":
#     iteration_count = 0
#     time.sleep(3)
#     while True:  # Kör loopen 20 gånger
#         find_and_click_item("laptopbag.png")  # Steg 1: Klicka på bag
#         time.sleep(0.5)
#         screenshot, game_position = capture_game_screen()
#         if screenshot is not None and detect_drowcrusher_text(screenshot, game_position):  # Endast fortsätt om Drowcrusher hittas
#             pyautogui.moveTo(game_position[0] + int(game_position[2] * 0.8), game_position[1] + int(game_position[3] * 0.2))  # Hovrar vid 80% från vänster, 20% från toppen
#             time.sleep(1)
#             find_and_click_item("cent.png")  # Steg 3: Klicka på item i inventory
#             time.sleep(1)
#             click_at_percentage(0.75, 0.765)  # Steg 4: Klicka 70% från vänster, 70% ned
#             time.sleep(0.5)
#             click_at_percentage(0.5, 0.5)  # Klicka i mitten av skärmen
#             time.sleep(8)
#             click_at_percentage(0.5, 0.5)
#             iteration_count += 1 
#         if iteration_count % 23 == 0:
#             press_physical_pause_key()
#             time.sleep(1)
#             find_and_click_item("cent.png")  # Steg 3: Klicka på item i inventory
#             time.sleep(2)
#             find_and_click_offset_item("quantity.png", retries=10)
#             time.sleep(2)
#             type_23()
#             time.sleep(2)
#             find_and_click_item("continue.png")
#             press_physical_pause_key()
#             iteration_count = 0
#                 # time.sleep(1)  # Valfri paus mellan iterationer för att undvika överbelastning
if __name__ == "__main__":
    iteration_count = 0
    time.sleep(3)

    while True:  # Oändlig loop
        print(f"🔄 Iteration: {iteration_count + 1}")

        # ✅ **Steg 1: Klicka på bag**
        bag_clicked = find_and_click_item("laptopbag.png")
        if not bag_clicked:
            print("⚠️ Bag hittades inte, hoppar över iterationen.")
            continue  # 🔄 Hoppa över resten av iterationen och börja om från början

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
