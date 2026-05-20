import cv2
import os

# --- Configuration ---
input_folder = "cropped_plates" 
output_folder = "preprocessed_plates"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Main loop through all cropped plates
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        full_path = os.path.join(input_folder, filename)
        
        # 1. Read the image
        img = cv2.imread(full_path)
        
        if img is None:
            print(f"Error reading: {filename}")
            continue
            
        # 2. Convert to Grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. Improve Contrast (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_img = clahe.apply(gray_img)
        
        # 4. Reduce Noise (Gaussian Blur)
        # 5x5
        blurred_img = cv2.GaussianBlur(contrast_img, (5, 5), 0)
        
        # 5. Binarization (Otsu's Method)
        _, binary_img = cv2.threshold(blurred_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 6. Save the preprocessed image
        save_path = os.path.join(output_folder, filename)
        cv2.imwrite(save_path, binary_img)
        print(f"--> Preprocessed and saved: {filename}")

print("Pre-processing complete! Images are ready for OCR.")