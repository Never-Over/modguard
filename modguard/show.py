import yaml
from modguard.core.boundary import BoundaryTrie


def boundary_trie_to_dict(boundary_trie):
    result = {}
    for node in boundary_trie:
        path = node.full_path
        if path == "":
            path = "root"
        sections = path.split(".")
        pointer = result
        for section in sections:
            if section not in pointer:
                pointer[section] = {}
            pointer = pointer[section]
        pointer["is_boundary"] = True

        for member in node.public_members.keys():
            pointer = result
            sections = member.split(".")
            for section in sections:
                if section not in pointer:
                    pointer[section] = {}
                pointer = pointer[section]
            pointer["is_public"] = True

    return result


def show(boundary_trie: BoundaryTrie) -> str:
    dict_repr = boundary_trie_to_dict(boundary_trie)
    result = yaml.dump(dict_repr)
    print(result)
    return result