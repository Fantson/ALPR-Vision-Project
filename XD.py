import os
import re
import sys

import cv2
import numpy as np


# ==========================================
# 1. Wczytywanie szablonów z folderu
# ==========================================
def load_templates(templates_folder):
    templates = {}
    if not os.path.exists(templates_folder):
        return templates

    for filename in os.listdir(templates_folder):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            char_name = filename.split(".")[0]
            path = os.path.join(templates_folder, filename)

            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            _, binary_template = cv2.threshold(
                img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
            )
            templates[char_name] = binary_template

    return templates


# ==========================================
# 2. Segmentacja - Wycinanie znaków z tablicy
# ==========================================
def segment_characters(binary_plate):
    contours, _ = cv2.findContours(
        binary_plate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    char_boxes = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        area = w * h
        if 800 < area < 20000 and 0.25 < aspect_ratio < 1.3:
            char_boxes.append((x, y, w, h))

    char_boxes = sorted(char_boxes, key=lambda b: b[0])

    characters = []
    for x, y, w, h in char_boxes:
        char_img = binary_plate[y : y + h, x : x + w]
        characters.append(char_img)

    return characters, char_boxes


# ==========================================
# 3. Helpers: Etykiety i Budowanie Bloków
# ==========================================
def create_side_label(text, width, height, color=(255, 255, 255)):
    """Tworzy pionowy (obrócony o 90 st.) pasek z tekstem po lewej stronie wiersza."""
    bg = np.zeros((width, height, 3), dtype=np.uint8)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1

    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

    text_x = (height - text_size[0]) // 2
    text_y = (width + text_size[1]) // 2

    cv2.putText(bg, text, (text_x, text_y), font, font_scale, color, thickness)

    rotated = cv2.rotate(bg, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return rotated


def build_rank_block(cells_data, rank_name, text_color):
    """Buduje pełny blok (3 wiersze: Z tablicy, Diff, Szablony) dla danej rangi."""
    chars_list = []
    diffs_list = []
    tpls_list = []

    scaled_w = 40 * 3
    scaled_h = 80 * 3
    text_h = 35

    def make_blank(h, w):
        b = np.zeros((h, w, 3), dtype=np.uint8)
        return cv2.copyMakeBorder(
            b, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[50, 50, 50]
        )

    for data in cells_data:
        if data is None:
            chars_list.append(make_blank(scaled_h, scaled_w))
            diffs_list.append(make_blank(scaled_h, scaled_w))
            tpls_list.append(make_blank(scaled_h + text_h, scaled_w))
        else:
            c_img, d_img, t_img, name, score = data

            c_bgr = cv2.cvtColor(
                cv2.resize(c_img, (scaled_w, scaled_h)), cv2.COLOR_GRAY2BGR
            )
            c_bgr = cv2.copyMakeBorder(
                c_bgr, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[100, 100, 100]
            )
            chars_list.append(c_bgr)

            d_bgr = cv2.cvtColor(
                cv2.resize(d_img, (scaled_w, scaled_h)), cv2.COLOR_GRAY2BGR
            )
            d_bgr = cv2.copyMakeBorder(
                d_bgr, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[100, 100, 100]
            )
            diffs_list.append(d_bgr)

            t_bgr = cv2.cvtColor(
                cv2.resize(t_img, (scaled_w, scaled_h)), cv2.COLOR_GRAY2BGR
            )
            bar = np.zeros((text_h, scaled_w, 3), dtype=np.uint8)
            cv2.putText(
                bar,
                f"{name} ({score * 100:.1f}%)",
                (5, 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                text_color,
                1,
            )

            t_combo = cv2.vconcat([t_bgr, bar])
            t_combo = cv2.copyMakeBorder(
                t_combo, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[100, 100, 100]
            )
            tpls_list.append(t_combo)

    row_chars = cv2.hconcat(chars_list)
    row_diffs = cv2.hconcat(diffs_list)
    row_tpls = cv2.hconcat(tpls_list)

    side_w = 40
    lbl_chars = create_side_label("Z tablicy", side_w, row_chars.shape[0], (0, 255, 0))
    lbl_diffs = create_side_label("Diff", side_w, row_diffs.shape[0], (0, 0, 255))
    lbl_tpls = create_side_label(rank_name, side_w, row_tpls.shape[0], text_color)

    full_chars = cv2.hconcat([lbl_chars, row_chars])
    full_diffs = cv2.hconcat([lbl_diffs, row_diffs])
    full_tpls = cv2.hconcat([lbl_tpls, row_tpls])

    block = cv2.vconcat([full_chars, full_diffs, full_tpls])

    sep = np.zeros((10, block.shape[1], 3), dtype=np.uint8)
    sep[:] = text_color
    block = cv2.vconcat([block, sep])

    return block


# ==========================================
# 4. Template Matching (Główny algorytm)
# ==========================================
def recognize_characters(
    characters, templates, expected_text="", diff_dir="diffs", img_num="0"
):
    if not os.path.exists(diff_dir):
        os.makedirs(diff_dir)

    recognized_text = ""
    standard_size = (40, 80)
    all_chars_matches = []

    for i, char_img in enumerate(characters):
        char_resized = cv2.resize(char_img, standard_size)
        good_matches = []

        for char_name, template_img in templates.items():
            template_resized = cv2.resize(template_img, standard_size)
            result = cv2.matchTemplate(
                char_resized, template_resized, cv2.TM_CCOEFF_NORMED
            )
            _, max_val, _, _ = cv2.minMaxLoc(result)

            # Połączono logikę: Próg 0.3 z brancha upstream
            if max_val > 0.3:
                good_matches.append((max_val, char_name, template_resized))

        good_matches = sorted(good_matches, key=lambda x: x[0], reverse=True)
        top_matches = good_matches[:3]

        if top_matches:
            recognized_text += top_matches[0][1]
        else:
            recognized_text += "?"

        all_chars_matches.append((char_resized, top_matches))

    # --- GENEROWANIE ZBIORCZEGO OBRAZKA ---
    if not all_chars_matches:
        return recognized_text

    all_grid_rows = []

    # ROW 0: Oczekiwany tekst (Ground Truth)
    if expected_text:
        expected_data = []
        for i, (char_resized, _) in enumerate(all_chars_matches):
            if i < len(expected_text):
                exp_char = expected_text[i]
                if exp_char in templates:
                    t_img = cv2.resize(templates[exp_char], standard_size)
                    diff_img = cv2.absdiff(char_resized, t_img)
                    res = cv2.matchTemplate(char_resized, t_img, cv2.TM_CCOEFF_NORMED)
                    _, score, _, _ = cv2.minMaxLoc(res)
                    expected_data.append(
                        (char_resized, diff_img, t_img, exp_char, score)
                    )
                else:
                    expected_data.append(None)
            else:
                expected_data.append(None)

        block = build_rank_block(expected_data, "EXPECTED", (0, 255, 255))
        all_grid_rows.append(block)

    # ROW 1+: Wyniki Rozpoznawania (Rank 1, Rank 2...)
    max_ranks = max([len(matches) for _, matches in all_chars_matches] + [0])

    for rank in range(max_ranks):
        rank_data = []
        for char_resized, matches in all_chars_matches:
            if rank < len(matches):
                score, t_name, t_img = matches[rank]
                diff_img = cv2.absdiff(char_resized, t_img)
                rank_data.append((char_resized, diff_img, t_img, t_name, score))
            else:
                rank_data.append(None)

        block = build_rank_block(rank_data, f"TYP (R{rank + 1})", (255, 150, 0))
        all_grid_rows.append(block)

    # --- SKLEJANIE CAŁOŚCI ---
    if all_grid_rows:
        final_summary_img = cv2.vconcat(all_grid_rows)

        # NAGŁÓWEK NA SAMEJ GÓRZE
        header_height = 120
        header_img = np.zeros(
            (header_height, final_summary_img.shape[1], 3), dtype=np.uint8
        )

        if expected_text:
            cv2.putText(
                header_img,
                f"EXPECTED:   {expected_text}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 255),
                3,
            )

        cv2.putText(
            header_img,
            f"RECOGNIZED: {recognized_text}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            3,
        )
        cv2.line(
            header_img,
            (0, header_height - 2),
            (final_summary_img.shape[1], header_height - 2),
            (255, 255, 255),
            2,
        )

        final_summary_img = cv2.vconcat([header_img, final_summary_img])

        # Dynamiczne generowanie nazwy pliku zależnie od tego, czy oczekiwany tekst istnieje
        if expected_text:
            out_filename = f"summary_{img_num}_{expected_text}.png"
        else:
            out_filename = f"summary_{img_num}.png"

        output_path = os.path.join(diff_dir, out_filename)
        cv2.imwrite(output_path, final_summary_img)

    return recognized_text


# ==========================================
# GŁÓWNA CZĘŚĆ SKRYPTU
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("BLAD_ARGUMENTU")
        sys.exit(1)

    sciezka_do_obrazka = sys.argv[1]

    # Ekstrakcja numeru z nazwy pliku (np. z "image_12.png" wyciągnie "12")
    base_name = os.path.basename(sciezka_do_obrazka)
    match = re.search(r"\d+", base_name)
    image_number = match.group() if match else os.path.splitext(base_name)[0]

    # Opcjonalny argument dla EXPECTED_RESULT (jeśli podany, generuje ROW 0)
    EXPECTED_RESULT = sys.argv[2] if len(sys.argv) > 2 else ""

    templates = load_templates("szablony")
    binary_plate = cv2.imread(sciezka_do_obrazka, cv2.IMREAD_GRAYSCALE)

    if binary_plate is not None:
        binary_plate = cv2.bitwise_not(binary_plate)
        chars_images, boxes = segment_characters(binary_plate)

        if len(chars_images) > 0 and len(templates) > 0:
            tekst = recognize_characters(
                chars_images,
                templates,
                expected_text=EXPECTED_RESULT,
                img_num=image_number,
            )
            print(tekst)  # DRUKUJE TYLKO WYNIK
        else:
            print("BRAK_ZNAKOW")
    else:
        print("BLAD_OBRAZKA")
