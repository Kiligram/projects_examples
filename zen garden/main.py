import copy
import random
from random import randint

# ----------------- GENERAL PARAMETERS ------------------------
GENERATIONS_LIMIT = 600  # maximum number of created generations
DECISIONS_N = 5   # number of randomly generated decisions in every gene (decision is made by monk in case of obstacle)
GENERATION_SIZE = 50  # minimum number of individuals in every generation
ELITISM_N = 5   # number of the best individuals that will be moved to the new generation without roulette
# -------------------------------------------------------------
# ----------------- MUTATION CHANCES --------------------------
NEW_GENE_CHANCE = 1  # chance that one gene in chromosome will be replaced by randomly generated one (range 0-1)

# Garden sizes and stones can be set below in function "main"


class Gene:
    def __init__(self, s_row, s_column, decisions):
        self.s_row = s_row
        self.s_column = s_column
        self.decisions = decisions


def create_garden(rows, columns, stones):
    garden = [[0] * columns for _ in range(rows)]
    for i in range(len(stones)):
        garden[stones[i][0]][stones[i][1]] = -1

    return garden


# function makes the monk move through the garden according to the genes
def move(garden, rows, columns, gen, gen_number, direction):
    cur_row = gen.s_row
    cur_column = gen.s_column
    decision_index = 0
    if garden[cur_row][cur_column] != 0:   # check if there is an obstacle in the start
        return "obstacle in start"

    garden[cur_row][cur_column] = gen_number
    while 1:
        if direction == "right":

            # if the monk has come to the edge of the garden
            if cur_column + 1 == columns:
                return True

            # if there is an obstacle on the way of the monk
            if garden[cur_row][cur_column + 1] != 0:

                # decide where to go if the starting position is a corner
                if cur_row == rows - 1:
                    if garden[cur_row - 1][cur_column] == 0 and gen.decisions[decision_index] == 'l':
                        direction = "up"
                        cur_row -= 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                # decide where to go if the starting position is a corner
                elif cur_row == 0:
                    if garden[cur_row + 1][cur_column] == 0 and gen.decisions[decision_index] == 'r':
                        direction = "down"
                        cur_row += 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                # if the monk has stuck, stop and calculate the fitness
                elif garden[cur_row - 1][cur_column] != 0 and garden[cur_row + 1][cur_column] != 0:
                    return False

                # if there are two possibilities where to turn in case of obstacle
                elif garden[cur_row - 1][cur_column] == 0 and garden[cur_row + 1][cur_column] == 0:
                    if gen.decisions[decision_index] == 'r':
                        direction = "down"
                        cur_row += 1
                    elif gen.decisions[decision_index] == 'l':
                        direction = "up"
                        cur_row -= 1
                    decision_index = (decision_index + 1) % len(gen.decisions)

                # go up if it is the only possibility
                elif garden[cur_row - 1][cur_column] == 0:
                    direction = "up"
                    cur_row -= 1

                # go down if it is the only possibility
                elif garden[cur_row + 1][cur_column] == 0:
                    direction = "down"
                    cur_row += 1

                garden[cur_row][cur_column] = gen_number

            # if there are no obstacle on the way of monk, go forward
            else:
                cur_column += 1
                garden[cur_row][cur_column] = gen_number

        elif direction == "left":
            if cur_column == 0:
                return True
            if garden[cur_row][cur_column - 1] != 0:

                if cur_row == rows - 1:
                    if garden[cur_row - 1][cur_column] == 0 and gen.decisions[decision_index] == 'r':
                        direction = "up"
                        cur_row -= 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                elif cur_row == 0:
                    if garden[cur_row + 1][cur_column] == 0 and gen.decisions[decision_index] == 'l':
                        direction = "down"
                        cur_row += 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                elif garden[cur_row - 1][cur_column] != 0 and garden[cur_row + 1][cur_column] != 0:
                    return False

                elif garden[cur_row - 1][cur_column] == 0 and garden[cur_row + 1][cur_column] == 0:
                    if gen.decisions[decision_index] == 'l':
                        direction = "down"
                        cur_row += 1
                    elif gen.decisions[decision_index] == 'r':
                        direction = "up"
                        cur_row -= 1
                    decision_index = (decision_index + 1) % len(gen.decisions)

                elif garden[cur_row - 1][cur_column] == 0:
                    direction = "up"
                    cur_row -= 1

                elif garden[cur_row + 1][cur_column] == 0:
                    direction = "down"
                    cur_row += 1

                garden[cur_row][cur_column] = gen_number

            else:
                cur_column -= 1
                garden[cur_row][cur_column] = gen_number

        elif direction == "down":
            if cur_row + 1 == rows:
                return True
            if garden[cur_row + 1][cur_column] != 0:

                if cur_column == columns - 1:
                    if garden[cur_row][cur_column - 1] == 0 and gen.decisions[decision_index] == 'r':
                        direction = "left"
                        cur_column -= 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                elif cur_column == 0:
                    if garden[cur_row][cur_column + 1] == 0 and gen.decisions[decision_index] == 'l':
                        direction = "right"
                        cur_column += 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                elif garden[cur_row][cur_column - 1] != 0 and garden[cur_row][cur_column + 1] != 0:
                    return False

                elif garden[cur_row][cur_column - 1] == 0 and garden[cur_row][cur_column + 1] == 0:
                    if gen.decisions[decision_index] == 'r':
                        direction = "left"
                        cur_column -= 1
                    elif gen.decisions[decision_index] == 'l':
                        direction = "right"
                        cur_column += 1
                    decision_index = (decision_index + 1) % len(gen.decisions)

                elif garden[cur_row][cur_column - 1] == 0:
                    direction = "left"
                    cur_column -= 1

                elif garden[cur_row][cur_column + 1] == 0:
                    direction = "right"
                    cur_column += 1

                garden[cur_row][cur_column] = gen_number

            else:
                cur_row += 1
                garden[cur_row][cur_column] = gen_number

        elif direction == "up":
            if cur_row == 0:
                return True
            if garden[cur_row - 1][cur_column] != 0:

                if cur_column == columns - 1:
                    if garden[cur_row][cur_column - 1] == 0 and gen.decisions[decision_index] == 'l':
                        direction = "left"
                        cur_column -= 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                elif cur_column == 0:
                    if garden[cur_row][cur_column + 1] == 0 and gen.decisions[decision_index] == 'r':
                        direction = "right"
                        cur_column += 1
                        decision_index = (decision_index + 1) % len(gen.decisions)
                    else:
                        return True

                elif garden[cur_row][cur_column - 1] != 0 and garden[cur_row][cur_column + 1] != 0:
                    return False

                elif garden[cur_row][cur_column - 1] == 0 and garden[cur_row][cur_column + 1] == 0:
                    if gen.decisions[decision_index] == 'r':
                        direction = "right"
                        cur_column += 1
                    elif gen.decisions[decision_index] == 'l':
                        direction = "left"
                        cur_column -= 1
                    decision_index = (decision_index + 1) % len(gen.decisions)

                elif garden[cur_row][cur_column - 1] == 0:
                    direction = "left"
                    cur_column -= 1

                elif garden[cur_row][cur_column + 1] == 0:
                    direction = "right"
                    cur_column += 1

                garden[cur_row][cur_column] = gen_number

            else:
                cur_row -= 1
                garden[cur_row][cur_column] = gen_number


