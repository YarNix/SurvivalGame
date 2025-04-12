from os.path import join
from pygame.color import Color

CL_WHITE = Color(255, 255, 255)
CL_BLACK = Color(0, 0, 0, 255)
CL_LGRAY = Color(180, 180, 180)
CL_TRANS = Color(0, 0, 0, 0)

CL_BTN_FOREGROUND = Color(0, 0, 0)
CL_BTN_BACKGROUND = Color(70, 129, 244)
CL_BTN_HOVER = Color(87, 131, 219)
CL_BTN_CLICK = Color(85, 194, 218)
NM_BTN_PADDING = Color(4, 4, 4, 4)

PT_ASSET = join("SurvivalGame", "asset")
PT_FONT = join(PT_ASSET, "fonts")
PT_SPRITE = join(PT_ASSET, "sprites") 
PT_AUDIO = join(PT_ASSET, "audios")
PT_IMAGE = join(PT_ASSET, "images")
PT_MAP = join(PT_ASSET, "map")

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
X_SCREEN_CENTER = SCREEN_WIDTH // 2
Y_SCREEN_CENTER = SCREEN_HEIGHT // 2
CELL_SIZE = 50

TICK_RATE = 60

INF = float('inf')