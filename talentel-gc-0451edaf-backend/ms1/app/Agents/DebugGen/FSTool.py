# --- File System Tool ---
import shutil
from pathlib import Path


class FileSystemTool:
    @staticmethod
    def read_file(file_path):
        path = Path(file_path)
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return None

    @staticmethod
    def write_file(file_path, content):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    @staticmethod
    def list_dir(dir_path):
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            return [str(p) for p in path.iterdir()]
        return []

    @staticmethod
    def copy_tree(src, dst):
        if Path(dst).exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
