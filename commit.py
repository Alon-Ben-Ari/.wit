# Upload 172
import datetime
import errno
import linecache
import logging
import os
import random
import shutil
import sys


def create_paths(paths):
    """Gets a list of  directories paths and create them.

    If the path already exist, do nothing.

    Args:
        paths (list): Directoris' paths.
    """
    for path in paths:
        try:
            os.mkdir(path)
        except OSError as err:
            if err.errno == errno.EEXIST:  # file already exists
                logging.basicConfig(
                    format='%(levelname)s: %(message)s', level=logging.INFO
                )
                logging.info(f'{path} already exists.')
            else:
                raise


def init():
    """Make '.wit' directory in the cwd.

    Args:
        None

    Returns:
        bool: True if the directory was created successfully,
          False otherwise.
    """
    cwd = os.getcwd()
    wit_path = os.path.join(cwd, '.wit')
    paths_to_create = (
        wit_path,
        os.path.join(wit_path, 'images'),
        os.path.join(wit_path, 'staging_area')
    )
    create_paths(paths_to_create)
    are_exist = all(map(os.path.exists, paths_to_create))
    return are_exist


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
        "'.wit' directory doesn't exist "
        f"in any parent-directory of {abs_path}.")


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
    destination = os.path.join(
        staging_area, os.path.relpath(abs_path, start=root)
    )
    if os.path.isfile(abs_path):
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        shutil.copy2(abs_path, destination)
    else:
        shutil.copytree(abs_path, destination)


def id_generator():
    """Generate an ID composed of 40 characters"""
    chars = '1234567890abcdef'
    return ''.join(random.choices(chars, k=40))


def create_commit_file(images_path, commit_id, references_path, message):
    """Document the detailes of the commit execution.

    Args:
        images_path (str): Path to 'images' dir in '.wit' dir.
        commit_id (str): ID generated by `id_generator`.
        references_path (str): Path to the references.txt file.
        message (str): User message.
    """
    commit_path = os.path.join(images_path, f'{commit_id}.txt')
    date = datetime.datetime.now(datetime.timezone.utc).astimezone()
    if os.path.exists(references_path):
        head_line = linecache.getline(references_path, 1)
        head = head_line.split('=')[1].strip()
    else:
        head = None
    content = (
        f'parent={head}\n'
        + f'date={date.strftime("%c %z")}\n'
        + f'message={message}'
    )
    with open(commit_path, 'w') as commit_file:
        commit_file.write(content)

 
def update_references(commit_id, references_path):
    """Update the refrences.txt file.

    Args:
        commit_id (str): ID generated by `id_generator`.
        references_path (str): Path to the references.txt file.
    """
    content = (
        f'HEAD={commit_id}\n'
        + f'master={commit_id}\n'
    )
    with open(references_path, 'w') as references_file:
        references_file.write(content)


def commit(message):
    """Copys the files in the staging area to the 'images' dir.

    Args:
        message (str): User message.
    """
    root = is_wit_exists(os.getcwd())
    commit_id = id_generator()
    wit_path = os.path.join(root, '.wit')
    images_path = os.path.join(wit_path, 'images')
    staging_area_path = os.path.join(wit_path, 'staging_area')
    commit_path = os.path.join(images_path, commit_id)
    references_path = os.path.join(wit_path, 'references.txt')

    create_commit_file(images_path, commit_id, references_path, message)
    shutil.copytree(staging_area_path, commit_path)
    update_references(commit_id, references_path)

 
if __name__ == '__main__':
    try:
        function = sys.argv[1]
    except IndexError:
        function = None
        print("Function name is missing.")
    if function == 'init':
        init()
    if function == 'add':
        try:
            path = sys.argv[2]
            add(path)
        except IndexError:
            print("Path argument is missing.")
    if function == 'commit':
        try:
            message = ' '.join(sys.argv[2:])
        except IndexError:
            message = ''
        commit(message)