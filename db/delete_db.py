import os

# Root path where the database files exist
root_path = r"C:\Users\chand\Desktop\clase streamlit\db"

# File extensions to delete - add more if needed
db_extensions = ['.db']

for subdir, dirs, files in os.walk(root_path):
    for file in files:
        file_path = os.path.join(subdir, file)
        if any(file.endswith(ext) for ext in db_extensions):
            print(f"Deleting: {file_path}")
            os.remove(file_path)

print("Database files deletion completed.")
