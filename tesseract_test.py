import sys

import cv2
import pytesseract

if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def rozpoznaj_tesseract(sciezka_do_obrazka):
    img = cv2.imread(sciezka_do_obrazka)
    if img is None:
        return "BLAD_OBRAZKA"

    konfiguracja = (
        r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    tekst = pytesseract.image_to_string(img, config=konfiguracja)

    return tekst.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("BLAD_ARGUMENTU")
        sys.exit(1)

    sciezka_do_obrazka = sys.argv[1]
    wynik = rozpoznaj_tesseract(sciezka_do_obrazka)

    if wynik:
        print(wynik)
    else:
        print("PUSTO")
