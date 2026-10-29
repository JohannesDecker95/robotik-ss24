#ifndef MOVE_H
#define MOVE_H

#include <Inventor/Qt/viewers/SoQtExaminerViewer.h>
#include <Inventor/SbLinear.h>
#include <Inventor/actions/SoSearchAction.h>
#include <Inventor/nodes/SoCoordinate3.h>
#include <Inventor/nodes/SoCube.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoRotation.h>
#include <Inventor/nodes/SoRotationXYZ.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoTransform.h>
#include <iostream>
#include <mutex>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <string>
#include <vector>

#define TO_RADIAN(x) (x * M_PI / 180.0)
#define TO_DEGREE(x) (x * 180.0 / M_PI)

using namespace std;
class Move
{
  private:
    // [0] - base, [1] - arm1, [2] - arm2, [3] - arm3, [4] - arm4, [5] - arm5, [6] - arm6
    // std::vector<double> angles{ 0.0, -140.0, 160.0, 0.0, 0.0, 0.0 };
    std::vector<double> angles{ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
    std::mutex anglesMutex;

    SoSeparator* robot;

  public:
    Move()                       = default;
    Move(const Move&)            = delete; // Kopierkonstruktor verbieten
    Move& operator=(const Move&) = delete; // Zuweisungsoperator verbieten

    ~Move() = default;

    void set_all_desired_angles(const std::vector<double>& angles);
    void set_robot(SoSeparator* robot);
    void set_rotation_angle_robot();
};

#endif // MOVE_H
