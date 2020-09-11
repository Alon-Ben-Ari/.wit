# Upload 176
import datetime
import errno
import filecmp
import logging
import os
import random
import shutil
import sys

from graphviz import Digraph


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


def update_activated_file(root, branch_name):
    path = os.path.join(root, '.wit', 'activated.txt')
    with open(path, 'w') as f:
        f.write(branch_name)


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
    update_activated_file(cwd, branch_name='master')
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
    parent_dir = abs_path
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
    staging_area = os.path.join(root, '.wit', 'staging_area')
    destination = os.path.join(
        staging_area, os.path.relpath(abs_path, start=root)
    )
    if os.path.isfile(abs_path):
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        shutil.copy2(abs_path, destination)
    else:
        if os.path.exists(destination):
            shutil.rmtree(destination)
        shutil.copytree(abs_path, destination)


def id_generator():
    """Generate an ID composed of 40 characters"""
    chars = '1234567890abcdef'
    return ''.join(random.choices(chars, k=40))


def get_ref(root):
    """Extract data from references.txt file.

    Args:
        root (str): Path to the root directory
          (which consist .wit directory).

    Returns:
        dict: The current 'HEAD' and 'master'.
    """
    references_path = os.path.join(root, '.wit', 'references.txt')
    with open(references_path, 'r') as f:
        lines = map(lambda x: x.strip('\n').split('='), f.readlines())
    references = {line[0]: line[1] for line in lines}
    return references


def create_commit_file(images_path, commit_id, root, message):
    """Document the detailes of the commit execution.

    Args:
        images_path (str): Path to 'images' dir in '.wit' dir.
        commit_id (str): ID generated by `id_generator`.
        references_path (str): Path to the references.txt file.
        message (str): User message.
    """
    commit_path = os.path.join(images_path, f'{commit_id}.txt')
    date = datetime.datetime.now(datetime.timezone.utc).astimezone()
    try:
        head = get_ref(root)['HEAD']
    except FileNotFoundError:
        head = None

    content = (
        f'parent={head}\n'
        + f'date={date.strftime("%c %z")}\n'
        + f'message={message}'
    )
    with open(commit_path, 'w') as commit_file:
        commit_file.write(content)


def get_active_branch(root):
    path = os.path.join(root, '.wit', 'activated.txt')
    with open(path, 'r') as f:
        return f.read()


def update_references(commit_id, root, head_only=False):
    """Change the commit id in the refrences.txt file.

    If the reference file doesn't exist, or 'HEAD' and
    the activated branch point at the same commit_id
    (according to activated.txt), than both of them gets
    the new id given to the function. If the active branch
    points at another id, or there is'nt any actived branch,
    than only 'HEAD' is changed.

    Args:
        commit_id (str): ID generated by `id_generator`.
        root (str): Path to the root directory.
        head_only (bool): Default to False. If True, only the
          'HEAD' gets the given ID. Usefull for 'checkout' comand.
    """
    references_path = os.path.join(root, '.wit', 'references.txt')
    branch = get_active_branch(root)
    if not os.path.exists(references_path):
        content = [f'HEAD={commit_id}\n', f'master={commit_id}\n']
    else:
        references = get_ref(root)
        if references['HEAD'] == references.get(f'{branch}', 'No branch') and not head_only:
            references[f'{branch}'] = commit_id
        references['HEAD'] = commit_id
        content = [f'{key}={val}\n' for key, val in references.items()]

    with open(references_path, 'w') as references_file:
        references_file.writelines(content)


def commit(message):
    """Copy the files in the staging area to the 'images' dir.

    Args:
        message (str): User message.
    """
    root = is_wit_exists(os.getcwd())
    commit_id = id_generator()
    wit_path = os.path.join(root, '.wit')
    images_path = os.path.join(wit_path, 'images')
    staging_area_path = os.path.join(wit_path, 'staging_area')
    commit_path = os.path.join(images_path, commit_id)

    create_commit_file(images_path, commit_id, root, message)
    shutil.copytree(staging_area_path, commit_path)
    update_references(commit_id, root)


def dir_files(dir_path, ignore_wit=False):
    """Create a list of a directory's files.

    Args:
        dir_path (str): The path of the directory.
        ignore_wit (bool): If one of the directories for comparement
          is the root dir (which consists the .wit dir), the .wit dir can
          be ignored.

    Returns:
        list: List of files' paths.
    """
    main_files = []
    for dirpath, dirnames, filenames in os.walk(dir_path):
        if ignore_wit and '.wit' in dirnames:
            dirnames.remove('.wit')
        for filename in filenames:
            main_files.append(os.path.join(dirpath, filename))
    return main_files


def compare_dirs(main_dir, compared_dir, content=True, ignore_wit=False):
    """Compare a directory's content to another's directory.

    Args:
        main_dir (str): The path of the main directory for the comparement.
          The functions iterates over the *main dir's* files and compare them
          to the parallel files in the compared_dir.
        compared_dir (str): The path for the second dir.
        content (bool): If True - compare the content of the files as well.
          If set to False, compare only the existence of files.
        ignore_wit (bool): If set to True, the functions doesn't iterate over
          files in the .wit directory. Usefull for finding untracked files.

    Return:
        list: Files' paths that exists in the main dir and not in the
          compared one, and that exits in both dirs and don't have
          same content.
    """
    diff_files = []
    main_files = dir_files(main_dir, ignore_wit)
    compared_files = dir_files(compared_dir, ignore_wit=False)

    compared_relpaths = tuple(map(
        lambda f: os.path.relpath(f, start=compared_dir),
        compared_files
    ))
    for f in main_files:
        f_relpath = os.path.relpath(f, start=main_dir)
        compared_f = os.path.join(compared_dir, f_relpath)
        if f_relpath not in compared_relpaths:
            diff_files.append(f)
        elif content and not filecmp.cmp(f, compared_f):
            diff_files.append(f)
    return diff_files


