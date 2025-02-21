import os
import re
import time
from pdf2image import convert_from_path
from PIL import ImageDraw, ImageFont
from PyPDF2 import PdfMerger

# Если значение короче, чем всего знакомест, добавляет к значению нужное количество знаков -
def pad_text(text, length, pad_char="-"):
    return text.ljust(length, pad_char)

# Рисует текст на изображении в клеточках с заданным интервалом, чтобы попадать в клетки
def draw_spaced_text(draw, text, start_x, y, font, spacing=39.4):
    x = start_x
    for char in text:
        draw.text((x, y), char, font=font, fill="black")
        x += spacing

def generate_pdf(data):
    temp_dir = "files/temp"
    output_dir = "files/generated_references"
    form_file = "files/form.pdf"
    font_file = "files/cour.ttf"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Функция для очистки текста от недопустимых символов
    def clean_text(text):
        if not text:
            return ""
        return re.sub(r"[^а-яА-ЯёЁ0-9_]", "", text)
    
    # Конвертируем PDF-шаблон в изображения
    images = convert_from_path(form_file)
    generated_files = []
    font = ImageFont.truetype(font_file, 44)
    
    # Определяем количество страниц в зависимости от типа налогоплательщика
    taxpayer_is_student = int(data.get("taxpayer_is_student", 1))
    pages_count = 1 if taxpayer_is_student == 1 else 2
    
    for i, img in enumerate(images[:pages_count]):
        draw = ImageDraw.Draw(img)
        
        if i == 0:
            # Координаты полей на первой странице
            fields = {
                "org_inn": (558, 40), "org_kpp": (558, 102), "spravka_number": (244, 360),
                "korr_number": (1071, 360), "otchet_period": (1466, 360), "org_desc_first": (46, 482),
                "org_desc_second": (46, 545), "org_desc_third": (46, 608), "org_desc_four": (46, 671),
                "study_form": (678, 787), "taxpayer_lastname": (204, 903), "taxpayer_firstname": (204, 973),
                "taxpayer_surname": (204, 1045), "taxpayer_inn": (205, 1115), "taxpayer_date_birth": (1030, 1115),
                "taxpayer_month_birth": (1149, 1115), "taxpayer_year_birth": (1268, 1115), "taxpayer_document_code": (322, 1242),
                "taxpayer_document_serial_number": (835, 1242), "taxpayer_document_date_issue": (322, 1312),
                "taxpayer_document_month_issue": (440, 1312), "taxpayer_document_year_issue": (560, 1312),
                "taxpayer_is_student": (756, 1382), "summa_rashodov_before_dot": (756, 1462),
                "summa_rashodov_after_dot": (1307, 1462), "authenticity_first": (48, 1630), "authenticity_second": (48, 1692),
                "authenticity_third": (48, 1754), "signature_date": (456, 1868), "signature_month": (573, 1868),
                "signature_year": (694, 1868), "pages_count": (364, 1948)
            }
            
            for key, (x, y) in fields.items():
                value = data.get(key, "")
                if key == "summa_rashodov_before_dot":
                    value = pad_text(value, 13)
                if key == "korr_number":
                    value = pad_text(value, 3)
                draw_spaced_text(draw, value, x, y, font, spacing=39.4)
        
        elif i == 1 and taxpayer_is_student == 0:
            # Координаты полей на второй странице (если налогоплательщик и обучающийся не одно лицо)
            fields = {
                "org_inn": (520, 40), "org_kpp": (520, 102),
                "student_lastname": (204, 293), "student_firstname": (204, 363), "student_surname": (204, 433), "student_inn": (204, 503),
                "student_date_birth": (1033, 503), "student_month_birth": (1150, 503), "student_year_birth": (1271, 503),
                "student_document_code": (323, 638), "student_document_serial_number": (836, 638),
                "student_document_date_issue": (321, 708), "student_document_month_issue": (437, 708),
                "student_document_year_issue": (559, 708)
            }
            
            for key, (x, y) in fields.items():
                value = data.get(key, "")
                draw_spaced_text(draw, value, x, y, font, spacing=39.4)


        taxpayer_lastname = clean_text(data.get("taxpayer_lastname", ""))
        taxpayer_firstname = clean_text(data.get("taxpayer_firstname", ""))
        taxpayer_surname = clean_text(data.get("taxpayer_surname", ""))
        reference_id = clean_text(data.get("spravka_number", ""))
        
        # Сохранение временного обработанного изображения в PDF
        output_filename = os.path.join(temp_dir, f"{taxpayer_lastname}_{taxpayer_firstname}_{taxpayer_surname}_{i}.pdf")
        img.save(output_filename, "PDF")
        generated_files.append(output_filename)

    # Формирование итогового имени файла
    date = time.strftime("%d.%m.%Y")
    final_filename = os.path.join(output_dir, f"{reference_id}_{taxpayer_lastname}_{taxpayer_firstname}_{taxpayer_surname}_справка_КНД_1151158_{date}.pdf")
    
    # Объединение в один PDF
    merger = PdfMerger()
    for file in generated_files:
        merger.append(file)
    merger.write(final_filename)
    merger.close()
    
    # Удаление временных файлов
    for file in generated_files:
        os.remove(file)
    
    return final_filename
