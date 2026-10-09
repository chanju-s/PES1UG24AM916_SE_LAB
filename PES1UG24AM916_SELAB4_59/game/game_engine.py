import random
import pygame
import math
from game.button import ChoiceButton

WIN_SCORE = 5
HISTORY_LEN = 5        # how many recent player throws to remember
FAVOR_THRESHOLD = 3    # same move this many times in the history counts as "favoring" it
COUNTER_PROB = 0.65    # chance the CPU plays the counter once a favorite is detected
COUNTERS = {"ROCK": "PAPER", "PAPER": "SCISSORS", "SCISSORS": "ROCK"}
COUNTDOWN_STEP = 400                 # ms per "3", "2", "1"
ANIM_DURATION = 3 * COUNTDOWN_STEP   # total pre-reveal animation time

def draw_rock(screen, cx, cy, s):
    pts = [(-0.45, 0.10), (-0.30, -0.30), (0.05, -0.45), (0.40, -0.25),
           (0.48, 0.15), (0.25, 0.42), (-0.20, 0.40)]
    poly = [(cx + x * s, cy + y * s) for x, y in pts]
    pygame.draw.polygon(screen, (130, 134, 142), poly)
    facet = [(cx - 0.30 * s, cy - 0.30 * s), (cx + 0.05 * s, cy - 0.45 * s),
             (cx + 0.10 * s, cy - 0.05 * s), (cx - 0.20 * s, cy + 0.05 * s)]
    pygame.draw.polygon(screen, (165, 169, 177), facet)
    pygame.draw.polygon(screen, (80, 84, 92), poly, 3)
    pygame.draw.line(screen, (90, 94, 102), (cx + 0.10 * s, cy - 0.05 * s), (cx + 0.25 * s, cy + 0.30 * s), 2)


def draw_paper(screen, cx, cy, s):
    w, h, fold = 0.80 * s, 0.95 * s, 0.25 * s
    x, y = cx - w / 2, cy - h / 2
    poly = [(x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h)]
    pygame.draw.polygon(screen, (240, 240, 235), poly)
    corner = [(x + w - fold, y), (x + w - fold, y + fold), (x + w, y + fold)]
    pygame.draw.polygon(screen, (205, 205, 215), corner)
    pygame.draw.polygon(screen, (150, 150, 160), corner, 2)
    pygame.draw.polygon(screen, (150, 150, 160), poly, 2)
    for i in range(4):
        ly = y + fold + 0.12 * s + i * 0.15 * s
        pygame.draw.line(screen, (170, 175, 190), (x + 0.12 * s, ly), (x + w - 0.12 * s, ly), 2)


def draw_scissors(screen, cx, cy, s):
    # finger loops
    for sign in (-1, 1):
        pygame.draw.circle(screen, (200, 60, 60), (int(cx + sign * 0.25 * s), int(cy + 0.30 * s)), int(0.15 * s), 4)
    # blades cross at the pivot
    blade = (205, 210, 220)
    pygame.draw.line(screen, blade, (cx - 0.20 * s, cy + 0.20 * s), (cx + 0.28 * s, cy - 0.45 * s), 6)
    pygame.draw.line(screen, blade, (cx + 0.20 * s, cy + 0.20 * s), (cx - 0.28 * s, cy - 0.45 * s), 6)
    pygame.draw.circle(screen, (90, 95, 105), (int(cx), int(cy - 0.07 * s)), 5)


