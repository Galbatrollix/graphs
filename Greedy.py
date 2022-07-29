import utilities


def greedy_search_solve(points, connections_dict):
    """
    Solves the Traveling Salesman Problem using greedy search algorithm.
    Takes list of points an dictionary of connections as arguments.
    Returns full path in form of list of consecutive node indexes, if found.
    If no path possible, returns empty list.
    """

    return __greedy_search_implementation([0], connections_dict, len(points))


def __greedy_search_implementation(state, connections_dict, node_num):
    """
    Finds approximate solution using greedy search approach.
    Uses backtracking in case of getting stuck on incomplete graph.
    If there is any valid cycle, this function will find one.

    State argument is a list with a starting node.
    Returns full route if any was found, else empty route.
    """
    # additional variables for backtracking
    current_nodes = 1
    checked_nodes = {x: set() for x in range(1, node_num + 1)}

    # as long as whole cycle isn't finished
    while len(state) != node_num + 1:
        # if backtracking didn't find a single possible way, exit function and return None
        if not state:
            return []

        list_of_children = utilities.children_states(state, connections_dict, node_num)
        list_of_children.sort(key=utilities.last_2_sort_key_maker(connections_dict))

        # choose state with smallest added distance that hasn't been checked yet
        for child in list_of_children:
            if child[-1] not in checked_nodes[current_nodes]:
                state = child
                checked_nodes[current_nodes].add(state[-1])
                current_nodes += 1
                break
        # if no valid/unchecked child states, backtrack one node
        else:
            del state[-1]
            checked_nodes[current_nodes] = set()
            current_nodes -= 1

    return state

