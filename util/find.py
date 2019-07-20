import os


def find_files(d, ext, excluded_dirs, excluded_files):
    files = []
    filter_filename = with_extension(ext)

    filter_dir = exclude_folders(excluded_dirs)
    for file_or_folder in os.listdir(d):
        full_path = os.path.join(d, file_or_folder)
        if os.path.isfile(full_path) \
                and filter_filename(file_or_folder)\
                and full_path not in excluded_files:
            files.append(full_path)
        elif os.path.isdir(full_path) and filter_dir(file_or_folder):
            files.extend(find_files(full_path, ext, excluded_dirs, excluded_files))
    return files


def with_extension(ext):
    def filter(file_name):
        return file_name.endswith(ext)
    return filter


def exclude_folders(dir_names):
    def filter(dir_name):
        return dir_name not in dir_names
    return filter
