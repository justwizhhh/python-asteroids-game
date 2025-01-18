import pyasge


class GameData:
    """ GameData stores the data that needs to be shared

    When using multiple states in a game, you will find that
    some game data needs to be shared. In this instance GameData
    is used to share access to data that the game and running
    states may need. You can think of this as a "blackboard" in
    UE terms.
    """

    def __init__(self) -> None:
        self.game_res = [0, 0]
        self.background = None
        self.fonts = {}
        self.inputs = None
        self.renderer = None

        self.max_score = 2000
        self.max_time = 30.0

        self.is_game_running = True
        self.was_game_paused = False
        self.score = 0
        self.time = 0