ICON_DRAWERS = {"ROCK": draw_rock, "PAPER": draw_paper, "SCISSORS": draw_scissors}

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.choices = ["ROCK", "PAPER", "SCISSORS"]
        btn_w, btn_h = 130, 50
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (width - total_w) // 2
        btn_y = height - 85

        self.buttons = [
            ChoiceButton("ROCK", pygame.Rect(start_x, btn_y, btn_w, btn_h), (160, 50, 50), (200, 70, 70)),
            ChoiceButton("PAPER", pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h), (40, 100, 170), (60, 130, 210)),
            ChoiceButton("SCISSORS", pygame.Rect(start_x + 2 * (btn_w + gap), btn_y, btn_w, btn_h), (180, 140, 30), (220, 180, 50)),
        ]

        self.player_choice = None
        self.cpu_choice = None
        self.result_text = "Make your move!"
        self.result_color = (220, 225, 235)

        self.player_score = 0
        self.cpu_score = 0
        self.history = []

        self.round_resolved_time = 0
        self.display_duration = 1800
        self.showing_result = False

        self.animating = False
        self.anim_start = 0
        self.pending_player = None
        self.pending_cpu = None

        self.match_over = False
        self.winner_text = ""

        self.font_title = pygame.font.SysFont(None, 36)
        self.font_hud = pygame.font.SysFont(None, 26)
        self.font_arena = pygame.font.SysFont(None, 32)
        self.font_count = pygame.font.SysFont(None, 72)

    def determine_winner(self, player, cpu):
        if player == cpu:
            return "TIE"
            
        rules = {
            ("ROCK", "SCISSORS"): "PLAYER",
            ("SCISSORS", "PAPER"): "PLAYER",
            ("PAPER", "ROCK"): "PLAYER",
            ("SCISSORS", "ROCK"): "CPU",
            ("PAPER", "SCISSORS"): "CPU",
            ("ROCK", "PAPER"): "CPU",
        }
        return rules.get((player, cpu), "TIE")

    def play_round(self, choice):
        self.pending_player = choice
        self.pending_cpu = self.choose_cpu_move()
        self.history.append(choice)
        self.history = self.history[-HISTORY_LEN:]

        self.player_choice = None
        self.cpu_choice = None
        self.result_text = "Get ready..."
        self.result_color = (190, 195, 205)
        self.showing_result = False
        self.animating = True
        self.anim_start = pygame.time.get_ticks()

    def resolve_round(self):
        self.animating = False
        self.player_choice = self.pending_player
        self.cpu_choice = self.pending_cpu

        outcome = self.determine_winner(self.player_choice, self.cpu_choice)
        if outcome == "PLAYER":
            self.player_score += 1
            self.result_text = f"You Win! {self.player_choice} beats {self.cpu_choice}."
            self.result_color = (80, 230, 120)
        elif outcome == "CPU":
            self.cpu_score += 1
            self.result_text = f"You Lose! {self.cpu_choice} beats {self.player_choice}."
            self.result_color = (240, 80, 80)
        else:
            self.result_text = f"It's a Draw! Both picked {self.player_choice}."
            self.result_color = (240, 210, 80)

        self.showing_result = True
        self.round_resolved_time = pygame.time.get_ticks()  # 1.8s timer starts at the reveal

        if self.player_score >= WIN_SCORE or self.cpu_score >= WIN_SCORE:
            self.match_over = True
            self.winner_text = "YOU WIN THE MATCH!" if self.player_score >= WIN_SCORE else "CPU WINS THE MATCH!"

    def handle_event(self, event):
        if self.match_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        if self.animating:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.contains(event.pos):
                    self.play_round(btn.choice_name)
                    break

    def update(self):
        if self.match_over:
            return
        now = pygame.time.get_ticks()
        if self.animating:
            if now - self.anim_start >= ANIM_DURATION:
                self.resolve_round()
            return
        if self.showing_result and (now - self.round_resolved_time >= self.display_duration):
            self.player_choice = None
            self.cpu_choice = None
            self.result_text = "Make your move!"
            self.result_color = (190, 195, 205)
            self.showing_result = False

    def choose_cpu_move(self):
        if len(self.history) >= FAVOR_THRESHOLD:
            favorite = max(self.choices, key=self.history.count)
            if self.history.count(favorite) >= FAVOR_THRESHOLD:
                counter = COUNTERS[favorite]
                if random.random() < COUNTER_PROB:
                    return counter
                return random.choice([c for c in self.choices if c != counter])
        return random.choice(self.choices)

    def reset(self):
        self.player_choice = None
        self.cpu_choice = None
        self.player_score = 0
        self.cpu_score = 0
        self.result_text = "Make your move!"
        self.result_color = (220, 225, 235)
        self.showing_result = False
        self.match_over = False
        self.winner_text = ""
        self.history = []
        self.animating = False

    def render(self, screen):
        screen.fill((24, 28, 36))

        title_surf = self.font_title.render("Rock Paper Scissors", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 14))

        p_surf = self.font_hud.render(f"Player Score: {self.player_score}", True, (100, 180, 255))
        c_surf = self.font_hud.render(f"CPU Score: {self.cpu_score}", True, (255, 120, 120))
        screen.blit(p_surf, (35, 52))
        screen.blit(c_surf, (self.width - c_surf.get_width() - 35, 52))

        pygame.draw.line(screen, (45, 52, 66), (25, 82), (self.width - 25, 82), 2)

        now = pygame.time.get_ticks()
        icon_cy, icon_size = 160, 70
        slots = (
            (self.width // 4, "Your Pick", self.player_choice),
            (3 * self.width // 4, "CPU Pick", self.cpu_choice),
        )
        for cx, label, choice in slots:
            lbl = self.font_hud.render(label, True, (225, 225, 230))
            screen.blit(lbl, (cx - lbl.get_width() // 2, 92))
            if self.animating:
                t = now - self.anim_start
                bob = -abs(math.sin(math.pi * t / COUNTDOWN_STEP)) * 14   # one fist pump per count
                draw_rock(screen, cx, icon_cy + bob, icon_size)
            elif choice:
                ICON_DRAWERS[choice](screen, cx, icon_cy, icon_size)
            else:
                dash = self.font_arena.render("--", True, (110, 116, 130))
                screen.blit(dash, (cx - dash.get_width() // 2, icon_cy - dash.get_height() // 2))

        if self.animating:
            step = 3 - min(2, (now - self.anim_start) // COUNTDOWN_STEP)
            num = self.font_count.render(str(step), True, (245, 245, 245))
            screen.blit(num, (self.width // 2 - num.get_width() // 2, icon_cy - num.get_height() // 2))

        res_surf = self.font_arena.render(self.result_text, True, self.result_color)
        screen.blit(res_surf, (self.width // 2 - res_surf.get_width() // 2, 205))

        if self.match_over:
            color = (80, 230, 120) if self.player_score >= WIN_SCORE else (240, 80, 80)
            banner = self.font_title.render(self.winner_text, True, color)
            hint = self.font_arena.render("Press R to restart", True, (225, 225, 230))
            screen.blit(banner, (self.width // 2 - banner.get_width() // 2, self.height - 120))
            screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 65))
        else:
            for btn in self.buttons:
                btn.render(screen)
