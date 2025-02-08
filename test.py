import cv2
import numpy as np
import pyautogui
import pytesseract
import pygetwindow as gw
import time

# 🔹 Ange sökvägen till Tesseract om det behövs (Windows-användare)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔹 Lista över felstavningar som ska accepteras
ROBBER_VARIANTS = ["robber", "rober", "r0bber", "r0ber", "robbr"]
SEARCHING_FOR_CLICK = False  # När detta är True, väntar vi 1 sekund och klickar 55% ner på skärmen

def get_game_window():
    """ Hitta spelrutans position och storlek på skärmen. """
    for window in gw.getWindowsWithTitle("[mountasi] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):  
        if window.isActive:
            return window.left, window.top, window.width, window.height
    return None

def capture_game_screen():
    """ Tar en skärmbild av spelrutan. """
    game_window = get_game_window()
    if not game_window:
        print([w.title for w in gw.getAllWindows()])
        print("❌ Spelet hittades inte! Kontrollera fönsternamnet.")
        return None, None

    x, y, w, h = game_window
    screenshot = pyautogui.screenshot(region=(x, y, w, h))  
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return screenshot, (x, y, w, h)

def filter_text_colors(image):
    """ Behåller endast gul och neongrön text, gör allt annat svart. """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 🔹 Färgfilter för gul text (Robber)
    lower_yellow = np.array([22, 150, 150])
    upper_yellow = np.array([35, 255, 255])

    # 🔹 Färgfilter för neongrön text
    lower_green = np.array([40, 200, 100])
    upper_green = np.array([80, 255, 255])

    # Skapa masker för att endast behålla gul och neongrön
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # Kombinera maskerna
    mask_combined = cv2.bitwise_or(mask_yellow, mask_green)

    # 🔹 Gör gul och neongrön text svart och allt annat svart
    result = cv2.bitwise_and(image, image, mask=mask_combined)

    # 🔹 Konvertera texten till svart på vit bakgrund
    result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    result = cv2.bitwise_not(result)

    return result

def detect_robber_text(image, game_position):
    """ Använder Tesseract för att identifiera texten 'Robber' och klicka på rätt plats. """
    global SEARCHING_FOR_CLICK  

    processed_image = filter_text_colors(image)

    # 🔹 Visa den filtrerade bilden för debug
    cv2.imshow("Filtrerad Text", processed_image)
    cv2.waitKey(500)
    cv2.destroyAllWindows()

    # 🔹 Använd OCR för att läsa texten
    data = pytesseract.image_to_data(processed_image, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)

    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        if any(variant in text for variant in ROBBER_VARIANTS):  
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

            # 🔹 Klicka 20 pixlar under mitten av texten
            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 30

            # 🔹 Flytta musen och klicka
            pyautogui.moveTo(click_x, click_y)
            pyautogui.click()

            print(f"✅ Klickade på '{text}' vid ({click_x}, {click_y})")

            time.sleep(1)  # Vänta 1 sekund innan vi klickar i mitten av skärmen på 55% höjd
            SEARCHING_FOR_CLICK = True
            return  

    print("❌ OCR hittade ingen 'Robber'-text.")

def click_middle_screen(game_position):
    """ Väntar 1 sekund och klickar 55% ner på skärmen i mitten. """
    global SEARCHING_FOR_CLICK

    _, _, game_w, game_h = game_position  # Hämta spelrutans storlek

    # 🔹 Beräkna mitten av bredden och 55% av höjden
    click_x = game_position[0] + game_w // 2
    click_y = game_position[1] + int(game_h * 0.50)

    # 🔹 Flytta musen och klicka
    pyautogui.moveTo(click_x, click_y)
    pyautogui.click()

    print(f"✅ Klickade på mitten av skärmen vid ({click_x}, {click_y})")

    time.sleep(0.3)  
    SEARCHING_FOR_CLICK = False  # Återgå till att leta efter "Robber"

# 🔹 Kör loopen för att leta efter Robber, sedan klicka i mitten av skärmen
while True:
    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        if SEARCHING_FOR_CLICK:
            print("🔍 Klickar 55% ner på skärmen i mitten...")
            click_middle_screen(game_position)
        else:
            print("🔍 Letar efter 'Robber'...")
            detect_robber_text(screenshot, game_position)
    
    time.sleep(1)  
