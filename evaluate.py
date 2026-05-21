import subprocess
import os
from difflib import SequenceMatcher

def podobienstwo_znakow(prawdziwy, odczytany):
    return SequenceMatcher(None, prawdziwy, odczytany).ratio() * 100

def uruchom_skrypt(nazwa_skryptu, sciezka_obrazka):
    try:
        wynik = subprocess.check_output(['python', nazwa_skryptu, sciezka_obrazka], text=True, stderr=subprocess.STDOUT)
        
        linie = wynik.strip().split('\n')
        return linie[-1].strip() if linie else ""
    except subprocess.CalledProcessError:
        return "BLAD_SKRYPTU"

if __name__ == "__main__":
    plik_txt = "prawdziwe.txt"
    
    if not os.path.exists(plik_txt):
        print(f"BŁĄD: Nie znaleziono pliku {plik_txt} z tablicami!")
        exit()
        
    # Wczytanie prawdziwych tablic z pliku .txt
    with open(plik_txt, 'r', encoding='utf-8') as f:
        lista_tablic = [linia.strip() for linia in f.readlines() if linia.strip()]
        
    liczba_testow = len(lista_tablic)
    poprawne_szablony = 0
    poprawne_tesseract = 0
    podobie_szablony = 0
    podobie_tesseract = 0
    
    print(f"Rozpoczynam zautomatyzowane testy dla {liczba_testow} tablic...\n")
    print("-" * 80)
    print(f"{'PLIK':<8} | {'PRAWDZIWA':<10} | {'SZABLONY':<20} | {'TESSERACT'}")
    print("-" * 80)
    
    for i, prawdziwa_tablica in enumerate(lista_tablic, start=1):
        sciezka_pliku = f"preprocessed_plates/{i}_image.png"
        
        if not os.path.exists(sciezka_pliku):
            print(f"{i}_image.png | BRAK PLIKU NA DYSKU")
            continue
            
        wynik_szablony = uruchom_skrypt("XD.py", sciezka_pliku)
        wynik_tesseract = uruchom_skrypt("tesseract_test.py", sciezka_pliku)
        
        if prawdziwa_tablica == wynik_szablony: 
            poprawne_szablony += 1
        podobie_szablony += podobienstwo_znakow(prawdziwa_tablica, wynik_szablony)
        
        if prawdziwa_tablica == wynik_tesseract: 
            poprawne_tesseract += 1
        podobie_tesseract += podobienstwo_znakow(prawdziwa_tablica, wynik_tesseract)
        
        print(f"{i:02d}_image | {prawdziwa_tablica:<10} | {wynik_szablony:<20} | {wynik_tesseract}")
        
    print("\n" + "=" * 50)
    print("                 RAPORT KOŃCOWY")
    print("=" * 50)
    
    print("--- ŚCIEŻKA 1: KLASYCZNA WIZJA KOMPUTEROWA (SZABLONY) ---")
    print(f"Tablice odczytane w 100%: {(poprawne_szablony / liczba_testow) * 100:.2f}%")
    print(f"Skuteczność pojedynczych znaków (Accuracy): {(podobie_szablony / liczba_testow):.2f}%")
    
    print("\n--- ŚCIEŻKA 2: MODEL REFERENCYJNY (TESSERACT OCR) ---")
    print(f"Tablice odczytane w 100%: {(poprawne_tesseract / liczba_testow) * 100:.2f}%")
    print(f"Skuteczność pojedynczych znaków (Accuracy): {(podobie_tesseract / liczba_testow):.2f}%")
    print("=" * 50)