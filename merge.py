import os

def merge_python_code(source_dir, output_file):
    # Папки, которые нужно игнорировать при поиске
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', '.idea', '.vscode'}
    
    # Файл, в который собирается код (чтобы он не считывал сам себя, если расширение .py)
    ignore_files = {os.path.basename(output_file), 'merge_code.py'}

    merged_files_count = 0

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(source_dir):
            # Фильтруем папки на лету, чтобы os.walk в них даже не заходил
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                if file.endswith('.py') and file not in ignore_files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            
                            # Добавляем красивый заголовок с путем к файлу для наглядности
                            outfile.write(f"\n\n{'='*60}\n")
                            outfile.write(f"# File: {file_path}\n")
                            outfile.write(f"{'='*60}\n\n")
                            
                            outfile.write(content)
                            merged_files_count += 1
                    except Exception as e:
                        print(f"Ошибка при чтении файла {file_path}: {e}")

    return merged_files_count

if __name__ == "__main__":
    # Укажите путь к проекту (точка означает текущую директорию)
    source_directory = "." 
    
    # Имя итогового файла
    output_filename = "merged_project_code.txt" 
    
    print("Начинаю сборку кода...")
    count = merge_python_code(source_directory, output_filename)
    print(f"Готово! Объединено файлов: {count}")
    print(f"Весь код сохранен в файле: {output_filename}")