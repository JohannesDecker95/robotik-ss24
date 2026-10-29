#include "../include/visualizer/environment.h"
#include "../include/visualizer/move.h"
#include "../include/visualizer/puzzle.h"
#include "../include/visualizer/robot.h"
#include "geometry_msgs/msg/detail/pose__struct.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include "interfaces/msg/angles.hpp"
#include "interfaces/msg/detail/segmented_puzzle_tile__struct.hpp"
#include "interfaces/msg/point2d.hpp"
#include "interfaces/msg/puzzle_boolean.hpp"
#include "interfaces/msg/puzzle_pose.hpp"
#include "interfaces/msg/segmented_puzzle_tile.hpp"
#include "rclcpp/logging.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"
#include "watchdog/Watchdog.hpp"

#include <Inventor/Qt/SoQt.h>
#include <Inventor/Qt/viewers/SoQtExaminerViewer.h>
#include <Inventor/SoDB.h>
#include <Inventor/SoPath.h>
#include <Inventor/SoSceneManager.h>
#include <Inventor/actions/SoGetMatrixAction.h>
#include <Inventor/actions/SoSearchAction.h>
#include <Inventor/nodes/SoCube.h>
#include <Inventor/nodes/SoFile.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoTexture2.h>
#include <Inventor/nodes/SoTransform.h>
#include <Inventor/nodes/SoTranslation.h>
#include <Inventor/sensors/SoIdleSensor.h>
#include <QApplication>
#include <QWidget>
#include <iostream>

using std::placeholders::_1;

const char* path             = "data/kuka_kr6.iv";
const char* environment_path = "data/environment.yaml";

struct PlacePuzzleQueueItem
{
    int32_t id;
    float x;
    float y;
    float z;
    float rx;
    float ry;
    float rz;
    float rotation;
};
class RobotVisualisation : public rclcpp::Node
{
  public:
    RobotVisualisation()
        : Node("robot_visualisation")
    {
        // Control Node
        control_subscription_ = this->create_subscription<interfaces::msg::Angles>(
            "/control/angles", 10, std::bind(&RobotVisualisation::angles_callback, this, _1));

        // Visualize Node
        // Digitalize sends all tiles in one burst, the queue must hold the whole puzzle or tiles get dropped
        puzzle_subscription_ = this->create_subscription<interfaces::msg::SegmentedPuzzleTile>(
            "/digitalize/imgs",
            100,
            std::bind(&RobotVisualisation::puzzle_callback, this, std::placeholders::_1));

        // Solve Node
        puzzle_start_pos = this->create_subscription<interfaces::msg::PuzzlePose>(
            "/solver/startpos", 10, std::bind(&RobotVisualisation::startpos_callback, this, _1));
    }

    SoSeparator* robotScene;
    SoSeparator* root;
    SoQtExaminerViewer* eviewer;

    void startViewer(int argc, char* argv[])
    {
        // Initialize the Qt system:
        QApplication app(argc, argv);

        // Make a main window:
        QWidget mainwin;
        mainwin.resize(800, 800);

        // Initialize SoQt
        SoQt::init(&mainwin);

        // The root of a scene graph
        root = new SoSeparator;
        root->ref();

        // Build the kr6 robot
        Robot robot = Robot(path);
        robotScene  = robot.load_model();
        root->addChild(robotScene);

        // Floor and tables of the robot cell
        root->addChild(load_environment(environment_path));

        // Initialize SoIdleSensor with the callback method
        SoIdleSensor* sensor = new SoIdleSensor(sensor_callback, this);
        sensor->schedule();

        SoIdleSensor* place_puzzle_sensor = new SoIdleSensor(place_puzzle_sensor_sensor_callback, this);
        place_puzzle_sensor->schedule();

        SoIdleSensor* pick_puzzle_sensor = new SoIdleSensor(pick_puzzle_sensor_sensor_callback, this);
        pick_puzzle_sensor->schedule();

        SoIdleSensor* drop_puzzle_sensor = new SoIdleSensor(drop_puzzle_sensor_sensor_callback, this);
        drop_puzzle_sensor->schedule();

        this->move.set_robot(robotScene);
        this->move.set_rotation_angle_robot();

        // Initialize an examiner viewer:
        eviewer = new SoQtExaminerViewer(&mainwin);
        eviewer->setBackgroundColor(SbColor(1.0f, 1.0f, 1.0f));
        eviewer->setSceneGraph(root);
        eviewer->setTitle("KUKA KR6 Visualisation");
        eviewer->show();

        // Pop up the main window.
        SoQt::show(&mainwin);

        // Loop until exit.
        SoQt::mainLoop();

        delete eviewer;
        root->unref();
    }