def fitness(garden, rows, columns, chromosome, print_flag):
    fitnessValue = 0
    genNum = 1
    garden_temp = copy.deepcopy(garden)
    for gen in chromosome:
        return_value = True
        if gen.s_column == 0:
            if gen.s_row == 0:  # if the starting point is (0, 0) (row, column)
                if gen.decisions[0] == 'r':     # if the first decision is 'r', the monk goes horizontally (to right)
                    return_value = move(garden_temp, rows, columns, gen, genNum, "right")
                else:
                    return_value = move(garden_temp, rows, columns, gen, genNum, "down")
            elif gen.s_row == rows - 1:
                if gen.decisions[0] == 'r':
                    return_value = move(garden_temp, rows, columns, gen, genNum, "right")
                else:
                    return_value = move(garden_temp, rows, columns, gen, genNum, "up")
            else:
                return_value = move(garden_temp, rows, columns, gen, genNum, "right")

        elif gen.s_column == columns - 1:
            if gen.s_row == 0:
                if gen.decisions[0] == 'r':
                    return_value = move(garden_temp, rows, columns, gen, genNum, "left")
                else:
                    return_value = move(garden_temp, rows, columns, gen, genNum, "down")
            elif gen.s_row == rows - 1:
                if gen.decisions[0] == 'r':
                    return_value = move(garden_temp, rows, columns, gen, genNum, "left")
                else:
                    return_value = move(garden_temp, rows, columns, gen, genNum, "up")
            else:
                return_value = move(garden_temp, rows, columns, gen, genNum, "left")

        elif gen.s_row == 0:
            return_value = move(garden_temp, rows, columns, gen, genNum, "down")
        elif gen.s_row == rows - 1:
            return_value = move(garden_temp, rows, columns, gen, genNum, "up")

        if not return_value:
            break

        if return_value != "obstacle in start":
            genNum += 1

    for row in garden_temp:
        for number in row:
            if number != 0 and number != -1:
                fitnessValue += 1

    if print_flag:
        printGarden(garden_temp)

    # print(fitnessValue)
    # printGarden(garden_temp)

    return fitnessValue


