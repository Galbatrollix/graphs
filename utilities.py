def euclidean_distance(point1, point2):
    """Calculates distance between two points in euclidean space"""
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


def distance_sort_key_maker(focus_point):
    """
    Creates a sort key used for sorting list of points
    based on distance to selected point.
    Takes selected point as a parameter.
    Returns key function.
    """

    def key_function(point):
        return euclidean_distance(point, focus_point)

    return key_function


def children_states(state, connections_dict, node_num):
    """
    Returns all possible states that can be created from provided state.
    State is a list of consecutive node IDs.
    Returns empty list if there are no available children states.
    """
    last_node = state[-1]
    all_nodes = set(connections_dict[last_node].keys())
    visited_nodes = set(state)
    available_nodes = all_nodes - visited_nodes

    list_of_children_states = []
    if available_nodes:
        for node in available_nodes:
            list_of_children_states.append(state + [node])
    # if road can be finished and ends can be connected
    elif len(state) == node_num and state[0] in connections_dict[last_node]:
        list_of_children_states.append(state + [state[0]])

    return list_of_children_states


def calculate_length_of_path(path, connections_dict):
    """
    Calculates length of path provided in state format (list of consecutively visited node IDs).
    Uses connections dict, provided as a parameter.
    """
    sum_ = 0
    for point1, point2 in zip(path, path[1:]):
        sum_ += connections_dict[point1][point2]
    return sum_


def whole_road_sort_key_maker(connections_dict):
    """
    Makes sort key function that will sort paths depending on their length.
    Takes connections dict as only argument, returns key function.
    """

    def key_function(x):
        conn = connections_dict
        return calculate_length_of_path(x, conn)

    return key_function


def last_2_sort_key_maker(connections_dict):
    """
    Makes sort key function that will sort paths depending on distance between last 2 cities in the path.
    Takes connections dict as only argument, returns key function.
    """

    def key_function(x):
        node1, node2 = x[-1], x[-2]
        return connections_dict[node1][node2]

    return key_function
