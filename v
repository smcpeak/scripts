#!/bin/sh
# view - script to view or play media
# the script choose which program to use based on file extension

if [ "$1" = "" ]; then
cat <<EOF
usage: $0 file [file..]

known file formats, an associated players
  mp3 audio: playlist -> xaudio
    .mp3 - MPEG layer 3 audio
    .txt - my own song playlist format

  Ogg audio: ogg123
    .ogg - Ogg Vorbis

  video: mplayer
    .asf - ?
    .mov - Apple Quicktime
    .mpg - MPEG video
    .avi - Windows AVI video format

  image: xv
    .jpg - JPEG
    .gif - GIF
    .png - Portable Network Graphics format

  postscript: gv
    .ps - Postscript
    .eps - Encapsulated Postscript

  Portable document format: acroread
    .pdf - Adobe PDF

  Archives: viewtargz
    .tgz - Gzipped tar file (also .tar.gz)
    .tar.bz2 - BZipped tar file
    .zip - Zipped archive (also .ZIP)

EOF
  exit 0
fi

while [ "$1" != "" ]; do
  fname="$1"
  shift

  case "$fname" in
    *.mp3|*.txt)
      playlist "$fname"
      ;;

    *.ogg)
      ogg123 "$fname"
      ;;

    *.asf|*.mov|*.mpg|*.avi)
      mplayer "$fname"
      ;;

    *.jpg|*.gif|*.png)
      xv "$fname"
      ;;
      
    *.ps|*.eps)
      gv "$fname"
      ;;
      
    *.pdf)
      acroread "$fname"
      ;;
      
    *.tgz|*.tar.gz|*.tar.bz2|*.zip)
      viewtargz "$fname"
      ;;
      
    *)
      echo "I don't know how to view $fname"
      exit 2
  esac
done
  