def printGarden(garden):
    print("-----------------------")
    for row in garden:
        for number in row:
            print(" " * (4 - len(str(number))), end="")
            if number == -1:
                print('\033[91m' + str(number) + '\033[0m', end="")
            else:
                print(number, end="")
        print("")


def find_duplicate_gene(chromosome, gene):
    for element in chromosome:
        if element.s_row == gene.s_row and element.s_column == gene.s_column:
            return True

    return False


def generate_gene(rows, columns):
    decisions = []
    for _ in range(DECISIONS_N):  # generate decisions that will be made in case of obstacle
        decisions.append('r' if randint(0, 1) else 'l')

    gene = None
    rand_num = randint(0, 3)
    if rand_num == 0:  # choose where the monk will start, 0 - left side, 1 - right side, 2 - top, 3 - bottom
        gene = Gene(randint(0, rows - 1), 0, decisions)
    elif rand_num == 1:
        gene = Gene(randint(0, rows - 1), columns - 1, decisions)
    elif rand_num == 2:
        gene = Gene(0, randint(0, columns - 1), decisions)
    elif rand_num == 3:
        gene = Gene(rows - 1, randint(0, columns - 1), decisions)

    return gene


def generate_chromosome(rows, columns, stones):
    chromosome = []
    amount = rows + columns + len(stones)
    i = 0
    while i < amount:
        gene = generate_gene(rows, columns)

        if find_duplicate_gene(chromosome, gene):
            continue

        chromosome.append(gene)
        i += 1

    return chromosome


def find_individual_in_roulette(fitness_values, position):
    index = 0
    sum_f = 0
    while index < len(fitness_values):
        sum_f += fitness_values[index]
        if sum_f >= position:
            break
        index += 1

    return index


def choose_by_roulette2(fitness_values, individuals, rows, columns):
    new_generation = []
    new_generation += get_the_best_individuals(fitness_values, individuals)
    fitness_sum = sum(fitness_values)

    while len(new_generation) < GENERATION_SIZE:
        chosen_individual1 = individuals[find_individual_in_roulette(fitness_values, randint(1, fitness_sum))]
        chosen_individual2 = individuals[find_individual_in_roulette(fitness_values, randint(1, fitness_sum))]
        if chosen_individual1 == chosen_individual2:
            continue

        new_generation += crossover(chosen_individual1, chosen_individual2, rows, columns)

    return new_generation


