import pandas as pd
import json
import os


def excel_to_json(excel_file_path, json_file_path):
    """
    Excel faylidan ma'lumotlarni o'qib, JSON faylga saqlaydi
    """
    try:
        # Excel faylni o'qish
        df = pd.read_excel(excel_file_path, sheet_name='product')

        # Ma'lumotlarni formatlash
        json_data = []
        for _, row in df.iterrows():
            # Ma'lumotlarni JSON formatida tayyorlash
            item = {
                "code": str(row['kod_product']),
                "name": row['nomi'],
                "category_code": str(row['kod{8}.cat']),
                "top": row['top'],
                "bottom": row['bottom'],
                "is_import": bool(row['is_import']),
                "is_weekly": bool(row['is_weekly']),
                "price": float(row['Narxi'])
            }
            json_data.append(item)

        # JSON faylga saqlash
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"Ma'lumotlar muvaffaqiyatli ravishda {json_file_path} faylga saqlandi.")
        return True

    except Exception as e:
        print(f"Xatolik yuz berdi: {str(e)}")
        return False


if __name__ == "__main__":
    # Excel fayl yo'li
    excel_file = "datas/planshet.xlsx"  # Excel faylingiz nomini kiriting

    # JSON fayl yo'li
    # Django loyiha tuzilishiga mos ravishda datas/products.json
    base_dir = os.getcwd()  # Joriy papka, Django loyihangiz papkasiga o'zgartiring
    json_file = os.path.join(base_dir, "datas", "products.json")

    # datas papkasini yaratish (agar mavjud bo'lmasa)
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    # Excel faylni JSON ga o'tkazish
    excel_to_json(excel_file, json_file)