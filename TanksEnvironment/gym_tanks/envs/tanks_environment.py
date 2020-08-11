import gym
from gym import spaces
from copy import deepcopy
import pygame

# Constants
NUM_ACTIONS = 5
"""
Actions are:
1: Up
2: Left
3: Down
4: Right
5: Shoot
"""
ACT_UP = 0
ACT_LEFT = 1
ACT_DOWN = 2
ACT_RIGHT = 3
ACT_SHOOT = 4

GRID_WIDTH = 62
GRID_HEIGHT = 47

# CELL CONSTANTS
CELL_GROUND = 0
CELL_WALL = 1
CELL_TANK_ME = 2
CELL_BULLET_ME = 3
CELL_TANK_ENEMY = 4
CELL_BULLET_ENEMY = 5

COLOR_GROUND = (209, 177, 161)
COLOR_WALL = (59, 1, 0)
COLOR_TANK_ME = (55, 55, 220)
COLOR_BULLET_ME = (27, 100, 255)
COLOR_TANK_ENEMY = (220, 0, 0)
COLOR_BULLET_ENEMY = (255, 69, 0)
COLOR_TREAD = (40, 40, 40)
COLOR_TREAD_DARK = (40, 40, 40)

MOVEMENT_SPEED = 1
SHOOT_COOLDOWN_LENGTH = 5

# class ArenaSpec():
#     def __init__(walls_function):
#         self.walls_function = walls_function

class Bullet:
    def __init__(self, init_pos, direction):
        self.position = init_pos
        self.direction = direction

    def __str__(self):
        return f"P:{self.position} D:{self.direction}"
    
    def __repr__(self):
        return f"P:{self.position} D:{self.direction}"

class State:
    def __init__(self, tank_me_pos, tank_enemy_pos, tank_me_dir, tank_enemy_dir, bullets = []):
        self.tank_me_pos = tank_me_pos
        self.tank_enemy_pos = tank_enemy_pos
        self.tank_me_dir = tank_me_dir
        self.tank_enemy_dir = tank_enemy_dir
        self.bullets = bullets

    def __str__(self):
        return f"Me: {self.tank_me_pos} - {self.tank_me_dir}\nEnemy:{self.tank_enemy_pos} - {self.tank_enemy_dir}\nBullets: {self.bullets}"

