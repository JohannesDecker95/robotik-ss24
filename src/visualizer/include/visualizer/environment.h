#ifndef ENVIRONMENT_H
#define ENVIRONMENT_H

#include <Inventor/nodes/SoSeparator.h>

// Builds the obstacles of the robot cell (floor, tables) as boxes from data/environment.yaml.
// pkg_control checks the robot against the same boxes.
SoSeparator* load_environment(const char* filename);

#endif // ENVIRONMENT_H
