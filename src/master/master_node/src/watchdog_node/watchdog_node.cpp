#include "watchdog_node.hpp"

using namespace std::chrono_literals;

WatchdogNode::WatchdogNode()
    : Node("WatchdogNode")
{

    publisher                     = create_publisher<std_msgs::msg::Bool>("/master/run", 10);
    subscription_watchdog_control = create_subscription<std_msgs::msg::Bool>(
        "/control/watchdog",
        10,
        std::bind(&WatchdogNode::watchdog_callback_control, this, std::placeholders::_1));

    subscription_watchdog_solver = create_subscription<std_msgs::msg::Bool>(
        "/solver/watchdog",
        10,
        std::bind(&WatchdogNode::watchdog_callback_solver, this, std::placeholders::_1));

    subscription_watchdog_digitalize = create_subscription<std_msgs::msg::Bool>(
        "/digitalize/watchdog",
        10,
        std::bind(&WatchdogNode::watchdog_callback_digitalize, this, std::placeholders::_1));

    subscription_watchdog_visualize = create_subscription<std_msgs::msg::Bool>(
        "/visualize/watchdog",
        10,
        std::bind(&WatchdogNode::watchdog_callback_visualize, this, std::placeholders::_1));

    rclcpp::Time last_callback_control;
    rclcpp::Time last_callback_solver;
    rclcpp::Time last_callback_digitalize;
    rclcpp::Time last_callback_visualize;

    timer = this->create_wall_timer(500ms, std::bind(&WatchdogNode::timer_callback, this));
}

void WatchdogNode::watchdog_callback_control(const std_msgs::msg::Bool::SharedPtr pMessage)
{
    last_callback_control = this->now();
    // RCLCPP_INFO(get_logger(), "Control Watchdog: %s", pMessage->data ? "true" : "false");
}

void WatchdogNode::watchdog_callback_solver(const std_msgs::msg::Bool::SharedPtr pMessage)
{
    last_callback_solver = this->now();
    // RCLCPP_INFO(get_logger(), "Solver Watchdog: %s", pMessage->data ? "true" : "false");
}
void WatchdogNode::watchdog_callback_digitalize(const std_msgs::msg::Bool::SharedPtr pMessage)
{
    last_callback_digitalize = this->now();
    // RCLCPP_INFO(get_logger(), "Digitalize Watchdog: %s", pMessage->data ? "true" : "false");
}
void WatchdogNode::watchdog_callback_visualize(const std_msgs::msg::Bool::SharedPtr pMessage)
{
    last_callback_visualize = this->now();
    // RCLCPP_INFO(get_logger(), "Visualize Watchdog: %s", pMessage->data ? "true" : "false");
}

void WatchdogNode::publish(bool b)
{
    std_msgs::msg::Bool message;
    message.data = b;
    publisher->publish(message);
}

void WatchdogNode::timer_callback()
{
    rclcpp::Time now   = this->now();
    control_running    = (now.seconds() - this->last_callback_control.seconds() < 5);
    solver_running     = (now.seconds() - this->last_callback_solver.seconds() < 5);
    visualizer_running = (now.seconds() - this->last_callback_visualize.seconds() < 5);
    digitalize_running = (now.seconds() - this->last_callback_digitalize.seconds() < 5);
}

bool WatchdogNode::get_node_status(NODE node)
{

    switch (node) {
        case CONTROL:
            return control_running;
        case SOLVER:
            return solver_running;
        case DIGITALIZE:
            return digitalize_running;
        case VISUALIZE:
            return visualizer_running;
    }
    return false;
}