class TanksEnvironment(gym.Env):

    # TODO metadata?
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(TanksEnvironment, self).__init__()

        # Define action and observation space (gym.spaces objects)
        # We're using DISCRETE actions for simplicity's sake
        self.action_space = spaces.MultiBinary(NUM_ACTIONS) # TODO remove magic number

        # We're using output image as input?
        # self.observation_space = spaces.Box(low=0, high=64, shape=)

        # Initial variables
        self.shootCooldown = 0

        # SETUP PYGAME VISUAL OUTPUT
        w, h = GRID_WIDTH * 10, GRID_HEIGHT * 10
        self.screen = pygame.display.set_mode((w, h))
        self.screen.fill((255, 255, 255))
        self.trace = self.screen.copy()
        self.clock = pygame.time.Clock()

    def step(self, action):
        # Execute one time step in the environment

        if NUM_ACTIONS != len(action):
            assert(False)

        up = action[ACT_UP] and not action[ACT_DOWN]
        down = action[ACT_DOWN] and not action[ACT_UP]
        left = action[ACT_LEFT] and not action[ACT_RIGHT]
        right = action[ACT_RIGHT] and not action[ACT_LEFT]
        shoot = action[ACT_SHOOT]

        nextState = deepcopy(self.lastState)
        done = False
        reward = 0

        if up and left:
            # nextState.tank_me_dir = "nw"
            nextState.tank_me_dir = (-1, -1)
            nextState.tank_me_pos = (max(nextState.tank_me_pos[0] - 1, 0), max(nextState.tank_me_pos[1] - 1, 0))
        elif up and right:
            # nextState.tank_me_dir = "ne"
            nextState.tank_me_dir = (1, -1)
            nextState.tank_me_pos = (min(nextState.tank_me_pos[0] + 1, GRID_WIDTH), max(nextState.tank_me_pos[1] - 1, 0))
        elif up:
            # nextState.tank_me_dir = "n"
            nextState.tank_me_dir = (0, -1)
            nextState.tank_me_pos = (nextState.tank_me_pos[0], max(nextState.tank_me_pos[1] - 1, 0))
        elif down and left:
            # nextState.tank_me_dir = "sw"
            nextState.tank_me_dir = (-1, 1)
            nextState.tank_me_pos = (max(nextState.tank_me_pos[0] - 1, 0), min(nextState.tank_me_pos[1] + 1, GRID_HEIGHT))
        elif down and right:
            # nextState.tank_me_dir = "se"
            nextState.tank_me_dir = (1, 1)
            nextState.tank_me_pos = (min(nextState.tank_me_pos[0] + 1, GRID_WIDTH), min(nextState.tank_me_pos[1] + 1, GRID_HEIGHT))
        elif down:
            nextState.tank_me_dir = (0, 1)
            nextState.tank_me_pos = (nextState.tank_me_pos[0], min(nextState.tank_me_pos[1] + 1, GRID_HEIGHT))
        elif left:
            nextState.tank_me_dir = (-1, 0)
            nextState.tank_me_pos = (max(nextState.tank_me_pos[0] - 1, 0), nextState.tank_me_pos[1])
        elif right:
            nextState.tank_me_dir = (1, 0)
            nextState.tank_me_pos = (min(nextState.tank_me_pos[0] + 1, GRID_WIDTH), nextState.tank_me_pos[1])

        if not self.isFreeCell(nextState.tank_me_pos):
            nextState.tank_me_pos = self.lastState.tank_me_pos

        # No AI for now, so we just leave tank_enemy_pos and tank_enemy_dir
        
        self.shootCooldown = max(0, self.shootCooldown - 1)

        if shoot and not self.inShootCooldown():
            nextState.bullets.append(Bullet(nextState.tank_me_pos, nextState.tank_me_dir))
            self.shootCooldown = SHOOT_COOLDOWN_LENGTH
        
        # Iterate bullets
        newBullets = []
        for bullet in nextState.bullets:
            bullet.position = (bullet.position[0] + bullet.direction[0], bullet.position[1] + bullet.direction[1])
            newCellMaterial = self.__INITIAL_GRID[bullet.position[0]][bullet.position[1]]
            distance_x = abs(bullet.position[0] - self.lastState.tank_enemy_pos[0])
            distance_y = abs(bullet.position[1] - self.lastState.tank_enemy_pos[1])
            if distance_x <= 1 and distance_y <= 1:
                done = True
                reward = 1
            elif newCellMaterial != CELL_WALL:
                newBullets.append(bullet)
        nextState.bullets = newBullets

        self.updateGrid(nextState)

        info = self.grid

        self.lastState = nextState

        return nextState, reward, done, info

    def updateGrid(self, newstate):
        self.grid = deepcopy(self.__INITIAL_GRID)
        for x in [-1, 0, 1]:
            for y in [-1, 0, 1]:
                if (self.grid[newstate.tank_me_pos[0] + x][newstate.tank_me_pos[1] + y] != CELL_WALL) and (self.grid[newstate.tank_me_pos[0] + x][newstate.tank_me_pos[1] + y] != CELL_TANK_ENEMY):
                    self.grid[newstate.tank_me_pos[0] + x][newstate.tank_me_pos[1] + y] = CELL_TANK_ME
                self.grid[newstate.tank_enemy_pos[0] + x][newstate.tank_enemy_pos[1] + y] = CELL_TANK_ENEMY
        for bullet in newstate.bullets:
            self.grid[bullet.position[0]][bullet.position[1]] = CELL_BULLET_ME

    def getGrid(self):
        return self.grid

    def isFreeCell(self, loc):
        isWall = self.__INITIAL_GRID[loc[0]][loc[1]] == CELL_WALL
        isTank = loc == self.lastState.tank_enemy_pos
        return not isWall and not isTank

    def inShootCooldown(self):
        return self.shootCooldown > 0

    def reset(self):
        self.grid = [[0 for y in range(GRID_HEIGHT)] for x in range(GRID_WIDTH)]

        # Barrier walls
        for x in range(0, GRID_WIDTH):
            self.grid[x][0] = CELL_WALL
            self.grid[x][1] = CELL_WALL
            self.grid[x][GRID_HEIGHT - 2] = CELL_WALL
            self.grid[x][GRID_HEIGHT - 1] = CELL_WALL

        for y in range(0, GRID_HEIGHT):
            self.grid[0][y] = CELL_WALL
            self.grid[1][y] = CELL_WALL
            self.grid[GRID_WIDTH - 2][y] = CELL_WALL
            self.grid[GRID_WIDTH - 1][y] = CELL_WALL

        # Guard walls
        for y in range(17, GRID_HEIGHT-17):
            self.grid[10][y] = CELL_WALL
            self.grid[GRID_WIDTH-10-1][y] = CELL_WALL

        # Tank positions
            # self.grid[5][23] = CELL_TANK_ENEMY
            # self.grid[GRID_WIDTH-5-1][23] = CELL_TANK_ME

        self.__INITIAL_GRID = deepcopy(self.grid)

        initialState = State((GRID_WIDTH-5-1, 23), (5, 23), (-1, 0), (1, 0), [])

        self.updateGrid(initialState)

        self.lastState = initialState

        for row in self.grid:
            print(row)    

        # Reset to initial state

    def render(self, mode='human', close=False):
        pygame.event.get()
        self.screen.fill((255, 255, 255))
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                color = COLOR_GROUND
                if (self.grid[i][j] == CELL_WALL):
                    color = COLOR_WALL

                pygame.draw.rect(self.screen, color, (i * 10, j * 10, 10, 10))


        i, j = self.lastState.tank_enemy_pos
        self.drawTank(i, j, self.lastState.tank_enemy_dir, COLOR_TANK_ENEMY)

        i, j = self.lastState.tank_me_pos
        self.drawTank(i, j, self.lastState.tank_me_dir, COLOR_TANK_ME)
        

        for bullet in self.lastState.bullets:
            i, j = bullet.position
            pygame.draw.rect(self.screen, COLOR_BULLET_ME, (i * 10, j * 10, 10, 10))

        # Enemy bullets not currently implemented    

        self.clock.tick(60)
        pygame.display.update()
    
    def drawTank(self, i, j, tank_dir, TANK_COLOR):
        pygame.draw.rect(self.screen, TANK_COLOR, (i * 10, j * 10, 10, 10))
        if (tank_dir == (-1, -1) or tank_dir == (1, 1)):
            pygame.draw.rect(self.screen, TANK_COLOR, ((i-1) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, TANK_COLOR, ((i+1) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i-1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+0) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+0) * 10, (j+1) * 10, 10, 10))
        elif (tank_dir == (-1, 1) or tank_dir == (1, -1)):
            pygame.draw.rect(self.screen, TANK_COLOR, ((i-1) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, TANK_COLOR, ((i+1) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i-1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+0) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+0) * 10, (j+1) * 10, 10, 10))
        elif (tank_dir == (-1, 0) or tank_dir == (1, 0)):
            pygame.draw.rect(self.screen, TANK_COLOR, ((i-1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, TANK_COLOR, ((i+1) * 10, (j-0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+1) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD_DARK, ((i+0) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i-1) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+1) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD_DARK, ((i+0) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i-1) * 10, (j+1) * 10, 10, 10))
        elif (tank_dir == (0, -1) or tank_dir == (0, 1)):
            pygame.draw.rect(self.screen, TANK_COLOR, ((i-0) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, TANK_COLOR, ((i+0) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+1) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD_DARK, ((i+1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i+1) * 10, (j-1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i-1) * 10, (j+1) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD_DARK, ((i-1) * 10, (j+0) * 10, 10, 10))
            pygame.draw.rect(self.screen, COLOR_TREAD, ((i-1) * 10, (j-1) * 10, 10, 10))

    def close(self):
        pass

    @staticmethod
    def _isHit(tank_loc, bullet_loc):
        return TanksEnvironment._distance(tank_loc, bullet_loc) <= 1

    @staticmethod
    def _distance(loc1, loc2):
        return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

TanksEnvironment().reset()