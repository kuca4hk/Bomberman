from collections import deque


class AStar:
    """
    Class for standard A* algorithm

    it is initialized with game map, method find_path finds the shortest path from start to goal and returns it
    """
    def __init__(self, game_map):
        self.height, self.width = game_map.shape
        self.game_map = game_map

    def find_path(self, start, goal):
        """
        returns the shortest path from start to goal

        uses the A* algorithm

        Inputs:
        -------
        start : tuple
            x and y of the start position
        goal : tuple
            x and y of the goal position

        Returns:
        --------
            path as a list of positions, first position is the start position and lat is the goal position
        """

        d = deque()

        su = (start[0], start[1], 0, self.count_heu(start, goal))
        ofina = [su]  # x,y,g (ujeta vzd od startu),h (heuristika cca do cile)
        expanded = []  # expandované uzly
        foundEnd = False

        for i in range(0, self.width * self.height * self.width * 20):
            if (su[0] == goal[0] and su[1] == goal[1]):
                expanded.append(su)
                foundEnd = True
                break
            if (len(ofina) == 0):
                break
            expanded.append(su)

            self.vrad_do_pole(ofina, self.get_valid_neighbours(su, goal), expanded, d)
            ofina.remove(su)
            if (len(ofina) == 0):
                break
            if (su[0] == ofina[0][0] and su[1] == ofina[0][1] and len(ofina) > 1):
                su = ofina[1]
            else:
                su = ofina[0]

        if (foundEnd):  # získání cesty
            exp = expanded.copy()
            d.append((start[0], start[1], 0, self.count_heu(start, goal)))
            while (not ((d[len(d) - 1][0] == goal[0] and d[len(d) - 1][1] == goal[1])) and len(exp) > 0):
                d = deque()
                d.append((start[0], start[1], 0, self.count_heu(start, goal)))
                i = 0
                while (i < len(exp)):
                    su = exp[i]
                    for n in self.get_valid_neighbours(su, goal):
                        if (n[0] == d[len(d) - 1][0] and n[1] == d[len(d) - 1][1]):
                            if (d[len(d) - 1][3] + d[len(d) - 1][2] <= su[3] + su[2]):
                                d.append(su)
                                break
                    i += 1
                if (len(d) <= 1):
                    break
                if (not ((d[0] == goal[0] and d[1] == goal[1]))):
                    exp.remove(d[len(d) - 1])

        path = deque()
        for u in d:
            path.append((u[0], u[1]))
        expandovane = deque()
        for e in expanded:
            expandovane.append((e[0], e[1]))
        return path

    def count_heu(self, node, goal):
        """
        Function returning the heuristic of entered node.
        Heuristic is counted as Manhattan distance between the node and the goal

        Input:
        ------
        node
            node for counting the heurostic, has x and y
        goal
            x nad y of the goal

        Returns:
        --------
            counted heuristic as a number
        """
        heu = abs(node[0] - goal[0]) + abs(node[1] - goal[1])
        return heu

    def get_valid_neighbours(self, su, goal):
        """
        Function returning valid neighbours of the su.
        Valid neighbour is node next to the entered node (su) which is not a wall
        """
        neighbours = []
        neighbour = (su[0], su[1] - 1, su[2] + 1)
        if ((self.is_valid_xy(neighbour[0], neighbour[1]) and self.is_empty(neighbour[0], neighbour[1]))):
            neighbours.append((neighbour[0], neighbour[1], neighbour[2], self.count_heu(neighbour, goal)))
        neighbour = (su[0], su[1] + 1, su[2] + 1)
        if ((self.is_valid_xy(neighbour[0], neighbour[1]) and self.is_empty(neighbour[0], neighbour[1]))):
            neighbours.append((neighbour[0], neighbour[1], neighbour[2], self.count_heu(neighbour, goal)))
        neighbour = (su[0] - 1, su[1], su[2] + 1)
        if ((self.is_valid_xy(neighbour[0], neighbour[1]) and self.is_empty(neighbour[0], neighbour[1]))):
            neighbours.append((neighbour[0], neighbour[1], neighbour[2], self.count_heu(neighbour, goal)))
        neighbour = (su[0] + 1, su[1], su[2] + 1)
        if ((self.is_valid_xy(neighbour[0], neighbour[1]) and self.is_empty(neighbour[0], neighbour[1]))):
            neighbours.append((neighbour[0], neighbour[1], neighbour[2], self.count_heu(neighbour, goal)))

        return neighbours

    def vrad_do_pole(self, arr, items, expanded, d):
        for item in items:
            exp = False
            for i in range(0, len(expanded)):
                if (expanded[i][0] == item[0] and expanded[i][1] == item[1]):
                    exp = True
                    break
            if (not exp):
                self.prioritizovana_fronta(arr, item, expanded)

    def prioritizovana_fronta(self, arr, item, expanded):
        # zjistí, jestli už stejný bod v poli není
        for i in range(0, len(arr)):
            if (arr[i][0] == item[0] and arr[i][1] == item[
                1]):  # pokud je lepší vymění ho (smaže a přidá v druhém for), jinak nepřidá
                if (arr[i][3] + arr[i][2] > item[3] + item[2]):
                    arr.remove(arr[i])
                else:
                    return
        # řadí od nejmenší hodnoty
        for i in range(0, len(arr)):
            if (arr[i][3] + arr[i][2] > item[3] + item[2]):
                arr.insert(i, item)
                return

        arr.append(item)

    def is_empty(self, x, y):
        if self.game_map[y, x] == 0:
            return True
        return False

    def is_valid_xy(self, x, y):
        """Function that checks wheter entered x and y are valid i.e. are empty/are not containing wall"""
        if x >= 0 and x < self.width and y >= 0 and y < self.height and self.game_map[y, x] == 0:
            return True
        return False
