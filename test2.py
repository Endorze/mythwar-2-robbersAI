import cv2
import numpy as np
import pyautogui
import pytesseract
import pygetwindow as gw
import time
import keyboard  # För att hantera F5-knapp

# 🔹 Ange sökvägen till Tesseract om det behövs (Windows-användare)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔹 Lista över felstavningar som ska accepteras
ROBBER_VARIANTS = ["robber", "rober", "r0bber", "r0ber", "robbr"]
SEARCHING_FOR_CLICK = False  
paused = False  # Styr om skriptet är pausat eller ej

def toggle_pause():
    """ Växlar mellan pausat och aktivt läge. """
    global paused
    paused = not paused
    print("⏸️ Skript pausat. Tryck F5 för att återuppta." if paused else "▶️ Skript återupptas.")

# 🔹 Lyssna på F5-knappen för att pausa/återuppta
keyboard.add_hotkey("f5", toggle_pause)

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

def is_outside_edge_restriction(click_x, click_y, game_position):
    """ Kontrollerar om klicket är **utanför** 10% från kanterna av skärmen. """
    game_x, game_y, game_w, game_h = game_position

    # 🔹 Definiera kanterna (yttersta 10%)
    edge_x_min = game_x + int(game_w * 0.1)  # 10% in från vänster
    edge_x_max = game_x + int(game_w * 0.9)  # 10% in från höger
    edge_y_min = game_y + int(game_h * 0.1)  # 10% in från toppen
    edge_y_max = game_y + int(game_h * 0.9)  # 10% in från botten

    # 🔹 Klickas endast om det är utanför kanterna
    return edge_x_min <= click_x <= edge_x_max and edge_y_min <= click_y <= edge_y_max

def detect_robber_text(image, game_position):
    """ Använder Tesseract för att identifiera texten 'Robber' och klicka om den är utanför kanterna. """
    global SEARCHING_FOR_CLICK  

    processed_image = filter_text_colors(image)

    # 🔹 Använd OCR för att läsa texten snabbare
    data = pytesseract.image_to_data(processed_image, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)

    for i in range(len(data["text"])):
        text = data["text"][i].lower().strip()
        if any(variant in text for variant in ROBBER_VARIANTS):  
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

            # 🔹 Klicka 30 pixlar under mitten av texten
            click_x = game_position[0] + x + w // 2
            click_y = game_position[1] + y + h + 30

            # 🔹 Kontrollera om klicket är **utanför 10% från kanterna**
            if is_outside_edge_restriction(click_x, click_y, game_position):
                # 🔹 Flytta musen och klicka
                pyautogui.moveTo(click_x, click_y)
                time.sleep(0.05)
                pyautogui.click()

                print(f"✅ Klickade på '{text}' vid ({click_x}, {click_y})")

                time.sleep(0.3)  
                SEARCHING_FOR_CLICK = True
                return  
            else:
                print(f"❌ Ignorerar '{text}' vid ({click_x}, {click_y}) - För nära kanten (10%).")

    print("❌ OCR hittade ingen 'Robber'-text utanför kanterna.")

def click_middle_screen(game_position):
    """ Väntar 0.5 sekunder och klickar 52% ner på skärmen i mitten. """
    global SEARCHING_FOR_CLICK

    _, _, game_w, game_h = game_position  # Hämta spelrutans storlek

    # 🔹 Beräkna mitten av bredden och 52% av höjden
    click_x = game_position[0] + game_w // 2
    click_y = game_position[1] + int(game_h * 0.52)

    # 🔹 Flytta musen och klicka
    pyautogui.moveTo(click_x, click_y)
    time.sleep(0.05)
    pyautogui.click()

    print(f"✅ Klickade på mitten av skärmen vid ({click_x}, {click_y})")

    time.sleep(0.2)  
    SEARCHING_FOR_CLICK = False  

# 🔹 Kör loopen för att leta efter Robber, sedan klicka i mitten av skärmen
while True:
    if paused:
        time.sleep(0.1)  # Vänta medan skriptet är pausat
        continue  # Hoppa över resten av loopen

    screenshot, game_position = capture_game_screen()
    if screenshot is not None:
        if SEARCHING_FOR_CLICK:
            print("🔍 Klickar 52% ner på skärmen i mitten...")
            click_middle_screen(game_position)
        else:
            print("🔍 Letar efter 'Robber'...")
            detect_robber_text(screenshot, game_position)
    
    time.sleep(0.05)  # 🔹 Gör sökningen snabbare genom att minska väntetiden
