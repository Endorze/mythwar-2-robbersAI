import pygetwindow as gw
import pyautogui
import cv2
import numpy as np
import pytesseract
import time
import random

# 🔹 1. Hämta spelets fönster
window_title = "[mountasi2] Myth War II Online( ENGLISH version 1.0.3 - 6137 )"
window = gw.getWindowsWithTitle(window_title)[0]

win_x, win_y = window.left, window.top
win_width, win_height = window.width, window.height

print(f"Spelets fönster: X={win_x}, Y={win_y}, Bredd={win_width}, Höjd={win_height}")

# 🔹 2. OCR - Läs av spelarens koordinater från spelet
import re

import re

import re

def get_player_position():
    """Läser spelarens X, Y-koordinater från spelets UI med en bredare OCR-region."""

    # 🔹 Öka OCR-regionen i bredd för att säkerställa att Y alltid fångas
    region_x1, region_y1 = win_x + 640, win_y + 50  # Startposition
    region_width, region_height = 55, 40  # Bredd ökad från 40px → 55px

    # Ta skärmdump av området där koordinaterna syns
    screenshot = pyautogui.screenshot(region=(region_x1, region_y1, region_width, region_height))
    img = np.array(screenshot)

    # 🔹 Konvertera till gråskala
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 🔹 Tydligare siffror med thresholding
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    # 🔹 Förstora bilden för bättre OCR-läsning
    binary = cv2.resize(binary, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)

    # 🔹 Brusreducering
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.medianBlur(binary, 3)

    # 🔹 Spara bild för debugging
    cv2.imwrite("ocr_debug.png", binary)

    # 🔹 OCR-inställningar: Endast siffror och kommatecken
    ocr_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,'
    position_text = pytesseract.image_to_string(binary, config=ocr_config)
    position_text = position_text.strip().replace("\n", "").replace(" ", "")

    print(f"OCR resultat: '{position_text}'")  # Debug

    try:
        # 🔹 Leta strikt efter X,Y-formatet
        match = re.match(r'(\d{1,3}),(\d{2,3})', position_text)  # Ser till att Y alltid har 2-3 siffror
        
        if match:
            x_pos, y_pos = int(match.group(1)), int(match.group(2))
        else:
            raise ValueError("OCR kunde inte identifiera ett giltigt X,Y-format.")

        # 🔹 Kontrollera att X och Y är inom giltiga gränser
        if 0 <= x_pos <= 150 and 0 <= y_pos <= 300:
            return x_pos, y_pos
        else:
            print(f"Felaktiga koordinater: {x_pos}, {y_pos} - Justerar automatiskt")
            x_pos = max(0, min(150, x_pos))
            y_pos = max(0, min(300, y_pos))
            return x_pos, y_pos

    except ValueError:
        print(f"OCR misslyckades, hittade: '{position_text}'")
        return None



# 🔹 3. Lista med waypoints (koordinater att följa)
route = [
    (40, 100),   # Gå till mitten av kartan
    (50, 150),  # Gå till höger
    (120, 200), # Gå neråt
    (40, 200),  # Gå till vänster
    (40, 50)    # Tillbaka till startpunkten
]

# 🔹 4. Flytta kameran i rätt riktning istället för att klicka på en exakt plats
def move_camera(direction, distance=100):
    """Flyttar kameran genom att klicka i rätt riktning med justerad rörelsestorlek."""
    center_x = win_x + win_width // 2  # Skärmens mittpunkt X
    center_y = win_y + win_height // 2  # Skärmens mittpunkt Y

    if direction == "UP":
        click_x, click_y = center_x, center_y - distance
    elif direction == "DOWN":
        click_x, click_y = center_x, center_y + distance
    elif direction == "LEFT":
        click_x, click_y = center_x - distance, center_y
    elif direction == "RIGHT":
        click_x, click_y = center_x + distance, center_y
    else:
        return  # Ogiltig riktning, gör inget

    pyautogui.moveTo(click_x, click_y, duration=0.3)  # Smidigare rörelse
    pyautogui.click()
    print(f"Klickar för att flytta {direction} med {distance}px")


# 🔹 5. Gå mot målet och klicka åt rätt håll
def move_to_target(target_x, target_y):
    """Flyttar kameran mot en given X, Y-koordinat i spelet."""
    while True:
        player_position = get_player_position()
        if not player_position:
            time.sleep(1)
            continue

        player_x, player_y = player_position
        print(f"Nuvarande position: ({player_x}, {player_y}), Målet: ({target_x}, {target_y})")

        if abs(player_x - target_x) <= 2 and abs(player_y - target_y) <= 2:
            print("Mål nått! Stannar.")
            break

        # Om långt från målet, gör större rörelse (100px), annars mindre (50px)
        movement_size = 100 if abs(player_x - target_x) > 10 or abs(player_y - target_y) > 10 else 50

        if abs(player_x - target_x) > abs(player_y - target_y):
            direction = "RIGHT" if target_x > player_x else "LEFT"
        else:
            direction = "DOWN" if target_y > player_y else "UP"

        move_camera(direction, distance=movement_size)
        time.sleep(1.5)  # Ge spelet tid att justera sig innan nästa klick


# 🔹 6. Loopa igenom alla punkter och repetera
while True:
    for coord in route:
        target_x, target_y = coord
        move_to_target(target_x, target_y)
        time.sleep(1)  
