import zlib
import os
import sys

def top_level():
    git_dir = os.getcwd()

    while git_dir != '/': #loops until reach / directory
        dirs = os.listdir(git_dir)

        for path in dirs:
            if path == '.git': #.git found
                return os.path.join(git_dir, path)

        os.chdir('..') #change to parent directory
        git_dir = os.getcwd()

        if git_dir == '/': #loop ends and git not found
            sys.stderr.write("Not inside a git repository")
            sys.exit(1)

'''
We can find branch names in the refs/heads folder.
Go into this folder and get a list of all the branch names, plus their commit hashes.
This will form a list of what will eventually become your starting commits for creating your commit graph.
'''
def local_branch_names(git_dir):

    branch_list = os.path.join(git_path, '.git/refs/heads/')

    c_hash = {}

    for paths, dirs, files in os.walk(branch_list):
        for file_name in files:
            branch_file = os.path.join(paths, file_name)
            branch_hash = open(branch_file, 'r').read().strip('\n')

            if branch_hash not in commit_hash:
                c_hash[file_name] = set()

            c_hash[file_name].append(branch_file)

    return c_hash

class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()

def get_parent_commits(git_dir, commit_hash): #Find commit_hash in the objects folder, decompress it, and get parent commits
    git_path = git_dir + commit_hash[:2] + "/" + commit_hash[2:]

    parent_commits = []

    if os.path.isfile(git_path):
        compressed = open(git_path, 'rb').read()
        decompressed = zlib.decompress(compressed)
        decompressed = decompressed.decode().split('\n')
        for line in decompressed:
            if line[:6] == 'parent':
                parent_commits.append(line[7:].strip())


    return parent_commits



def build_commit_graph(git_dir, local_branch_heads):
    commit_nodes = {}
    root_hashes = set()
    visited = set()

    stack = []
    
    for hash, val in local_branch_heads.items():
        stack.append(hash)
        

    while stack:
        #get the next element from stack, store it in commit_hash, and remove it from the stack
        commit_hash = stack.pop()

        if commit_hash in visited: #What do you do if the commit we’re on is already in visited?
            continue

        visited.add(commit_hash)

        if commit_hash not in commit_nodes: #What do you do if the commit we’re on isn’t in commit_nodes?
            commit_nodes[commit_hash] = CommitNode(commit_hash)

        commit_node = commit_nodes[commit_hash]

        commit_node.parents = get_parent_commits(git_dir + '/objects/', commit_hash)
        #Find commit_hash in the objects folder, decompress it, and get parent commits



        if not commit_node.parents:
            root_hashes.add(commit_hash) #What list do we add commit_hash to if it doesn’t have any parent commits?

        for p in commit_node.parents: #What do we do if p isn’t in visited?
            if p not in visited:
                stack.append(p)
            if p not in commit_nodes: #What do we do if p isn’t in commit_nodes?
                commit_nodes[p] = CommitNode(p)
            commit_nodes[p].children.add(commit_hash) #how do we record that commit_hash is a child of commit node p?
    return commit_nodes, root_hashes


def get_topo_ordered_commits (commit_nodes, root_hashes):
    order = []
    visited = set()
    temp_stack = []
    stack = sorted(root_hashes)
    while stack:
        v = stack.pop()
        if v in visited: #what do you do if v is already visited?
            continue
        visited.add(v)
        while temp_stack and v not in commit_nodes[temp_stack[-1]].children:
            g = temp_stack.pop()
            order.append(g)
        temp_stack.append(v)
        for c in sorted(commit_nodes[v].children):
            if c in visited: #What do you do is c has already been visited?
                continue
            stack.append(c)
    while temp_stack: #Add the rest of the temp_stack to the order
        p = temp_stack.pop()
        order.append(p)
    return order

def print_topo_ordered_commits_with_branch_names(commit_nodes, topo_ordered_commits, head_to_branches):
    jumped = False
    for i in range(len(topo_ordered_commits)):
        commit_hash = topo_ordered_commits[i]
        if jumped:
            jumped = False
            sticky_hash = ' '.join(commit_nodes[commit_hash].children)
            print(f'={sticky_hash}')
        branches = sorted(head_to_branches[commit_hash]) if commit_hash in head_to_branches else []
        print(commit_hash + (' ' + ' '.join(branches) if branches else ''))
        if i+1 < len(topo_ordered_commits) and topo_ordered_commits[i+1] not in commit_nodes[commit_hash].parents:
            jumped = True
            sticky_hash = ' '.join(commit_nodes[commit_hash].parents)
            print(f'{sticky_hash}=\n')

def topo_order_commits():
    git_dir = top_level()
    local_branch_heads = local_branch_names(git_dir)
    commit_nodes, root_hashes = build_commit_graph(git_dir, local_branch_heads)
    topo_ordered_commits = get_topo_ordered_commits(commit_nodes, root_hashes)
    print_topo_ordered_commits_with_branch_names(commit_nodes, topo_ordered_commits, local_branch_heads)
    
if __name__ == '__main__':
    topo_order_commits()

