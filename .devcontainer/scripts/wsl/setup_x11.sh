#!/usr/bin/env sh

# Install Xauth server for Windows
# https://sourceforge.net/projects/vcxsrv/files/latest/download

sudo apt install -y xauth xorg

say() { if ! ${quiet:-false}; then printf '%s\n' "$@"; fi; }
err() { echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2; }

# File name of the Windows xserver program
win_xserver='vcxsrv.exe'

# Full path to the Windows xauth program for the running xserver
# PROGRA~1 is the short name for "Program Files", which solves spaces issues
win_xauth_exe='/mnt/c/PROGRA~1/VcXsrv/xauth.exe'

# Screen to use for the DISPLAY (can be either an integer or a decimal)
screen='0.0'

# Normally xauth defaults to ~/.Xauthority, but a different file will allow automatically removing outdated entries
xauthority_file="$HOME/.Xauthority"

# Whether or not to force recreation of the .Xauthority file
force=false

while getopts ":a:e:fhqs:x:" OPT; do
  case "$OPT" in
    a) win_xauth_exe="${OPTARG}" ;;
    e) screen="${OPTARG}" ;;
    f) force=true ;;
    h)
      cat << EOL
Configure X11 from WSL to the Windows host X Window server

wsl_x11_setup.sh [-a PATH] [-e NUM] [-f] [-q] [-s FILENAME] [-x PATH]

  -a Specify the xauth.exe path to use

  -e Specify the screen to use for the DISPLAY
       Can be either an integer or a decimal

  -f Force recreation of .Xauthority file

  -h Display this help text

  -q Prevent all output

  -s Specify the file name of the Windows xserver program
       This will be used to verify the server is running

  -x Specify the .Xauthority file to use

EOL
      exit 0
      ;;
    q) quiet=true ;;
    s) win_xserver="${OPTARG}" ;;
    x) xauthority_file="${OPTARG}" ;;
    \?)
      err "Argument '-${OPTARG}' not recognized"
      exit 3
      ;;
  esac
done
shift $((OPTIND - 1))

# Get the adapter address on WSL2
_remote_ip="$(awk '/nameserver/ { print $2; exit 0 }' < /etc/resolv.conf)"
# An alternative way to retrieve the real adapter address on WSL2, which would be different than /etc/resolv.conf if you
# happened to make changes to that file.
if [ -z "$_remote_ip" ]; then
  _remote_ip="$(/mnt/c/Windows/System32/ipconfig.exe \
    | awk 'BEGIN{RS="\r\n"} NR==1,/vEthernet \(WSL\):/ {next}; $1=="IPv4" {print $NF; exit}')"
fi

export DISPLAY="${_remote_ip}:${screen}"

# Tests whether the currently defined DISPLAY is already configured in xauth
check_xauth() {
  touch "$xauthority_file"
  say "Checking for existence of current DISPLAY ($DISPLAY) in $xauthority_file file"
  [ -n "$(xauth -f "$xauthority_file" -n list "$DISPLAY")" ]
}

# Validates that the configured X11 forwarding is working
validate_x11_forwarding() {
  say "Validating X11 forwarding is working"
  xset q 1> /dev/null 2>&1
}

# Simple check for a running existence of the win_xserver process. This is faster, though less reliable, than check_processes
check_tasklist() {
  say "Checking task list for existence of $win_xserver"
  /mnt/c/Windows/System32/tasklist.exe /V /FI "IMAGENAME eq $win_xserver" /FI "STATUS eq running" /NH 2> /dev/null \
    | grep -qs "^$win_xserver"
}

# Checks whether the process list contains an entry with the win_xserver process running on the same display to which we
# intend to connect. This is slower, though more reliable, than check_tasklist
check_processes() {
  say "Checking process list for existence of $win_xserver"
  _processes="$(/mnt/c/Windows/System32/Wbem/wmic.exe path win32_process get commandline /format:list \
    | sed -e 's/ \{2,\}//' \
    | grep -o "${win_xserver%.*}.*:[0-9]\.\?[0-9]\?")"
  echo "$_processes" | grep -qs "${win_xserver%.*}" && echo "$_processes" | grep -qs "\s:${screen%.*}"
}

# Creates a temporary xauth token on the Windows side that'll allow an authorized connection
add_cookie_to_remote() {
  if [ ! -f "$win_xauth_exe" ]; then
    err "Windows xauth.exe program not found at '$win_xauth_exe'"
    return 3
  fi
  _key="$(printf '%s\n' "generate localhost:${screen%.*} . trusted timeout 604800" 'list' 'quit' \
    | "$win_xauth_exe" -i -n -q 2> /dev/null)"
  touch "$xauthority_file"
  xauth -f "$xauthority_file" -q remove "$DISPLAY"
  say "Adding DISPLAY to xauth"
  [ -n "$_key" ] && xauth -f "$xauthority_file" -q add "$DISPLAY" . "${_key##* }"
}

# Use check_tasklist for slightly quicker, less reliable check, or check_processes for a more reliable, slighly slower check
if ! check_tasklist; then
  err "$win_xserver is not running on display $DISPLAY"
  exit 1
fi
if ! $force && check_xauth && validate_x11_forwarding; then
  say 'xauth is already set up'
  exit 0
fi
if ! add_cookie_to_remote; then
  err "Unable to create MIT-MAGIC-COOKIE-1 for display $DISPLAY"
  exit 2
else
  say "Successfully set up X11 for $DISPLAY"
  exit 0
fi
