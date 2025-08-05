"""
A test of Wolfram's elementary cellular automata, inspired by The Coding Train
(https://thecodingtrain.com/challenges/179-wolfram-ca).

Written by Noah Emmanuel Ambard
"""

import pygame as pg
from random import randint, random, shuffle
from time import time
from typing import Literal


SCREEN_WIDTH = 800
SCREEN_HEIGHT: int = SCREEN_WIDTH

# The width and height of a cell in a generation
CELL_SIZE: float = 5

# The number of seconds that the delay between cycles should last for
CYCLE_DELAY_S: float = 2.5

# The number of cells in a generation
GENERATION_LEN: int = int(SCREEN_WIDTH / CELL_SIZE)

# The decimal number representation of the ruleset, or -1 to choose randomly
RULE_VALUE: int | Literal[-1] = -1 # 126

# Whether the program should cycle through new cellular automata
SHOULD_CYCLE = True

# Whether every ruleset should be used, or just the ones in RULES
USE_ALL_RULES = False

# A list of all the valid rulesets for this program
RULES = [1, 6, 7, 9, 18, 22, 26, 28, 30, 37, 41, 45, 50, 54, 57, 59, 60,
         61, 62, 65, 69, 70, 73, 74, 75, 77, 79, 81, 82, 84, 91, 92, 94,
         99, 101, 102, 105, 107, 109, 118, 121, 126, 129, 131, 132, 133,
         135, 137, 141, 143, 145, 146, 147, 149, 150, 151, 157, 158,
         161, 163, 166, 167, 169, 177, 182, 185, 188, 189, 195, 197,
         201, 203, 205, 206, 211, 212, 214, 215, 222, 225, 229, 230,
         241, 242, 246]


class Ruleset:
    """
    A ruleset mapping each possible combination of a binary cell and its
    neighbours to a new state, thus forming a set of rules
    """

    def __init__(self, rule_value: int):
        """
        Creates a ruleset mapping each possible combination of a binary cell
        and its neighbours to a new state out of its decimal representation,
        `rule_value`
        """

        # Each bit represents a new state for a cell
        rule_bin: str = bin(rule_value)[2:].rjust(8, "0")

        self._rules: dict[str, int] = {}

        # Map each possible combination of a binary cell and its neighbours to
        # a new state as specified by rule_value
        for i in range(8):
            neighbourhood: str = bin(7 - i)[2:].rjust(3, "0")
            self._rules[neighbourhood] = int(rule_bin[i])


    def get_rule(self, a: int, b: int, c: int) -> int:
        """
        Returns the new state for binary cell `b` given its current state and
        the states of its neighbours `a` and `c`
        """
        
        return self._rules[str(a) + str(b) + str(c)]


class Generation:
    """
    A one-dimensional generation of cells
    """
    
    def __init__(self, len: int):
        """
        Creates an empty one-dimensional generation of cells of length `len`
        """

        # Zero out the generation
        self._cells = [0] * len


    def draw(self, screen: pg.Surface, x: float, y: float,
             cell_size: float) -> None:
        """
        Draws this generation of cells at the given y level on the given screen

        Parameters
        __________

        screen: pg.Surface
            The screen to draw on
        x: float
            The x location to start drawing this generation at
        y: float
            The y location to start drawing this generation at
        cell_size: float
            The width and height of a cell
        """

        for i in range(self.get_len()):
            x1: float = x + i * cell_size
            y1 = y
            x2: float = x1 + cell_size
            y2: float = y1 + cell_size

            points = ((x1, y1), (x2, y1), (x2, y2), (x1, y2))
            c = 255 - self.get_cell(i) * 255

            # pg.draw.rect() with floating point values produces weird white
            # lines between cells on my computer, thus pg.draw.polygon()
            pg.draw.polygon(screen, (c, c, c), points)


    def evolve_copy(self, ruleset: Ruleset) -> "Generation":
        """
        Returns a new generation of cells evolved from this generation using
        `ruleset`
        """
        
        gen_len: int = self.get_len()
        new_generation = Generation(gen_len)
        
        # Transform each cell based off of its current state and its neighbours'
        # states
        for i in range(gen_len):
            prev_cell = self.get_cell((gen_len + i - 1) % gen_len)
            cell = self.get_cell(i)
            next_cell = self.get_cell((i + 1) % gen_len)

            new_generation.set_cell(i, ruleset.get_rule(prev_cell, cell, next_cell))
        
        return new_generation 


    def get_cell(self, index: int) -> int:
        """
        Returns the state of the cell at `index`
        """
        
        return self._cells[index]
    

    def set_cell(self, index: int, cell: int) -> None:
        """
        Sets the state of the cell at `index` to 0 if `cell` is 0 or 1 otherwise
        """
        
        self._cells[index] = 0 if cell == 0 else 1


    def get_len(self) -> int:
        """
        Returns the length of this generation
        """
        
        return len(self._cells)


    def randomize(self) -> None:
        """
        Randomizes the cells in this generation by first zero-ing it out, then
        adding one or more 1s
        """
        
        len: int = self.get_len()

        self._cells = [0] * len

        # Add one or more 1s randomly
        self.set_cell(randint(0, len - 1), 1)
        while random() < 0.5:
            self.set_cell(randint(0, len - 1), 1)


