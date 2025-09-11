import pandas as pd
import os

def process_catalog_data():
    try:
        # catalog.xlsx faylini o'qish
        catalog_df = pd.read_excel('catalog.xlsx', sheet_name='tayyori')
        
        # Ma'lumotlarni olish va yangi DataFrame yaratish
        product_data = pd.DataFrame({
            'kod_unique': catalog_df['B'] if 'B' in catalog_df.columns else catalog_df.iloc[:, 1],  # B ustuni
            'nomi': catalog_df['C'] if 'C' in catalog_df.columns else catalog_df.iloc[:, 2],        # C ustuni  
            'kod': catalog_df['F'] if 'F' in catalog_df.columns else catalog_df.iloc[:, 5],         # F ustuni
            'barcode': catalog_df['D'] if 'D' in catalog_df.columns else catalog_df.iloc[:, 3],     # D ustuni
            'bottom': '100%',
            'is_weekly': 3,
            'is_import': 1,
            'narxi': 100000,
            'is_special': 1,
            'is_index': 1
        })
        
        # datas papkasini yaratish (agar mavjud bo'lmasa)
        os.makedirs('datas', exist_ok=True)
        
        # planshet_data.xlsx faylini yaratish yoki yangilash
        output_file = 'datas/planshet_data.xlsx'
        
        # Agar fayl mavjud bo'lsa, mavjud ma'lumotlarni o'qish
        if os.path.exists(output_file):
            with pd.ExcelWriter(output_file, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
                product_data.to_excel(writer, sheet_name='product', index=False)
        else:
            # Yangi fayl yaratish
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                product_data.to_excel(writer, sheet_name='product', index=False)
        
        print(f"Ma'lumotlar muvaffaqiyatli {output_file} fayliga yozildi!")
        print(f"Jami {len(product_data)} ta yozuv qayta ishlandi.")
        
        # Natijani ko'rsatish
        print("\nBirinchi 5 ta yozuv:")
        print(product_data.head())
        
    except FileNotFoundError:
        print("catalog.xlsx fayli topilmadi! Faylning mavjudligini tekshiring.")
    except Exception as e:
        print(f"Xatolik yuz berdi: {str(e)}")

if __name__ == "__main__":
    process_catalog_data()