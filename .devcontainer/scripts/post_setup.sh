#!/usr/bin/env bash
# Wird einmalig nach dem Erstellen des Containers ausgeführt (postCreateCommand).

WORKSPACE_DIR="$HOME/workspace"
cd "$WORKSPACE_DIR" || exit 1

# ROS-Abhängigkeiten aus den package.xml-Dateien nachinstallieren.
# SoQt ist im Image aus den Quellen gebaut und hat keinen rosdep-Eintrag.
rosdep update
sudo apt-get update
rosdep install --from-paths src --ignore-src -y --skip-keys "SoQt"

# ROS und das Workspace-Overlay (falls schon gebaut) in jeder neuen Shell automatisch laden.
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    [ -f "$rc" ] || continue
    shell_ext="${rc##*.}"
    shell_ext="${shell_ext%rc}"
    # Die .zshrc im Image endet ohne Zeilenumbruch, daher jede Zeile mit führendem \n anhängen.
    if ! grep -qF "/opt/ros/humble/setup.$shell_ext" "$rc"; then
        printf '\n%s\n' "source /opt/ros/humble/setup.$shell_ext" >> "$rc"
    fi
    line="[ -f $WORKSPACE_DIR/install/setup.$shell_ext ] && source $WORKSPACE_DIR/install/setup.$shell_ext"
    if ! grep -qF "$line" "$rc"; then
        printf '\n%s\n' "$line" >> "$rc"
    fi
done

echo "=============== Finished ==============="
