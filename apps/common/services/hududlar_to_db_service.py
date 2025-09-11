import json
from dataclasses import dataclass
from typing import BinaryIO, Optional

from django.db import transaction

from apps.home.models import Region, District


@dataclass
class ImportResult:
    regions_created: int = 0
    regions_existing: int = 0
    districts_created: int = 0
    districts_existing: int = 0


class HududJsonImporter:
    """
    hududlar.json struktura:
    [
      {
        "kod": "1700",
        "viloyat": "Toshkent viloyati",
        "childs": [
          {"tumankod": "1705", "tuman": "Bo'stonliq tumani"},
          ...
        ]
      },
      ...
    ]
    """

    def __init__(self, file_obj: Optional[BinaryIO] = None, *, data: Optional[list] = None):
        """
        file_obj: InMemoryUploadedFile/TemporaryUploadedFile (admin’dan keladi)
        data: oldindan o‘qilgan list (testlar yoki boshqa manba uchun)
        """
        self.file_obj = file_obj
        self.data = data

    def _load_data(self) -> list:
        if self.data is not None:
            return self.data
        if not self.file_obj:
            raise ValueError("JSON fayl berilmagan")
        self.file_obj.seek(0)
        try:
            return json.load(self.file_obj)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON o‘qishda xato: {e}") from e

    @transaction.atomic
    def run(self) -> ImportResult:
        payload = self._load_data()
        result = ImportResult()

        for region_data in payload:
            code = str(region_data.get("kod", "")).strip()
            name = str(region_data.get("viloyat", "")).strip()
            if not code or not name:
                # kod yoki nom bo'sh bo'lsa tashlaymiz
                continue

            region, created = Region.objects.get_or_create(
                code=code,
                defaults={"name": name}
            )
            if created:
                result.regions_created += 1
            else:
                # agar nom o‘zgargan bo‘lsa, yangilab qo‘yish mumkin (ixtiyoriy)
                if region.name != name and name:
                    region.name = name
                    region.save(update_fields=["name"])
                result.regions_existing += 1

            childs = region_data.get("childs", []) or []
            for district_data in childs:
                d_code = str(district_data.get("tumankod", "")).strip()
                d_name = str(district_data.get("tuman", "")).strip()
                if not d_code or not d_name:
                    continue

                _, d_created = District.objects.get_or_create(
                    code=d_code,
                    region=region,
                    defaults={"name": d_name}
                )
                if d_created:
                    result.districts_created += 1
                else:
                    d = District.objects.get(code=d_code, region=region)
                    if d.name != d_name and d_name:
                        d.name = d_name
                        d.save(update_fields=["name"])
                    result.districts_existing += 1

        return result
