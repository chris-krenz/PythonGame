# -*- coding: utf-8 -*-

"""
Simple 2D shooter game built using pygame as a personal project.
Github: https://github.com/chris-krenz/PythonGame
Demo:

Assets:
 - Images:
   - https://www.artstation.com/marketplace/p/9gW6/pumpkin-ghost-2d-character-sprite
   - https://www.artstation.com/marketplace/p/1MRv/big-hands-robot-2d-character-sprite
 - Music: https://www.chosic.com/download-audio/25500/

Sources:
 - https://www.pygame.org/wiki/GettingStarted
 - https://openbookproject.net/thinkcs/python/english3e/pygame.html
 - https://www.youtube.com/watch?v=i6xMBig-pP4 (Tim Ruscica)
"""

__author__ = "Chris Krenz"
__maintainer__ = "Chris Krenz"
__credits__ = "Chris Krenz and sources cited above."
__email__ = "ckrenz@bu.edu"

__copyright__ = "n/a"
__license__ = "n/a"

__version__ = "1.1"
__status__ = "Development"


import os
import pygame
import time
start_time = time.time()  # for profiling


os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()
clock = pygame.time.Clock()
zero = 0
score = 0
display = pygame.display.Info()
(width, height) = (display.current_w, display.current_h)  # Default 850, 500
pygame.display.set_caption('First Python Game')
win = pygame.display.set_mode((width, height), pygame.RESIZABLE)

os.chdir('C:/Users/Chris/PycharmProjects/HelloWorld/PythonGame')
bg = pygame.image.load('img/background/bg.jpg')
char = pygame.image.load('img/robot/Idle/Idle_000.png')

# Sound Effects.................................................................
proj_sound = pygame.mixer.Sound('snd/proj.wav')  # Should be .wav not .mp3
pygame.mixer.Sound.set_volume(proj_sound, 0.1)
hit_sound = pygame.mixer.Sound('snd/hit.wav')

# Music.........................................................................
pygame.mixer.Sound.set_volume(hit_sound, 0.1)
pygame.mixer.music.load('snd/Everyone_is_so_alive.mp3')
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)


