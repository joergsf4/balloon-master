// GENERIERT von tools/gen_assets.py - nicht von Hand ändern.
#ifndef WORLDS_GEN_H
#define WORLDS_GEN_H

#include "bank8.h"
#include "bank3.h"
#include "bank4.h"
#include "bank5.h"
#include "bank6.h"
#include "bank7.h"

#define NUM_WORLDS 6
static const World *const worlds[NUM_WORLDS] = { &world_london, &world_sea, &world_storm, &world_cave, &world_moon, &world_ny };
static const unsigned char world_bank[NUM_WORLDS] = { 8, 3, 4, 5, 6, 7 };   // ROM-Bank der Weltdaten (London = 8)

#endif
