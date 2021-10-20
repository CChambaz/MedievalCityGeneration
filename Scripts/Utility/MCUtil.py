from enum import Enum

BlocType = {
    'DIRT':0,
    'COARSE_DIRT':1,
    'GRASS_BLOCK':2,
    'MYCELIUM':4,
    'GRAVEL':5,
    'SAND':6,
    'RED_SAND':7,
    'CLAY':8,
    'STONE':9,
    'COBBLESTONE':10,
    'SMOOTH_STONE':11,
    'GRANITE':12,
    'POLISHED_GRANITE':13,
    'BEDROCK':14,
    'DIORITE':15,
    'POLISHED_DIORITE':16,
    'OBSIDIAN':17,
    'ANDESITE':18,
    'POLISHED_ANDESITE':19,
    'MOSSY_COBBLESTONE':20,
    'BRICKS':21,
    'TERRACOTTA':22,
    'SANDSTONE':23,
    'RED_SANDSTONE':24,
    'SNOW_BLOCK':25,
    'ICE':26,
    'PACKED_ICE':27,
    'BLUE_ICE':28,
    'WATER':29,
    'COAL_ORE':30,
    'IRON_ORE':31,
    'GOLD_ORE':32,
    'DIAMOND_ORE':33,
    'EMERALD_ORE':34,
    'REDSTONE_ORE':35,
    'LAPIS_ORE':36,
    'FARMLAND':37,
    'GRASS_PATH':38,
    'WATER_AREA': 39,
    'EMPTY':40
}

TerrainTypeColor = {
    0:'brown',          #DIRT
    1:'brown',          #COARSE_DIRT
    2:'green',          #GRASS_BLOCK
    3:'brown',          #PODZOL
    4:'darkgray',       #MYCELIUM
    5:'gray',           #GRAVEL
    6:'sandybrown',     #SAND
    7:'orangered',      #RED_SAND
    8:'gray',           #CLAY
    9:'gray',           #STONE
    10:'gray',          #COBBLESTONE
    11:'gray',          #SMOOTH_STONE
    12:'sienna',        #GRANITE
    13:'sienna',        #POLISHED_GRANITE
    14:'darkgray',      #BEDROCK
    15:'lightgray',     #DIORITE
    16:'lightgray',     #POLISHED_DIORITE
    17:'darkviolet',    #OBSIDIAN
    18:'gray',          #ANDESITE
    19:'gray',          #POLISHED_ANDESITE
    20:'gray',          #MOSSY_COBBLESTONE
    21:'firebrick',     #BRICKS
    22:'saddlebrown',   #TERRACOTTA
    23:'beige',         #SANDSTONE
    24:'beige',         #RED_SANDSTONE
    25:'white',         #SNOW_BLOCK
    26:'cyan',          #ICE
    27:'cyan',          #PACKED_ICE
    28:'cyan',          #BLUE_ICE
    29:'navy',          #WATER
    30:'gold',          #COAL_ORE
    31:'gold',          #IRON_ORE
    32:'gold',          #GOLD_ORE
    33:'gold',          #DIAMOND_ORE
    34:'gold',          #EMERALD_ORE
    35:'gold',          #REDSTONE_ORE
    36:'gold',          #LAPIS_ORE
    37:'brown',         #FARMLAND
    38:'lightgreen',    #GRASS_PATH
    39:'darkcyan',      #WATER_AREA
    40:'black'
}