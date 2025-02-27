import pygetwindow as gw
import pyautogui
import cv2
import numpy as np
import pytesseract
import time
import random
import keyboard  # 🔹 För att lyssna på F5
import re

from good_robber_farmer import search_and_click_robber

# 🔹 1. Hämta spelets fönster
window_title = "[mountasi2] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"
window = gw.getWindowsWithTitle(window_title)[0]

win_x, win_y = window.left, window.top
win_width, win_height = window.width, window.height

print(f"Spelets fönster: X={win_x}, Y={win_y}, Bredd={win_width}, Höjd={win_height}")

# 🔹 Variabel för att styra pausfunktion
paused = False

# 🔹 2. Funktion för att pausa/starta botten med F5
def toggle_pause():
    global paused
    paused = not paused
    if paused:
        print("🛑 Pausad! Tryck F5 igen för att fortsätta.")
    else:
        print("▶️ Fortsätter!")

# 🔹 Lyssna efter F5 för att pausa/fortsätta
keyboard.add_hotkey("f5", toggle_pause)


def get_npc_positions():
    """Läser av NPC-namn från skärmen och returnerar positioner där vi bör undvika att klicka."""
    
    # 🔹 Hämta en större skärmdump där NPC-namn syns
    full_screenshot = pyautogui.screenshot(region=(win_x, win_y, win_width, win_height))
    img = np.array(full_screenshot)

    # 🔹 Konvertera till HSV för att identifiera gula textfärger
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # 🔹 Färggränser för gul text (NPC-namn)
    lower_yellow = np.array([25, 200, 200])  # Justerat för att fånga F8FC00
    upper_yellow = np.array([35, 255, 255])

    # 🔹 Skapa mask för gul färg
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # 🔹 Applicera masken
    filtered_img = cv2.bitwise_and(img, img, mask=mask_yellow)

    # 🔹 Konvertera till gråskala och binärbild
    gray = cv2.cvtColor(filtered_img, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    # 🔹 Förstora texten för bättre OCR-läsning
    binary = cv2.resize(binary, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)

    # 🔹 Ta bort brus och spara bild för debugging
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.medianBlur(binary, 3)
    cv2.imwrite("npc_debug.png", binary)

    # 🔹 OCR-inställningar
    ocr_config = r'--oem 3 --psm 6'
    text_data = pytesseract.image_to_string(binary, config=ocr_config)

    # 🔹 Hitta NPC-positioner där namn är synliga
    npc_positions = []
    for i, line in enumerate(text_data.split("\n")):
        line = line.strip().lower()
        if "robber" in line:  # 🔹 Endast NPC:er med "robber" är godkända
            continue  # Ignorera dessa

        # 🔹 Skapa en "förbjuden zon" runt NPC
        y_pos = win_y + (i * 25)  # Ungefärlig Y-position baserat på textens rad
        npc_positions.append(y_pos)

    print(f"📛 Förbjudna områden (NPC): {npc_positions}")
    return npc_positions


# 🔹 3. OCR - Läs av spelarens koordinater från spelet
def get_player_position():
    """Läser spelarens X, Y-koordinater från spelets UI med färgfiltrering.
       Om OCR misslyckas, klickar den en gång söderut för att justera positionen.
    """

    # 🔹 Exakt OCR-region
    region_x1, region_y1 = win_x + 640, win_y + 50
    region_width, region_height = 55, 40

    # Ta skärmdump av området
    screenshot = pyautogui.screenshot(region=(region_x1, region_y1, region_width, region_height))
    img = np.array(screenshot)

    # 🔹 Konvertera till HSV (bättre för färgfiltrering)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # 🔹 Definiera färggränser för vitgrå (E0E4E0) och gul (F8FC00)
    lower_white = np.array([0, 0, 224])  
    upper_white = np.array([180, 20, 255])

    lower_yellow = np.array([25, 200, 200])  
    upper_yellow = np.array([35, 255, 255])

    # 🔹 Skapa mask för att behålla endast dessa färger
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # 🔹 Kombinera maskerna
    mask = cv2.bitwise_or(mask_white, mask_yellow)

    # 🔹 Applicera masken på originalbilden
    filtered_img = cv2.bitwise_and(img, img, mask=mask)

    # 🔹 Konvertera till gråskala och binärbild
    gray = cv2.cvtColor(filtered_img, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    # 🔹 Förstora och förbättra texten
    binary = cv2.resize(binary, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.medianBlur(binary, 3)

    # 🔹 Spara debug-bild för att granska filtreringen
    cv2.imwrite("ocr_debug.png", binary)

    # 🔹 OCR-inställningar
    ocr_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,'
    position_text = pytesseract.image_to_string(binary, config=ocr_config).strip().replace("\n", "").replace(" ", "")

    print(f"OCR resultat: '{position_text}'")  # Debug

    try:
        match = re.match(r'(\d{1,3}),(\d{2,3})', position_text)
        if match:
            x_pos, y_pos = int(match.group(1)), int(match.group(2))
        else:
            raise ValueError("OCR kunde inte identifiera ett giltigt X,Y-format.")

        if 0 <= x_pos <= 150 and 0 <= y_pos <= 300:
            return x_pos, y_pos
        else:
            print(f"Felaktiga koordinater: {x_pos}, {y_pos} - Justerar automatiskt")
            return max(0, min(150, x_pos)), max(0, min(300, y_pos))

    except ValueError:
        print(f"❌ OCR misslyckades! Klickar söderut för att justera positionen...")
        move_camera("DOWN")  # 🔹 Klickar söderut en gång
        time.sleep(1)  # Väntar innan nästa OCR-försök
        return None



    try:
        match = re.match(r'(\d{1,3}),(\d{2,3})', position_text)  # Säkerställer rätt format
        if match:
            x_pos, y_pos = int(match.group(1)), int(match.group(2))
        else:
            raise ValueError("OCR kunde inte identifiera ett giltigt X,Y-format.")

        if 0 <= x_pos <= 150 and 0 <= y_pos <= 300:
            return x_pos, y_pos
        else:
            print(f"Felaktiga koordinater: {x_pos}, {y_pos} - Justerar automatiskt")
            return max(0, min(150, x_pos)), max(0, min(300, y_pos))

    except ValueError:
        print(f"OCR misslyckades, hittade: '{position_text}'")
        return None

# 🔹 4. Lista med waypoints (koordinater att följa)
route = [
    (40, 100),
    (50, 130),
    (40, 170),
    (40, 220),
    (60, 260),
    (90, 260),
    (90, 260),
    (110, 225),
    (105, 179),
    (84, 146),
    (95, 95),
    (60, 93),
]

# 🔹 5. Flytta kameran i rätt riktning istället för att klicka på en exakt plats
def move_camera(direction):
    """Flyttar kameran genom att klicka 40% av skärmens storlek bort från mitten i rätt riktning,
       men undviker att klicka nära NPC-zoner (gula namn som inte innehåller 'robber')."""
    global paused
    if paused:
        return  # Gör inget om spelet är pausat

    center_x = win_x + win_width // 2
    center_y = win_y + win_height // 2

    move_x = int(win_width * 0.3)  # 30% av skärmens bredd
    move_y = int(win_height * 0.3)  # 30% av skärmens höjd

    if direction == "UP":
        click_x, click_y = center_x, center_y - move_y
    elif direction == "DOWN":
        click_x, click_y = center_x, center_y + move_y
    elif direction == "LEFT":
        click_x, click_y = center_x - move_x, center_y
    elif direction == "RIGHT":
        click_x, click_y = center_x + move_x, center_y
    else:
        return

    # 🔹 Hämta NPC-positioner för att undvika dem
    npc_positions = get_npc_positions()

    # 🔹 Om det finns NPC-zoner, kontrollera att vi inte klickar nära en NPC
    for npc_y in npc_positions:
        if abs(click_y - npc_y) < 50:  # Om vi är inom 50px från en NPC
            print("⚠️ Förbjuden zon upptäckt nära! Justerar klick...")
            # Flytta bort från NPC, men håll klicket inom spelfönstret
            if direction == "DOWN":
                click_y = min(click_y + 60, win_y + win_height - 5)  # Justera nedåt om möjligt
            elif direction == "UP":
                click_y = max(click_y - 60, win_y + 5)  # Justera uppåt om möjligt

    # 🔹 Se till att klicket håller sig inom spelfönstret
    click_x = max(win_x + 5, min(click_x, win_x + win_width - 5))
    click_y = max(win_y + 5, min(click_y, win_y + win_height - 5))

    pyautogui.moveTo(click_x, click_y, duration=0.3)
    pyautogui.click()
    print(f"Klickar för att flytta {direction} med 30% av skärmen ({move_x}px, {move_y}px)")



# 🔹 6. Gå mot målet och klicka åt rätt håll
def move_to_target(target_x, target_y):
    """Flyttar kameran mot en given X, Y-koordinat i spelet med tolerans på ±30."""
    global paused
    while True:
        if paused:
            time.sleep(0.5)
            continue  # Vänta om spelet är pausat

        player_position = get_player_position()
        if not player_position:
            time.sleep(1)
            continue

        player_x, player_y = player_position
        print(f"Nuvarande position: ({player_x}, {player_y}), Målet: ({target_x}, {target_y})")

        # 🔹 Tolerans: Om X är inom ±30 och Y är inom ±30, räknas målet som uppnått
        if abs(player_x - target_x) <= 30 and abs(player_y - target_y) <= 30:
            print("✅ Mål nått (inom 30 pixlar)! Går vidare till nästa punkt.")
            break  # Gå vidare till nästa mål i listan

        if abs(player_x - target_x) > abs(player_y - target_y):
            direction = "RIGHT" if target_x > player_x else "LEFT"
        else:
            direction = "DOWN" if target_y > player_y else "UP"

        move_camera(direction)  # 🔹 Tar bort argumentet 'distance'
        time.sleep(1.5)



# 🔹 7. Loopa igenom alla punkter och repetera
if __name__ == "__main__":
    while True:
        for coord in route:
            if paused:
                time.sleep(0.5)
                continue  # Vänta om spelet är pausat

            target_x, target_y = coord
            move_to_target(target_x, target_y)

            time.sleep(1)
            found_robber = search_and_click_robber()

            print("Found robber: ", found_robber)

            if found_robber:
                time.sleep(20)
