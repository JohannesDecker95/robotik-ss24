#include "main_window/main_window.hpp"

#include <QApplication>
#include <QPushButton>
#include <rclcpp/rclcpp.hpp>

int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);

    QApplication app(argc, argv);
    MainWindow mainWindow;

    std::shared_ptr<WatchdogNode> watchdogNode = std::make_shared<WatchdogNode>();
    mainWindow.watchdogNode                    = watchdogNode;

    std::thread executor_thread([&watchdogNode]() {
        rclcpp::spin(watchdogNode);
        rclcpp::shutdown();
    });
    executor_thread.detach();

    mainWindow.setFixedSize(500, 500);
    mainWindow.show();

    return app.exec();
}
