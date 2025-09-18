import pygame
from vector import Vector2
from constants import *
from entity import Entity
from modes import ModeController
from sprites import GhostSprites

# VISION_RADIUS_TILES = 10

class Ghost(Entity):
    def __init__(self, node, pacman=None, blinky=None):
        Entity.__init__(self, node)
        self.pacman_without_walls = None
        self.can_see_pacman = None
        self.name = GHOST
        self.points = 200
        self.goal = Vector2()
        self.directionMethod = self.randomOrGoalDirection
        self.pacman = pacman
        self.mode = ModeController(self)
        self.blinky = blinky
        self.homeNode = node
        self.spawnNode = None
        self.visible = True
        self.baseSpeed = 100
        self.setSpeed(self.baseSpeed)
        self.force_chase = False
        self.difficulty = None
        self.vision_radius_tiles = 7
        self._vision_radius_px = self.vision_radius_tiles * TILEWIDTH

    def reset(self):
        Entity.reset(self)
        self.points = 200
        self.directionMethod = self.randomOrGoalDirection
        self.force_chase = False

    def update(self, dt):
        self.sprites.update(dt)
        self.mode.update(dt)
        # if self.mode.current is SCATTER:
        #     self.scatter()
        # if self.mode.current is CHASE:
        #    self.chase()
        Entity.update(self, dt)

    def scatter(self):
        self.goal = Vector2()

    def chase(self):
        self.goal = self.pacman.position

    def getChaseTarget(self): # for hard level
        if self.pacman is None:
            return self.goal
        return self.pacman.position.copy()

    def spawn(self):
        if self.spawnNode is not None:
            self.goal = self.spawnNode.position

    def setSpawnNode(self, node):
        self.spawnNode = node

    def startSpawn(self):
        self.mode.setSpawnMode()
        if self.mode.current == SPAWN:
            self.setSpeed(150)
            self.goal = Vector2()
            self.directionMethod = self.goalDirection
            self.spawn()

    def startFreight(self):
        self.mode.setFreightMode()
        if self.mode.current == FREIGHT:
            self.setSpeed(50)
            self.goal = Vector2()
            self.directionMethod = self.randomDirection

    def normalMode(self):
        self.setSpeed(self.baseSpeed)
        self.directionMethod = self.randomOrGoalDirection
        self.goal = Vector2()
        self.force_chase = False

    def randomOrGoalDirection(self, directions):
        if self.difficulty == "EASY":
            if self.canSeePacman():
                print(f"Ghost{self.name} saw a pacman!")
                self.goal = self.pacman.position.copy()
                return self.goalDirection(directions) # повертаємо напрямок (вгору...) за який найшвидше дійдемо до цілі

            random_direction = self.randomDirection(directions)
            neighbor_node = self.node.neighbors[random_direction]
            if neighbor_node:
                self.goal = neighbor_node.position

            return random_direction

        if self.difficulty == "HARD":
            # if self.force_chase and self.pacman is not None:
            #     self.goal = self.pacman.position.copy()
            #     return self.goalDirection(directions)

            self.can_see_pacman = self.canSeePacman()

            if self.can_see_pacman or self.force_chase and self.pacman is not None:
                print(f"Ghost {self.name} saw Pacman!")
                self.goal = self.getChaseTarget()
                return self.goalDirection(directions)

            random_direction = self.randomDirection(directions)
            neighbor_node = self.node.neighbors[random_direction]
            if neighbor_node:
                self.goal = neighbor_node.position
            return random_direction

        if self.difficulty == "MEDIUM":
            self.pacman_without_walls = self.pacmanWithoutWalls()

            if self.pacman_without_walls and self.pacman is not None:
                print(f"Ghost {self.name} saw Pacman!")
                self.goal = self.pacman.position.copy()
                return self.goalDirection(directions)

            random_direction = self.randomDirection(directions)
            neighbor_node = self.node.neighbors[random_direction]
            if neighbor_node:
                self.goal = neighbor_node.position
            return random_direction

    def pacmanWithoutWalls(self): # for hard level
        if self.pacman is None:
            return False

        dist = (self.pacman.position - self.position).magnitude()
        if dist > self._vision_radius_px:
            return False

        return True

    def canSeePacman(self):
        if self.pacman is None:
            return False

        dist = (self.pacman.position - self.position).magnitude()
        if dist > self._vision_radius_px:
            return False

        node_a = self.node
        node_b = self.pacman.node
        if node_a is None or node_b is None:
            return False

        same_row = (node_a.position.y == node_b.position.y)
        same_col = (node_a.position.x == node_b.position.x)
        if not (same_row or same_col):
            return False

        return self._hasStraightLineOfSight(node_a, node_b)

    def _hasStraightLineOfSight(self, node_a, node_b): # Якщо можна дійти до вузла Пакмена лише прямими кроками і не впертись у стіну -> лінія видимості
        if node_a is None or node_b is None:
            return False

        if node_a.position.y == node_b.position.y:
            direction = RIGHT if node_b.position.x > node_a.position.x else LEFT
            cur = node_a
            while cur is not None and cur is not node_b:
                nxt = cur.neighbors.get(direction)
                if nxt is None:
                    return False
                cur = nxt
            return cur is node_b

        elif node_a.position.x == node_b.position.x:
            direction = DOWN if node_b.position.y > node_a.position.y else UP
            cur = node_a
            while cur is not None and cur is not node_b:
                nxt = cur.neighbors.get(direction)
                if nxt is None:
                    return False
                cur = nxt
            return cur is node_b

        return False

    def renderDebug(self, screen):
        if self.goal is not None and self.visible:
            # Draw goal as a green circle
            goal_pos = self.goal.asInt()
            pygame.draw.circle(screen, WHITE, goal_pos, 8)

            # Draw line from ghost to goal
            pygame.draw.line(screen, WHITE, self.position.asInt(), goal_pos, 2)


