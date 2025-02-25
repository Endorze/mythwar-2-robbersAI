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

paused = False  

def terminate_script():
    print("❌ Skriptet avslutas.")
    sys.exit()

keyboard.add_hotkey("f5", terminate_script)

def get_game_window():
    """ Hitta spelrutans position och storlek på skärmen. """
    for window in gw.getWindowsWithTitle("[mountasi2] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):  
        if window.isActive:
            return window.left, window.top, window.width, window.height
    return None

def smooth_click(x, y):
    """ Rör musen mjukt till destinationen och utför ett klick. """
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.2)
    pyautogui.click()  # Direkt klick istället för mouseDown/mouseUp
    """ Rör musen mjukt till destinationen och utför ett klick. """
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.2)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.mouseUp()

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
    """ Behåller endast skarp gul text för att identifiera 'Drowcrusher', gör allt annat svart. """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([20, 150, 150])
    upper_yellow = np.array([35, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    result = cv2.bitwise_and(image, image, mask=mask_yellow)
    result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    result = cv2.bitwise_not(result)
    return result

def detect_drowcrusher_text(image, game_position):
    """ Identifiera 'Drowcrusher' och klicka på den om den finns kvar. """
    processed_image = filter_text_colors(image)
    data = pytesseract.image_to_data(processed_image, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)
    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        if "drowcrusher" in text:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 60  # Justerat till 50 pixlar nedåt
            print(f"✅ Klickar på '{text}' vid ({click_x}, {click_y})")
            smooth_click(click_x, click_y)
            return True  
    print("❌ OCR hittade ingen 'Drowcrusher'-text eller den försvann.")
    return False

def find_and_click_item(item_image_path):
    """ Hittar och klickar på ett item i inventory baserat på en referensbild """
    screenshot = pyautogui.screenshot()
    screenshot.save("inventory_screenshot.png")
    inventory_img = cv2.imread("inventory_screenshot.png", cv2.IMREAD_UNCHANGED)
    template = cv2.imread(item_image_path, cv2.IMREAD_UNCHANGED)
    result = cv2.matchTemplate(inventory_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val > 0.8:
        x, y = max_loc
        smooth_click(x + template.shape[1] // 2, y + template.shape[0] // 2)
        return True
    print("Item hittades inte.")
    return False

def click_at_percentage(x_percent, y_percent):
    """ Klickar vid en viss procentuell position på skärmen. """
    game_window = get_game_window()
    if not game_window:
        print("❌ Spelet hittades inte! Kontrollera fönsternamnet.")
        return
    game_x, game_y, game_w, game_h = game_window
    screen_width, screen_height = game_w, game_h
    x = game_x + int(screen_width * x_percent)
    y = game_y + int(screen_height * y_percent)
    smooth_click(x, y)

def main():
    find_and_click_item("bag.png")  # Steg 1: Klicka på bag
    time.sleep(1)
    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        detect_drowcrusher_text(screenshot, game_position)  # Steg 2: Leta efter Drowcrusher och klicka
    time.sleep(1)
    find_and_click_item("image.png")  # Steg 3: Klicka på item i inventory
    time.sleep(1)
    click_at_percentage(0.75, 0.765)  # Steg 4: Klicka 70% från vänster, 70% ned
    time.sleep(1)
    click_at_percentage(0.5, 0.5)  # Klicka i mitten av skärmen
    time.sleep(8)
    click_at_percentage(0.5, 0.5)

if __name__ == "__main__":
    for _ in range(20):  # Kör loopen 20 gånger
        find_and_click_item("bag.png")  # Steg 1: Klicka på bag
        time.sleep(0.5)
        screenshot, game_position = capture_game_screen()
        if screenshot is not None and detect_drowcrusher_text(screenshot, game_position):  # Endast fortsätt om Drowcrusher hittas
            pyautogui.moveTo(game_position[0] + int(game_position[2] * 0.8), game_position[1] + int(game_position[3] * 0.2))  # Hovrar vid 80% från vänster, 20% från toppen
            time.sleep(0.5)
            find_and_click_item("image.png")  # Steg 3: Klicka på item i inventory
            time.sleep(0.5)
            click_at_percentage(0.75, 0.765)  # Steg 4: Klicka 70% från vänster, 70% ned
            time.sleep(0.5)
            click_at_percentage(0.5, 0.5)  # Klicka i mitten av skärmen
            time.sleep(6)
            click_at_percentage(0.5, 0.5)
        time.sleep(1)  # Valfri paus mellan iterationer för att undvika överbelastning