class Player(object):
    """
    Object representing player's character. Single instance. Handles drawing,
    movement (walking, sprinting, jumping), and damage taken.
    """
    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vel: int = 4  # 2: slow walk/synced w/ gnd; ~10: sprint
        self.jump: float = 2        # spacebar
        self.jumping = False
        self.jumping_cnt = 10
        self.left = False           # left arrow
        self.right = False          # right arrow
        self.walking_cnt = 0
        self.face = self.idle[0]
        self.sprint: int = 5        # ctrl
        # 4 things in a tuple1 seen as rec (x, y, w, h) by draw.rect
        self.box = (self.x + 96, self.y + 64, 128, 128)

    path_idle = 'img/robot/Idle/'
    idle_files = [f for f in os.listdir(path_idle) if f.endswith('.png')]
    idle = []
    for name in idle_files:
        idle.append(
            pygame.image.load(os.path.join(path_idle, name)).convert_alpha())

    path_walk = 'img/robot/Walking/'
    walk_files = [f for f in os.listdir(path_walk) if f.endswith('.png')]
    walk = []
    for name in walk_files:
        walk.append(
            pygame.image.load(os.path.join(path_walk, name)).convert_alpha())

    def draw(self, win):
        """
        Draws the player's character and animations, also handling movement.
        :param win: display window
        """
        if self.walking_cnt >= 108:  # 36 sprites, each with 3 frames each
            self.walking_cnt = 0

        if self.left:
            win.blit(pygame.transform.flip(self.walk[self.walking_cnt // 3],
                                           True, False), (self.x, self.y))
            self.face = pygame.transform.flip(self.idle[0], True, False)
            self.walking_cnt += 1 + 2 * zero
        elif self.right:
            win.blit(self.walk[self.walking_cnt // 3], (self.x, self.y))
            self.face = self.idle[0]
            self.walking_cnt += 1 + 2 * zero
        else:
            win.blit(self.face, (self.x, self.y))
            self.walking_cnt = 0
        self.box = (self.x + 96, self.y + 64, 128, 128)
        # pygame.draw.rect(win, (255, 0, 0), self.box, 2)

    def hit(self):
        """
        Handles player being hit by MOB. Displays damage taken and resets the
        character's position (i.e. respawns).
        """
        self.jumping = False
        self.jumping_cnt = 10
        self.x = 250
        self.y = round(height * 0.6)
        self.walking_cnt = 0
        font1 = pygame.font.SysFont('couriernew', 100)  # for death note
        text = font1.render('-5', True, (255, 0, 0))
        win.blit(text, ((width // 2) -
                        (text.get_width() // 2), (height // 2) -
                        (text.get_height() // 2)))
        pygame.display.update()
        i = 0
        while i < 50:
            pygame.time.delay(10)
            i += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    i = 301
                    pygame.quit()


class Projectile(object):
    """
    Projectile object shot out from player. Multiple instances may be flying at
    once. Unaffected by gravity directly but affected by player's vector of
    motion (due to player input and/or gravity), so can be shot at almost any
    angle by jumping. Disappears on hitting MOB. Fire rate is limited.
    """
    def __init__(self, x: float, y: float, rad: float, 
                 color: tuple[int, int, int], facing: int, 
                 vert: int, vel: float):
        self.x = x
        self.y = y
        self.rad = rad
        self.color = color
        self.facing = facing
        self.vert = vert
        self.vel = facing * (vel + 8)

    def draw(self, win):
        """
        Draws the projectile
        :param win: display window
        """
        pygame.draw.circle(win, self.color, (self.x, self.y), self.rad)


class MOB(object):
    """
    Mobile OBjects that can both damage the player on contact or be damaged by
    the projectiles on contact. If they take sufficient damage, will disappear.
    Handles drawing, movement, and damage taken.
    """
    def __init__(self, x: float, y: float, w: float, h: float, end: float):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.end = end
        self.hpath = [self.x, self.end]
        self.vpath = [self.y, height * 0.1]
        self.walk_count = 0
        self.hvel = 9
        self.vvel = 9
        self.box = (self.x + 15, self.y + 6, 40, 50)
        self.hp = 100
        self.extant = True

    path_float = 'img/ghost/Idle/'
    float_files = [f for f in os.listdir(path_float) if f.endswith('.png')]
    float = []
    for name in float_files:
        float.append(
            pygame.image.load(os.path.join(path_float, name)).convert_alpha())

    def draw(self, win):
        """
        Draws the MOB's character and animations.
        :param win: display window
        """
        self.move()
        if self.extant:
            if self.walk_count + 1 >= 97:  # +1 is to offset for index being 0
                self.walk_count = 0

            if self.hvel > 0:
                win.blit(self.float[self.walk_count // 3], (self.x, self.y))
                self.walk_count += 1
            else:
                win.blit(pygame.transform.flip(self.float[self.walk_count // 3],
                                               True, False), (self.x, self.y))
                self.walk_count += 1
            self.box = (self.x + 96, self.y + 64, 128, 128)
            # pygame.draw.rect(win, (255, 0, 0), self.box, 2)
            pygame.draw.rect(win, (255, 0, 0),
                             (self.box[0], self.box[1] - 20, self.box[2], 10))
            pygame.draw.rect(win, (0, 0, 255),
                             (self.box[0], self.box[1] - 20,
                              self.box[2] - round((self.box[2]/100) *
                                                  (100 - self.hp)), 10))

    def move(self):
        """
        Handles MOB's automated movement. MOBs move continuously, unaffected by
        player or projectiles; movement only ends upon death.
        """
        if self.hvel > 0:
            if self.x <= self.hpath[1]:
                self.x += self.hvel
            else:
                self.hvel = -self.hvel
                self.walk_count = 0
        else:
            if self.x >= self.hpath[0]:
                self.x += self.hvel
            else:
                self.hvel = -self.hvel
                self.walk_count = 0

        if self.vvel > 0:
            if self.y >= self.vpath[1]:
                self.y -= self.vvel
            else:
                self.vvel = -self.vvel
                self.walk_count = 0
        else:
            if self.y <= self.vpath[0]:
                self.y -= self.vvel
            else:
                self.vvel = -self.vvel
                self.walk_count = 0

    def hit(self):
        """
        Handles MOB being hit by projectile.
        """
        if self.hp > 0:
            self.hp -= 50
        if self.hp <= 0:
            self.extant = False
        print('hit')


def redraw_win():
    """
    Continuously draws game window and (living) object within the game window.
    """
    # ~'blitting' == rendering
    win.blit(pygame.transform.scale(bg, (width, height)), (0, 0))
    text = font.render('Score: ' + str(score), True, (200, 200, 200))
    win.blit(text, (round((width / 2) - text.get_width()), round(height * 0.1)))
    robot.draw(win)
    mob.draw(win)
    for proj in projs:
        proj.draw(win)
    pygame.display.update()


# General game objects and meta vars............................................
font = pygame.font.SysFont('couriernew', 80, True, True)   # for Score
robot = Player(width // 2, round(height * 0.6), 256, 256)
mob = MOB(100, round(height * 0.6), 256, 256, width * 0.9)
projs = []
facing = 1
proj_timer = 5
safe_timer = 0
respawn_timer = 0


# ============================================================================ #
# MAIN LOOP
# ============================================================================ #
running = True
while running:
    clock.tick(27)  # 27

# Handling display and meta game events.........................................
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # In IDE, win may not close, so '.quit()'
            running = False
        if event.type == pygame.VIDEORESIZE:  # TODO: Improve adaptive resizing
            # old_surface = win
            display = pygame.display.Info()
            (width, height) = (event.w, event.h)
            win = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            # win.blit(old_surface, (0, 0))

# Player movement...............................................................
    keys = pygame.key.get_pressed()

    if keys[pygame.K_RCTRL] or keys[pygame.K_LCTRL]:
        zero = 1
    else:
        zero = 0

    if keys[pygame.K_LEFT] and robot.x > robot.vel:
        robot.x -= robot.vel * robot.sprint ** zero
        robot.left = True
        robot.right = False
        facing = -1
    elif keys[pygame.K_RIGHT] and robot.x < (width - robot.w - robot.vel):
        robot.x += robot.vel * robot.sprint ** zero
        robot.right = True
        robot.left = False
        facing = 1
    else:
        robot.right = False
        robot.left = False

    if not robot.jumping:
        if keys[pygame.K_UP]:
            robot.jumping = True
    else:
        if robot.jumping_cnt >= -10:
            neg = 1
            if robot.jumping_cnt < 0:
                neg = -1
            # Quadratic arc; round() to avoid float warning
            robot.y -= round((robot.jumping_cnt ** 2) * robot.jump * neg)
            robot.jumping_cnt -= 2
        else:
            robot.jumping = False
            robot.jumping_cnt = 10

# Handling projectiles..........................................................
    proj_timer += 1
    if keys[pygame.K_SPACE] and len(projs) < 10:
        if proj_timer >= 30:
            if robot.jumping:
                vert = robot.jumping_cnt
            else:
                vert = 0
            projs.append(
                Projectile(round(robot.x + robot.w // 2 + 35),
                           round(robot.y + robot.h // 2 + 32), 7, (225, 0, 0),
                           facing, vert, (robot.vel * 3) * robot.sprint ** zero)
            )
            proj_sound.play()
            proj_timer = 0

    for proj in projs:
        if mob.extant:
            if (proj.x + proj.rad >= mob.box[0]) and \
               (proj.x - proj.rad <= mob.box[0] + mob.box[2]):
                if (proj.y + proj.rad >= mob.box[1]) and \
                   (proj.y - proj.rad <= mob.box[1] + mob.box[3]):
                    mob.hit()
                    hit_sound.play()
                    score += 1
                    projs.pop(projs.index(proj))
        if 0 < proj.x < width:
            proj.x += proj.vel
            proj.y -= proj.vert
        else:
            projs.pop(projs.index(proj))

# Handling player-MOB interactions..............................................
    safe_timer += 1
    if mob.extant and safe_timer >= 10:
        if (robot.box[0] + robot.box[2] >= mob.box[0]) and \
                robot.box[0] <= (mob.box[0] + mob.box[2]):
            if (robot.box[1] + robot.box[3] >= mob.box[1]) and \
                    robot.box[1] <= (mob.box[1] + mob.box[3]):
                robot.hit()
                hit_sound.play()
                score -= 5
            safe_timer = 0

    if not mob.extant:
        respawn_timer += 1
        if respawn_timer >= 30:
            mob.extant = True
            mob.hp = 100
            respawn_timer = 0


# Redraw/loop end...............................................................
    redraw_win()

pygame.quit()
print("--- %s seconds ---" % (time.time() - start_time))
