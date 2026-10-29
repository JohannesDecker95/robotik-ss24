#pragma once

/*>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
>>>>>>>>>>>>>>>>>>>>>>>>> CLASS DEFINITION <<<<<<<<<<<<<<<<<<<<<<<<<<
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<*/
#include "rclcpp/node.hpp"
#include "std_msgs/msg/bool.hpp" // IWYU pragma: keep

enum NODE
{
    CONTROL,
    SOLVER,
    DIGITALIZE,
    VISUALIZE
};

class WatchdogNode : public rclcpp::Node
{
    // idea of the timer is to fire up every 5 seconds and look if the last wtd message was longer than 5
    // seconds ago make a struct that stores the current value of the running variable and a timestamp when
    // the last was received
    // rclcpp::TimerBase::SharedPtr timer;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr publisher;

    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr subscription_watchdog_control;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr subscription_watchdog_digitalize;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr subscription_watchdog_solver;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr subscription_watchdog_visualize;

    void watchdog_callback_control(const std_msgs::msg::Bool::SharedPtr pMessage);
    void watchdog_callback_solver(const std_msgs::msg::Bool::SharedPtr pMessage);
    void watchdog_callback_digitalize(const std_msgs::msg::Bool::SharedPtr pMessage);
    void watchdog_callback_visualize(const std_msgs::msg::Bool::SharedPtr pMessage);

    bool control_running;
    bool digitalize_running;
    bool solver_running;
    bool visualizer_running;

    rclcpp::Time last_callback_control;
    rclcpp::Time last_callback_solver;
    rclcpp::Time last_callback_digitalize;
    rclcpp::Time last_callback_visualize;

    rclcpp::TimerBase::SharedPtr timer;
    void timer_callback();

  public:
    WatchdogNode();
    void publish(bool b);

    bool get_node_status(NODE node);
};