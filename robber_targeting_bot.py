import cv2
import numpy as np
import pyautogui
import pytesseract
import pygetwindow as gw
import time

# 🔹 Ange sökvägen till Tesseract om det behövs (Windows-användare)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔹 Lista över felstavningar som ska accepteras
ROBBER_VARIANTS = ["robber", "rober", "r0bber", "r0ber", "robbr", "robbr"]

def get_game_window():
    """ Hitta spelrutans position och storlek på skärmen. """
    for window in gw.getWindowsWithTitle("[mountasi] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):  # Ändra "SPELNAME" till ditt spelnamn
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
    screenshot = pyautogui.screenshot(region=(x, y, w, h))  # Fånga bara spelets fönster
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return screenshot, (x, y)

def filter_yellow_text(image):
    """ Hittar gul text och gör den svart, medan allt annat blir vitt. """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 🔹 Justera dessa värden om det behövs!
    lower_yellow = np.array([22, 150, 150])  # Lägre gräns för illgul
    upper_yellow = np.array([35, 255, 255]) 

    # Skapa en mask där endast gul text behålls
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Konvertera texten till svart och resten till vitt
    result = cv2.bitwise_not(mask)
    return result

def detect_robber_text(image, game_position):
    """ Använder Tesseract för att identifiera texten 'Robber' och klicka på rätt plats. """
    processed_image = filter_yellow_text(image)

    # 🔹 Visa den filtrerade bilden för debug
    cv2.imshow("Filtrerad Gul Text", processed_image)
    cv2.waitKey(500)  # Visa i 0.5 sekunder
    cv2.destroyAllWindows()

    # 🔹 Använd OCR för att läsa texten
    data = pytesseract.image_to_data(processed_image, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)

    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        if any(variant in text for variant in ROBBER_VARIANTS):  # Leta efter varianter av "Robber"
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

            # 🔹 Justera klickpositionen (20 pixlar under texten)
            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 20

            # 🔹 Flytta musen och klicka
            pyautogui.moveTo(click_x, click_y)
            pyautogui.click()

            print(f"✅ Klickade på '{text}' vid ({click_x}, {click_y})")
            time.sleep(0.3)  # Vänta lite mellan varje klick
            return  # Sluta efter första klicket

    print("❌ OCR hittade ingen 'Robber'-text.")

# 🔹 Kör loopen för att leta efter Robber
while True:
    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        detect_robber_text(screenshot, game_position)
    time.sleep(1)  # Vänta 1 sekund innan nästa skanning
