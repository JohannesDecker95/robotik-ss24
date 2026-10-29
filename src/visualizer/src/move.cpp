#include "../include/visualizer/move.h"

void set_rotation_angle_one_rotation_node(string arm_name, double angle, SoSeparator* robot)
{
    SoSearchAction search;
    search.setName(SbName(arm_name.c_str()));
    search.setSearchingAll(true);
    search.setInterest(SoSearchAction::FIRST);
    search.apply(robot);

    SoPath* path = search.getPath();
    if (path != NULL) {
        path->ref();
        SoNode* foundNode = path->getTail();
        if (foundNode) {
            SoRotationXYZ* rotationNode = dynamic_cast<SoRotationXYZ*>(foundNode);
            if (rotationNode) {
                rotationNode->angle.setValue(angle);
            } else {
                std::cout << "Rotation node not found." << std::endl;
            }
        }
        path->unref();
    } else {
        std::cout << "Rotation node: " << arm_name << " not found." << std::endl;
    }
}

void Move::set_rotation_angle_robot()
{
    std::lock_guard<std::mutex> guard(anglesMutex);
    set_rotation_angle_one_rotation_node("kr6_base_animate", this->angles[0], this->robot);
    set_rotation_angle_one_rotation_node("kr6_arm1_animate", this->angles[1], this->robot);
    set_rotation_angle_one_rotation_node("kr6_arm2_animate", this->angles[2], this->robot);
    set_rotation_angle_one_rotation_node("kr6_arm3_animate", this->angles[3], this->robot);
    set_rotation_angle_one_rotation_node("kr6_arm4_animate", this->angles[4], this->robot);
    set_rotation_angle_one_rotation_node("kr6_arm5_animate", this->angles[5], this->robot);
}

void Move::set_all_desired_angles(const std::vector<double>& angles)
{
    std::lock_guard<std::mutex> guard(anglesMutex);
    this->angles = angles;
}

void Move::set_robot(SoSeparator* robot)
{
    this->robot = robot;
}
