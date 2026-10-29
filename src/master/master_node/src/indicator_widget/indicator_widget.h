#ifndef INDICATOR_WIDGET_H
#define INDICATOR_WIDGET_H

#include <QColor>
#include <QLabel>

class IndicatorWidget : public QLabel
{
    Q_OBJECT

  public:
    explicit IndicatorWidget(QWidget* parent = nullptr);
    enum State
    {
        StateOk,
        StateError
    };

  public slots:
    void setState(bool state);
    void setState(State state);

  private:
    void updateStyleSheet();
    QColor currentColor;
};

#endif