  private:
    Move move;

    std::map<int, SoSeparator*>* puzzle_map = new std::map<int, SoSeparator*>();

    bool picked = false;

    std::list<PlacePuzzleQueueItem> place_puzzle_queue;
    std::list<std::string> pick_puzzle_queue;
    std::list<std::string> drop_puzzle_queue;

    std::mutex place_puzzle_mutex;
    std::mutex pick_puzzle_mutex;
    std::mutex drop_puzzle_mutex;

    rclcpp::Subscription<interfaces::msg::Angles>::SharedPtr control_subscription_;
    rclcpp::Subscription<interfaces::msg::SegmentedPuzzleTile>::SharedPtr puzzle_subscription_;
    rclcpp::Subscription<interfaces::msg::PuzzlePose>::SharedPtr puzzle_start_pos;

    // Sensors
    // ----------------------------------------------------------------------------------------------------------------------
    static void sensor_callback(void* data, SoSensor* sensor)
    {
        RobotVisualisation* self = static_cast<RobotVisualisation*>(data);
        self->move.set_rotation_angle_robot();
        sensor->schedule();
    }

    static void place_puzzle_sensor_sensor_callback(void* data, SoSensor* sensor)
    {
        RobotVisualisation* self = static_cast<RobotVisualisation*>(data);
        self->place_puzzle_queue_methode();
        sensor->schedule();
    }

    static void pick_puzzle_sensor_sensor_callback(void* data, SoSensor* sensor)
    {
        RobotVisualisation* self = static_cast<RobotVisualisation*>(data);
        self->pick_puzzle_queue_methode();
        sensor->schedule();
    }

    static void drop_puzzle_sensor_sensor_callback(void* data, SoSensor* sensor)
    {
        RobotVisualisation* self = static_cast<RobotVisualisation*>(data);
        self->drop_puzzle_queue_methode();
        sensor->schedule();
    }

    // Robot Callbacks
    // --------------------------------------------------------------------------------------------------------------
    void angles_callback(const interfaces::msg::Angles msg)
    {
        auto angles = msg.angles;
        // RCLCPP_INFO(this->get_logger(),
        //             "Received angles: [%f, %f, %f, %f, %f, %f]",
        //             angles.data[0],
        //             angles.data[1],
        //             angles.data[2],
        //             angles.data[3],
        //             angles.data[4],
        //             angles.data[5]);
        move.set_all_desired_angles(angles.data);

        puzzlebool_callback(msg.id, msg.picked);
    }

    // Puzzle Callbacks
    // --------------------------------------------------------------------------------------------------------------
    void startpos_callback(const interfaces::msg::PuzzlePose msg)
    {
        std::lock_guard<std::mutex> guard(place_puzzle_mutex);

        geometry_msgs::msg::Pose pose = msg.pose;
        PlacePuzzleQueueItem item;

        item.id = msg.id;

        item.x = pose.position.x;
        item.y = pose.position.y;
        item.z = pose.position.z;

        item.rx       = pose.orientation.x;
        item.ry       = pose.orientation.y;
        item.rz       = pose.orientation.z;
        item.rotation = pose.orientation.w;

        place_puzzle_queue.push_back(item);
    }

