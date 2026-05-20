import cv2
import pytesseract

# ==========================================
# KONFIGURACJA ŚCIEŻKI DO TESSERACTA (Tylko Windows!)
# Jeśli zainstalowałeś Tesseracta w innym miejscu, zmień ten folder.
# Na Linux/Mac zazwyczaj można tę linijkę zakomentować.
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def rozpoznaj_tesseract(sciezka_do_obrazka):
    # Wczytanie zbinaryzowanego obrazka z pre-processingu
    img = cv2.imread(sciezka_do_obrazka)
    
    if img is None:
        print(f"BŁĄD: Nie można wczytać pliku {sciezka_do_obrazka}!")
        return

    # ==========================================
    # KONFIGURACJA SILNIKA OCR
    # --psm 7: Traktuj obraz jako pojedynczą linię tekstu (idealne dla tablic)
    # -c tessedit_char_whitelist: Wymuszamy TYLKO wielkie litery i cyfry
    # ==========================================
    konfiguracja = r'--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    # Odpalenie OCR na obrazku
    tekst = pytesseract.image_to_string(img, config=konfiguracja)
    
    return tekst.strip() # .strip() usuwa niepotrzebne spacje i entery na końcu

# ==========================================
# GŁÓWNA CZĘŚĆ SKRYPTU
# ==========================================
if __name__ == "__main__":
    # Tesseract działa na dokładnie tym samym obrazku co metoda szablonów
    plik_wejsciowy = "preprocessed_plates/1_image.png"
    
    print("Uruchamianie Tesseract OCR...")
    wynik = rozpoznaj_tesseract(plik_wejsciowy)
    
    if wynik:
        print(f"--- WYNIK TESSERACT OCR ---")
        print(f"Odczytano: {wynik}")
    else:
        print("Tesseract nic nie odczytał. Obrazek może być za bardzo zamazany.")