#include "../include/visualizer/puzzle.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <limits>

// Function to parse the polygon points from the SVG file
std::vector<std::pair<float, float>> parseSVGPolygon(const std::string& filePath) {
    std::vector<std::pair<float, float>> points;
    std::ifstream file(filePath);
    if (!file.is_open()) {
        std::cerr << "Failed to open SVG file." << std::endl;
        return points;
    }
    std::cout << "Opened SVG file." << std::endl;

    std::string line;
    while (std::getline(file, line)) {
        if (line.find("<polygon") != std::string::npos) {
            size_t start = line.find("points=\"") + 8;
            size_t end = line.find("\"", start);
            std::string pointsStr = line.substr(start, end - start);
            std::istringstream ss(pointsStr);
            std::string point;
            while (std::getline(ss, point, ' ')) {
                size_t comma = point.find(',');
                float x = std::stof(point.substr(0, comma));
                float y = std::stof(point.substr(comma + 1));
                points.emplace_back(x, y);
            }
            break;
        }
    }

    return points;
}

// Function to load texture from a file
SoTexture2* loadTexture(const std::string& filename) {
    SoTexture2* texture = new SoTexture2;
    texture->filename.setValue(filename.c_str());
    return texture;
}

// Function to calculate the bounding box of the points
std::pair<std::pair<float, float>, std::pair<float, float>> calculateBoundingBox(const std::vector<std::pair<float, float>>& points) {
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::min();
    float maxY = std::numeric_limits<float>::min();

    for (const auto& point : points) {
        if (point.first < minX) minX = point.first;
        if (point.second < minY) minY = point.second;
        if (point.first > maxX) maxX = point.first;
        if (point.second > maxY) maxY = point.second;
    }

    return {{minX, minY}, {maxX, maxY}};
}

// Function to create a 3D model from the points
SoSeparator* get_puzzle(const std::vector<std::pair<float, float>>& points, SoTexture2* texture, int textureWidth, int textureHeight) {
    if (points.empty()) {
        std::cerr << "No points provided." << std::endl;
        return nullptr;
    }

    // Create a scene graph
    SoSeparator* puzzle = new SoSeparator;
    puzzle->ref();

    float height = 0.5; // Height of the 3D puzzle

    // Create 3D coordinates from parsed points
    SoCoordinate3* coords = new SoCoordinate3;
    coords->point.deleteValues(0);

    int numPoints = points.size();

    // Add bottom and top points
    for (const auto& point : points) {
        coords->point.set1Value(coords->point.getNum(), SbVec3f(point.first * PUZZLE_SCALE_FACTOR, point.second * PUZZLE_SCALE_FACTOR, 0));
        coords->point.set1Value(coords->point.getNum(), SbVec3f(point.first * PUZZLE_SCALE_FACTOR, point.second * PUZZLE_SCALE_FACTOR, height));
    }

    // Triangulate the polygon with poly2tri
    std::vector<p2t::Point*> polyline;
    for (const auto& point : points) {
        polyline.push_back(new p2t::Point(point.first, point.second));
    }
    p2t::CDT cdt(polyline);
    cdt.Triangulate();
    std::vector<p2t::Triangle*> triangles = cdt.GetTriangles();

    // Create an IndexedFaceSet to connect the points
    SoIndexedFaceSet* faceSet = new SoIndexedFaceSet;

    // Create the side faces
    for (int i = 0; i < numPoints; ++i) {
        int next = (i + 1) % numPoints;
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), i * 2);             // Bottom point
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), next * 2);          // Next bottom point
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), next * 2 + 1);      // Next top point
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), i * 2 + 1);         // Top point
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), SO_END_FACE_INDEX); // End of face
    }

    // Create the top face with triangulated points
    for (const auto& triangle : triangles) {
        for (int i = 0; i < 3; ++i) {
            auto it = std::find_if(points.begin(), points.end(),
                [&triangle, i](const std::pair<float, float>& point) {
                    return point.first == static_cast<float>(triangle->GetPoint(i)->x) &&
                           point.second == static_cast<float>(triangle->GetPoint(i)->y);
                });
            int idx = std::distance(points.begin(), it);
            faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), idx * 2 + 1); // Top face points
        }
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), SO_END_FACE_INDEX);
    }

    // Create the bottom face with triangulated points
    for (const auto& triangle : triangles) {
        for (int i = 2; i >= 0; --i) {
            auto it = std::find_if(points.begin(), points.end(),
                [&triangle, i](const std::pair<float, float>& point) {
                    return point.first == static_cast<float>(triangle->GetPoint(i)->x) &&
                           point.second == static_cast<float>(triangle->GetPoint(i)->y);
                });
            int idx = std::distance(points.begin(), it);
            faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), idx * 2); // Bottom face points
        }
        faceSet->coordIndex.set1Value(faceSet->coordIndex.getNum(), SO_END_FACE_INDEX);
    }

    // Create a DrawStyle to set the line width
    SoDrawStyle* drawStyle = new SoDrawStyle;
    drawStyle->lineWidth = 2.0f; // Set the line width to 2.0

    // Create a material to set the color of the object
    SoMaterial* material = new SoMaterial;
    material->diffuseColor.setValue(0.8f, 0.8f, 0.8f); // Set the color to grey

    // Create and set texture coordinates
    SoTextureCoordinate2* texCoords = new SoTextureCoordinate2;
    for (const auto& point : points) {
        float u = point.first / textureWidth;
        float v = point.second / textureHeight;

        texCoords->point.set1Value(texCoords->point.getNum(), SbVec2f(u, v));
        texCoords->point.set1Value(texCoords->point.getNum(), SbVec2f(u, v));
    }

    // Add the draw style, material, coordinates, texture coordinates, and face set to the scene graph
    puzzle->addChild(drawStyle);
    puzzle->addChild(material);
    puzzle->addChild(coords);
    puzzle->addChild(texCoords);
    puzzle->addChild(texture);
    puzzle->addChild(faceSet);

    return puzzle;
}
