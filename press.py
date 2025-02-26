import keyboard
import time

def type_23():
    time.sleep(2)
    keyboard.send('backspace')
    keyboard.press('backspace')
    time.sleep(0.2)
    keyboard.send('backspace')  # För säkerhets skull, radera en extra gång
    time.sleep(0.5)  # Ge tid för fältet att uppdateras
    keyboard.write("23")

if __name__ == "__main__":
    type_23()