class Blinky(Ghost):
    def __init__(self, node, pacman=None, blinky=None):
        Ghost.__init__(self, node, pacman, blinky)
        self.name = BLINKY
        self.color = RED
        self.sprites = GhostSprites(self)

    def getChaseTarget(self): # hard level
        if self.pacman is None:
            return self.goal
        # print(f"{self.name}ціль на 4 клітинки спереду пакмена")
        dir_vec = self.pacman.directions.get(self.pacman.direction, Vector2()) # взнаємо напрямок пакмена: вгору, вниз... та дістаємо вектор під цим напрямком
        return (self.pacman.position + dir_vec * TILEWIDTH * 4).copy()


class Pinky(Ghost):
    def __init__(self, node, pacman=None, blinky=None):
        Ghost.__init__(self, node, pacman, blinky)
        self.name = PINKY
        self.color = PINK
        self.sprites = GhostSprites(self)

    def scatter(self):
        self.goal = Vector2(TILEWIDTH*NCOLS, 0)

    # def chase(self):
    #     self.goal = self.pacman.position + self.pacman.directions[self.pacman.direction] * TILEWIDTH * 4


class Inky(Ghost):
    def __init__(self, node, pacman=None, blinky=None):
        Ghost.__init__(self, node, pacman, blinky)
        self.name = INKY
        self.color = TEAL
        self.sprites = GhostSprites(self)

    def scatter(self):
        self.goal = Vector2(TILEWIDTH*NCOLS, TILEHEIGHT*NROWS)

    # def chase(self):
    #     vec1 = self.pacman.position + self.pacman.directions[self.pacman.direction] * TILEWIDTH * 2
    #     vec2 = (vec1 - self.blinky.position) * 2
    #     self.goal = self.blinky.position + vec2


class Clyde(Ghost):
    def __init__(self, node, pacman=None, blinky=None):
        Ghost.__init__(self, node, pacman, blinky)
        self.name = CLYDE
        self.color = ORANGE
        self.sprites = GhostSprites(self)

    def scatter(self):
        self.goal = Vector2(0, TILEHEIGHT*NROWS)

    def getChaseTarget(self): # for hard level
        if self.pacman is None:
            return self.goal
        # print(f"{self.name}ціль на 4 клітинки спереду пакмена")
        dir_vec = self.pacman.directions.get(self.pacman.direction, Vector2())
        return (self.pacman.position + dir_vec * TILEWIDTH * 4).copy()

    # def chase(self):
    #     d = self.pacman.position - self.position
    #     ds = d.magnitudeSquared()
    #     if ds <= (TILEWIDTH * 8)**2:
    #         self.scatter()
    #     else:
    #         self.goal = self.pacman.position + self.pacman.directions[self.pacman.direction] * TILEWIDTH * 4


class GhostGroup(object):
    def __init__(self, node, pacman, difficulty="EASY"):
        self.show_Goals = False # for visible goal lines of ghosts
        self.blinky = Blinky(node, pacman)
        self.pinky = Pinky(node, pacman)
        self.inky = Inky(node, pacman, self.blinky)
        self.clyde = Clyde(node, pacman)
        self.ghosts = [self.blinky, self.pinky, self.inky, self.clyde]
        self.difficulty = difficulty
        for ghost in self.ghosts:
            ghost.difficulty = difficulty

            if difficulty == "EASY":
                ghost.vision_radius_tiles = 10
            elif difficulty == "MEDIUM":
                ghost.vision_radius_tiles = 7
            elif difficulty == "HARD":
                ghost.vision_radius_tiles = 7

    def __iter__(self):
        return iter(self.ghosts)

    def update(self, dt):
        if self.difficulty == "HARD":
            any_seen = False
            for g in self.ghosts:
                if g.canSeePacman():
                    any_seen = True
                    break

            for g in self.ghosts:
                if g.mode.current is SPAWN:
                    g.force_chase = False
                else:
                    g.force_chase = any_seen

                if g.force_chase and g.pacman is not None:
                    g.goal = g.getChaseTarget() # щоб Blinky and Clyde на чотири клітинки спереду були від позиції пакмена
                    g.can_see_pacman = True

            for ghost in self:
                ghost.update(dt)

        if self.difficulty == "EASY" or self.difficulty == "MEDIUM":
            for ghost in self:
                ghost.update(dt)

    def startFreight(self):
        for ghost in self:
            ghost.startFreight()
        self.resetPoints()

    def setSpawnNode(self, node):
        for ghost in self:
            ghost.setSpawnNode(node)

    def updatePoints(self):
        for ghost in self:
            ghost.points *= 2

    def resetPoints(self):
        for ghost in self:
            ghost.points = 200

    def hide(self):
        for ghost in self:
            ghost.visible = False

    def show(self):
        for ghost in self:
            ghost.visible = True

    def reset(self):
        for ghost in self:
            ghost.reset()

    def render(self, screen):
        for ghost in self:
            ghost.render(screen)
            if self.show_Goals: 
                ghost.renderDebug(screen)
    
            