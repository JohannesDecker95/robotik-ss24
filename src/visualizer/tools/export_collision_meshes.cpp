// Exports the robot geometry rendered by the visualizer as collision meshes for pkg_control.
//
// Usage: export_collision_meshes <robot.iv> <output dir>
//
// Every link file referenced by the robot model (File node, e.g. kr6_arm1.iv) is written to
// <output dir>/<link>.stl as binary STL in meters. The triangles are given in robot base
// coordinates with all joints at zero, exactly as Coin3D tessellates them for rendering.
// The coordinate axes (inputCoord.iv) are a drawing aid and are not exported.
#include <Inventor/SoDB.h>
#include <Inventor/SoInput.h>
#include <Inventor/SoPrimitiveVertex.h>
#include <Inventor/actions/SoCallbackAction.h>
#include <Inventor/nodes/SoFile.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoShape.h>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <map>
#include <string>
#include <vector>

struct Export
{
    std::vector<std::string> files; // file nodes currently being traversed, outermost first
    std::map<std::string, std::vector<SbVec3f>> triangles;
};

static SoCallbackAction::Response file_enter(void* data, SoCallbackAction*, const SoNode* node)
{
    std::string name = static_cast<const SoFile*>(node)->name.getValue().getString();
    if (name == "inputCoord.iv") return SoCallbackAction::PRUNE;
    static_cast<Export*>(data)->files.push_back(name.substr(0, name.rfind('.')));
    return SoCallbackAction::CONTINUE;
}

static SoCallbackAction::Response file_leave(void* data, SoCallbackAction*, const SoNode* node)
{
    std::string name = static_cast<const SoFile*>(node)->name.getValue().getString();
    if (name != "inputCoord.iv") static_cast<Export*>(data)->files.pop_back();
    return SoCallbackAction::CONTINUE;
}

static void triangle_callback(void* data, SoCallbackAction* action, const SoPrimitiveVertex* v1,
                              const SoPrimitiveVertex* v2, const SoPrimitiveVertex* v3)
{
    Export* exp = static_cast<Export*>(data);
    if (exp->files.empty()) return;

    // the link is the outermost file, nested files belong to it
    std::vector<SbVec3f>& triangles = exp->triangles[exp->files.front()];
    const SbMatrix& model = action->getModelMatrix();
    for (const SoPrimitiveVertex* v : {v1, v2, v3}) {
        SbVec3f p;
        model.multVecMatrix(v->getPoint(), p);
        triangles.push_back(p / 1000.0f); // model is in millimeters
    }
}

static void write_stl(const std::string& filename, const std::vector<SbVec3f>& points)
{
    std::ofstream file(filename, std::ios::binary);
    char header[80] = "KR6 collision mesh, meters, robot base frame, all joints at zero";
    uint32_t count = points.size() / 3;
    file.write(header, sizeof(header));
    file.write(reinterpret_cast<const char*>(&count), sizeof(count));
    for (size_t i = 0; i < points.size(); i += 3) {
        SbVec3f normal = (points[i + 1] - points[i]).cross(points[i + 2] - points[i]);
        if (normal.length() > 0) normal.normalize();
        float values[12];
        for (int k = 0; k < 3; ++k) {
            values[k]     = normal[k];
            values[3 + k] = points[i][k];
            values[6 + k] = points[i + 1][k];
            values[9 + k] = points[i + 2][k];
        }
        uint16_t attributes = 0;
        file.write(reinterpret_cast<const char*>(values), sizeof(values));
        file.write(reinterpret_cast<const char*>(&attributes), sizeof(attributes));
    }
}

int main(int argc, char** argv)
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <robot.iv> <output dir>\n", argv[0]);
        return 1;
    }
    SoDB::init();
    SoInput input;
    if (!input.openFile(argv[1])) return 1;
    SoSeparator* root = SoDB::readAll(&input);
    if (root == NULL) return 1;
    root->ref();

    Export exp;
    SoCallbackAction action;
    action.addPreCallback(SoFile::getClassTypeId(), file_enter, &exp);
    action.addPostCallback(SoFile::getClassTypeId(), file_leave, &exp);
    action.addTriangleCallback(SoShape::getClassTypeId(), triangle_callback, &exp);
    action.apply(root);
    root->unref();

    for (const auto& [link, points] : exp.triangles) {
        std::string filename = std::string(argv[2]) + "/" + link + ".stl";
        write_stl(filename, points);
        printf("%s: %zu triangles\n", filename.c_str(), points.size() / 3);
    }
    return 0;
}