class State:
    """
    A structure holding global state information for the program
    """
    
    def __init__(self, screen: pg.Surface, clock: pg.time.Clock,
                 generation: Generation, cell_size: float, cycle_delay_s: float,
                 rule_value: int | Literal[-1], rules: list[int],
                 should_cycle: bool, screen_width: int, screen_height: int):
        """
        Initializes a structure holding global state information for the program

        Parameters
        __________

        screen: pg.Surface
            The application screen
        clock: pg.time.Clock
            The application clock
        generation: Generation
            The first generation of cells for the first cycle
        cell_size: float
            The width and height of a cell
        cycle_delay_s: float
            The number of seconds that the delay between cellular automata
            cycles should last for 
        rules: list[int]
            A list of decimal representations of all the rulesets that this
            program can use
        should_cycle: bool
            Whether this program should cycle through cellular automata
        screen_width: int
            The width of the application screen
        screen_height: int
            The height of the application screen
        """

        # The number of seconds that the delay between cellular automata
        # cycles should last for
        self.CYCLE_DELAY_S = cycle_delay_s

        # Whether the application should cycle through rulesets
        self.SHOULD_CYCLE = should_cycle
        
        self.SCREEN = screen
        self.CLOCK = clock

        self.cell_size = cell_size

        # The seconds that have passed since the delay between started
        self.cycle_delay_start_s: float = 0
        # Whether we are between cycles and should be delaying or not
        self.is_cycle_delay = False

        self.generations = [generation]
        self.gen_num = 0
        
        # Whether the main functionality of the program should be paused or not
        self.is_paused = False
        # Whether the application should still be running or not
        self.is_running = True

        # The x offset to centre the display; almost everything should use this
        self.off_x: float = 0
        # The y offset to centre the display; almost everything should use this
        self.off_y: float = 0

        # The current position in random_rules
        self.cycle_index = 0

        self.random_rules = rules
        shuffle(self.random_rules)

        # If rule_value is -1, start with a random rule, otherwise, start with
        # rule_value
        if rule_value == -1:
            self.ruleset = Ruleset(self.random_rules[self.cycle_index])
        else:
            self.ruleset = Ruleset(rule_value)

        self.screen_width = screen_width
        self.screen_height = screen_height


def reset(s: State) -> None:
    """
    Resets the application state for another cellular automata cycle
    """
    
    s.SCREEN.fill("white")

    # Create the first generation
    s.generations = [Generation(len(s.generations))]
    s.gen_num = 0
    s.generations[0].randomize()

    s.cycle_index += 1
    if s.cycle_index >= len(s.random_rules):
        s.cycle_index = 0
    
    s.ruleset = Ruleset(s.random_rules[s.cycle_index])


