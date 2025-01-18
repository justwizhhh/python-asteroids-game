import enum
import math
import random

import pyasge

class GameObject:

    def __init__(self):
        self.sprite = pyasge.Sprite()
        self.move_direction = [0.0, 0.0]

class AsteroidState(enum.Enum):
    LARGE = 0,
    MEDIUM = 1,
    SMALL = 2

class Asteroid(GameObject):
    def __init__(self):
        super().__init__()
        self.move_speed = 5
        self.min_scale = 1.7
        self.max_scale = 2.1
        self.max_spin_speed = 0.05

        self.large_state_score = 20
        self.medium_state_score = 50
        self.small_state_score = 100

        self.is_destroyed = False
        self.spinning_sprite = pyasge.Sprite()
        self.spin = 0
        self.current_state = AsteroidState.LARGE
        self.current_score = self.large_state_score

    def Move(self):
        self.sprite.x += self.move_direction[0] * self.move_speed
        self.sprite.y += self.move_direction[1] * self.move_speed

        # Visual sprite used primarily for spinning effect
        self.spinning_sprite.x = self.sprite.x
        self.spinning_sprite.y = self.sprite.y
        pass

    def Spin(self):
        self.spinning_sprite.rotation += self.spin

    def ResetState(self, orig_asteroid):
        match orig_asteroid.current_state:
            case AsteroidState.LARGE:
                self.current_state = AsteroidState.MEDIUM
                self.current_score = self.medium_state_score
                pass
            case AsteroidState.MEDIUM:
                self.current_state = AsteroidState.SMALL
                self.current_score = self.small_state_score
                pass
            case AsteroidState.SMALL:
                self.is_destroyed = True
                pass

        pass


class Ship(GameObject):
    def __init__(self):
        super().__init__()
        self.health = 5
        self.max_speed = 6.5
        self.acceleration = 0.1
        self.turn_speed = 5.25
        self.hurt_knockback = 4
        self.invincibility_timer = 2
        self.invincibility_flash = 0.05

        self.collisionSprite = pyasge.Sprite()
        self.hor_input = 0
        self.ver_input = 0
        self.current_health = self.health
        self.current_speed = 0
        self.current_angle = 0
        self.current_timer = 0
        self.current_flash_timer = 0

    def Accel(self):
        if self.current_speed < self.max_speed:
            self.current_speed += self.acceleration

        self.ResetMoveDir()
        pass

    def Decel(self):
        if self.current_speed > -self.max_speed:
            self.current_speed -= self.acceleration

        self.ResetMoveDir()
        pass

    def Turn(self, direction):
        # Direction should either be 1 or -1 (right or left)
        self.current_angle += self.turn_speed * direction if direction != 0 else 0
        pass

    def ResetMoveDir(self):
        self.move_direction[0] = math.cos(math.radians(self.current_angle))
        self.move_direction[1] = math.sin(math.radians(self.current_angle))

    def Move(self):
        # Physical ship movement
        self.collisionSprite.x += self.move_direction[0] * self.current_speed
        self.collisionSprite.y += self.move_direction[1] * self.current_speed

        # Visual ship movement
        self.sprite.rotation = math.radians(self.current_angle + 90)
        self.sprite.x = self.collisionSprite.x
        self.sprite.y = self.collisionSprite.y

        pass

    def Hurt(self, asteroid):
        # Applies damage and knockback to the player whenever they collide with an asteroid
        self.current_health -= 1
        self.current_angle = math.degrees(math.atan2(asteroid.sprite.y - self.sprite.y, asteroid.sprite.x - self.sprite.x))
        self.current_speed = -self.hurt_knockback
        self.current_timer = self.invincibility_timer

    def InvincibilityFlash(self):
        # Keeps track of the player's flashing animation when they get hurt
        if self.current_flash_timer <= 0:
            self.sprite.opacity = 0 if self.sprite.opacity == 255 else 255
            self.current_flash_timer = self.invincibility_flash


class Projectile(GameObject):
    def __init__(self):
        super().__init__()
        self.move_speed = 12.0
        self.life_span = 0.8

        self.is_shot = False
        self.current_life_span = 0

    def Move(self, delta_time):
        self.sprite.x += self.move_direction[0] * self.move_speed
        self.sprite.y += self.move_direction[1] * self.move_speed

        # Only allow the projectile to stay on screen for so long before getting destroyed
        self.current_life_span += delta_time
        if self.current_life_span >= self.life_span:
            self.Collision()

    def Collision(self):
        self.is_shot = False
        self.sprite.opacity = 0
        self.current_life_span = 0

        pass

class Alien(GameObject):
    def __init__(self):
        super().__init__()
        self.move_speed = 4.5
        self.turn_angle = 45.0
        self.spawn_margin = 100.0

        self.death_score = 200

        self.spawn_timer_min = 3
        self.spawn_timer_max = 11
        self.projectile_timer_time = 0.75
        self.player_distance_check = 400

        self.is_active = False
        self.is_timer_active = False
        self.escape_attempted = False
        self.spawn_timer = 0
        self.projectile_timer = 0

        pass

    def Move(self):
        self.sprite.x += self.move_direction[0] * self.move_speed
        self.sprite.y += self.move_direction[1] * self.move_speed

        pass

    def ChangeDirection(self, player):
        new_angle = round(math.degrees(math.atan2(
            self.sprite.y - player.sprite.y,
            player.sprite.x - self.sprite.x)))

        if -180 <= new_angle <= -90:
            new_angle = -135
        elif -90 <= new_angle <= 0:
            new_angle = -45
        elif 0 <= new_angle <= 90:
            new_angle = 45
        elif 90 <= new_angle <= 180:
            new_angle = 135

        self.move_direction[0] = math.cos(math.radians(new_angle))
        self.move_direction[1] = math.sin(math.radians(new_angle))

        self.escape_attempted = True

        pass

    def ResetTimer(self):
        self.spawn_timer = random.uniform(self.spawn_timer_min, self.spawn_timer_max)
        self.is_timer_active = True

        pass

class AlienProjectile(Projectile):
    def __init__(self):
        super().__init__()
        self.life_span = 0.65

        pass


class HealthIcon(GameObject):
    def __init__(self):
        super().__init__()

        pass