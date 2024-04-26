import random
import pandas as pd
from collections import defaultdict, OrderedDict
from pprint import pprint
import plotly.express as px
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def object_function(solution, dis_dict):
    total_time = 0
    for start, end in zip(solution[:-1], solution[1:]):
        total_time += dis_dict[str(start)][str(end)]

    return total_time


def get_neighbors(solution):
    # swapping two elements
    neighbors = []
    for i in range(len(solution)):
        for j in range(i+1, len(solution)):
            neighbor = solution[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            neighbors.append(neighbor)

    return neighbors


def tabu_search(initial_solution, max_iterations, tabu_list_size, dis_dict):
    best_solution = initial_solution
    best_obj = object_function(best_solution, dis_dict)
    current_solution = initial_solution
    # cur_obj = object_function(current_solution, dis_dict)
    tabu_list = OrderedDict()
    # best_obj_list = []
    # iter_best_obj_list = []

    for _ in range(max_iterations):
        neighbors = get_neighbors(current_solution)
        best_neighbor = None
        best_neighbor_obj = float('inf')

        for neighbor in neighbors:
            if str(neighbor) not in tabu_list:
                neighbor_obj = object_function(neighbor, dis_dict)
                if neighbor_obj < best_neighbor_obj:
                    best_neighbor = neighbor
                    best_neighbor_obj = neighbor_obj

        if best_neighbor is None:
            break

        current_solution = best_neighbor
        tabu_list[str(best_neighbor)] = best_neighbor_obj
        if len(tabu_list) > tabu_list_size:
            tabu_list.popitem(last=False)

        # minimum
        if best_neighbor_obj < best_obj:
            best_solution = best_neighbor
            best_obj = best_neighbor_obj
        # best_obj_list.append(best_obj)
        # iter_best_obj_list.append(best_neighbor_obj)

    # return best_solution, best_obj, best_obj_list, iter_best_obj_list
    return best_solution, best_obj


def rand_graph(num_nodes, max_dis, max_stay_time):
    dis_dict = defaultdict(
        lambda: defaultdict(lambda: float('inf')))
    stay_dict = defaultdict(dict)
    for i in range(num_nodes):
        stay_dict[str(i)] = random.randint(1, max_stay_time)
        for j in range(i+1, num_nodes):
            temp_dis = random.randint(1, max_dis)
            dis_dict[str(i)][str(j)] = temp_dis
            dis_dict[str(j)][str(i)] = temp_dis
    return dis_dict, stay_dict


def plot_solution(best_obj_list, iter_best_obj_list):
    data = {
        'iter': [i for i in range(len(iter_best_obj_list))],
        'best_obj': best_obj_list,
        'iter_best_obj': iter_best_obj_list
    }
    df = pd.DataFrame(data)
    fig = px.line(df, x="iter", y=['best_obj', 'iter_best_obj'])
    fig.show()


if __name__ == "__main__":
    """
    條件：
    1. 走過所有點
    2. 加入各點停留時間
    3. buffer time
    4. obj: min duration time
    5. start time, end time
    5. 考慮營業時間
    """
    # plot_solution()
    start_time = time.time()
    num_node = 40

    initial_solution = [i for i in range(num_node)]
    dis_dict, stay_dict = rand_graph(
        num_nodes=num_node, max_dis=10, max_stay_time=30)
    pprint(dis_dict)
    pprint(stay_dict)
    max_iterations = 100
    tabu_list_size = 2 ** len(initial_solution)

    best_solution, best_obj, best_obj_list, iter_best_obj_list = tabu_search(
        initial_solution, max_iterations, tabu_list_size, dis_dict)
    total_staying_time = sum(stay_dict.values())
    best_obj -= total_staying_time
    logging.info(f"Best solution: {best_solution}")
    logging.info(
        f"Best solution obj: {best_obj}")
    end_time = time.time()
    execution_time = end_time-start_time
    logging.info(f"Excution time: {execution_time}")
    plot_solution(best_obj_list, iter_best_obj_list)
