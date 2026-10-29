# Entwicklungsumgebung für das Projekt, nur auf Basis öffentlicher Images und Paketquellen.
# ros:humble-ros-base ist ein Docker Official Image (Ubuntu 22.04) für amd64 und arm64,
# läuft also auch auf Apple Silicon nativ.
FROM ros:humble-ros-base-jammy

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    ROS_INSTALL_PATH=/opt/ros/humble

# ROS-Pakete und Systembibliotheken:
# - ros-humble-desktop: ROS-Werkzeuge (rqt, rviz2) wie im früheren Team-Image
# - cv-bridge und Lint-/Test-Pakete werden von den Paketen unter src/ benötigt
# - Coin3D/SoQt und Qt 5 für Visualizer und Master-Node
# - Python-Bibliotheken aus den Ubuntu-Paketen (OpenCV, Tk-Backend für matplotlib)
# - Xvfb, fluxbox, x11vnc und noVNC für das virtuelle Display im Browser;
#   hsetroot braucht fluxbox zum Setzen des Hintergrunds, sonst erscheint ein Fehler-Popup
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-humble-desktop \
        ros-humble-cv-bridge \
        ros-humble-ament-lint-auto \
        ros-humble-ament-lint-common \
        ros-humble-ament-cmake-gtest \
        build-essential cmake g++ git curl jq sudo zsh \
        qtbase5-dev libqt5widgets5 libcoin-dev libsoqt520-dev \
        libgl1-mesa-dri libglu1-mesa-dev mesa-utils x11-utils x11-xserver-utils xauth \
        python3-pip python3-dev python3-opencv python3-tk python3-matplotlib python3-scipy python3-pil \
        xvfb x11vnc fluxbox hsetroot novnc websockify \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten der ROS-Nodes, die es nicht als Ubuntu-Paket gibt.
# - pip muss aktualisiert werden, sonst lässt sich roboticstoolbox-python 1.1.1 nicht bauen.
# - numpy < 2, weil das System-OpenCV und cv_bridge gegen numpy 1.x gebaut sind.
# - spatialgeometry >= 1.2 ist mit roboticstoolbox-python 1.1.1 inkompatibel (TypeError bei RevoluteMDH).
# - python-fcl prüft in pkg_control die Bahnen auf Kollisionen.
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir \
        "numpy<2" \
        roboticstoolbox-python==1.1.1 \
        spatialgeometry==1.1.0 \
        python-fcl==0.7.0.11 \
        rdp==0.8 \
        scikit-image

# Benutzer für den Devcontainer (UID 1000 passt zum Standardbenutzer unter Linux).
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/zsh \
    && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /home/$USERNAME

RUN touch ~/.Xauthority \
    && echo "source /opt/ros/humble/setup.zsh" >> ~/.zshrc \
    && echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc \
    && rosdep update --rosdistro humble

CMD ["/bin/zsh"]