def render_cycle(s: State) -> None:
    """
    Renders one cellular automata cycle tick or takes a break in between cycles
    """

    if s.is_cycle_delay:
        # Wait for the delay between cycles to expire
        if time() - s.cycle_delay_start_s < s.CYCLE_DELAY_S:
            return
            
        reset(s)
        s.cycle_delay_start_s = 0
        s.is_cycle_delay = False

    new_y: float = s.off_y + (s.gen_num * s.cell_size)
    screen_bottom: float = s.screen_height - s.off_y

    if new_y + s.cell_size <= screen_bottom:
        # Draw the current generation
        s.generations[s.gen_num].draw(s.SCREEN, s.off_x, new_y, s.cell_size)
        
        # Evolve the generation
        s.generations += [s.generations[s.gen_num].evolve_copy(s.ruleset)]
        s.gen_num += 1
    else:
        if s.SHOULD_CYCLE:
            s.is_cycle_delay = True
            s.cycle_delay_start_s = time()
        else:
            s.is_paused = True


def resize_screen(event: pg.event.Event, s: State) -> None:
    """
    Resizes the screen, scaling cellular automata to fit. Exits early if `event`
    is not `pygame.WINDOWSIZECHANGED`
    """
    
    if event.type != pg.WINDOWSIZECHANGED:
        return
    
    # Calculates the difference in scale from the previous screen dimensions;
    # using min() because its the minimum dimension which has to change for
    # the scale to change:

    # I figured this formula out!!!
    delta_zoom: float = min(event.x, event.y) / min(s.screen_width, s.screen_height)
    s.screen_width = event.x
    s.screen_height = event.y
    
    s.cell_size *= delta_zoom
    
    # Calculate the new offsets to centre content:

    x_diff: int = s.screen_width - s.screen_height
    s.off_x = 0 if x_diff <= 0 else int(x_diff / 2)

    y_diff: int = s.screen_height - s.screen_width
    s.off_y = 0 if y_diff <= 0 else int(y_diff / 2)
    
    s.SCREEN.fill("white")

    s.SCREEN.lock()

    for y in range(s.gen_num):
        s.generations[y].draw(s.SCREEN, s.off_x, s.off_y + y * s.cell_size,
                              s.cell_size)

    s.SCREEN.unlock()


def setup() -> State:
    """
    Initializes the application
    """

    global CELL_SIZE, CYCLE_DELAY_S, GENERATION_LEN, RULE_VALUE, RULES, \
           SHOULD_CYCLE, SCREEN_WIDTH, SCREEN_HEIGHT, USE_ALL_RULES

    # Set the icon and title of the window
    pg.display.set_icon(pg.image.load("assets/icon.png"))
    pg.display.set_caption("Wolfram's Elementary Cellular Automata")

    # Set the size and flags for the window
    screen: pg.Surface = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                             pg.RESIZABLE)
    screen.fill("white")

    if USE_ALL_RULES:
        RULES = [i for i in range(256)]

    clock = pg.time.Clock()

    # Create the first generation
    generation = Generation(GENERATION_LEN)
    generation.randomize()

    return State(screen, clock, generation, CELL_SIZE, CYCLE_DELAY_S,
                 RULE_VALUE, RULES, SHOULD_CYCLE, SCREEN_WIDTH, SCREEN_HEIGHT)


def loop(s: State) -> None:
    """
    Runs one tick of the application
    """
    
    for event in pg.event.get():
        # Handle a quit request
        if event.type == pg.QUIT:
            s.is_running = False
        # Handle resizing the window
        elif event.type == pg.WINDOWSIZECHANGED:
            resize_screen(event, s)

    # Optimize by only locking once, before the drawing
    s.SCREEN.lock()

    if not s.is_paused:
        render_cycle(s) 

    # Optimize by only locking once, before the drawing
    s.SCREEN.unlock()

    # Display the new frame
    pg.display.flip()

    # TODO: Get actual refresh rate of display to prevent screen tearing
    s.CLOCK.tick(60)


if __name__ == "__main__":
    pg.init()

    state: State = setup()

    while state.is_running:
        loop(state)

pg.quit()
