#!/usr/bin/env python3
"""
This script takes as input, on the command line, the name of a C++
source file, and produces as output (on stdout) the text of that file,
annotated with the locations of the definitions of all non-definition
function and method declarations in the file.

Additional files may be specified after the first; they are sent to the
clangd server to provide context, but only the first file is annotated.

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

  // `<symbol>` DEFINED AT <file>:<line>

in "<file>:<line>" format.  It omit the directory of the file name.

For example, if the input file contains:

  struct S {
    int foo();
  };
  void bar();

then the output might look like:

  struct S {
    int foo(); // `foo` DEFINED AT file.cc:34
  };
  void bar(); // `bar` DEFINED AT file.cc:132
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple


# Global log file.
log_file: Optional[TextIO] = None

def log(s: str) -> None:
  if log_file:
    log_file.write(s)
    log_file.write("\n")
    log_file.flush()


# True if we are running Cygwin Python.
is_cygwin: bool = (sys.platform == "cygwin")


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

    global log_file
    self.log_file = log_file

  def _log(self, direction: str, msg: Dict[str, Any]) -> None:
    if self.log_file:
      json.dump({"direction": direction, "msg": msg}, self.log_file, indent=2)
      self.log_file.write("\n")
      self.log_file.flush()

  def _send(self, method: str, params: Optional[Dict[str, Any]]) -> int:
    self.id_counter += 1
    msg_id = self.id_counter
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    self.stdin.write(header + body)
    self.stdin.flush()
    self._log("send", msg)
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
        self._log("recv", msg)
        if expected_id is None or msg.get("id") == expected_id or "method" in msg:
          return msg

  def request(self, method: str, params: Optional[Dict[str, Any]]) -> Any:
    msg_id = self._send(method, params)
    while True:
      resp = self._read_response(msg_id)
      if resp and resp.get("id") == msg_id:
        return resp.get("result")

  def notify(self, method: str, params: Dict[str, Any]) -> None:
    msg = {"jsonrpc": "2.0", "method": method, "params": params}
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    self.stdin.write(header + body)
    self.stdin.flush()
    self._log("send", msg)

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

def cygwin_to_mixed_path(src_path: str) -> str:
  """Convert `path` to a Cygwin "mixed" Windows path."""

  b = subprocess.check_output(['cygpath', '-m', src_path])
  return b.decode().strip()

def uri_from_path(path: Path) -> str:
  abspath: str = str(path.resolve())
  if is_cygwin:
    abspath = cygwin_to_mixed_path(abspath)

  # TODO: This hardcodes the Windows-specific triple slash.
  return "file:///" + abspath

def path_from_uri(uri: str) -> str:
  # TODO: This also hardcodes the Windows-specific triple slash.
  return Path(uri[7:]).name if uri.startswith("file:///") else uri

# --- main logic --------------------------------------------------------------

def main() -> None:
  parser = argparse.ArgumentParser(description="Annotate C++ source with definition locations.")
  parser.add_argument("files", nargs="+", help="C++ source files (first is annotated)")
  parser.add_argument("--log", dest="log", help="Log JSON messages to file")
  args = parser.parse_args()

  file_paths = [Path(f).resolve() for f in args.files]
  main_file = file_paths[0]
  text = main_file.read_text(encoding="utf-8")
  lines = text.splitlines()

  global log_file
  if args.log:
    log_file = open(args.log, "w")

  client = ClangdClient()

  try:
    # Initialize LSP
    client.request("initialize", {
      "rootUri": uri_from_path(main_file.parent),
      "capabilities": {
        "textDocument": {
          "documentSymbol": {
            "hierarchicalDocumentSymbolSupport": True
          }
        }
      },
    })
    client.notify("initialized", {})

    # Open each file, waiting for diagnostics
    for fp in file_paths:
      client.notify("textDocument/didOpen", {
        "textDocument": {
          "uri": uri_from_path(fp),
          "languageId": "cpp",
          "version": 1,
          "text": fp.read_text(encoding="utf-8"),
        }
      })
      client.wait_for_notification("textDocument/publishDiagnostics")

    # Query symbols for main file
    main_file_uri = uri_from_path(main_file)
    symbols = client.request("textDocument/documentSymbol", {
      "textDocument": {"uri": main_file_uri}
    })

    decls: List[Tuple[int, str]] = []

    def visit(symbols: List[Dict[str, Any]]) -> None:
      wanted_symbol_kinds = (
        6,         # Method
        9,         # Constructor
        12,        # Function
      )

      for sym in symbols:
        kind = sym.get("kind")
        if kind in wanted_symbol_kinds:
          name = sym.get("name")
          sel_range = sym["selectionRange"]
          decl_line = sel_range["start"]["line"]
          # Query definition
          log(f"Querying definition of `{name}`:")
          defs = client.request("textDocument/definition", {
            "textDocument": {"uri": main_file_uri},
            "position": sel_range["start"],
          })
          if defs:
            if len(defs) > 1:
              log(f"Multiple ({len(defs)}) definitions found for `{name}`.  Using first.")
            def0 = defs[0]
            def_uri = def0["uri"]
            def_line = def0["range"]["start"]["line"]
            # Different location => it's just a declaration
            if def_uri != main_file_uri or def_line != decl_line:
              def_file = path_from_uri(def_uri)
              log(f"Definition of `{name}` is at {def_file}:{def_line+1}.")
              decls.append((decl_line, f"// `{name}` DEFINED AT {def_file}:{def_line+1}"))
            else:
              log(f"Definition of `{name}` is at the same line as its declaration, treating decl as defn.")
          else:
            log(f"No definitions found for `{name}`.")

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
    if log_file:
      log_file.close()


if __name__ == "__main__":
  main()
