# Solver

The ROS package `pkg_solver` receives the segmented puzzle pieces from Digitalize, solves the puzzle with the algorithmic approach (geometric edge matching, `submodules/src`) and sends the pieces one by one to Control.

## Getting Started

How to set up, build and run the project is described in the [README in the project root](../../README.md#inbetriebnahme). All Python dependencies of the ROS solver node are installed in the dev container ([.devcontainer/Dockerfile](../../.devcontainer/Dockerfile)); new packages need to be added there.
