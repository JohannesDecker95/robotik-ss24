#pragma once
#include "rclcpp/rclcpp.hpp"

#include <std_msgs/msg/bool.hpp>

using namespace std::chrono_literals;

class Watchdog : public rclcpp::Node
{
    rclcpp::TimerBase::SharedPtr timer;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr publisher;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr subscription;

  public:
    Watchdog();
    void timer_callback();
    void listener_callback(const std_msgs::msg::Bool::SharedPtr pMessage);
    bool run = false;
};