# Projektstudium Robotik (SS24)

Ein virtueller Roboter soll automatisiert ein Puzzle lösen.

https://github.com/user-attachments/assets/066d19be-bd08-47ee-b655-860c3f94c7c0

## Inbetriebnahme

Das Projekt läuft in einem Docker-Devcontainer. Auf dem eigenen Rechner wird außer Docker und VS Code nichts installiert.

### Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (unter Linux genügt Docker Engine), gestartet
- [Visual Studio Code](https://code.visualstudio.com/) mit der Erweiterung **Dev Containers** (`ms-vscode-remote.remote-containers`)
- ca. 10 GB freier Speicherplatz
- Internetzugang beim ersten Start. Geladen werden nur öffentliche Quellen: das offizielle Image `ros:humble-ros-base-jammy` von Docker Hub sowie Pakete von Ubuntu, packages.ros.org und PyPI. Eine Anmeldung ist nicht nötig.

Das Image läuft auf Intel/AMD (`amd64`) und auf Apple Silicon bzw. ARM (`arm64`) jeweils nativ.

### 1. Container öffnen

1. Den Projektordner in VS Code öffnen.
2. `Strg+Umschalt+P` (macOS: `Cmd+Umschalt+P`) → **Dev Containers: Reopen in Container**.
3. Die passende Konfiguration für das eigene Betriebssystem wählen:
   - **ROS 2 Development Container for Mac OS X** (`.devcontainer/mac`)
   - **ROS 2 Development Container for Linux** (`.devcontainer/linux`)
   - **ROS 2 Development Container for WSL** (`.devcontainer/wsl`)

Beim ersten Mal baut Docker das Projekt-Image aus [.devcontainer/Dockerfile](.devcontainer/Dockerfile) (ca. 4 GB). Das dauert je nach Verbindung etwa 5–15 Minuten. Danach führt der Container automatisch [post_setup.sh](.devcontainer/scripts/post_setup.sh) aus (`rosdep install` und Shell-Konfiguration). Spätere Starts dauern nur wenige Sekunden.

### 2. Display einrichten

Master-Node und Visualizer sind grafische Anwendungen.

**macOS:** Der Container startet ein virtuelles Display. VS Code leitet Port 6080 automatisch weiter. Im Browser öffnen:

```
http://localhost:6080/vnc.html
```

Dort auf **Verbinden** klicken. Die Fenster der Anwendungen erscheinen später in diesem Browser-Tab. XQuartz ist nicht nötig.

**Linux:** Die Fenster erscheinen direkt auf dem Desktop. Vorher **auf dem Host** dem Container den Zugriff auf den X-Server erlauben:

```bash
xhost +local:
```

**Windows (WSL):** Den X-Server [VcXsrv](https://sourceforge.net/projects/vcxsrv/files/latest/download) installieren und starten, dann **in WSL** [.devcontainer/scripts/wsl/setup_x11.sh](.devcontainer/scripts/wsl/setup_x11.sh) ausführen.

> Wenn X11 unter Linux oder WSL Probleme macht, kann auch dort das virtuelle Display genutzt werden: im Container `export DISPLAY=:1 && .devcontainer/scripts/start_display.sh` ausführen, dann `http://localhost:6080/vnc.html` öffnen.

### 3. Workspace bauen

Im VS-Code-Terminal (das bereits im Container läuft), im Workspace-Verzeichnis `/home/vscode/workspace`:

```bash
colcon build
source install/setup.zsh
```

Der Build dauert etwa eine halbe Minute. Warnungen bei `master_node` und `visualizer` sind normal. Neue Terminals laden `install/setup.zsh` automatisch; das `source` ist nur im Terminal nötig, in dem gebaut wurde. Alternativ in VS Code: `Strg+Umschalt+B` → **Build ROS Package All**.

### 4. System starten

**Unbedingt aus dem Workspace-Verzeichnis starten.** Der Visualizer lädt Robotermodell und Umgebung über die relativen Pfade `data/kuka_kr6.iv` und `data/environment.yaml`.

```bash
cd /home/vscode/workspace
ros2 launch master_node application_launch.py
```

Das startet alle fünf Nodes. Danach:

1. Im Fenster **Master Node** warten, bis alle vier Anzeigen (Control, Solver, Visualize, Digitalize) grün sind. Das dauert ca. 10–30 Sekunden.
2. Auf **Run** klicken.

Ab dann läuft alles automatisch. Den Fortschritt zeigt das Terminal:

| Schritt | Log-Ausgabe | Dauer (ca.) |
| --- | --- | --- |
| Digitalize verschickt die 49 Puzzleteile aus `sam_imgs/` | `Image received: ID=…` | 1 min |
| Solver berechnet die Lösung | `Start puzzle solving.` → `Finished puzzle solving.` | 30 s |
| Control fährt Teil für Teil an, das Fenster **KUKA KR6 Visualisation** zeigt die Bewegung | `Puzzle Piece picked up.` / `Puzzle Piece placed.` | ca. 14 s pro Teil |

Im Visualizer lässt sich die Ansicht mit der Maus drehen (linke Taste), verschieben (mittlere Taste) und zoomen (Mausrad).

Beenden: `Strg+C` im Terminal, in dem `ros2 launch` läuft.

### Erneut ausführen

Der Solver speichert die empfangenen Teile und die extrahierten Kanten in `src/solver/images/` (inklusive `extracted_pieces.json`) und verwendet diesen Cache beim nächsten Lauf wieder. Wenn sich die Eingabebilder ändern, den Ordner vorher löschen:

```bash
rm -rf src/solver/images
```

### Alternative ohne VS Code (Linux mit X11)

Derselbe Container lässt sich auch per Docker Compose starten. Danach weiter mit Schritt 3 und 4 im Container:

```bash
cd .devcontainer/scripts/manual_deploy
docker compose up -d --build
docker exec -it ros2-humble-devcontainer zsh
```

### Fehlerbehebung

| Problem | Ursache / Lösung |
| --- | --- |
| Eine Anzeige im Master bleibt rot | Der Node ist abgestürzt. Im Launch-Terminal nach `Traceback` oder `process has died` suchen. |
| Visualizer startet nicht oder zeigt keinen Roboter | `ros2 launch` wurde nicht aus `/home/vscode/workspace` gestartet. |
| `Package 'master_node' not found` | Workspace nicht gebaut oder nicht gesourct: `colcon build && source install/setup.zsh`. |
| macOS: `localhost:6080` lädt nicht | In VS Code im Tab **Ports** prüfen, ob 6080 weitergeleitet wird. Sonst im Container `.devcontainer/scripts/start_display.sh` ausführen. |
| Linux: `could not connect to display` | Auf dem Host `xhost +local:` ausführen und den Container neu starten. |
| Nach Änderungen am Dockerfile passiert nichts | `Strg+Umschalt+P` → **Dev Containers: Rebuild Container**. |

## Projektüberblick

Das System besteht aus fünf ROS-2-Nodes (ROS 2 Humble), die über Topics und eine Action miteinander sprechen:

```
              Puzzleteile                Nächstes Teil              Gelenkwinkel
Digitalize ───────────────► Solver ───────────────────► Control ───────────────► Visualizer
     │                         │      Startposition                                  ▲
     │                         └─────────────────────────────────────────────────────┤
     └───────────────────────────────── Puzzleteile (Bilder + Kontur) ───────────────┘

Master: GUI mit Statusanzeige aller Nodes und Run/Stop-Knopf
```

| Paket | Pfad | Aufgabe |
| --- | --- | --- |
| `interfaces` | `src/messages/interfaces` | Eigene Messages und die Action `Segment` |
| `master_node` | `src/master/master_node` | Master-GUI (Qt), überwacht die Watchdogs der anderen Nodes |
| `pkg_digitalize` | `src/ditialize/pkg_digitalize` | Liest die Puzzleteile aus `sam_imgs/` und verschickt sie |
| `pkg_solver` | `src/solver/pkg_solver` | Löst das Puzzle und schickt Teil für Teil an Control |
| `pkg_control` | `src/control/pkg_control` | Kollisionsfreie Bahnplanung und inverse Kinematik (Robotics Toolbox, python-fcl) |
| `visualizer` | `src/visualizer` | 3D-Visualisierung des KUKA KR6 und der Roboterzelle mit Coin3D/SoQt |

### Roboterzelle und Kollisionsprüfung

Der Roboter steht auf einem Boden zwischen zwei Tischen: Auf dem Bereitstellungstisch liegt das nächste Teil, auf dem Puzzletisch wird das Puzzle gelegt. Boden und Tische sind in [data/environment.yaml](data/environment.yaml) als Quader beschrieben, zusammen mit der Aufnahmeposition und dem Ursprung des Puzzles. Solver, Control und Visualizer lesen dieselbe Datei. Wer einen Tisch verschiebt, muss die Positionen dort mit anpassen.

Control plant jede Bewegung so, dass sich die Glieder des Roboters weder gegenseitig noch Boden oder Tische durchdringen:

- **Volumenmodell:** Geprüft werden die Dreiecksnetze, die der Visualizer rendert. Sie liegen als STL in [data/collision/](data/collision/). Nach Änderungen an den `.iv`-Dateien des Roboters werden sie neu erzeugt mit `ros2 run visualizer export_collision_meshes data/kuka_kr6.iv data/collision`.
- **Sicherheitsabstand:** 10 mm zwischen allen geprüften Körpern. Nur der Flansch darf beim Greifen und Ablegen bis auf 1 mm an die Tischplatte heran.
- **Bahnen:** Für das Ziel wird eine kollisionsfreie Gelenkstellung gesucht, dann fährt der Roboter im Gelenkraum dorthin und senkt sich die letzten 5 cm senkrecht ab. Die Bahn wird lückenlos geprüft: Der Prüfschritt richtet sich nach dem aktuellen Abstand, sodass sich zwischen zwei Prüfungen kein Punkt des Roboters weiter bewegt, als Platz ist.
- **Gelenkgrenzen** in [robot.py](src/control/pkg_control/pkg_control/robot.py) verhindern, dass benachbarte Glieder ineinanderklappen. Benachbarte Glieder berühren sich im Gelenk konstruktionsbedingt und werden deshalb nicht paarweise geprüft.

Findet Control keine kollisionsfreie Bewegung, meldet es das auf `/control/panic` und fährt nicht. Die Tests in [test_collision.py](src/control/pkg_control/test/test_collision.py) planen Greifen und Ablegen für mehrere Positionen auf dem Puzzletisch und prüfen jede gesendete Gelenkstellung:

```bash
cd /home/vscode/workspace/src/control/pkg_control && python3 -m pytest test/test_collision.py
```

## Entwicklungsumgebung im Detail

Das Projekt-Image ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)) ist eigenständig und baut auf dem offiziellen Docker-Hub-Image `ros:humble-ros-base-jammy` auf (Ubuntu 22.04, ROS 2 Humble). Es installiert:

