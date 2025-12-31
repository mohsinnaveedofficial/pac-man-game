import pygame
import heapq
import random
from collections import deque


GRID_SIZE = 20
TILE = 25
WIDTH = GRID_SIZE * TILE
HEIGHT = GRID_SIZE * TILE
FPS = 40

WALL_PROB = 0.22
GHOST_REPLAN_FRAMES = 30
GHOST_MOVE_FRAMES = 15


WHITE = (240, 240, 240)
BLACK = (30, 30, 30)
YELLOW = (255, 200, 0)
RED = (220, 60, 60)
BLUE = (50, 120, 220)
GREY = (200, 200, 200)
GREEN = (100, 220, 100)
LIGHT_GREEN = (150, 255, 150)


BG_COLOR        = (22, 22, 28)
WALL_COLOR      = (50, 60, 90)
WALL_BORDER     = (80, 90, 130)
PATH_COLOR      = (70, 160, 255)
PLAYER_COLOR    = YELLOW
GHOST_COLOR     = RED
GOAL_COLOR      = (150, 255, 150)
GRID_LINE_COLOR = (60, 60, 80)



def in_bounds(pos):
    x, y = pos
    return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

def neighbors(pos):
    x, y = pos
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x+dx, y+dy
        if in_bounds((nx, ny)):
            yield (nx, ny)

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def generate_maze(start, ghost_start, prob=WALL_PROB):
    while True:
        grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if (x,y) in (start, ghost_start):
                    grid[y][x] = 0
                else:
                    grid[y][x] = 1 if random.random() < prob else 0
        
        sx, sy = start
        gx, gy = ghost_start
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if in_bounds((sx+dx, sy+dy)):
                    grid[sy+dy][sx+dx] = 0
                if in_bounds((gx+dx, gy+dy)):
                    grid[gy+dy][gx+dx] = 0
        if is_connected(grid, start, ghost_start):
            return grid

def is_connected(grid, a, b):
    q = deque()
    visited = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
    q.append(a)
    visited[a[1]][a[0]] = True
    while q:
        x,y = q.popleft()
        if (x,y) == b:
            return True
        for nx, ny in neighbors((x,y)):
            if not visited[ny][nx] and grid[ny][nx] == 0:
                visited[ny][nx] = True
                q.append((nx,ny))
    return False

def random_goal_cell(grid, player_pos, ghost_pos):
    empty_cells = []
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] == 0 and (x,y) != player_pos and (x,y) != ghost_pos:
                empty_cells.append((x,y))
    return random.choice(empty_cells) if empty_cells else (GRID_SIZE-2, 1)


def astar(grid, start, goal):
    if start == goal:
        return [start]

    open_heap = []
    heapq.heappush(open_heap, (0 + manhattan(start, goal), 0, start, None))
    came_from = {}
    g_score = {start:0}
    closed = set()

    while open_heap:
        f, g, current, parent = heapq.heappop(open_heap)
        if current in closed:
            continue
        came_from[current] = parent
        if current == goal:
            path = []
            node = current
            while node is not None:
                path.append(node)
                node = came_from.get(node)
            path.reverse()
            return path
        closed.add(current)
        for nb in neighbors(current):
            x,y = nb
            if grid[y][x]==1:
                continue
            tentative_g = g +1
            if nb in g_score and tentative_g >= g_score[nb]:
                continue
            g_score[nb] = tentative_g
            f_score = tentative_g + manhattan(nb, goal)
            heapq.heappush(open_heap,(f_score, tentative_g, nb, current))
    return []


class Player:
    def __init__(self,pos):
        self.pos = pos
    def move(self,direction,grid):
        dx,dy = direction
        nx, ny = self.pos[0]+dx, self.pos[1]+dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and grid[ny][nx]==0:
            self.pos = (nx,ny)


class Ghost:
    def __init__(self,pos,color=RED):
        self.pos = pos
        self.path = []
        self.target = None
        self.color = color
    def plan_path(self,grid,target):
        path = astar(grid,self.pos,target)
        self.path = path[1:] if len(path)>1 else []
        self.target = target
    def step_along_path(self):
        if self.path:
            self.pos = self.path.pop(0)



