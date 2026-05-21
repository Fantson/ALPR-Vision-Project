import cv2
import numpy as np
import os
import sys

def load_templates(templates_folder):
    templates = {}
    if not os.path.exists(templates_folder):
        return templates

    for filename in os.listdir(templates_folder):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            char_name = filename.split('.')[0]
            path = os.path.join(templates_folder, filename)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            _, binary_template = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            templates[char_name] = binary_template
            
    return templates

def segment_characters(binary_plate):
    contours, _ = cv2.findContours(binary_plate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    char_boxes = []
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        area = w * h
        if 800 < area < 20000 and 0.25 < aspect_ratio < 1.3:
            char_boxes.append((x, y, w, h))
            
    char_boxes = sorted(char_boxes, key=lambda b: b[0])
    characters = []
    for (x, y, w, h) in char_boxes:
        char_img = binary_plate[y:y+h, x:x+w]
        characters.append(char_img)
        
    return characters, char_boxes

def recognize_characters(characters, templates):
    recognized_text = ""
    for char_img in characters:
        best_match = "?"
        best_score = -1
        standard_size = (40, 80)
        char_resized = cv2.resize(char_img, standard_size)
        
        for char_name, template_img in templates.items():
            template_resized = cv2.resize(template_img, standard_size)
            result = cv2.matchTemplate(char_resized, template_resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_score:
                best_score = max_val
                best_match = char_name
                
        if best_score > 0.3:
            recognized_text += best_match
            
    return recognized_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("BLAD_ARGUMENTU")
        sys.exit(1)
        
    sciezka_do_obrazka = sys.argv[1]
    templates = load_templates("szablony")
    binary_plate = cv2.imread(sciezka_do_obrazka, cv2.IMREAD_GRAYSCALE)
    
    if binary_plate is not None:
        binary_plate = cv2.bitwise_not(binary_plate)
        chars_images, boxes = segment_characters(binary_plate)
        
        if len(chars_images) > 0 and len(templates) > 0:
            tekst = recognize_characters(chars_images, templates)
            print(tekst) # DRUKUJE TYLKO WYNIK
        else:
            print("BRAK_ZNAKOW")
    else:
        print("BLAD_OBRAZKA")