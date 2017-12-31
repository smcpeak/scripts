#!/usr/bin/env python

import chess.syzygy
import sys

if len(sys.argv) < 3:
  print("usage: " + sys.argv[0] + " <tablebase-dir> <board FEN>");
  sys.exit(2);

tablebase_dir = sys.argv[1];
board_fen = sys.argv[2];

tablebases = chess.syzygy.open_tablebases(tablebase_dir);
board = chess.Board(board_fen);
print(board);

print("dtz=" + str(tablebases.probe_dtz(board)) +
      " wdl=" + str(tablebases.probe_wdl(board)));

sys.exit(0)

# EOF
