#!/bin/sh
# view - script to view or play media
#
# the script chooses which program to use based on file extension

if [ "$1" = "" -a -f "playlist.txt" ]; then
  # shorthand: say 'v' in a directory with a playlist to play it
  exec "$0" playlist.txt
fi

if [ -d "$1" -a -f "$1/playlist.txt" ]; then
  # yet more shorthand: say 'v' *of* a directory with a playlist
  cd "$1"
  exec "$0" playlist.txt
fi

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
    .mpg - MPEG video (also .mpeg)
    .avi - Windows AVI video format
    .wmv - Windows Media Video
    .wma - Windows Media Audio

  streaming video: realplayer
    .rmm,.rm - realplayer

  image: xv
    .jpg - JPEG
    .gif - GIF
    .png - Portable Network Graphics format

  postscript: gv
    .ps    - Postscript
    .ps.gz - Compressed postscript
    .eps   - Encapsulated Postscript

  Portable document format: acroread
    .pdf - Adobe PDF

  Archives: viewtargz
    .tgz     - Gzipped tar file (also .tar.gz)
    .tar.bz2 - BZipped tar file
    .zip     - Zipped archive (also .ZIP)

  Certificates: openssl
    .pem - PEM certificate
    .crt - PEM certificate
    .der - DER certificate

EOF
  exit 0
fi

while [ "$1" != "" ]; do
  fname="$1"
  shift

  case `echo "$fname" | tolower` in
    *.mp3|*.txt)
      playlist "$fname"
      ;;

    *.ogg)
      ogg123 "$fname"
      ;;

    *.asf|*.mov|*.mpg|*.mpeg|*.avi|*.wmv|*.wma)
      mplayer "$fname"
      ;;

    *.rmm|*.rm)
      realplay "$fname"
      ;;

    *.jpg|*.gif|*.png)
      xv "$fname"
      ;;

    *.ps|*.ps.gz|*.eps)
      gv "$fname"
      ;;

    *.pdf)
      acroread "$fname"
      ;;
      
    *.tgz|*.tar.gz|*.tar.bz2|*.zip)
      viewtargz "$fname"
      ;;

    *.pem|*.crt)
      openssl x509 -in "$fname" -text
      ;;

    *.der)
      openssl x509 -in "$fname" -inform der -text
      ;;

    *)
      echo "I don't know how to view $fname"
      exit 2
  esac
done
  

