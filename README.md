# Automatyczne Rozpoznawanie Tablic Rejestracyjnych (ALPR)

**Projekt zrealizowany w ramach przedmiotu Wizja Komputerowa.**

**Zespół projektowy:**
* Łukasz Pachla (Lider zespołu, Baza danych)
* Damian Pietryka (Pre-processing, OpenCV)
* Przemysław Potoczny (Model referencyjny Tesseract, Metryki)
* Jakub Reczko (Segmentacja, OCR za pomocą szablonów)

##  Krótki opis projektu
Celem projektu jest stworzenie systemu do odczytu numerów rejestracyjnych z polskich, białych tablic. System wykorzystuje klasyczne metody wizji komputerowej (OpenCV). Zamiast automatycznej detekcji całego auta, zastosowano interaktywne zaznaczanie narożników tablicy. 

**Główne etapy działania potoku (pipeline):**
1. Interaktywna lokalizacja i transformacja perspektywiczna (Warping do 540x114 px).
2. Pre-processing: Konwersja do skali szarości, wyrównanie kontrastu (CLAHE), rozmycie Gaussa i binaryzacja Otsu.
3. Ekstrakcja znaków (analiza konturów).
4. Rozpoznawanie znaków (własny algorytm dopasowywania szablonów oraz model referencyjny Tesseract OCR).

##  Instrukcja instalacji zależności

Projekt wymaga środowiska Python w wersji 3.11 lub 3.12.

1. Sklonuj repozytorium:
   ```bash
   git clone [https://github.com/Fantson/ALPR-Vision-Project.git](https://github.com/Fantson/ALPR-Vision-Project.git)
   cd ALPR-Vision-Project
   ```
2. Utwórz i aktywuj środowisko wirtualne:
    ```bash
    python -m venv venv
    # Aktywacja na Windows:
    venv\Scripts\activate
    ```
3. Zainstaluj wymagane biblioteki:
    ```bash
    pip install -r requirements.txt
    ```
4. Ważne dla systemu Windows: Projekt wymaga zainstalowanego silnika Tesseract OCR (np. z UB-Mannheim). Upewnij się, że ścieżka do pliku tesseract.exe jest poprawnie ustawiona w kodzie skryptu.

## Instrukcja uruchomienia projektu

Cały potok przetwarzania (pipeline) systemu został podzielony na niezależne moduły realizujące konkretne zadania inżynierskie. Aby uruchomić pełną ścieżkę diagnostyczną i testową, należy wykonać poniższe kroki w podanej kolejności.

Przed uruchomieniem upewnij się, że środowisko wirtualne jest aktywne (`venv\Scripts\activate`).

### Krok 1: Interaktywna transformacja perspektywiczna
Pierwszy moduł służy do ręcznego wskazania pozycji tablicy na surowych zdjęciach samochodów.
1. Umieść oryginalne zdjęcia pojazdów w folderze `car_images/`.
2. Uruchom skrypt transformacji:
   ```bash
   python image_transform.py
   ```
Na ekranie pojawi się okno z pierwszym zdjęciem. Kliknij myszką 4 rogi tablicy rejestracyjnej w dokładnie podanej kolejności:

- TL (Lewy górny)
- TR (Prawy górny)
- BR (Prawy dolny)
- BL (Lewy dolny)

Po kliknięciu czwartego punktu, wciśnij dowolny klawisz, aby program zapisał wyprostowany wycinek (o znormalizowanych wymiarach 520x114 px) do folderu cropped_plates/ i automatycznie przeszedł do kolejnego zdjęcia.

3. Przetwarzanie wstępne (Pre-processing)
Upewnij się, że w folderze cropped_plates/ znajdują się wycięte tablice z Kroku 2.
Uruchom skrypt przetwarzania:
    ```bash
    python preprocessing.py
    ```
Skrypt dokona konwersji do skali szarości, zaaplikuje adaptacyjne wyrównanie histogramu (CLAHE), rozmycie Gaussa oraz binaryzację metodą Otsu. Przeprocesowane czarno-białe obrazy zostaną zapisane w folderze preprocessed_plates/

4. Przygotowanie danych do testów automatycznych
Przed uruchomieniem modułu ewaluacji należy przygotować plik z poprawnymi numerami rejestracyjnymi, które posłużą jako punkt odniesienia do wyliczenia skuteczności (Accuracy).

W głównym katalogu projektu utwórz plik tekstowy o nazwie prawdziwe.txt

Wpisz do niego faktyczne numery rejestracyjne z testowanych pojazdów — każdy numer w nowej linijce, zachowując kolejność plików w folderze preprocessed_plates/ (np. pierwsza linijka odpowiada zdjęciu 1_image.png, druga 2_image.png itd.).

5. Uruchomienie zautomatyzowanej ewaluacji
Główny moduł testowy automatycznie przetestuje obie ścieżki rozpoznawania znaków i wygeneruje zbiorczy raport techniczny.

Upewnij się, że w folderze szablony/ znajdują się wzorcowe pliki znaków dla klasycznego OCR.

Uruchom skrypt ewaluacyjny:
    ```bash
    python evaluate.py
    ```
Program uruchomi równolegle autorski algorytm segmentacji i dopasowania szablonów (ocr_engine.py) oraz model referencyjny (tesseract_test.py) dla każdego zdjęcia.

Na koniec w konsoli wyświetli się szczegółowa tabela porównawcza oraz Raport Końcowy zawierający procent tablic odczytanych w 100% oraz dokładną skuteczność rozpoznawania pojedynczych znaków (Accuracy) dla obu metod.

6. Opcjonalnie: Testowanie pojedynczych obrazów
Jeśli chcesz przetestować działanie samego algorytmu rozpoznawania znaków na konkretnym, pojedynczym pliku bez uruchamiania całego zestawu, możesz przekazać ścieżkę do zdjęcia jako argument w konsoli:

Test autorskiego algorytmu szablonów:
    ```bash
    python ocr_engine.py preprocessed_plates/1_image.png
    ```
Test modelu Tesseract OCR:
    ```bash
    python tesseract_test.py preprocessed_plates/1_image.png
    ```
