from pyray import *
import random, time
import os

class Game:

    def __init__(self):
        self.WIDTH = 1000
        self.HEIGHT = 500
        self.FPS = 30
        self.cards_number = 10
        self.rec_width = 110
        self.rec_height = 188
        self.recs = {}
        self.window_close = False
        path = os.path.dirname(os.path.abspath(__file__))
        self.card_textures = (load_texture(path + "/resources/diluc.png"),
        load_texture(path + "/resources/eula.png"),
        load_texture(path + "/resources/fishl.png"),
        load_texture(path + "/resources/ganyu.png"),
        load_texture(path + "/resources/kokomi.png"))
        self.shirt = load_texture(path + "/resources/shirt.png")
        self.background = load_texture(path + "/resources/background.png")

    # Refreshing initializasion
    def refresh(self):
        self.card_picked = False
        self.index_of_picked_card = None
        self.end_game = False
        self.score = 0
        self.fails = 0

    # Creating dictionary recs
    def cardsCreating(self, x, y, number, recsInOneRow, intervalCol = 80, intervalRow = 40):
        col = 0
        row = 0
        for i in range(0, number):
            if col % recsInOneRow == 0 and i != 0:
                col = 0
                row += 1
            self.recs[i] = [Rectangle(x + (self.rec_width * col) + (intervalCol * col), y + (self.rec_height * row) + (intervalRow * row), self.rec_width, self.rec_height), \
                            self.pairs_cards[i], True]
            col += 1

    # Change state cards
    def cardsState(self, state):
        for i in self.recs:
            self.recs[i][2] = state

    # Drawing cards
    def cardsDrawing(self):
        for i in self.recs:
            # draw_rectangle_rec(self.recs[i][0], DARKPURPLE)
            if self.recs[i][2] == True:
                draw_texture_rec(self.card_textures[self.recs[i][1]], Rectangle(0,0, 110, 188), (self.recs[i][0].x, self.recs[i][0].y), WHITE)
            else:
                draw_texture_rec(self.shirt, Rectangle(0,0, 110, 188), (self.recs[i][0].x, self.recs[i][0].y), WHITE)
        # draw_texture_rec(self.card_textures[self.recs[1][1]], Rectangle(0,0, 110, 188), (self.recs[1][0].x, self.recs[1][0].y), WHITE)
        # draw_texture_rec(self.shirt, Rectangle(0,0, 110, 188), (self.recs[0][0].x, self.recs[0][0].y), WHITE)

    #Creating random list 
    def randomizer(self, value):
        rand_list = list(range(0, int(value / 2)))
        pairs = rand_list + rand_list
        random.shuffle(pairs)
        return pairs
    
    def drawBackground(self):
        draw_texture(self.background, 0, 0, WHITE)

    def closeWindow(self):
        if window_should_close(): self.window_close = True

    # Card click check
    def cardClicked(self):
        mouse = get_mouse_position()
        for i in range(0, len(self.recs)):
            if mouse.x >= self.recs[i][0].x and mouse.x <= self.recs[i][0].x + self.recs[i][0].width \
            and mouse.y >= self.recs[i][0].y and mouse.y <= self.recs[i][0].y + self.recs[i][0].height:
                self.recs[i][2] = True
                self.card_picked = not self.card_picked
                if self.card_picked:
                    self.index_of_picked_card = self.recs[i][1]
                elif self.index_of_picked_card == self.recs[i][1]:
                    self.score += 1
                else:
                    self.fails += 1

    # Draw window
    def show(self):
        set_target_fps(self.FPS)
        while not self.window_close:
            self.refresh()
            self.pairs_cards = self.randomizer(self.cards_number)
            print(self.pairs_cards, end="\n\n")
            self.cardsCreating(60, 60, self.cards_number, 5)
            inspection = timer = time.time() + 6
            timer_end = False
            while self.fails <= 2 and not self.window_close and not self.end_game:
                self.closeWindow()
                current_time = time.time()
                begin_drawing()
                draw_fps(20,20)
                clear_background(DARKBLUE)
                self.drawBackground()
                if is_mouse_button_pressed(MOUSE_LEFT_BUTTON) and timer_end:
                    self.cardClicked()
                elif int(timer-current_time) == 0 and not timer_end:
                    self.cardsState(False)
                    timer = time.time() + 21
                    timer_end = True
                elif timer > inspection and int(timer-current_time) == 0 and not self.end_game:
                    self.end_game = True
                self.cardsDrawing()
                if int(timer-current_time) > 0:
                    draw_text(f"TIME LEFT:{int(timer-current_time)}", 420, 20, 24, LIGHTGRAY)
                draw_text(f"SCORE:{self.score}", 820, 20, 24, LIGHTGRAY)
                draw_text(f"FAILS:{self.fails}", 700, 20, 24, LIGHTGRAY)
                end_drawing()
            while not is_mouse_button_pressed(MOUSE_LEFT_BUTTON) and not self.window_close:
                self.closeWindow()
                begin_drawing()
                clear_background(DARKBLUE)
                self.drawBackground()
                rec = Rectangle(0, 0, self.WIDTH, self.HEIGHT)
                color = Color(0, 0, 0, 168)
                draw_rectangle_rec(rec, color)
                draw_text(f"SCORE:{self.score}", 420, 200, 24, LIGHTGRAY)
                draw_text(f"FAILS:{self.fails}", 425, 240, 24, LIGHTGRAY)
                draw_text(f"PRESS ANY MOUSE BUTTON", 305, 280, 24, LIGHTGRAY)
                end_drawing()
        close_window()

init_window(1000, 500, "Cards")
set_config_flags(ConfigFlags.FLAG_VSYNC_HINT)
set_trace_log_level(TraceLogLevel.LOG_ALL)
test = Game()
test.show()