import random
import math
import enum
import pyasge
import GameObject
from gamedata import GameData


def isInside(sprite_1: pyasge.Sprite, sprite_2: pyasge.Sprite, margin: float) -> bool:
    # 'margin' can be used to calculate collisions between scaled-down bounding boxes
    collision_x = sprite_1.x + (sprite_1.width * sprite_1.scale) - margin >= sprite_2.x + margin \
                  and sprite_2.x + (sprite_2.width * sprite_2.scale) - margin >= sprite_1.x + margin

    collision_y = sprite_1.y + (sprite_1.height * sprite_1.scale) - margin >= sprite_2.y + margin \
                  and sprite_2.y + (sprite_2.height * sprite_2.scale) - margin >= sprite_1.y + margin

    if collision_x and collision_y:
        return True
    pass


def isInsideText(object_sprite: pyasge.Sprite, text_sprite: pyasge.Text) -> bool:
    collision_x = object_sprite.x + (object_sprite.width * object_sprite.scale) >= text_sprite.x \
                  and text_sprite.x + text_sprite.width >= object_sprite.x

    collision_y = object_sprite.y + (object_sprite.height * object_sprite.scale) >= text_sprite.y - text_sprite.height \
                  and text_sprite.y >= object_sprite.y

    if collision_x and collision_y:
        return True
    pass


class GameState(enum.Enum):
    MAIN_MENU = 0,
    GAMEPLAY = 1,
    WIN_MENU = 2,
    LOSE_MENU = 3


class GameMode(enum.Enum):
    ENDLESS = 0,
    TIMED = 1


