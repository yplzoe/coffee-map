import random
import numpy as np
from collections import defaultdict
from pprint import pprint


def object_function(solution):
    return -(solution[3]*solution[0])
    # return -sum(solution[:2])


def get_neighbors(solution):
    # swapping two elements
    neighbors = []
    for i in range(len(solution)):
        for j in range(i+1, len(solution)):
            neighbor = solution[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            neighbors.append(neighbor)

    return neighbors


def tabu_search(initial_solution, max_iterations, tabu_list_size):
    best_solution = initial_solution
    current_solution = initial_solution
    tabu_list = []

    for _ in range(max_iterations):
        neighbors = get_neighbors(current_solution)
        best_neighbor = None
        best_neighbor_fitnes = float('inf')

        for neighbor in neighbors:
            if neighbor not in tabu_list:
                neighbor_fitness = object_function(neighbor)
                if neighbor_fitness < best_neighbor_fitnes:
                    best_neighbor = neighbor
                    best_neighbor_fitnes = neighbor_fitness

        if best_neighbor is None:
            break

        current_solution = best_neighbor
        tabu_list.append(best_neighbor)
        if len(tabu_list) > tabu_list_size:
            tabu_list.pop(0)

        if object_function(best_neighbor) < object_function(best_solution):  # minimum
            best_solution = best_neighbor
    return best_solution


def rand_graph(num_nodes, max_dis, max_stay_time):
    dis_hist = defaultdict(
        lambda: defaultdict(lambda: float('inf')))
    stay_hist = defaultdict(dict)
    for i in range(num_nodes):
        stay_hist[str(i)] = random.randint(1, max_stay_time)
        for j in range(i+1, num_nodes):
            temp_dis = random.randint(1, max_dis)
            dis_hist[str(i)][str(j)] = temp_dis
            dis_hist[str(j)][str(i)] = temp_dis
    return dis_hist, stay_hist


if __name__ == "__main__":

    # find
    initial_solution = [1, 2, 3, 4, 5]
    # travel_time=
    buffer_time = 10  # min
    max_iterations = 100
    tabu_list_size = 32  # 2^len(initial_solution)

    best_solution = tabu_search(
        initial_solution, max_iterations, tabu_list_size)
    print(f"Best solution: {best_solution}")
    print(f"Best solution fitness: {object_function(best_solution)}")
