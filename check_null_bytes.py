import os

root_dir = os.path.abspath(os.path.dirname(__file__))

print(f"Controllo caratteri null nei file Python sotto: {root_dir}\n")

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith('.py'):
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    if b'\x00' in content:
                        print(f"[!] Carattere null trovato in: {file_path}")
            except Exception as e:
                print(f"[ERRORE] Impossibile leggere {file_path}: {e}")

print("\nControllo completato.") 