#ifndef ROBOT_H
#define ROBOT_H

#include <Inventor/nodes/SoSeparator.h>
#include <string>


// Define your class and its members
class Robot {
public:
    

    Robot(const char *filename);
    ~Robot();

    SoSeparator *load_model();
    void move(int arm_1, int arm_2, int arm_3, int arm_4, int arm_5, int arm_6);
    
    SoSeparator *getRobot();

private:
    const char *filename;
    SoSeparator *robot;

    SoSeparator *readFile(const char *filename);
};

#endif // ROBOT_H