def get_the_best_individuals(fitness_values, individuals):
    best_individuals = []
    fitness_v_copy = copy.deepcopy(fitness_values)
    for _ in range(ELITISM_N):
        index = 0
        best = fitness_v_copy[0]
        best_index = 0
        while index < len(fitness_v_copy):
            if fitness_v_copy[index] > best:
                best = fitness_v_copy[index]
                best_index = index
            index += 1
        best_individuals.append(individuals[best_index])
        fitness_v_copy[best_index] = -1

    return best_individuals


def mutate_new_gen(chromosome, rows, columns):
    if random.random() <= NEW_GENE_CHANCE:
        gene = generate_gene(rows, columns)
        while find_duplicate_gene(chromosome, gene):
            gene = generate_gene(rows, columns)

        chromosome[randint(0, len(chromosome) - 1)] = gene


def crossover(first_individual, second_individual, rows, columns):
    new_individuals = []
    new_child1 = []
    new_child2 = []
    cross_point = randint(1, len(first_individual) - 1)

    new_child1 += copy.deepcopy(first_individual[:cross_point])
    new_child1 += copy.deepcopy(second_individual[cross_point:])

    new_child2 += copy.deepcopy(second_individual[:cross_point])
    new_child2 += copy.deepcopy(first_individual[cross_point:])

    i = 0
    while i < cross_point:  # find and eliminate the duplicity
        if find_duplicate_gene(new_child1[cross_point:], new_child1[i]):
            for gene in first_individual[cross_point:]:
                if not find_duplicate_gene(new_child1, gene):
                    new_child1[i] = copy.deepcopy(gene)
                    break

        if find_duplicate_gene(new_child2[cross_point:], new_child2[i]):
            for gene in second_individual[cross_point:]:
                if not find_duplicate_gene(new_child2, gene):
                    new_child2[i] = copy.deepcopy(gene)
                    break

        i += 1

    mutate_new_gen(new_child1, rows, columns)
    mutate_new_gen(new_child2, rows, columns)

    new_individuals.append(new_child1)
    new_individuals.append(new_child2)

    return new_individuals


def find_solution(garden, stones, rows, columns):
    individuals = []
    fitness_values = []
    for _ in range(GENERATION_SIZE):
        individuals.append(generate_chromosome(rows, columns, stones))

    for chromosome in individuals:
        fitness_values.append(fitness(garden, rows, columns, chromosome, False))

    # print(fitness_values)

    free_cells_in_garden = rows * columns - len(stones)
    found = False

    generation = 0
    for generation in range(GENERATIONS_LIMIT):
        print(f"Generation #{generation}. Average fitness: {int(sum(fitness_values) / len(fitness_values))}. Max: {max(fitness_values)}")
        if max(fitness_values) == free_cells_in_garden:
            found = True
            break
        individuals = choose_by_roulette2(fitness_values, individuals, rows, columns)
        fitness_values.clear()
        for chromosome in individuals:
            fitness_values.append(fitness(garden, rows, columns, chromosome, False))

    if found:
        print(f"Solution was found in generation #{generation}")
        fitness(garden, rows, columns, individuals[fitness_values.index(max(fitness_values))], True)
    else:
        print("Solutions was not found")
        print("The best individual: ")
        print(f"Fitness: {max(fitness_values)}")
        fitness(garden, rows, columns, individuals[fitness_values.index(max(fitness_values))], True)

    return generation


def test(generationsNumber, garden, stones, rows, columns):
    sumGenerations = 0
    for _ in range(generationsNumber):
        sumGenerations += find_solution(garden, stones, rows, columns)

    print(f"Average found in generation #{int(sumGenerations/10)}")


def main():

    # ----------GARDEN SETTINGS----------
    stones = [[2, 1],
              [1, 5],
              [3, 4],
              [4, 2],
              [6, 8],
              [6, 9]]
    rows = 10
    columns = 12
    # -----------------------------------

    garden = create_garden(rows, columns, stones)

    find_solution(garden, stones, rows, columns)

    # test(10, garden, stones, rows, columns)


main()