def status():
    """Return status to the user.

    Args:
        None

    Returns:
        str: The last 'commit' directory (head), files paths
          to be committed, files paths not staged for commit and
          untracked files.
        bool: True if there are files under 'Changes to be committed'
          or 'Changes not staged for commit'.
    """
    root = is_wit_exists(os.getcwd())
    head = get_ref(root)["HEAD"]
    wit_path = os.path.join(root, '.wit')
    last_commit_path = os.path.join(wit_path, 'images', head)
    staging_path = os.path.join(wit_path, 'staging_area')
    status_dict = {
        "HEAD": head,
        "Changes to be committed": compare_dirs(staging_path, last_commit_path),
        "Changes not staged for commit": compare_dirs(staging_path, root),
        "Untracked files": compare_dirs(root, staging_path,
                                        content=False, ignore_wit=True),
    }
    return status_dict


class NotSavedChangesError(Exception):
    pass


def update_root_dir(root, commit_path):
    """Copy files from the given commit directory
       to the root directory. Replace if needed."""
    for dirpath, _, filenames in os.walk(commit_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            destination = os.path.join(
                root, os.path.relpath(filepath, start=commit_path)
            )
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            shutil.copy2(filepath, destination)


def update_staging_area(wit_path, commit_path):
    """Remove the current staging dir and copy the
       given commit directory's content to a new staging directory"""
    staging_area = os.path.join(wit_path, 'staging_area')
    shutil.rmtree(staging_area)
    shutil.copytree(commit_path, staging_area)


def is_safe_checkout():
    """Return if there are 'Changes to be committed' or
       'Changes not staged for commit' according to `status()`"""
    all_changes_saved = (not (status()["Changes to be committed"]
                         + status()["Changes not staged for commit"]))
    if not all_changes_saved:
        raise NotSavedChangesError("There are changes not yet staged or commited.")
    else:
        return True


def checkout(identifier):
    """Update the root directory and the data files.

    Copys the files in the given commit dir to the root dir.
    Replaces the staging area's content with the commit dir's
    content. Update refrence.txt and activated.txt (if a commit_id
    was given then there is no active branch).

    Args:
        identifier (str): An existing commit id or branch name.
    """
    is_safe_checkout()
    root = is_wit_exists(os.getcwd())
    wit_path = os.path.join(root, '.wit')

    is_branch = get_ref(root).get(f'{identifier}', False)
    if is_branch:
        branch = identifier
        commit_id = is_branch
    else:
        branch = ''
        commit_id = identifier
    update_activated_file(root, branch_name=branch)

    commit_path = os.path.join(wit_path, 'images', commit_id)
    update_root_dir(root, commit_path)
    update_references(commit_id, root, head_only=True)
    update_staging_area(wit_path, commit_path)


def get_commit_data(root, commit_id):
    """Extract data from commit_id.txt file.

    Args:
        commit_id (str): An existing directory's commit_id.

    Returns:
        dict: The 'parent', 'date' and 'message' values
          from the file.
    """
    commit_f_path = os.path.join(
        root, '.wit', 'images', f'{commit_id}.txt'
    )
    with open(commit_f_path, 'r') as f:
        lines = map(lambda x: x.strip('\n').split('='), f.readlines())
    return {line[0]: line[1] for line in lines}


def make_ids_list(root):
    """Return a list of the commit_id directories
       ordered according to the parent directory of each one,
       starting from the HEAD directory."""
    head = get_ref(root)['HEAD']
    ordered_commit_id = [head]
    parent = get_commit_data(root, head)['parent']
    while parent != 'None':
        ordered_commit_id.append(parent)
        parent = get_commit_data(root, parent)['parent']
    return ordered_commit_id


def graph():
    """Create a flow chart of the commit directories tree.

    Args:
        None

    Returns:
        Digraph: A styled graph object of the tree.
    """
    root = is_wit_exists(os.getcwd())
    commit_ids = list(map(lambda x: x[:6], make_ids_list(root)))
    commit_graph = Digraph(
        'commit_graph', filename='commit_id_tree', format='png'
    )
    commit_graph.attr(rankdir='RL')
    commit_graph.attr(
        'node', style='filled', fillcolor="cornflowerblue", shape='circle'
    )
    commit_graph.attr('edge', style='filled', fillcolor="cornflowerblue")
    commit_graph.edge('HEAD', commit_ids[0])
    if get_ref(root)['master'] == get_ref(root)['HEAD']:
        commit_graph.edge('master', get_ref(root)['master'][:6])
    for i, com_id in enumerate(commit_ids):
        if (i + 1) == len(commit_ids):
            return commit_graph
        commit_graph.edge(com_id, commit_ids[i + 1])


def branch(name):
    """Add the given branch name to references.txt"""
    root = is_wit_exists(os.getcwd())
    ref_path = os.path.join(root, '.wit', 'references.txt')
    head = get_ref(root)['HEAD']
    with open(ref_path, 'a') as f:
        f.write(f'{name}={head}')


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
    if function == 'status':
        for key, val in status().items():
            print(f"{key}:\n{val}\n")
    if function == 'checkout':
        try:
            commit_id = sys.argv[2]
            checkout(commit_id)
        except IndexError:
            print("commit_id argument is missing.")
    if function == 'graph':
        graph().view()
    if function == 'branch':
        try:
            name = sys.argv[2]
            branch(name)
        except IndexError:
            print("name argument is missing.")
