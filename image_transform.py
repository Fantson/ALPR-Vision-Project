import cv2
import numpy as np
import os

# --- Configuration ---
input_folder = "car_images" 
output_folder = "cropped_plates" 

# Max window size for display
display_width = 1024 
display_height = 768

# --- Global variables ---
points = []
display_img = None

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function called on mouse click
def mark_corners(event, x, y, flags, param):
    global points, display_img
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append([x, y])
            # Draw a dot
            cv2.circle(display_img, (x, y), 4, (0, 0, 255), -1)
            
            # Draw lines
            if len(points) > 1:
                cv2.line(display_img, tuple(points[-2]), tuple(points[-1]), (0, 255, 0), 2)
            if len(points) == 4:
                cv2.line(display_img, tuple(points[3]), tuple(points[0]), (0, 255, 0), 2)
            
            cv2.imshow("Mark 4 corners", display_img)

# Open file for coordinates
coordinates_file = open("corner_coordinates_all.txt", "w")

# Main loop through ALL images in folder
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        full_path = os.path.join(input_folder, filename)
        original_img = cv2.imread(full_path)

        if original_img is None:
            print(f"Error reading: {filename}")
            continue

        orig_h, orig_w = original_img.shape[:2]
        
        # Scale down ONLY if image is larger than our display limits
        if orig_w > display_width or orig_h > display_height:
            scale_x = orig_w / display_width
            scale_y = orig_h / display_height
            scale = max(scale_x, scale_y)
            
            new_w = int(orig_w / scale)
            new_h = int(orig_h / scale)
            
            display_img = cv2.resize(original_img.copy(), (new_w, new_h))
            actual_scale_x = orig_w / new_w
            actual_scale_y = orig_h / new_h
        else:
            display_img = original_img.copy()
            actual_scale_x = 1.0
            actual_scale_y = 1.0

        points = [] # Reset points
        
        print(f"Processing: {filename}. Click 4 corners (TL, TR, BR, BL). Any key to skip.")
        
        cv2.imshow("Mark 4 corners", display_img)
        cv2.setMouseCallback("Mark 4 corners", mark_corners)
        
        key = cv2.waitKey(0)
        
        if len(points) == 4:
            # Scale clicked points back to original high-res image dimensions
            original_points = []
            for p in points:
                orig_x = int(p[0] * actual_scale_x)
                orig_y = int(p[1] * actual_scale_y)
                original_points.append([orig_x, orig_y])

            # 1. Save coordinates
            record = f"{filename}," + ",".join([f"{p[0]},{p[1]}" for p in original_points]) + "\n"
            coordinates_file.write(record)
            
            # 2. Perspective transform on ORIGINAL high-res image
            pts_src = np.float32(original_points)
            width, height = 520, 114 # Polish plate proportions
            pts_dst = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
            
            matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
            cropped_plate = cv2.warpPerspective(original_img, matrix, (width, height))
            
            # 3. Save result
            save_path = os.path.join(output_folder, filename)
            cv2.imwrite(save_path, cropped_plate)
            print(f"--> Saved: {filename}")
        else:
            print(f"--> Skipped: {filename}")

cv2.destroyAllWindows()
coordinates_file.close()
print("Done! All images processed.")