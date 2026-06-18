import subprocess
import os
from difflib import SequenceMatcher

def podobienstwo_znakow(prawdziwy, odczytany):
    return SequenceMatcher(None, prawdziwy, odczytany).ratio() * 100

def dystans_levenshteina(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for index2, char2 in enumerate(s2):
        new_distances = [index2 + 1]
        for index1, char1 in enumerate(s1):
            if char1 == char2:
                new_distances.append(distances[index1])
            else:
                new_distances.append(1 + min((distances[index1], distances[index1 + 1], new_distances[-1])))
        distances = new_distances
    return distances[-1]

def napraw_format_tablicy(tekst):
    if not tekst or len(tekst) < 4:
        return tekst
    
        
    wymus_litery = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '7': 'Z'}
    wymus_cyfry = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8', 'P': 'R'}
    
    ile_liter_z_przodu = 3 if len(tekst) == 8 else 2
    
    naprawiony = ""
    for i, znak in enumerate(tekst):
        if i < ile_liter_z_przodu:
            naprawiony += wymus_litery.get(znak, znak)
        else:
            naprawiony += znak
                
    if len(naprawiony) > 8:
        naprawiony = naprawiony[:8]
        
    return naprawiony

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
        
    with open(plik_txt, 'r', encoding='utf-8') as f:
        lista_tablic = [linia.strip() for linia in f.readlines() if linia.strip()]
        
    liczba_testow = len(lista_tablic)
    poprawne_szablony = 0
    poprawne_tesseract = 0
    jeden_blad_szablony = 0
    jeden_blad_tesseract = 0
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
            
        surowy_szablony = uruchom_skrypt("XD.py", sciezka_pliku)
        surowy_tesseract = uruchom_skrypt("tesseract_test.py", sciezka_pliku)
        
        wynik_szablony = napraw_format_tablicy(surowy_szablony)
        wynik_tesseract = napraw_format_tablicy(surowy_tesseract)
        
        if prawdziwa_tablica == wynik_szablony: 
            poprawne_szablony += 1
        elif dystans_levenshteina(prawdziwa_tablica, wynik_szablony) == 1:
            jeden_blad_szablony += 1
            
        podobie_szablony += podobienstwo_znakow(prawdziwa_tablica, wynik_szablony)
        
        if prawdziwa_tablica == wynik_tesseract: 
            poprawne_tesseract += 1
        elif dystans_levenshteina(prawdziwa_tablica, wynik_tesseract) == 1:
            jeden_blad_tesseract += 1
            
        podobie_tesseract += podobienstwo_znakow(prawdziwa_tablica, wynik_tesseract)
        
        print(f"{i:02d}_image | {prawdziwa_tablica:<10} | {wynik_szablony:<20} | {wynik_tesseract}")
        
    print("\n" + "=" * 70)
    print("                 RAPORT KOŃCOWY")
    print("=" * 70)
    
    print("--- ŚCIEŻKA 1: KLASYCZNA WIZJA KOMPUTEROWA (SZABLONY) ---")
    print(f"Tablice odczytane idealnie (0 błędów):    {(poprawne_szablony / liczba_testow) * 100:.2f}%")
    print(f"Skuteczność praktyczna (MAX 1 błąd):      {((poprawne_szablony + jeden_blad_szablony) / liczba_testow) * 100:.2f}%")
    print(f"Skuteczność pojedynczych znaków (Char):   {(podobie_szablony / liczba_testow):.2f}%")
    
    print("\n--- ŚCIEŻKA 2: MODEL REFERENCYJNY (TESSERACT OCR) ---")
    print(f"Tablice odczytane idealnie (0 błędów):    {(poprawne_tesseract / liczba_testow) * 100:.2f}%")
    print(f"Skuteczność praktyczna (MAX 1 błąd):      {((poprawne_tesseract + jeden_blad_tesseract) / liczba_testow) * 100:.2f}%")
    print(f"Skuteczność pojedynczych znaków (Char):   {(podobie_tesseract / liczba_testow):.2f}%")
    print("=" * 70)