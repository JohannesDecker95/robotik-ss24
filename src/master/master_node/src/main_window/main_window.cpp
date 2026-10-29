#include "main_window.hpp"

#include "rclcpp/executors.hpp" // IWYU pragma: keep

#include <QThread>

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
    , centralWidget(new QWidget(this))

{
    setWindowTitle("Master Node");
    setCentralWidget(centralWidget);
    mainLayout      = new QVBoxLayout;
    indicatorLayout = new QFormLayout;
    buttonLayout    = new QHBoxLayout;

    runButton  = new QPushButton("Run");
    stopButton = new QPushButton("Stop");
    runButton->setFixedHeight(50);
    runButton->setEnabled(false);
    stopButton->setFixedHeight(50);
    buttonLayout->addWidget(runButton);
    buttonLayout->addWidget(stopButton);

    controlIndicator    = new IndicatorWidget();
    solverIndicator     = new IndicatorWidget();
    visualizeIndicator  = new IndicatorWidget();
    digitalizeIndicator = new IndicatorWidget();

    controlLabel    = new QLabel("Control");
    solverLabel     = new QLabel("Solver");
    visualizeLabel  = new QLabel("Visualize");
    digitalizeLabel = new QLabel("Digitalize");
    QFont font      = controlLabel->font();
    font.setPointSize(18);
    font.setBold(true);
    controlLabel->setFont(font);
    solverLabel->setFont(font);
    visualizeLabel->setFont(font);
    digitalizeLabel->setFont(font);

    indicatorLayout->addRow(controlIndicator, controlLabel);
    indicatorLayout->addRow(solverIndicator, solverLabel);
    indicatorLayout->addRow(visualizeIndicator, visualizeLabel);
    indicatorLayout->addRow(digitalizeIndicator, digitalizeLabel);

    mainLayout->addLayout(indicatorLayout);
    mainLayout->addStretch();
    mainLayout->addLayout(buttonLayout);

    centralWidget->setLayout(mainLayout);

    timerId = startTimer(500);

    connect(runButton, &QPushButton::clicked, this, &MainWindow::on_startButton_clicked);
    connect(stopButton, &QPushButton::clicked, this, &MainWindow::on_stopButton_clicked);
}

MainWindow::~MainWindow()
{
    delete indicatorLayout;
    delete runButton;
    delete stopButton;

    delete controlIndicator;
    delete solverIndicator;
    delete visualizeIndicator;
    delete digitalizeIndicator;

    delete controlLabel;
    delete solverLabel;
    delete visualizeLabel;
    delete digitalizeLabel;
}

void MainWindow::on_startButton_clicked()
{
    watchdogNode->publish(true);
}
void MainWindow::on_stopButton_clicked()
{
    watchdogNode->publish(false);
}

void MainWindow::timerEvent(QTimerEvent* event)
{
    auto controlState = watchdogNode->get_node_status(CONTROL);
    controlIndicator->setState(controlState);

    auto solverState = watchdogNode->get_node_status(SOLVER);
    solverIndicator->setState(solverState);

    auto digitalizeState = watchdogNode->get_node_status(DIGITALIZE);
    digitalizeIndicator->setState(digitalizeState);

    auto visualizeState = watchdogNode->get_node_status(VISUALIZE);
    visualizeIndicator->setState(visualizeState);

    runButton->setEnabled(controlState && solverState && digitalizeState && visualizeState);
}
