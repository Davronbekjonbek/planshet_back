import json
import os
from collections import defaultdict
from typing import Dict, List, Any


class TINProcessor:
    def __init__(self):
        self.unique_tins = {}
        self.stats = {
            'total_records': 0,
            'unique_tins': 0,
            'duplicate_count': 0
        }

    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """JSON faylini yuklash"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"✅ Fayl muvaffaqiyatli yuklandi: {file_path}")
            return data if isinstance(data, list) else [data]
        except FileNotFoundError:
            print(f"❌ Fayl topilmadi: {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ JSON format xatosi: {e}")
            return []

    def process_records(self, records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Recordlarni qayta ishlash va TINlarni unique qilish"""
        print("🔄 Ma'lumotlar qayta ishlanmoqda...")

        for record in records:
            self.stats['total_records'] += 1
            tin = record.get('tin', '')

            if tin:
                if tin not in self.unique_tins:
                    self.unique_tins[tin] = record
                    self.stats['unique_tins'] += 1
                else:
                    self.stats['duplicate_count'] += 1
                    # Agar kerak bo'lsa, yangi ma'lumotlarni yangilash
                    self.update_record_if_newer(tin, record)

        return self.unique_tins

    def update_record_if_newer(self, tin: str, new_record: Dict[str, Any]):
        """Yangi record eskisiga nisbatan yangirok bo'lsa yangilash"""
        existing = self.unique_tins[tin]

        # payment_date bo'yicha solishtirish
        new_date = new_record.get('payment_date', '')
        existing_date = existing.get('payment_date', '')

        if new_date > existing_date:
            self.unique_tins[tin] = new_record
            print(f"🔄 TIN {tin} uchun yangi ma'lumot yangilandi")

    def save_unique_records(self, output_file: str, format_type: str = 'json'):
        """Unique recordlarni faylga saqlash"""
        unique_records = list(self.unique_tins.values())

        if format_type.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(unique_records, file, ensure_ascii=False, indent=2)
        elif format_type.lower() == 'csv':
            import csv
            if unique_records:
                with open(output_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=unique_records[0].keys())
                    writer.writeheader()
                    writer.writerows(unique_records)

        print(f"✅ Unique ma'lumotlar saqlandi: {output_file}")

    def print_statistics(self):
        """Statistikani chiqarish"""
        print("\n📊 STATISTIKA:")
        print(f"Jami recordlar: {self.stats['total_records']}")
        print(f"Unique TINlar: {self.stats['unique_tins']}")
        print(f"Dublikatlar: {self.stats['duplicate_count']}")
        print(f"Samaradorlik: {(self.stats['unique_tins'] / self.stats['total_records'] * 100):.1f}%")

    def get_tin_analysis(self) -> Dict[str, Any]:
        """TINlar bo'yicha tahlil"""
        analysis = defaultdict(list)

        for tin, record in self.unique_tins.items():
            company_name = record.get('name', 'Noma\'lum')
            analysis[company_name].append(tin)

        return dict(analysis)


def main():
    """Asosiy funksiya"""
    processor = TINProcessor()

    # Fayl yo'lini belgilash
    input_file = input("JSON fayl yo'lini kiriting (misol: data.json): ").strip()
    if not input_file:
        input_file = "data.json"  # Default fayl nomi

    # Ma'lumotlarni yuklash
    records = processor.load_json_file(input_file)
    if not records:
        print("❌ Ma'lumotlar yuklanmadi!")
        return

    # Ma'lumotlarni qayta ishlash
    unique_records = processor.process_records(records)

    # Chiqish formatini tanlash
    output_format = input("Chiqish formati (json/csv) [json]: ").strip().lower()
    if not output_format:
        output_format = 'json'

    # Chiqish fayl nomini belgilash
    output_file = input(f"Chiqish fayl nomi [unique_tins.{output_format}]: ").strip()
    if not output_file:
        output_file = f"unique_tins.{output_format}"

    # Natijalarni saqlash
    processor.save_unique_records(output_file, output_format)

    # Statistikani ko'rsatish
    processor.print_statistics()

    # TIN tahlilini ko'rsatish
    show_analysis = input("\nTINlar tahlilini ko'rsatish kerakmi? (y/n) [n]: ").strip().lower()
    if show_analysis == 'y':
        analysis = processor.get_tin_analysis()
        print("\n🏢 KOMPANIYALAR BO'YICHA TAHLIL:")
        for company, tins in analysis.items():
            print(f"{company}: {len(tins)} ta TIN")

# QISQA VERSIYA - Tezkor ishlatish uchun
def quick_process(input_file: str, output_file: str = "unique_tins.json"):
    """Tezkor qayta ishlash - bir qatorda"""
    processor = TINProcessor()
    records = processor.load_json_file(input_file)

    if records:
        processor.process_records(records)
        processor.save_unique_records(output_file)
        processor.print_statistics()
        return processor.unique_tins
    return None

# Skriptni ishga tushirish
if __name__ == "__main__":
    print("🚀 TIN Unique Processor - JSON faylini qayta ishlash")
    print("=" * 50)
    quick_process("data-preview-2371.json", "output.json")
    # main()



# Misol ishlatish:
