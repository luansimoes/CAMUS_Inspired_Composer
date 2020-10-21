import random as rd
import music21 as m21
from music21 import stream, duration, chord, note
import sys


class CA:
    def __init__(self, cells, rule):
        self.cells = cells
        self.active = None
        self.updateActive()
        self.rule = rule
    
    def apply_rules(self):
        self.cells = self.rule(self.cells)
        self.updateActive()
        return self.active
    
    def updateActive(self):
        self.active = [i for i,cell in enumerate(self.cells) if cell]

class GameOfLife(CA):
    def __init__(self, cells, boundaries, neighbourhood_size):
        super().__init__(cells, boundaries)
        self.nh_size = neighbourhood_size
        self.updateActive()

    def get_neighbours(self, i, j):
        return [self.cells[lin%len(self.cells)][col%len(self.cells)] 
                        for lin in range((i-self.nh_size), (i+self.nh_size+1), 1)
                        for col in range((j-self.nh_size), (j+self.nh_size+1), 1)
                        if (lin!=i or col!=j)]

    def apply_rules(self):
        for i, row in enumerate(self.cells):
            for j in range(len(row)):
                self.cells[i][j] = self.update_cell(i, j)
        self.updateActive()
        return self.active
    
    def update_cell(self, i, j):
        if self.cells[i][j]:
            return int(self.rule[1]>=self.getAliveNeighbours(i,j)>=self.rule[0])
        else:
            return int(self.rule[3]>=self.getAliveNeighbours(i,j)>=self.rule[2])
    
    def getAliveNeighbours(self, i, j):
        return sum(self.get_neighbours(i, j))

    def updateActive(self):
        self.active = [[(i,j) for j,cell in enumerate(self.cells[i]) if cell] for i in range(len(self.cells))]
    

class DemonCyclicSpace(CA):
    def __init__(self, cells, neighbourhood_size, number_of_states, rule='self.update_cells'):
        super().__init__(cells, rule)
        self.nh_size = neighbourhood_size
        self.nr_states = number_of_states
    
    def get_neighbours(self, i, j):
        return [self.cells[lin%len(self.cells)][col%len(self.cells)] 
                        for lin in range((i-self.nh_size), (i+self.nh_size+1), 1)
                        for col in range((j-self.nh_size), (j+self.nh_size+1), 1)
                        if (lin!=i or col!=j)]
    
    #Verifica a existência do próximo estado na vizinhança
    def next_in_neighbourhood(self, i, j):
        neighbours = self.get_neighbours(i, j)
        return (self.cells[i][j]+1)%self.nr_states in neighbours
    
    def update_cells(self):
        return [[(self.cells[i][j]+1)%self.nr_states if self.next_in_neighbourhood(i, j) else self.cells[i][j] for j in range(len(self.cells[i]))] for i in range(len(self.cells))]
    
    def apply_rules(self):
        self.cells = eval(self.rule)()
        return self.cells





def xor(a,b):
    return int(bool(a)!=bool(b))

def chord_rule(cells):
    return [xor( cells[(i-1)%12], cells[(i+1)%12]) for i in range(len(cells))]

def generate_using_generic_chord_CA(input_cells, tam=10):
    chord_automata = CA(input_cells, chord_rule)
    harmony = [chord_automata.active] + [chord_automata.apply_rules() for i in range(tam-1)]
    return harmony

def generate_GOL_chord_CA(input_cells, boundaries, k=10):
    chord_automata = GameOfLife(input_cells, boundaries, 1)
    [chord_automata.apply_rules() for i in range(k-1)]
    harmony = [[cell[1] for cell in cells] for cells in chord_automata.apply_rules()]
    return harmony


