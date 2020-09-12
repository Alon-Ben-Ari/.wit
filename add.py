# Upload 171
import os
import shutil
import sys


class WitDirNotFoundError(Exception):
    pass


def is_wit_exists(abs_path):
    """Checks if .wit directory exists in any parent-directory.

    Args:
        abs_path (str): An absolute path whose parent-directories
          are checked.
    
    Returns:
        str: The path of the directory that consist the
          .wit directory, if exists.
    
    Raises:
        WitDirNotFoundError: An error occurred if .wit 
          directory doesn't exist. 
    """
    parent_dir = os.path.dirname(abs_path)
    drive = os.path.join(os.path.splitdrive(abs_path)[0], os.sep)
    while parent_dir != drive:
        wit_path = os.path.join(parent_dir, ".wit")
        is_exists = os.path.exists(wit_path)
        if is_exists:
            return parent_dir
        parent_dir = os.path.dirname(parent_dir)          
    raise WitDirNotFoundError(
        f"'.wit' directory doesn't exist in any parent-directory of {abs_path}.")


def add(path):
    """Copy a file or directory to the staging area.

    Copy all the parent directories of the path to the 
    root directory (which consists '.wit' dir). A directory
    is copied with all of its content. 

    Args:
        path (str): An absolute or relative path.
    """
    abs_path = os.path.abspath(path)
    root = is_wit_exists(abs_path)
    staging_area = os.path.join(os.path.join(root, '.wit'), 'staging_area')
    destination = os.path.join(staging_area, os.path.relpath(abs_path, start=root))
    if os.path.isfile(abs_path):
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        shutil.copy2(abs_path, destination)
    else:
        shutil.copytree(abs_path, destination)


if __name__ == '__main__':
    try:
        function = sys.argv[1]
    except IndexError:
        function = None
        print("Function name is missing.")
    if function == 'add':
        try:
            path = sys.argv[2]
            add(path)
        except IndexError:
            print("Path argument is missing.")