#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

# Imports
from collections import OrderedDict
from peewee import *
import datetime
import os
import random
import string
import sys

# If the python version is 2
if sys.version_info.major == 2:
    import __builtin__
    __builtin__.input = __builtin__.raw_input

# General Functions
def clear():
    """ Clear the screen """
    os.system('cls' if os.name == 'nt' else 'clear')

# General Classes
class Text:
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

# Setting up database
db = SqliteDatabase('tower_defense.db')

class Save_Entry(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    _base_health = IntegerField(default=0)
    _metal_shards = CharField(max_length=255, unique=False)
    _towers = TextField()
    _enemies = TextField()
    class Meta:
        database = db
if __name__ == '__main__':
    db.connect()
    db.create_tables([Save_Entry], safe=True)

# Game Variables
grid_max_x = 12
grid_max_y = 7
cells = []
for y in list(range(1, grid_max_y + 1)):
    for x in list(range(1, grid_max_x + 1)):
        cells.append((x, y))
towers = []
enemies = []
base_health = 3
metal_shards = 3.0

# Game Classes
class Point():
    def get_pair(self):
        """ Returns the data as a tuple """
        return (self.x, self.y)
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Tower():
    def get_scope(self):
        """ Returns a list of all points within the tower's range """
        scope = []
        position = self.location
        # Quadrant I
        for x in list(range(position.x, position.x + self.range + 1)):
            for y in list(range(position.y, position.y + self.range + 1)):
                if (x, y) in cells and (x, y) not in scope:
                    scope.append((x, y))
        # Quadrant II
        for x in list(range(position.x - self.range, position.x + 1)):
            for y in list(range(position.y, position.y + self.range + 1)):
                if (x, y) in cells and (x, y) not in scope:
                    scope.append((x, y))
        # Quadrant III
        for x in list(range(position.x - self.range, position.x + 1)):
            for y in list(range(position.y - self.range, position.y + 1)):
                if (x, y) in cells and (x, y) not in scope:
                    scope.append((x, y))
        # Quadrant IV
        for x in list(range(position.x, position.x + self.range + 1)):
            for y in list(range(position.y - self.range, position.y + 1)):
                if (x, y) in cells and (x, y) not in scope:
                    scope.append((x, y))
        return scope
    def get_symbol(self):
        """ Returns the correct symbol for the tower """
        if self.health == 2:
            return "+"
        elif self.health == 1:
            return "x"
    def all_data(self):
        """ Returns a full report of the instance """
        return self.location.get_pair() + (self.health, self.strength, self.range)
    def __init__(self, x, y, health=2, strength=1, range=1):
        self.location = Point(x, y)
        self.health = health
        self.strength = strength
        self.range = range

class Invader():
    def conquer(self):
        """ Moves forward and attacks any tower in front of it """
        global towers
        moved = False
        for index, tower in enumerate(towers):
            if (self.location.x + 1, self.location.y) == tower.location.get_pair():
                moved = True
                towers[index].health -= self.strength
                if towers[index].health < 1:
                    del towers[index]
        front_cell = (self.location.x + 1, self.location.y)
        if not moved and front_cell in cells:
            moved = False
            for index, enemy in enumerate(enemies):
                if enemy.location.get_pair() == front_cell:
                    moved = True
            if not moved:
                self.location.x += 1
    def get_symbol(self):
        """ Returns the correct symbol for the invader """
        if self.health == 2:
            return ">"
        elif self.health == 1:
            return "-"
    def all_data(self):
        """ Returns a full report of the instance """
        return self.location.get_pair() + (self.health, self.strength)
    def __init__(self, y, x=1, health=2, strength=1):
        self.location = Point(x, y)
        self.health = health
        self.strength = strength

# Game Functions
def game_over():
    """ Prompts player on wether to play again or not """
    play_again = input("Play Again? [Y]es/[N]o\n> ").strip().lower()
    if play_again == "y":
        os.execl(sys.executable, sys.executable, *sys.argv)
    elif play_again == "n":
        #sys.exit()
        print("[Program Ended]")
    else:
        print("Sorry, incorrect response:")
        game_over()

def quit():
    """ Asks the player if he/she wants to quit """
    confirmed = input("Quit? [Y]es/[N]o\n>").strip().lower()
    if confirmed == "y":
        game_over()
    elif confirmed == "n":
        draw_map()
    else:
        print("Sorry, incorrect response")
        quit()

def enemy_turn():
    """ Enemy side's turn """
    global enemies
    for index, enemy in enumerate(enemies):
        enemies[index].conquer()
        if enemy.location.x == grid_max_x:
            global base_health
            base_health -= 1
            del enemies[index]
            if base_health < 1:
                print("[Game Over]")
                game_over()
    if random.randint(1, 4) == 4:
        new_invader = Invader(random.randint(1, grid_max_y))
        overlapping = False
        global towers
        for index, tower in enumerate(towers):
            if tower.location.get_pair() == new_invader.location.get_pair():
                towers[index].health -= 1
                if towers[index].health < 1:
                    del towers[index]
                overlapping = True
        if not overlapping:
            enemies.append(new_invader)
    draw_map()

def finished_viewing(func):
    """ Asks player if he/she is done viewing and then runs a function """
    if input("Enter the letter d when you are done viewing:\n> ").strip().lower() == 'd':
        func()
    else:
        finished_viewing(func)

def attack_invaders():
    """ Attacks all enemies within range of towers """
    if input("Warning: after attacking invaders you will end your turn, is that okay? [Y]es/[N]o\n> ").strip().lower() == 'y':
        global towers
        global enemies
        for tower in towers:
            for index, enemy in enumerate(enemies):
                if enemy.location.get_pair() in tower.get_scope():
                    enemies[index].health -= tower.strength
                    if enemy.health < 1:
                        global metal_shards
                        metal_shards += 0.25
                        del enemies[index]
        draw_map(False)
        finished_viewing(enemy_turn)
    else:
        draw_map()

def view_key():
    """ Prints map key to command line """
    print("Gun Tower: +,   Damaged Gun Tower: x")
    print("Invader: >,   Damaged Invader: -")
    print("Base: *")
    finished_viewing(draw_map)

def add_tower():
    """ Buys a tower an places it to the point specified by the player """
    confirmed = input("You will need to use one metal shard, is that okay? [Y]es/[N]o\n> ").strip().lower()
    if confirmed == 'y':
        location = input("Gun Tower Location (format: LetterNumber, example: C3): ").strip().lower()
        global metal_shards
        # If there are enough metal shards
        if metal_shards >= 1.0:
            # And if the location specified is formatted correct
            if location[1:].isdigit() and location[0].isalpha():
                # And if the location is on the grid
                if int(location[1]) <= grid_max_x and ord(location[0]) - 96 <= grid_max_y:
                    overlapping = False
                    global towers
                    for tower in towers:
                        if tower.location.get_pair() == (int(location[1:]), ord(location[0]) - 96):
                            overlapping = True
                            print("Sorry, there's already a gun tower at that location.")
                            add_tower()
                    for enemy in enemies:
                        if enemy.location.get_pair() == (int(location[1:]), ord(location[0]) - 96):
                            overlapping = True
                            print("Sorry, there's currently an invader at that location.")
                            add_tower()
                    # And if there is nothing already at that point
                    if not overlapping:
                        metal_shards -= 1.0
                        towers.append(Tower(int(location[1:]), ord(location[0]) - 96))
                else:
                    print("Sorry, point not in the grid")
                    add_tower()
            else:
                print("Sorry, incorrect response.")
                add_tower()
        else:
            print("Sorry, not enough metal shards.")
            add_tower()
    elif confirmed != 'n':
        print("Sorry, incorrect response")
        add_tower()
    draw_map()

def save_data():
    """ Saves data to database """
    Save_Entry.create(_base_health=base_health, _metal_shards=str(metal_shards), _towers='-'.join([str(tower.all_data()) for tower in towers]), _enemies='-'.join([str(enemy.all_data()) for enemy in enemies]))
    draw_map()

def read_save_data():
    """ Reads save data and updates game variables """
    save_data = Save_Entry.select().order_by(Save_Entry.timestamp.desc()).get()
    global base_health
    base_health = save_data._base_health
    global metal_shards
    metal_shards = float(save_data._metal_shards)
    global towers
    towers = [tower[1:len(tower) - 1].split(",") for tower in save_data._towers.split("-")]
    try:
        towers = [Tower(int(tower[0]), int(tower[1]), int(tower[2]), int(tower[3]), int(tower[4])) for tower in towers]
    except:
        towers = []
    global enemies
    enemies = [enemy[1:len(enemy) - 1].split(",") for enemy in save_data._enemies.split("-")]
    try:
        enemies = [Invader(int(enemy[1]), int(enemy[0]), int(enemy[2]), int(enemy[3])) for enemy in enemies]
    except:
        enemies = []

def options():
    """ Shows the player his/her options and then asks and runs the next action """
    menu = OrderedDict([
        ('s', save_data),
        ('v', view_key),
        ('p', add_tower),
        ('a', attack_invaders),
        ('e', enemy_turn),
        ('q', quit)
    ])
    print("Options: [S]ave, [V]iew Key, [P]lace tower, [A]ttack Invaders, [E]nd Turn, [Q]uit")
    action = input("> ").lower().strip()
    if action in menu:
        menu[action]()
    else:
        print("Sorry, incorrect response")
        options()

def draw_map(show_options=True):
    """ Print the map to command line """
    clear()
    tile = '|' +  Text.BOLD + Text.UNDERLINE + '{}' + Text.END
    num2letter = dict(zip(range(1, 27), string.ascii_uppercase))
    print('\n')
    print("Base's Health: {}".format(base_health) + " " * 8 + "Metal Shards: {}".format(metal_shards))
    if grid_max_x < 10:
        more_than_nine = ""
    else:
        more_than_nine = " " + " ".join(list(u'\u2022' * (grid_max_x - 9)))
    print("  " + " ".join([str(num) for num in list(range(1, 10))]) + more_than_nine)
    for cell in cells:
        printed = False
        # If cell isn't part of the right edge
        if cell[0] < grid_max_x:
            if cell[0] == 1:
                if cell[1] > 26:
                    print(u'\u2022', end='')
                else:
                    print(num2letter[cell[1]], end='')
            global towers
            for index, tower in enumerate(towers):
                if cell == tower.location.get_pair():
                    printed = True
                    print(tile.format(towers[index].get_symbol()), end='')
            global enemies
            for index, enemy in enumerate(enemies):
                if cell == enemy.location.get_pair():
                    printed = True
                    print(tile.format(enemies[index].get_symbol()), end='')
            if not printed:
                print(tile.format(' '), end='')
        # If cell is part of the right edge
        elif cell[0] == grid_max_x:
            for index, tower in enumerate(towers):
                if cell == tower.location.get_pair():
                    printed = True
                    print(tile.format(towers[index].get_symbol()), end='|\n')
            for index, enemy in enumerate(enemies):
                if cell == enemy.location.get_pair():
                    printed = True
                    print(tile.format(enemies[index].get_symbol()), end='|*\n')
            if not printed:
                print(tile.format(' '), end='|*\n')
    if show_options:
        options()

# Start Game
def start_game():
    game_type = input("[N]ew Game or [L]oad Game?\n> ").lower().strip()
    if game_type == 'n':
       draw_map()
    elif game_type == 'l':
        try:
            read_save_data()
            draw_map()
        except:
            print("No save data found")
            start_game()
    else:
        print("Sorry, incorrect response")
        start_game()
start_game()
