#include "../include/visualizer/environment.h"

#include <Inventor/nodes/SoCube.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoPolygonOffset.h>
#include <Inventor/nodes/SoTranslation.h>
#include <yaml-cpp/yaml.h>

SoSeparator* load_environment(const char* filename)
{
    YAML::Node config;
    try {
        config = YAML::LoadFile(filename);
    } catch (const YAML::Exception& e) {
        fprintf(stderr, "Cannot read file %s: %s\n", filename, e.what());
        exit(1);
    }

    // environment.yaml is in meters, the scene in millimeters
    SoSeparator* environment = new SoSeparator;

    // Puzzle pieces lie only a millimeter above the table top. Push the obstacles back in the depth
    // buffer, otherwise the table shows through the pieces at flat viewing angles (z-fighting).
    SoPolygonOffset* offset = new SoPolygonOffset;
    offset->factor          = 4.0f;
    offset->units           = 4.0f;
    environment->addChild(offset);

    for (const YAML::Node& box : config["obstacles"]) {
        SoSeparator* separator = new SoSeparator;

        SoMaterial* material = new SoMaterial;
        material->diffuseColor.setValue(
            box["color"][0].as<float>(), box["color"][1].as<float>(), box["color"][2].as<float>());
        separator->addChild(material);

        SoTranslation* translation = new SoTranslation;
        translation->translation.setValue(box["center"][0].as<float>() * 1000,
                                          box["center"][1].as<float>() * 1000,
                                          box["center"][2].as<float>() * 1000);
        separator->addChild(translation);

        SoCube* cube = new SoCube;
        cube->width  = box["size"][0].as<float>() * 1000;
        cube->height = box["size"][1].as<float>() * 1000;
        cube->depth  = box["size"][2].as<float>() * 1000;
        separator->addChild(cube);

        environment->addChild(separator);
    }
    return environment;
}