def draw_grid(surface, grid):
    surface.fill(BG_COLOR)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
            if grid[y][x]==1:
                pygame.draw.rect(surface, WALL_COLOR, rect, border_radius=5)
                pygame.draw.rect(surface, WALL_BORDER, rect, 2, border_radius=5)
            pygame.draw.rect(surface, GRID_LINE_COLOR, rect, 1)


def draw_path(surface, path):
    for (x,y) in path:
        cx = x*TILE + TILE//2
        cy = y*TILE + TILE//2
        pygame.draw.circle(surface, PATH_COLOR, (cx, cy), 5)

def draw_goal(surface, pos):
    x, y = pos
    rect = pygame.Rect(x*TILE+5, y*TILE+5, TILE-10, TILE-10)
    pygame.draw.rect(surface, GOAL_COLOR, rect, border_radius=6)



def draw_image(surface, image, pos):
    x, y = pos
    surface.blit(image, (x*TILE, y*TILE))



def show_intro(screen, font):
    screen.fill((15, 15, 25))

    title = font.render("PAC-MAN ", True, (255,255,255))
    controls = font.render("Use UP / DOWN / LEFT / RIGHT arrow keys ", True, (200,200,200))
    start_text = font.render("Press SPACE to start", True, (100,255,150))

    screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
    screen.blit(controls, controls.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))
    screen.blit(start_text, start_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80)))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False





def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pac-Man")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30)

  
    ghost_img = pygame.image.load("ghost.png").convert_alpha()
    ghost_img = pygame.transform.scale(ghost_img, (TILE, TILE))
   
    pacman_img = pygame.image.load("pacman.png").convert_alpha()
    pacman_img = pygame.transform.scale(pacman_img, (TILE, TILE))

    
    show_intro(screen, font)

    pac_start = (1,1)
    ghost_start = (GRID_SIZE-2, GRID_SIZE-2)
    grid = generate_maze(pac_start, ghost_start, WALL_PROB)

    player = Player(pac_start)
    ghost = Ghost(ghost_start)
    goal_cell = random_goal_cell(grid, pac_start, ghost_start)
    score = 0

    running = True
    game_over = False

    frame_count = 0
    ghost_move_timer = 0
    last_player_pos_for_replan = player.pos

    ghost.plan_path(grid, player.pos)

    while running:
        clock.tick(FPS)
        frame_count += 1
        ghost_move_timer += 1

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running = False
            if not game_over and event.type==pygame.KEYDOWN:
                if event.key==pygame.K_UP: player.move((0,-1),grid)
                elif event.key==pygame.K_DOWN: player.move((0,1),grid)
                elif event.key==pygame.K_LEFT: player.move((-1,0),grid)
                elif event.key==pygame.K_RIGHT: player.move((1,0),grid)

        if not game_over and (player.pos!=last_player_pos_for_replan or frame_count%GHOST_REPLAN_FRAMES==0):
            ghost.plan_path(grid,player.pos)
            last_player_pos_for_replan = player.pos

        if not game_over and ghost_move_timer >= GHOST_MOVE_FRAMES:
            ghost.step_along_path()
            ghost_move_timer = 0

        if ghost.pos == player.pos:
            game_over = True
        if player.pos == goal_cell:
            score += 1
            goal_cell = random_goal_cell(grid,player.pos,ghost.pos)

        draw_grid(screen,grid)
        draw_goal(screen, goal_cell)

        if ghost.path:
            draw_path(screen,[ghost.pos]+ghost.path)

        draw_image(screen, pacman_img, player.pos)
        draw_image(screen, ghost_img, ghost.pos)


        score_text = font.render(f"Score: {score}",True,(255,255,255))
        screen.blit(score_text,(10,10))

        if game_over:
            text = font.render("GAME OVER!",True,RED)
            screen.blit(text, text.get_rect(center=(WIDTH//2,HEIGHT//2)))
            sub = font.render("Press ESC or close window to quit",True,GREEN)
            screen.blit(sub, sub.get_rect(center=(WIDTH//2,HEIGHT//2+40)))

        pygame.display.flip()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

    pygame.quit()


if __name__=="__main__":
    main()