class MyASGEGame(pyasge.ASGEGame):
    # The main gameplay class

    def __init__(self, settings: pyasge.GameSettings):
        # Initialises the whole game
        # This includes the game settings, and global shared data

        pyasge.ASGEGame.__init__(self, settings)
        self.renderer.setClearColour(pyasge.COLOURS.BLACK)

        # create a game data object, we can store all shared game content here
        self.data = GameData()
        self.data.settings = settings
        self.data.inputs = self.inputs
        self.data.renderer = self.renderer
        self.data.game_res = [settings.window_width, settings.window_height]

        # register the key and mouse click handlers for this class
        self.key_id = self.data.inputs.addCallback(pyasge.EventType.E_KEY, self.keyHandler)
        self.mouse_id = self.data.inputs.addCallback(pyasge.EventType.E_MOUSE_CLICK, self.clickHandler)

        # -----------
        # -- Gameplay objects --
        # -----------
        self.current_game_state = GameState.MAIN_MENU
        self.current_game_mode = GameMode.ENDLESS

        # Initialising player ship
        self.player = GameObject.Ship()
        self.initPlayer()

        # Initialising the asteroids
        self.asteroids = []
        self.asteroid_max_count = 3

        self.asteroid_spawn_margin = 250
        self.asteroid_split_chunks = 2
        self.asteroid_split_rescale = 0.35

        for i in range(self.asteroid_max_count):
            self.asteroids.append(GameObject.Asteroid())
            self.initAsteroid(self.asteroids[i])

        # Initialising the player's projectiles
        self.projectiles = []
        self.max_projectiles = 3

        for i in range(self.max_projectiles):
            self.projectiles.append(GameObject.Projectile())
            self.initProjectile(self.projectiles[i])

        # Initialising the alien and its projectiles
        self.alien = GameObject.Alien()
        self.initAlien()

        self.alien_projectile = GameObject.AlienProjectile()
        self.initAlienProjectile()

        self.pause_option = 0
        self.data.time = self.data.max_time

        # -----------
        # -- UI objects --
        # -----------
        self.background = pyasge.Sprite()
        self.initBackground()

        # Main menu UI
        self.menu_title = None
        self.menu_endless_mode = None
        self.menu_timed_mode = None
        self.menu_retry = None
        self.menu_back_to_title = None
        self.menu_quit = None

        self.initMenu()

        # Gameplay screen UI
        self.scoreboard = None
        self.scoreboard_x_pos = 0
        self.initScoreboard()
        self.timer = None
        self.initTimer()
        self.health_icons = []
        for i in range(self.player.health):
            self.health_icons.append(GameObject.GameObject())
            self.initHealthIcon(self.health_icons[i], i)

        # Pause screen UI
        self.pause_text = None
        self.pause_continue_text = None
        self.pause_quit_text = None
        self.initPauseScreen()

        # Lose screen UI
        self.lose_text = None
        self.lose_score_text = None
        self.initLoseScreen(True)

        # Win screen UI
        self.win_text = None
        self.win_score_text = None
        self.initWinScreen()

    def setUpText(self, text_object, text_string, x_pos, y_pos, colour=pyasge.COLOURS.WHITE):
        text_object.string = text_string
        text_object.position = [x_pos, y_pos]
        text_object.colour = colour
        pass

    # -----------
    # -- Game object and UI initialisation --
    # -----------

    def initBackground(self) -> bool:
        if self.background.loadTexture("/data/images/custom/spaceBackground.png"):
            self.background.z_order = -15
            return True

    def initMenu(self) -> bool:
        # Initialising the title text
        self.data.fonts["MainFont"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 80)
        self.menu_title = pyasge.Text(self.data.fonts["MainFont"])
        self.setUpText(self.menu_title, "Too Many Asteroids", 310, 200, pyasge.COLOURS.CADETBLUE)

        self.data.fonts["SubFont"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 48)
        self.menu_endless_mode = pyasge.Text(self.data.fonts["SubFont"])
        self.menu_timed_mode = pyasge.Text(self.data.fonts["SubFont"])
        self.menu_retry = pyasge.Text(self.data.fonts["SubFont"])
        self.menu_back_to_title = pyasge.Text(self.data.fonts["SubFont"])
        self.menu_quit = pyasge.Text(self.data.fonts["SubFont"])

        self.setUpText(self.menu_endless_mode, "Endless Mode", 250, 500)
        self.setUpText(self.menu_timed_mode, "Timed Mode", 1000, 500)
        self.setUpText(self.menu_retry, "Retry", 250, 600)
        self.setUpText(self.menu_back_to_title, "Back to Title", 1000, 600)
        self.setUpText(self.menu_quit, "Quit", 725, 850)

        return True

    def initScoreboard(self) -> bool:
        # Initialising the text that will show the score
        self.data.fonts["ScoreFont"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 60)
        self.scoreboard = pyasge.Text(self.data.fonts["ScoreFont"])
        self.scoreboard_x_pos = 1510
        self.setUpText(self.scoreboard, "0", self.scoreboard_x_pos, 110)

        return True

    def initTimer(self) -> bool:
        # Initialising the timer display text
        self.data.fonts["TimerFont"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 40)
        self.timer = pyasge.Text(self.data.fonts["TimerFont"])
        self.setUpText(self.timer, "Time: 0:00", 70, 90)

        return True

    def initPauseScreen(self) -> bool:
        self.data.fonts["PauseText"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 60)
        self.data.fonts["PauseButtonText"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 45)

        self.pause_text = pyasge.Text(self.data.fonts["PauseText"])
        self.pause_continue_text = pyasge.Text(self.data.fonts["PauseButtonText"])
        self.pause_quit_text = pyasge.Text(self.data.fonts["PauseButtonText"])

        self.setUpText(self.pause_text, "Game Paused", 550, 240)
        self.setUpText(self.pause_continue_text, "Continue", 680, 500)
        self.setUpText(self.pause_quit_text, "Back to Title", 630, 580, pyasge.COLOURS.DARKGREY)

        return True

    def initLoseScreen(self, is_time_over) -> bool:
        # Initialising the game-over screen text when you die
        self.data.fonts["LoseText"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 46)
        self.lose_text = pyasge.Text(self.data.fonts["LoseText"])
        self.setUpText(self.lose_text,
                       ("Game Over! You have run out of health.", "Game Over! You have run out of time.")[is_time_over],
                       250, 380, pyasge.COLOURS.RED)

        self.data.fonts["ScoreText"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 46)
        self.lose_score_text = pyasge.Text(self.data.fonts["ScoreText"])
        self.setUpText(self.lose_score_text,
                       "Your final score is " + str(self.data.score) + "!",
                       500, 460)

        return True

    def initWinScreen(self) -> bool:
        # Initialising the game-over screen text when you win
        self.data.fonts["WinText"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 60)
        self.win_text = pyasge.Text(self.data.fonts["WinText"])
        self.setUpText(self.win_text, "You win!", 645, 300, pyasge.COLOURS.GREEN)

        self.data.fonts["ScoreText"] = self.data.renderer.loadFont("/data/fonts/KGHAPPY.ttf", 46)
        self.win_score_text = pyasge.Text(self.data.fonts["ScoreText"])
        self.setUpText(self.win_score_text,
                       "Your final score is " + str(self.data.score) + ".",
                       455, 390)
        self.win_score_text.x = (self.data.game_res[0] / 2) - (self.win_score_text.width / 2)

        return True

    def initPlayer(self) -> bool:
        # This code initialises the spaceship code, similar to how the fish were loaded in,
        # and positions it at the centre of the screen
        if self.player.sprite.loadTexture("data/images/kenney_simple-space/PNG/Retina/ship_G.png"):
            self.player.sprite.x = (self.data.game_res[0] / 2) - (self.player.sprite.width / 2)
            self.player.sprite.y = (self.data.game_res[1] / 2) - (self.player.sprite.height / 2)
            self.player.sprite.scale = 0.5

            # This code will ensure that player ship collisions remain consistent, you can leave it how it is
            self.player.collisionSprite.loadTexture("data/images/kenney_simple-space/PNG/Retina/ship_G.png")
            self.player.collisionSprite.x = self.player.sprite.x
            self.player.collisionSprite.y = self.player.sprite.y
            self.player.collisionSprite.scale = self.player.sprite.scale

            return True

        return False

    def initHealthIcon(self, health_icon, position) -> bool:
        # Initialising the health display graphics
        if health_icon.sprite.loadTexture("data/images/kenney_simple-space/PNG/Retina/ship_G.png"):
            health_icon.sprite.scale = 0.5

            health_icon.sprite.y = 150
            health_icon.sprite.x = 1465 - ((health_icon.sprite.width * 1.25 * position) * health_icon.sprite.scale)

            return True

        return False

    def initAsteroid(self, asteroid) -> bool:
        # Randomised textures for the asteroids
        self.texture_file = ""
        texture_index = random.randint(0, 3)
        match texture_index:
            case 0:
                self.texture_file = "/data/images/kenney_simple-space/PNG/Retina/meteor_detailedLarge.png"
                pass
            case 1:
                self.texture_file = "/data/images/kenney_simple-space/PNG/Retina/meteor_large.png"
                pass
            case 2:
                self.texture_file = "/data/images/kenney_simple-space/PNG/Retina/meteor_squareDetailedLarge.png"
                pass
            case 3:
                self.texture_file = "/data/images/kenney_simple-space/PNG/Retina/meteor_squareLarge.png"
                pass
            case _:
                self.texture_file = "/data/images/kenney_simple-space/PNG/Retina/meteor_large.png"
                pass

        if asteroid.sprite.loadTexture(self.texture_file):
            asteroid.sprite.z_order = -10
            asteroid.spinning_sprite.loadTexture(self.texture_file)

            # Set a position for the asteroids, while ensuring it never overlaps with the player's sprite
            asteroid.sprite.x = self.player.sprite.x
            while (self.player.sprite.x - self.asteroid_spawn_margin) <= asteroid.sprite.x <= (
                    self.player.sprite.x + self.asteroid_spawn_margin):
                asteroid.sprite.x = random.uniform(0, self.data.game_res[0]) + (asteroid.sprite.width / 2)

            asteroid.sprite.y = self.player.sprite.y
            while (self.player.sprite.y - self.asteroid_spawn_margin) <= asteroid.sprite.y <= (
                    self.player.sprite.y + self.asteroid_spawn_margin):
                asteroid.sprite.y = random.uniform(0, self.data.game_res[1]) + (asteroid.sprite.height / 2)

            # Randomised sprite rotation for visual effect
            asteroid.spinning_sprite.rotation = random.uniform(0.0, 1.0)
            asteroid.spin = random.uniform(-asteroid.max_spin_speed, asteroid.max_spin_speed)

            # Give the asteroid a randomised direction and size (scale)
            asteroid.move_direction = [random.uniform(1, -1), random.uniform(1, -1)]
            asteroid.sprite.scale = random.uniform(asteroid.min_scale, asteroid.max_scale)
            asteroid.spinning_sprite.scale = asteroid.sprite.scale

            asteroid.Move()
            return True
        return False

    def initProjectile(self, projectile) -> bool:
        if projectile.sprite.loadTexture("data/images/kenney_simple-space/PNG/Retina/star_small.png"):
            projectile.sprite.opacity = 0

            return True

        return False

    def initAlien(self):
        if self.alien.sprite.loadTexture("data/images/kenney_simple-space/PNG/Retina/enemy_E.png"):
            self.alien.sprite.z_order = -10

            self.alien.is_active = False
            self.alien.ResetTimer()

            self.spawnAlien()

            return True

        return False

    def initAlienProjectile(self) -> bool:
        if self.alien_projectile.sprite.loadTexture("data/images/kenney_simple-space/PNG/Retina/star_tiny.png"):
            self.alien_projectile.sprite.opacity = 0

            return True

        return False

    # -----------
    # -- Player input processing --
    # -----------

    def clickHandler(self, event: pyasge.ClickEvent) -> None:
        pass

    def resetKeys(self):
        self.player.hor_input = 0
        self.player.ver_input = 0

    def keyHandler(self, event: pyasge.KeyEvent) -> None:
        # Act only if a button has been pressed
        if event.action == pyasge.KEYS.KEY_PRESSED:

            # Closes the game whenever Escape is pressed regardless of game state
            if event.key == pyasge.KEYS.KEY_ESCAPE:
                exit()

            if self.data.is_game_running:
                # Main gameplay logic for when we are not paused or looking at a menu
                if event.key == pyasge.KEYS.KEY_SPACE:
                    self.spawnProjectile()

                # Player turning movement
                if event.key == pyasge.KEYS.KEY_LEFT:
                    self.player.hor_input -= 1
                if event.key == pyasge.KEYS.KEY_RIGHT:
                    self.player.hor_input += 1

                # Player accelerating and decelerating
                if event.key == pyasge.KEYS.KEY_UP:
                    self.player.ver_input += 1
                if event.key == pyasge.KEYS.KEY_DOWN:
                    self.player.ver_input -= 1

                # Pausing
                if event.key == pyasge.KEYS.KEY_ENTER:
                    if self.current_game_state == GameState.GAMEPLAY:
                        self.resetKeys()
                        self.pause_option = 0
                        self.pause_continue_text.colour = pyasge.COLOURS.WHITE
                        self.pause_quit_text.colour = pyasge.COLOURS.DARKGREY

                        self.data.is_game_running = False
            else:
                # Un-pausing
                if event.key == pyasge.KEYS.KEY_ENTER:
                    # Control given back to the player no matter what game state they are going to be in
                    self.data.is_game_running = True
                    self.resetKeys()
                    if self.pause_option == 1:
                        self.respawn(True)
                        self.current_game_state = GameState.MAIN_MENU

                # Pause menu navigation
                if event.key == pyasge.KEYS.KEY_UP:
                    self.pause_option = 0
                    self.pause_continue_text.colour = pyasge.COLOURS.WHITE
                    self.pause_quit_text.colour = pyasge.COLOURS.DARKGREY
                if event.key == pyasge.KEYS.KEY_DOWN:
                    self.pause_option = 1
                    self.pause_continue_text.colour = pyasge.COLOURS.DARKGREY
                    self.pause_quit_text.colour = pyasge.COLOURS.WHITE

            pass

        # This event is triggered whenever a button is released
        if event.action == pyasge.KEYS.KEY_RELEASED:
            if self.data.is_game_running:
                # Check if the player was pausing the game, to eliminate all previous inputs that might've been pressed
                # Player turning movement
                if event.key == pyasge.KEYS.KEY_LEFT:
                    self.player.hor_input += 1
                if event.key == pyasge.KEYS.KEY_RIGHT:
                    self.player.hor_input -= 1

                # Player accelerating and decelerating
                if event.key == pyasge.KEYS.KEY_UP:
                    self.player.ver_input -= 1
                if event.key == pyasge.KEYS.KEY_DOWN:
                    self.player.ver_input += 1

        pass

    # -----------
    # -- Gameplay functions --
    # -----------

    def startGame(self):
        self.player.collisionSprite.x = self.data.game_res[0] / 2 - self.player.sprite.width / 2
        self.player.collisionSprite.y = self.data.game_res[1] / 2 - self.player.sprite.height / 2
        self.current_game_state = GameState.GAMEPLAY

    def breakAsteroid(self, asteroid: GameObject.Asteroid):
        if asteroid.current_state != GameObject.AsteroidState.SMALL:
            for i in range(self.asteroid_split_chunks):
                new_asteroid = GameObject.Asteroid()
                self.asteroids.append(new_asteroid)
                self.initAsteroid(new_asteroid)

                # Spawn a new asteroid, and place it on the same position as the previous one
                new_asteroid.sprite.x = asteroid.sprite.x
                new_asteroid.spinning_sprite.x = new_asteroid.sprite.x
                new_asteroid.sprite.y = asteroid.sprite.y
                new_asteroid.spinning_sprite.y = new_asteroid.sprite.y

                # Set up the asteroid with a randomised size like in 'initAsteroid'
                new_asteroid.sprite.scale = (asteroid.sprite.scale * self.asteroid_split_rescale) * random.uniform(
                    new_asteroid.min_scale,
                    new_asteroid.max_scale)
                new_asteroid.spinning_sprite.scale = new_asteroid.sprite.scale

                new_asteroid.ResetState(asteroid)

        asteroid.is_destroyed = True
        pass

    def screenWrap(self, game_object: pyasge.Sprite):
        # Target object's position is checked every frame
        # If it exceeds the screen, wrap the position back around

        # TO DO --- REWRITE USING WORLD BOUNDS MAYBE ---

        if game_object.x > self.data.game_res[0] + (game_object.width * game_object.scale):
            game_object.x = -game_object.width * game_object.scale + 0.1
        if game_object.x < -game_object.width * game_object.scale:
            game_object.x = self.data.game_res[0] + (game_object.width * game_object.scale) + 0.1

        if game_object.y > self.data.game_res[1] + (game_object.height * game_object.scale):
            game_object.y = -game_object.height * game_object.scale + 0.1
        if game_object.y < -game_object.height * game_object.scale:
            game_object.y = self.data.game_res[1] + (game_object.height * game_object.scale) + 0.1

        pass

    def playerHurt(self, other_object) -> None:
        if self.player.current_timer <= 0:
            if self.player.current_health > 1:
                self.player.Hurt(other_object)
            else:
                self.initLoseScreen(False)
                self.current_game_state = GameState.LOSE_MENU

        pass

    def spawnProjectile(self) -> None:
        # Find a projectile in the 'projectiles' array which is not being used right now
        for i in range(self.max_projectiles):
            if not self.projectiles[i].is_shot:
                # Set up the new object and ready it for movement
                new_projectile = self.projectiles[i]

                new_projectile.sprite.opacity = 1
                new_projectile.sprite.x = self.player.sprite.x
                new_projectile.sprite.y = self.player.sprite.y
                new_projectile.move_direction[0] = math.cos(math.radians(self.player.current_angle))
                new_projectile.move_direction[1] = math.sin(math.radians(self.player.current_angle))

                new_projectile.is_shot = True
                break
            else:
                continue

        pass

    def projectileScreenDelete(self, projectile: GameObject.Projectile()) -> None:
        # -- UNUSED --
        # Check if a projectile is off-screen or not
        # If it exceeds the screen resolution, delete the projectile
        if projectile.is_shot:
            if projectile.sprite.x < (0 - projectile.sprite.width) or projectile.sprite.x > (
                    self.data.game_res[0] + projectile.sprite.width) \
                    or projectile.sprite.y < (0 - projectile.sprite.height) or projectile.sprite.y > (
                    self.data.game_res[1] + projectile.sprite.height):
                projectile.is_shot = False
                projectile.sprite.opacity = 0

                pass
        pass

    def spawnAlien(self) -> None:
        self.alien.is_active = False
        self.alien.escape_attempted = False

        # Spawns the current alien on the left/right side of the screen before allowing it to move
        spawn_side = random.randint(0, 1)

        # Configuring spawn position and move direction
        if spawn_side == 1:
            self.alien.sprite.x = self.data.game_res[0] + self.alien.sprite.width
        else:
            self.alien.sprite.x = -self.alien.sprite.width

        self.alien.sprite.y = random.randint(self.alien.spawn_margin, self.data.game_res[1]
                                             - self.alien.spawn_margin
                                             - self.alien.sprite.height)

        self.alien.move_direction[0] = -((spawn_side * 2) - 1)
        self.alien.move_direction[1] = 0

        pass

    def spawnAlienProjectile(self) -> None:
        self.alien.projectile_timer = self.alien.projectile_timer_time

        # Set up the projectile and its position/angle
        projectile = self.alien_projectile

        projectile.sprite.opacity = 1
        projectile.sprite.x = self.alien.sprite.x
        projectile.sprite.y = self.alien.sprite.y

        new_angle = math.degrees(
            math.atan2(self.player.sprite.y - projectile.sprite.y, self.player.sprite.x - projectile.sprite.x))
        projectile.move_direction[0] = math.cos(math.radians(new_angle))
        projectile.move_direction[1] = math.sin(math.radians(new_angle))

        projectile.is_shot = True

        pass

    def updateScore(self, score):
        self.data.score += score
        self.scoreboard.string = str(self.data.score)

        pass

    def respawn(self, full_restart: bool):
        self.asteroids.clear()

        for i in range(self.asteroid_max_count):
            self.asteroids.append(GameObject.Asteroid())
            self.initAsteroid(self.asteroids[i])

        if full_restart:
            # Reset player position and speed
            self.player.opacity = 0
            self.player.current_health = self.player.health

            # Remove all on-screen instances of projectiles, aliens, and alien projectiles
            for i in range(self.max_projectiles):
                if self.projectiles[i].is_shot:
                    self.projectiles[i].is_shot = False
                    self.projectiles[i].sprite.opacity = 0

            self.spawnAlien()
            if self.alien_projectile.is_shot:
                self.alien_projectile.is_shot = False
                self.alien_projectile.sprite.opacity = 0

            self.data.time = self.data.max_time
            self.data.score = 0
            self.scoreboard.string = str(self.data.score)
        pass

    # -----------
    # -- Update functions --
    # -----------

    def update(self, game_time: pyasge.GameTime) -> None:

        if self.data.is_game_running:
            # -- Object movements --
            # Player movements
            if self.player.ver_input != 0:
                if self.player.ver_input == 1:
                    self.player.Accel()
                if self.player.ver_input == -1:
                    self.player.Decel()
            else:
                # If the player's speed is close enough to zero, stop applying acceleration/deceleration
                if not (-self.player.acceleration < self.player.current_speed < self.player.acceleration):
                    self.player.current_speed -= \
                        self.player.acceleration * math.copysign(1, self.player.current_speed)
                else:
                    self.player.current_speed = 0

            self.player.Move()
            self.screenWrap(self.player.collisionSprite)
            self.player.Turn(self.player.hor_input)

            # Check if there are still any asteroids to move around
            # If not, respawn all of them
            if all(element.is_destroyed is True for element in self.asteroids):
                self.respawn(False)
            else:
                for asteroid in self.asteroids:
                    # Asteroid collisions and movements
                    if self.current_game_state == GameState.GAMEPLAY:
                        if not asteroid.is_destroyed:
                            self.screenWrap(asteroid.sprite)
                            asteroid.Move()
                            asteroid.Spin()

                            if isInside(self.player.sprite, asteroid.sprite, 0):
                                self.playerHurt(asteroid)
                                self.breakAsteroid(asteroid)

                            if isInside(self.player.sprite, self.alien.sprite, 0):
                                self.playerHurt(asteroid)

                    # Projectile collisions
                    for projectile in self.projectiles:
                        if projectile.is_shot:

                            # Menu interactions
                            if self.current_game_state == GameState.MAIN_MENU:
                                if isInsideText(projectile.sprite, self.menu_endless_mode):
                                    projectile.Collision()
                                    self.current_game_mode = GameMode.ENDLESS
                                    self.startGame()

                                if isInsideText(projectile.sprite, self.menu_timed_mode):
                                    projectile.Collision()
                                    self.current_game_mode = GameMode.TIMED
                                    self.startGame()

                                if isInsideText(projectile.sprite, self.menu_quit):
                                    exit(0)

                            elif self.current_game_state == GameState.WIN_MENU \
                                    or self.current_game_state == GameState.LOSE_MENU:
                                if isInsideText(projectile.sprite, self.menu_retry):
                                    projectile.Collision()
                                    self.current_game_state = GameState.GAMEPLAY
                                    self.respawn(True)

                                if isInsideText(projectile.sprite, self.menu_back_to_title):
                                    projectile.Collision()
                                    self.current_game_state = GameState.MAIN_MENU
                                    self.respawn(True)

                            # Gameplay interactions
                            elif self.current_game_state == GameState.GAMEPLAY:
                                if isInside(asteroid.sprite, projectile.sprite, 0.2):
                                    if not asteroid.is_destroyed:
                                        self.updateScore(asteroid.current_score)

                                        projectile.Collision()
                                        self.breakAsteroid(asteroid)

                                if isInside(self.alien.sprite, projectile.sprite, 0.2):
                                    self.updateScore(self.alien.death_score)

                                    projectile.Collision()
                                    self.spawnAlien()
                                    self.alien.ResetTimer()

            for projectile in self.projectiles:
                if projectile.is_shot:
                    projectile.Move(game_time.fixed_timestep)
                    self.screenWrap(projectile.sprite)

            # Alien logic
            if self.current_game_state is GameState.GAMEPLAY:
                if self.alien.is_active is True:
                    self.alien.Move()

                    # Checking the distance between it and the player object
                    if not self.alien.escape_attempted:
                        p = [self.alien.sprite.x, self.alien.sprite.y]
                        q = [self.player.sprite.x, self.player.sprite.y]
                        distance = math.dist(p, q)
                        if distance <= self.alien.player_distance_check:
                            self.alien.ChangeDirection(self.player)

                    # Respawning checks
                    if self.alien.sprite.x >= self.data.game_res[0] + (self.alien.sprite.width * 2) \
                            or self.alien.sprite.x <= (-self.alien.sprite.width * 2):
                        self.spawnAlien()
                        self.alien.ResetTimer()

                    if self.alien.sprite.y >= self.data.game_res[1] + (self.alien.sprite.height * 2) \
                            or self.alien.sprite.y <= (-self.alien.sprite.height * 2):
                        self.spawnAlien()
                        self.alien.ResetTimer()

                # Projectile logic
                if self.alien_projectile.is_shot:
                    self.alien_projectile.Move(game_time.fixed_timestep)
                    self.screenWrap(self.alien_projectile.sprite)

                    if isInside(self.player.sprite, self.alien_projectile.sprite, 0.2):
                        self.alien_projectile.Collision()
                        self.playerHurt(self.alien_projectile)

            # -- UI updates --
            self.scoreboard.x = self.scoreboard_x_pos - self.scoreboard.width

    pass

    def fixed_update(self, game_time: pyasge.GameTime) -> None:
        if self.current_game_state == GameState.GAMEPLAY:
            if self.data.is_game_running:
                # Gameplay timer when the player gets hurt and temporarily becomes invincible
                if self.player.current_timer >= 0:
                    self.player.current_timer -= game_time.fixed_timestep
                    self.player.current_flash_timer -= game_time.fixed_timestep
                    self.player.InvincibilityFlash()

                # Timer for alien AI
                if self.alien.is_timer_active:
                    if self.alien.spawn_timer >= 0:
                        self.alien.spawn_timer -= game_time.fixed_timestep
                    else:
                        self.alien.is_active = True

                if not self.alien_projectile.is_shot and self.alien.is_active:
                    if self.alien.projectile_timer >= 0:
                        self.alien.projectile_timer -= game_time.fixed_timestep
                    else:
                        self.spawnAlienProjectile()

                # UI timer for showing the player how much time they have left
                if self.current_game_mode == GameMode.TIMED:
                    self.data.time -= game_time.fixed_timestep
                    minutes, seconds = divmod(self.data.time, 60)
                    self.timer.string = "Time: " + str(math.floor(minutes)) + ":" + \
                                        ("0" if len(str(math.floor(seconds))) == 1 else "") + str(math.floor(seconds))

                    if self.data.time <= 0:
                        # Checking for win conditions
                        if self.data.score >= self.data.max_score:
                            self.initWinScreen()
                            self.current_game_state = GameState.WIN_MENU
                        else:
                            self.initLoseScreen(True)
                            self.current_game_state = GameState.LOSE_MENU

                        self.respawn(True)

        pass

    # -----------
    # -- Rendering --
    # -----------

    def render(self, game_time: pyasge.GameTime) -> None:
        """
        This is the variable time-step function. Use to update
        animations and to render the game-world. The use of
        ``frame_time`` is essential to ensure consistent performance.
        @param game_time: The tick and frame deltas.
        """

        self.data.renderer.render(self.player.sprite)
        for i in range(self.max_projectiles):
            self.data.renderer.render(self.projectiles[i].sprite)

        match self.current_game_state:
            case GameState.MAIN_MENU:
                self.data.renderer.render(self.menu_title)
                self.data.renderer.render(self.menu_endless_mode)
                self.data.renderer.render(self.menu_timed_mode)
                self.data.renderer.render(self.menu_quit)

                pass
            case GameState.GAMEPLAY:
                if self.data.is_game_running:
                    # Rendering the main gameplay objects
                    for asteroid in self.asteroids:
                        if not asteroid.is_destroyed:
                            self.data.renderer.render(asteroid.spinning_sprite)

                    self.data.renderer.render(self.alien.sprite)
                    self.data.renderer.render(self.alien_projectile.sprite)

                else:
                    # Pause screen UI text
                    self.data.renderer.render(self.pause_text)
                    self.data.renderer.render(self.pause_continue_text)
                    self.data.renderer.render(self.pause_quit_text)

                self.data.renderer.render(self.background)

                # Rendering the rest of the UI assets
                self.data.renderer.render(self.scoreboard)
                if self.current_game_mode == GameMode.TIMED:
                    self.data.renderer.render(self.timer)
                for i in range(self.player.current_health):
                    self.data.renderer.render(self.health_icons[i].sprite)

                pass
            case GameState.WIN_MENU:
                self.data.renderer.render(self.win_text)
                self.data.renderer.render(self.win_score_text)
                self.data.renderer.render(self.menu_retry)
                self.data.renderer.render(self.menu_back_to_title)

                pass
            case GameState.LOSE_MENU:
                self.data.renderer.render(self.lose_text)
                self.data.renderer.render(self.lose_score_text)
                self.data.renderer.render(self.menu_retry)
                self.data.renderer.render(self.menu_back_to_title)

                pass

    pass


def main():
    """
    Creates the game and runs it
    For ASGE Games to run they need settings. These settings
    allow changes to the way the game is presented, its
    simulation speed and also its dimensions. For this project
    the FPS and fixed updates are capped at 60hz and Vsync is
    set to adaptive.
    """
    settings = pyasge.GameSettings()
    settings.window_width = 1600
    settings.window_height = 900
    settings.fixed_ts = 60
    settings.fps_limit = 60
    settings.window_mode = pyasge.WindowMode.WINDOWED
    settings.vsync = pyasge.Vsync.ADAPTIVE
    game = MyASGEGame(settings)
    game.run()


if __name__ == "__main__":
    main()
