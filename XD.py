import cv2
import numpy as np
import os

# ==========================================
# 1. Wczytywanie szablonów z folderu
# ==========================================
def load_templates(templates_folder):
    """
    Wczytuje obrazki szablonów z podanego folderu.
    Oczekuje plików o nazwach np. 'A.jpg', '1.jpg'.
    """
    templates = {}
    if not os.path.exists(templates_folder):
        print(f"BŁĄD: Utwórz folder '{templates_folder}' i wrzuć tam wycięte litery/cyfry!")
        return templates

    for filename in os.listdir(templates_folder):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            char_name = filename.split('.')[0] # Pobiera literę z nazwy pliku
            path = os.path.join(templates_folder, filename)
            
            # Wczytujemy szablon i od razu robimy z niego czarno-biały (binarny)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            _, binary_template = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            templates[char_name] = binary_template
            
    return templates

# ==========================================
# 2. Segmentacja - Wycinanie znaków z tablicy
# ==========================================
def segment_characters(binary_plate):
    """
    Znajduje kontury na tablicy, filtruje śmieci (naklejki) i zwraca 
    posortowane wycinki znaków (od lewej do prawej).
    """
    # Znajdowanie konturów (RETR_EXTERNAL bierze tylko zewnętrzne obrysy)
    contours, _ = cv2.findContours(binary_plate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    char_boxes = []
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        area = w * h
        
        # FILTROWANIE: Polskie znaki są przeważnie wysokie i wąskie (proporcje ok. 0.2 - 0.8)
        # Odrzucamy mikroskopijne plamki (szum) i naklejki legalizacyjne
        if 500 < area < 15000 and 0.2 < aspect_ratio < 0.9:
            char_boxes.append((x, y, w, h))
            
    # Sortowanie znaków od lewej do prawej (po współrzędnej X)
    char_boxes = sorted(char_boxes, key=lambda b: b[0])
    
    characters = []
    for (x, y, w, h) in char_boxes:
        char_img = binary_plate[y:y+h, x:x+w]
        characters.append(char_img)
        
    return characters, char_boxes

# ==========================================
# 3. Template Matching (Ruchome okno)
# ==========================================
def recognize_characters(characters, templates):
    """
    Porównuje wycięte znaki z szablonami i zwraca odczytany tekst.
    """
    recognized_text = ""
    
    for char_img in characters:
        best_match = "?"
        best_score = -1
        
        # Zmieniamy rozmiar wyciętego znaku do standardowego rozmiaru (np. 40x80)
        # Żeby Template Matching działał, obraz i szablon muszą mieć ten sam rozmiar!
        standard_size = (40, 80)
        char_resized = cv2.resize(char_img, standard_size)
        
        for char_name, template_img in templates.items():
            template_resized = cv2.resize(template_img, standard_size)
            
            # Przesuwanie okna - cv2.matchTemplate (porównywanie piksel po pikselu)
            result = cv2.matchTemplate(char_resized, template_resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            # Jeśli wynik dopasowania jest lepszy niż poprzedni, zapisujemy go
            if max_val > best_score:
                best_score = max_val
                best_match = char_name
                
        # Jeśli dopasowanie ma sensowny wynik (powyżej 50%), dodajemy do tekstu
        if best_score > 0.5:
            recognized_text += best_match
            
    return recognized_text

# ==========================================
# GŁÓWNA CZĘŚĆ SKRYPTU
# ==========================================
if __name__ == "__main__":
    # 1. Ładowanie szablonów
    # (Pamiętaj o stworzeniu folderu 'szablony' i dorzuceniu kilku wyciętych liter!)
    templates = load_templates("szablony")
    
    # 2. Wczytanie TWOJEGO zbinaryzowanego obrazka
    # Zmieniona nazwa pliku na Twoją
    binary_plate = cv2.imread("preprocessed_plates/3_image.png", cv2.IMREAD_GRAYSCALE)
    
    if binary_plate is not None:
        # ODWRÓCENIE KOLORÓW - To jest kluczowe dla Twojego zdjęcia!
        # Zmieniamy czarne litery na białe, żeby findContours je znalazło
        binary_plate = cv2.bitwise_not(binary_plate)

        # 3. Wycięcie znaków
        chars_images, boxes = segment_characters(binary_plate)
        
        if len(chars_images) > 0 and len(templates) > 0:
            # 4. Rozpoznawanie
            tekst = recognize_characters(chars_images, templates)
            print(f"--- WYNIK ROZPOZNANIA (Metoda Szablonów) ---")
            print(f"Odczytano: {tekst}")
        else:
            print("Brak szablonów lub nie wykryto żadnych liter. Sprawdź filtry w kodzie.")