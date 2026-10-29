How to set up, build and run the project is described in the [README in the project root](../../README.md#inbetriebnahme).

# Interfaces

The package `interfaces` defines the messages and the action the nodes exchange. Besides these, the nodes use standard messages: `geometry_msgs/PoseArray` on `/solver/nextpiece` (pickup and place pose of the next piece, Solver → Control), `diagnostic_msgs/DiagnosticStatus` on `/control/panic` (errors of Control) and the watchdog topics `/<node>/watchdog` monitored by the master.

| Interface | Topic / action | From → to |
| --- | --- | --- |
| `SegmentedPuzzleTile` | `/digitalize/imgs` | Digitalize → Visualizer |
| `Segment` | `/digitalize/segment` | Solver (client) → Digitalize (server) |
| `PuzzlePose` | `/solver/startpos` | Solver → Visualizer |
| `PuzzleBoolean` | `/control/puzzlebool` | Control → Solver |
| `Angles` | `/control/angles` | Control → Visualizer |

# Messages
## SegmentedPuzzleTile
```
int32 id
sensor_msgs/Image png
Point2d[] points
```
A segmented puzzle tile: its id, the image and the approximated contour as list of points.
## Point2d
```
int32 x
int32 y
```
Represents a 2d point. A list of `Point2d`s forms a shape / contour (of a puzzle piece).
## PuzzlePose
```
# id of the puzzle piece
int32 id
# pose of the puzzle piece (with x- and y-axis aligned with image x- and y-axis) in robot base frame
geometry_msgs/Pose pose
```
Where the solver provides the next piece, so the visualizer can show it there before it is picked up.
## PuzzleBoolean
```
# toggle-data for a puzzle piece
bool data
# id of the specific piece
string id
```
`true` when Control has picked up the piece, `false` when it has been placed. The solver provides the next piece after a piece has been placed.
## Angles
```
# angle data
std_msgs/Float64MultiArray angles
# boolean to indicate if puzzle piece is picked up or not
bool picked
# id of the puzzle piece
int32 id
```
The six joint angles of the robot in rad, published by Control at 100 Hz while the robot moves, together with the piece the robot currently carries.
# Actions
## Segment
```
<empty> # No request must be provided
---
bool success # Result: all images were sent
int32 png_total_count # Result: total count of images sent, for the receiver to confirm it got all images
---
sensor_msgs/Image png # Feedback
int32 id # Feedback
```
Triggers the digitalize node to send the segmented puzzle pieces. The images are returned one by one as feedback to the action.
