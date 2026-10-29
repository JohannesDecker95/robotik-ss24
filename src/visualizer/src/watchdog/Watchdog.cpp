#include "Watchdog.hpp"

Watchdog::Watchdog()
    : Node("visualize_watchdog")
{
    subscription = this->create_subscription<std_msgs::msg::Bool>(
        "/master/run", 10, std::bind(&Watchdog::listener_callback, this, std::placeholders::_1));

    publisher = this->create_publisher<std_msgs::msg::Bool>("/visualize/watchdog", 10);

    timer = this->create_wall_timer(1000ms, std::bind(&Watchdog::timer_callback, this));
}

void Watchdog::listener_callback(const std_msgs::msg::Bool::SharedPtr pMessage)
{
    if (pMessage->data == true) {
        run = true;
    } else {
        throw;
    }
    // if msg
    //     .data == True : run = True else : raise("Shutdown")
}

void Watchdog::timer_callback()
{
    std_msgs::msg::Bool message;
    message.data = true;
    publisher->publish(message);
}