    void puzzle_callback(const interfaces::msg::SegmentedPuzzleTile::SharedPtr msg) const
    {
        // ID
        int id = msg->id;

        RCLCPP_INFO(this->get_logger(), "Received puzzle tile with ID: %d", id);

        // Picture
        SoTexture2* texture = new SoTexture2;
        SoSFImage& soImage  = texture->image;

        // Extrahieren der Bildgröße und der Anzahl der Kanäle
        SbVec2s size(msg->png.width, msg->png.height);
        int numComponents = 0;

        if (msg->png.encoding == "rgb8") {
            numComponents = 3;
        } else if (msg->png.encoding == "rgba8") {
            numComponents = 4;
        } else if (msg->png.encoding == "mono8") {
            numComponents = 1;
        } else if (msg->png.encoding == "8UC4") {
            numComponents = 4; // Assuming 8UC4 is similar to rgba8
        } else {
            RCLCPP_ERROR(this->get_logger(), "Unsupported image encoding: %s", msg->png.encoding.c_str());
            return;
        }

        const unsigned char* data = msg->png.data.data();
        soImage.setValue(size, numComponents, data);

        // Points
        std::vector<std::pair<float, float>> points;
        for (const auto& point : msg->points) {
            points.emplace_back(point.x, point.y);
        }

        SoSeparator* puzzle_tile = get_puzzle(points, texture, msg->png.width, msg->png.height);

        // Transform the Puzzle to the image origin
        SoTranslation* translation = new SoTranslation();
        translation->translation.setValue(
            SbVec3f(-(static_cast<float>(msg->png.width) * PUZZLE_SCALE_FACTOR) / 2,
                    -(static_cast<float>(msg->png.height) * PUZZLE_SCALE_FACTOR) / 2,
                    0));
        puzzle_tile->insertChild(translation, 0);

        RCLCPP_INFO(this->get_logger(), "Size Height: %d Width: %d", msg->png.height, msg->png.width);
        puzzle_map->insert(std::make_pair(id, puzzle_tile));
    }

    void puzzlebool_callback(int id, bool pick)
    {
        std::string boolStr = pick ? "true" : "false";

        if (picked == false && pick == true) {
            std::lock_guard<std::mutex> guard(pick_puzzle_mutex);
            pick_puzzle_queue.push_back(std::to_string(id));
            picked = true;
            RCLCPP_INFO(this->get_logger(), "Picked Puzzle: [pick: %s, id: %d]", boolStr.c_str(), id);
        } else if (picked == true && pick == false) {
            std::lock_guard<std::mutex> guard(drop_puzzle_mutex);
            drop_puzzle_queue.push_back(std::to_string(id));
            picked = false;
            RCLCPP_INFO(this->get_logger(), "Dropped Puzzle: [pick: %s, id: %d]", boolStr.c_str(), id);
        }
    }

    // Puzzle Methodes
    // --------------------------------------------------------------------------------------------------------------
    void place_puzzle_queue_methode()
    {
        std::lock_guard<std::mutex> guard(place_puzzle_mutex);
        for (const auto& item : place_puzzle_queue) {
            place_puzzle(item.id, item.x, item.y, item.z, item.rx, item.ry, item.rz, item.rotation);
        }
        place_puzzle_queue.clear();
    }

    void place_puzzle(int32_t id, float x, float y, float z, float rx, float ry, float rz, float rotation)
    {
        if (puzzle_map->find(id) != puzzle_map->end()) {
            SoSeparator* puzzle = (*puzzle_map)[id];

            std::string name = "transform_" + std::to_string(id);

            // Create and configure a new transform node
            SoTransform* newTransform = new SoTransform();
            newTransform->setName(SbName(name.c_str()));
            newTransform->translation.setValue(x, y, z);
            newTransform->rotation.setValue(SbRotation(SbVec3f(rx, ry, rz), rotation));

            puzzle->insertChild(newTransform, 0);

            root->addChild(puzzle);

            RCLCPP_INFO(this->get_logger(),
                        "Placed puzzle ID: %d at position (%f, %f, %f) with rotation",
                        id,
                        x,
                        y,
                        z);
        } else {
            RCLCPP_WARN(this->get_logger(), "Puzzle with ID: %d not found", id);
        }
    }

