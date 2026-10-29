#ifndef PUZZLE_H
#define PUZZLE_H

#define PUZZLE_SCALE_FACTOR 0.04

#include <Inventor/Qt/SoQt.h>
#include <Inventor/Qt/viewers/SoQtExaminerViewer.h>
#include <Inventor/nodes/SoCoordinate3.h>
#include <Inventor/nodes/SoDrawStyle.h>
#include <Inventor/nodes/SoIndexedFaceSet.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoTexture2.h>
#include <Inventor/nodes/SoTextureCoordinate2.h>
#include <poly2tri/poly2tri.h>
#include <vector>
#include <utility>
#include <string>

// Function prototypes
std::vector<std::pair<float, float>> parseSVGPolygon(const std::string& filePath);
SoTexture2* loadTexture(const std::string& filename);
std::pair<std::pair<float, float>, std::pair<float, float>> calculateBoundingBox(const std::vector<std::pair<float, float>>& points);
SoSeparator* get_puzzle(const std::vector<std::pair<float, float>>& points, SoTexture2* texture, int textureWidth, int textureHeight);

#endif // PUZZLE_H