- **ROS-Pakete:** `ros-humble-desktop` (rqt, rviz2), `cv_bridge` sowie die Lint- und Test-Pakete, die die Pakete unter `src/` verlangen.
- **Coin3D, SoQt und Qt 5** aus den Ubuntu-Paketen (`libcoin-dev`, `libsoqt520-dev`, `qtbase5-dev`) für Visualizer und Master-Node.
- **Python-Pakete:** OpenCV, matplotlib (mit Tk), SciPy und Pillow aus Ubuntu; über pip `roboticstoolbox-python==1.1.1`, `spatialgeometry==1.1.0`, `python-fcl` (Kollisionsprüfung), `rdp` und `scikit-image`. `numpy` ist auf < 2 begrenzt, weil das System-OpenCV und `cv_bridge` gegen numpy 1.x gebaut sind.
- **Virtuelles Display:** Xvfb, fluxbox, x11vnc und noVNC. Gestartet wird es über [start_display.sh](.devcontainer/scripts/start_display.sh).
- **Benutzer `vscode`** (UID 1000, sudo ohne Passwort, Shell zsh). ROS ist in `.zshrc` und `.bashrc` bereits eingebunden.

## Weitere Dokumentation

- Videos und Screenshots eines kompletten Laufs: [Medien/](Medien/)
- Projektdokumentation: [Projektdokumentation/main.pdf](Projektdokumentation/main.pdf)
- Präsentationen: [Projektpräsentation/](Projektpräsentation/)
- Wiki-Zusammenfassung (Schnittstellen, Teams, Termine): [Robotik_SS24_Wiki_Zusammenfassung.md](Robotik_SS24_Wiki_Zusammenfassung.md)
- Hinweise der einzelnen Teams: `README.md` in den jeweiligen Ordnern unter `src/`

Projektdokumentation und Präsentationen zeigen den Stand vom Juni 2024. Bahnplanung und Roboterzelle wurden seitdem geändert: Damals fuhr der Roboter auf einer Bézier-Bahn ohne Kollisionsprüfung, und die Teile lagen auf Bodenhöhe. Den aktuellen Stand beschreibt der Abschnitt [Roboterzelle und Kollisionsprüfung](#roboterzelle-und-kollisionsprüfung).
