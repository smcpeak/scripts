#!/usr/bin/env python3
"""
This script takes as input, on the command line, the name of a C++
source file, and produces as output (on stdout) the text of that file,
annotated with the locations of the definitions of all non-definition
function and method declarations in the file.

To identify non-definition function and method declarations, and to find
their definitions, it uses the Language Server Protocol (LSP).  It
starts a `clangd` child process, and issues LSP queries to it.

It uses LSP "textDocument/documentSymbol" to find the declarations, and
"textDocument/definition" can find their definitions.  Since the
"documentSymbol" reply does not indicate whether the occurrence is a
definition, it is necessary to ask for the definition for all functions
and methods, and then ignore those for which the definition is at the
same file and line as the symbol being queried.

For each non-definition function or method declaration, it annotates the
line that has its start location by appending a C++ single-line
comment with the file and line number of the definition start location,
in format like:

  // DEFINED AT <file>:<line>

in "<file>:<line>" format.  It omit the directory of the file name.

For example, if the input file contains:

  struct S {
    int foo();
  };
  void bar();

then the output might look like:

  struct S {
    int foo(); // DEFINED AT file.cc:34
  };
  void bar(); // DEFINED AT file.cc:132
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- LSP client helper ------------------------------------------------------

class ClangdClient:
  def __init__(self, clangd_cmd: str = "clangd") -> None:
    # Determine stderr destination
    stderr_path = os.environ.get("CLANGD_STDERR")
    if stderr_path:
      stderr_file = open(stderr_path, "w")
    else:
      tmp = tempfile.NamedTemporaryFile(prefix="clangd-", suffix=".log", delete=True, dir="/tmp")
      stderr_file = open(tmp.name, "w")

    self.proc = subprocess.Popen(
      [clangd_cmd, "--pretty"],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=stderr_file,
      text=True,
      bufsize=0,
    )
    assert self.proc.stdin and self.proc.stdout
    self.stdin = self.proc.stdin
    self.stdout = self.proc.stdout
    self.id_counter = 0

  def _send(self, method: str, params: Optional[Dict[str, Any]]) -> int:
    self.id_counter += 1
    msg_id = self.id_counter
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    self.stdin.write(header + body)
    self.stdin.flush()
    return msg_id

  def _read_response(
    self,
    expected_id: Optional[int] = None) -> Optional[Dict[str, Any]]:

    while True:
      header = self.stdout.readline()
      if not header:
        return None
      if header.startswith("Content-Length:"):
        length = int(header.split(":")[1].strip())
        # consume empty line
        self.stdout.readline()
        body = self.stdout.read(length)
        msg: Dict[str, Any] = json.loads(body)
        if expected_id is None or msg.get("id") == expected_id:
          return msg

  def request(self, method: str, params: Optional[Dict[str, Any]]) -> Any:
    msg_id = self._send(method, params)
    resp = self._read_response(msg_id)
    return resp.get("result") if resp else None

  def notify(self, method: str, params: Dict[str, Any]) -> None:
    msg = {"jsonrpc": "2.0", "method": method, "params": params}
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    self.stdin.write(header + body)
    self.stdin.flush()

  def wait_for_notification(self, method: str) -> Dict[str, Any]:
    while True:
      msg = self._read_response(expected_id=None)
      if msg and msg.get("method") == method:
        return msg

  def shutdown(self) -> None:
    # Request shutdown
    self.request("shutdown", None)
    # Exit notification
    self.notify("exit", {})
    self.proc.terminate()
    self.proc.wait()


# --- utility ----------------------------------------------------------------

def uri_from_path(path: Path) -> str:
  return "file://" + str(path.resolve())

def path_from_uri(uri: str) -> str:
  return Path(uri[7:]).name if uri.startswith("file://") else uri

# --- main logic --------------------------------------------------------------

def main() -> None:
  if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} FILE", file=sys.stderr)
    sys.exit(1)

  file_path = Path(sys.argv[1]).resolve()
  text = file_path.read_text(encoding="utf-8")
  lines = text.splitlines()

  client = ClangdClient()

  try:
    # Initialize LSP
    client.request("initialize", {
      "rootUri": uri_from_path(file_path.parent),
      "capabilities": {},
    })
    client.notify("initialized", {})

    # Open the file
    client.notify("textDocument/didOpen", {
      "textDocument": {
        "uri": uri_from_path(file_path),
        "languageId": "cpp",
        "version": 1,
        "text": text,
      }
    })

    # Wait for diagnostics before proceeding
    client.wait_for_notification("textDocument/publishDiagnostics")

    symbols = client.request("textDocument/documentSymbol", {
      "textDocument": {"uri": uri_from_path(file_path)}
    })

    decls: List[Tuple[int, str]] = []

    def visit(symbols: List[Dict[str, Any]]) -> None:
      for sym in symbols:
        kind = sym.get("kind")
        if kind in (12, 6):  # 12=Function, 6=Method
          loc = sym["location"]
          decl_uri = loc["uri"]
          decl_line = loc["range"]["start"]["line"]
          # Query definition
          defs = client.request("textDocument/definition", {
            "textDocument": {"uri": decl_uri},
            "position": loc["range"]["start"],
          })
          if defs:
            def0 = defs[0]
            def_uri = def0["uri"]
            def_line = def0["range"]["start"]["line"]
            # Different location => it's just a declaration
            if def_uri != decl_uri or def_line != decl_line:
              decls.append((decl_line, f"// DEFINED AT {path_from_uri(def_uri)}:{def_line+1}"))
        if "children" in sym:
          visit(sym["children"])

    visit(symbols or [])

    # Annotate lines
    decl_map = {line: comment for line, comment in decls}
    for i, line in enumerate(lines):
      if i in decl_map:
        print(f"{line}  {decl_map[i]}")
      else:
        print(line)
  finally:
    client.shutdown()


if __name__ == "__main__":
  main()
