#include "indicator_widget.h"

static const int SIZE = 50;
static const QString greenSS =
    QString("color: white;border-radius: %1;background-color: qlineargradient(spread:pad, x1:0.145, y1:0.16, "
            "x2:1, y2:1, stop:0 rgba(20, 252, 7, 255), stop:1 rgba(25, 134, 5, 255));")
        .arg(SIZE / 2);
static const QString redSS =
    QString("color: white;border-radius: %1;background-color: qlineargradient(spread:pad, x1:0.145, y1:0.16, "
            "x2:0.92, y2:0.988636, stop:0 rgba(255, 12, 12, 255), stop:0.869347 rgba(103, 0, 0, 255));")
        .arg(SIZE / 2);

IndicatorWidget::IndicatorWidget(QWidget* parent)
    : QLabel(parent)
{
    // Set to ok by default
    setState(StateError);
    setFixedSize(SIZE, SIZE);
}

void IndicatorWidget::setState(State state)
{
    switch (state) {
        case StateOk:
            setStyleSheet(greenSS);
            break;
        case StateError:
            setStyleSheet(redSS);
            break;
        default:
            setStyleSheet(redSS);
            break;
    }
}

void IndicatorWidget::setState(bool state)
{
    setState(state ? StateOk : StateError);
}
