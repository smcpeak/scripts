#!/bin/sh
# Run Handbrake to convert to 30 FPS, 720p.

if [ "x$1" = "x" ]; then
  echo "usage: $0 filename.mp4"
  exit 2
fi

case "$1" in
  *.mp4)
    base=$(basename --suffix=.mp4 "$1")
    ;;

  *)
    echo "Argument should end in '.mp4'."
    exit 2
    ;;
esac

HandBrakeCLI.exe \
  --preset-import-file $(cygpath -m $HOME/scripts/data/handbrake-720p-30fps.json) \
  -i "$base.mp4" -o "$base-30fps.mp4"

# EOF
