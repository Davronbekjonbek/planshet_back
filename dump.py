# dump_to_json.py
from django.core.management import call_command
import io

with open("db.json", "w", encoding="utf-8") as f:
    call_command("dumpdata", exclude=["auth", "contenttypes"], indent=2, stdout=f)