    void pick_puzzle_queue_methode()
    {
        std::lock_guard<std::mutex> guard(pick_puzzle_mutex);
        for (const auto& item : pick_puzzle_queue) {
            pick_puzzle(item);
        }
        pick_puzzle_queue.clear();
    }

    void pick_puzzle(std::string id)
    {
        int num = std::stoi(id);
        if (puzzle_map->find(num) != puzzle_map->end()) {
            SoSeparator* puzzle = (*puzzle_map)[num];

            std::string name = "transform_" + id;

            // Setup search action
            SoSearchAction searchAction;
            searchAction.setName(SbName(name.c_str()));
            searchAction.apply(puzzle);

            SoPath* path = searchAction.getPath();
            if (path) {
                SoNode* node = path->getTail();
                if (node) {
                    puzzle->removeChild(node);
                }
            }

            root->removeChild(puzzle);
            robotScene->addChild(puzzle);
        }
    }

    void drop_puzzle_queue_methode()
    {
        std::lock_guard<std::mutex> guard(drop_puzzle_mutex);
        for (const auto& item : drop_puzzle_queue) {
            drop_puzzle(item);
        }

        drop_puzzle_queue.clear();
    }

    void drop_puzzle(std::string id)
    {
        int num = std::stoi(id);
        if (puzzle_map->find(num) != puzzle_map->end()) {
            SoSeparator* puzzle = (*puzzle_map)[num];
            puzzle->setName("puzzle");

            SbMatrix sbmatrix = getTransform(puzzle);

            SbVec3f translation, scale;
            SbRotation rotation, scaleOrientation;
            sbmatrix.getTransform(translation, rotation, scale, scaleOrientation);

            // Hinzufuegen der gleichen Transformation zur Ziel-Szene
            SoTransform* newTransform = new SoTransform;
            newTransform->setName(SbName(("transform" + id).c_str()));
            RCLCPP_INFO(this->get_logger(),
                        "Placed puzzle ID: %s at position (%f, %f, %f)",
                        id.c_str(),
                        translation[0],
                        translation[1],
                        translation[2]);
            newTransform->translation.setValue(translation);
            newTransform->rotation.setValue(rotation);
            newTransform->scaleFactor.setValue(scale);
            newTransform->scaleOrientation.setValue(scaleOrientation);

            robotScene->removeChild(puzzle);

            puzzle->insertChild(newTransform, 0);

            root->addChild(puzzle);
        }
    }

    SbMatrix getTransform(SoSeparator* node)
    {
        SoSearchAction* searchaction = new SoSearchAction;
        searchaction->setNode(node);
        searchaction->apply(root);

        SoPath* path = searchaction->getPath();
        assert(path != NULL);

        // Then apply the SoGetMatrixAction to get the full transformation
        // matrix from world space.

        const SbViewportRegion vpr         = eviewer->getViewportRegion();
        SoGetMatrixAction* getmatrixaction = new SoGetMatrixAction(vpr);
        getmatrixaction->apply(path);

        SbMatrix transformation = getmatrixaction->getMatrix();

        // And if you want to access the individual transformation
        // components of the matrix:

        SbVec3f translation;
        SbRotation rotation;
        SbVec3f scalevector;
        SbRotation scaleorientation;

        transformation.getTransform(translation, rotation, scalevector, scaleorientation);
        return transformation;
    }
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node         = std::make_shared<RobotVisualisation>();
    auto watchdogNode = std::make_shared<Watchdog>();

    std::thread executor_thread([&watchdogNode]() {
        rclcpp::spin(watchdogNode);
        rclcpp::shutdown();
    });
    executor_thread.detach();

    while (watchdogNode->run != true)
        ;

    // Start ROS spinning in a separate thread
    std::thread ros_thread([&]() { rclcpp::spin(node); });

    // Start the GUI in the main thread
    node->startViewer(argc, argv);

    // Join the ROS thread before shutting down
    ros_thread.join();

    rclcpp::shutdown();
    return 0;
}
