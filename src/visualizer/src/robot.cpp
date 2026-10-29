#include "../include/visualizer/robot.h"

Robot::Robot(const char *filename)
{
    this->filename = filename;
}

Robot::~Robot()
{
}

SoSeparator *Robot::load_model()
{
    this->robot = readFile(filename);
    return robot;
}

SoSeparator *Robot::getRobot()
{
    return robot;
}

SoSeparator *Robot::readFile(const char *filename)
{
    // Open the input file
    SoInput mySceneInput;
    if (!mySceneInput.openFile(filename))
    {
        fprintf(stderr, "Cannot open file %s\n", filename);
        exit(1);
    }

    // Read the whole file into the database
    SoSeparator *file = SoDB::readAll(&mySceneInput);
    if (file == NULL)
    {
        fprintf(stderr, "Problem reading file\n");
        exit(1);
    }
    
    mySceneInput.closeFile();
    return file;
}
