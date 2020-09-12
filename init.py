# Upload 170
import errno
import logging
import os
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
                logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
                logging.info(f'{path} already exists.')
            else:
                raise


def init():
    """Make '.wit' directory in the cwd. 

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


if __name__ == '__main__':
    try:
        function = sys.argv[1]
    except IndexError:
        function = None
        print("Function name is missing.")
    if function == 'init':
        init()