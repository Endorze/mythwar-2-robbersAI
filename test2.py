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
clicked_robber = False  # Om detta är True, flytta musen till mitten efteråt

def get_game_window():
    """ Hitta spelrutans position och storlek på skärmen. """
    for window in gw.getWindowsWithTitle("[mountasi] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"):  
        if window.isActive:
            return window.left, window.top, window.width, window.height
    return None

def activate_game_window():
    """ Gör spelets fönster aktivt innan vi klickar. """
    game_window = gw.getWindowsWithTitle("[mountasi] Myth War II Online( ENGLISH version 1.0.3 - 6137 )")
    if game_window:
        game_window[0].activate()
        time.sleep(0.3)  # Ge spelet en kort tid att aktiveras

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
    """ Behåller endast gul text, gör allt annat svart. """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 🔹 Färgfilter för gul text (Robber)
    lower_yellow = np.array([22, 150, 150])
    upper_yellow = np.array([35, 255, 255])

    # Skapa mask för att endast behålla gul text
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # 🔹 Gör gul text svart och allt annat svart
    result = cv2.bitwise_and(image, image, mask=mask_yellow)

    # 🔹 Konvertera texten till svart på vit bakgrund
    result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    result = cv2.bitwise_not(result)

    return result

def detect_robber_text(image, game_position):
    """ Använder Tesseract för att identifiera texten 'Robber', klickar på den och aktiverar efterföljande klick i mitten. """
    global clicked_robber  

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
            click_y = game_position[1] + y + h + 20

            # 🔹 Aktivera spelets fönster innan klick
            activate_game_window()

            # 🔹 Flytta musen och klicka
            pyautogui.moveTo(click_x, click_y, duration=0.2)
            pyautogui.mouseDown()
            time.sleep(0.05)  # Håll nere klicket kort
            pyautogui.mouseUp()

            print(f"✅ Klickade på '{text}' vid ({click_x}, {click_y})")

            time.sleep(1)  # Vänta 1 sekund innan vi rör oss mot mitten av skärmen
            clicked_robber = True  # Aktivera flaggan för nästa klick
            return  

    print("❌ OCR hittade ingen 'Robber'-text.")

def click_middle_screen(game_position):
    """ Flyttar musen till mitten och 50% av höjden och klickar efter 0.5 sekunder. """
    global clicked_robber

    if not clicked_robber:
        return  # Om vi inte klickade på en Robber, gör inget

    _, _, game_w, game_h = game_position  # Hämta spelrutans storlek

    # 🔹 Beräkna mitten av bredden och 50% av höjden
    click_x = game_position[0] + game_w // 2
    click_y = game_position[1] + int(game_h * 0.50)

    # 🔹 Aktivera spelet innan klick
    activate_game_window()

    # 🔹 Flytta musen till mitten och vänta 0.5 sekunder innan klick
    pyautogui.moveTo(click_x, click_y, duration=0.2)
    time.sleep(0.5)  # Vänta innan klick

    # 🔹 Klicka
    pyautogui.mouseDown()
    time.sleep(0.05)  # Håll nere klicket kort
    pyautogui.mouseUp()

    print(f"✅ Klickade 50% ner på skärmen vid ({click_x}, {click_y})")

    time.sleep(0.3)  
    clicked_robber = False  # Återställ flaggan så att vi letar efter en ny "Robber"

# 🔹 Kör loopen för att leta efter Robber, sedan klicka 50% ner om vi har tryckt på en Robber
while True:
    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        if clicked_robber:
            print("🔍 Flyttar mot 50% av skärmen och klickar...")
            click_middle_screen(game_position)
        else:
            print("🔍 Letar efter 'Robber'...")
            detect_robber_text(screenshot, game_position)
    
    time.sleep(1)  
