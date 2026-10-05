// GENERIERT von tools/gen_assets.py - nicht von Hand ändern
#pragma once

#include "world.h"

#define FONT_TILE_START 120
#define BG_TILE_BASE 120
#define SPR_FONT_START 84
#define SPRITE_TILE_BYTES 3840

// Objekte: erstes Tile, Breite und Höhe in Tiles (Tiles zeilenweise)
#define BALLOON_IDLE 1
#define BALLOON_IDLE_W 3
#define BALLOON_IDLE_H 4
#define BALLOON_BURN 13
#define BALLOON_BURN_W 3
#define BALLOON_BURN_H 4
#define BIRD_UP 25
#define BIRD_UP_W 2
#define BIRD_UP_H 2
#define BIRD_DOWN 29
#define BIRD_DOWN_W 2
#define BIRD_DOWN_H 2
#define BARREL 33
#define BARREL_W 2
#define BARREL_H 2
#define ROPE 37
#define ROPE_W 1
#define ROPE_H 1
#define HOOK 38
#define HOOK_W 1
#define HOOK_H 2
#define FUEL_BAR 40
#define FUEL_BAR_W 9
#define FUEL_BAR_H 1
#define FUEL_BAR_RED 49
#define FUEL_BAR_RED_W 9
#define FUEL_BAR_RED_H 1
#define FUEL_CAP 58
#define FUEL_CAP_W 1
#define FUEL_CAP_H 1
#define BOLT_A 59
#define BOLT_A_W 2
#define BOLT_A_H 3
#define BOLT_B 65
#define BOLT_B_W 2
#define BOLT_B_H 3
#define CANNONBALL 71
#define CANNONBALL_W 1
#define CANNONBALL_H 1
#define FIREBALL_A 72
#define FIREBALL_A_W 1
#define FIREBALL_A_H 1
#define FIREBALL_B 73
#define FIREBALL_B_W 1
#define FIREBALL_B_H 1
#define BOULDER 74
#define BOULDER_W 1
#define BOULDER_H 1
#define CANNON_PUFF 75
#define CANNON_PUFF_W 1
#define CANNON_PUFF_H 1
#define SPARK_Y_BIG 76
#define SPARK_Y_BIG_W 1
#define SPARK_Y_BIG_H 1
#define SPARK_Y_SMALL 77
#define SPARK_Y_SMALL_W 1
#define SPARK_Y_SMALL_H 1
#define SPARK_R_BIG 78
#define SPARK_R_BIG_W 1
#define SPARK_R_BIG_H 1
#define SPARK_R_SMALL 79
#define SPARK_R_SMALL_W 1
#define SPARK_R_SMALL_H 1
#define SPARK_W_BIG 80
#define SPARK_W_BIG_W 1
#define SPARK_W_BIG_H 1
#define SPARK_W_SMALL 81
#define SPARK_W_SMALL_W 1
#define SPARK_W_SMALL_H 1
#define PANEL 82
#define PANEL_W 1
#define PANEL_H 1
#define LIFE 83
#define LIFE_W 1
#define LIFE_H 1

// Hintergrundobjekte (London, liegen in Bank 8): Breite und Höhe in Tiles
#define SKYLINE_W 32
#define SKYLINE_H 8
#define STORM_CLOUD_W 7
#define STORM_CLOUD_H 4
#define TOWER_BRIDGE_W 16
#define TOWER_BRIDGE_H 12
#define GREY_TOWER_W 5
#define GREY_TOWER_H 15
#define ARCH_BUILDING_W 7
#define ARCH_BUILDING_H 8
#define BRICK_TOWER_W 5
#define BRICK_TOWER_H 12
#define PAVEMENT_W 1
#define PAVEMENT_H 1
#define ROAD_W 1
#define ROAD_H 1
#define ROAD_DASH_W 1
#define ROAD_DASH_H 1
#define GROUND_TOP_W 1
#define GROUND_TOP_H 1
#define GROUND_FILL_W 1
#define GROUND_FILL_H 1
#define CLOUD_W 6
#define CLOUD_H 2

// gemeinsame Sprites (alle Welten), liegen im festen Bereich: src/shared_data.c
extern const unsigned char sprite_palette[16];
extern const unsigned char sprite_tiles[SPRITE_TILE_BYTES];
