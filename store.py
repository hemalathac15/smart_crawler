import json
import os

class DataStore:
  @staticmethod
  def save_json(file_path, payload_data):
      """Automatically saves runtime dict structures to JSON formatting."""
      dir_name = os.path.dirname(file_path)
      if dir_name:
          os.makedirs(dir_name, exist_ok=True)

      try:
          with open(file_path, "w", encoding="utf-8") as file:
              json.dump(payload_data, file, indent=4, ensure_ascii=False)
          print(f"[✔] Merics pipeline storage dump saved -> {file_path}")
      except IOError as e:
            print(f"[✘] Critical System Failure writing to database target: {e}")