#ifndef MAIN_WINDOW_H
#define MAIN_WINDOW_H

#include "indicator_widget/indicator_widget.h"
#include "qabstractbutton.h"
#include "rclcpp/node.hpp"       // IWYU pragma: keep
#include "std_msgs/msg/bool.hpp" // IWYU pragma: keep
#include "watchdog_node/watchdog_node.hpp"

#include <QFormLayout>
#include <QMainWindow>
#include <QPushButton>
#include <QVBoxLayout>

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

    int timerId;
    void timerEvent(QTimerEvent* event);

  public:
    MainWindow(QWidget* parent = nullptr);
    ~MainWindow();

    std::shared_ptr<WatchdogNode> watchdogNode;

  private slots:
    void on_startButton_clicked();
    void on_stopButton_clicked();

  private:
    QWidget* centralWidget;

    QVBoxLayout* mainLayout;
    QFormLayout* indicatorLayout;
    QHBoxLayout* buttonLayout;
    QButtonGroup* buttons;
    QPushButton* runButton;
    QPushButton* stopButton;

    IndicatorWidget* controlIndicator;
    IndicatorWidget* digitalizeIndicator;
    IndicatorWidget* solverIndicator;
    IndicatorWidget* visualizeIndicator;

    QLabel* controlLabel;
    QLabel* digitalizeLabel;
    QLabel* solverLabel;
    QLabel* visualizeLabel;
};
#endif