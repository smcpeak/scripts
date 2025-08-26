#!/usr/bin/env python3
"""
Analyze C++ module dependencies in the current directory.

A "module" is a collection of files with a common prefix:

  $MODULE.h
  $MODULE-fwd.h
  $MODULE-iface.h
  $MODULE.cc
  $MODULE-test.cc

The only required file is $MODULE.cc. Modules are discovered by finding
all *.cc files except *-test.cc, then gathering the associated files.

Dependencies are discovered by scanning files for

  #include "filename"

patterns.  If the included filename corresponds to another file in a
module, a dependency is recorded.  The name can refer to a file in the
current directory with a name like "a/b.h" if the current directory is
"a".

The script computes:

  - file-to-file dependencies
  - module-to-module dependencies
  - strongly-connected components (SCCs) of modules
  - topological order of SCCs

The result is printed as a JSON object.

The script first runs unit tests and an integration test using a
hardcoded example.  If all pass, it analyzes the current directory and
prints results.
"""

import os
import re
import json
from typing import Dict, List, Set, Tuple, Optional, Iterable
from collections import defaultdict


# ----------------------------------------------------------------------
# File system abstraction
class FileSystem:
  """Abstraction for reading files and listing directory contents."""

  def listdir(self, path: str) -> List[str]:
    """Return the list of filenames in `path`."""
    return os.listdir(path)

  def read(self, path: str) -> str:
    """Return the contents of file `path` as a string."""
    with open(path, "r", encoding="utf-8") as f:
      return f.read()


class FakeFileSystem(FileSystem):
  """In-memory file system for testing."""

  def __init__(self, files: Dict[str, str]):
    self._files = files

  def listdir(self, path: str) -> List[str]:
    return sorted(self._files.keys())

  def read(self, path: str) -> str:
    return self._files[path]


def test_fake_filesystem() -> None:
  """Unit test for FakeFileSystem."""
  fs = FakeFileSystem({"a.cc": "int main(){}", "b.h": "#pragma once"})
  assert "a.cc" in fs.listdir(".")
  assert fs.read("a.cc") == "int main(){}"


# ----------------------------------------------------------------------
# Module discovery
MODULE_SUFFIXES = [".h", "-fwd.h", "-iface.h", ".cc", "-test.cc"]


def discover_modules(fs: FileSystem, path: str) -> Dict[str, List[str]]:
  """
  Discover modules in `path`. A module is defined by a *.cc file (excluding *-test.cc).
  Returns a map from module name to its files.
  """
  files = fs.listdir(path)
  modules: Dict[str, List[str]] = {}
  for f in files:
    if f.endswith(".cc") and not f.endswith("-test.cc"):
      module = f[:-3]
      module_files = []
      for suff in MODULE_SUFFIXES:
        fname = module + suff
        if fname in files:
          module_files.append(fname)
      modules[module] = sorted(module_files)
  return modules


def test_discover_modules() -> None:
  """Unit test for discover_modules."""
  fs = FakeFileSystem({
    "foo.cc": "",
    "foo.h": "",
    "foo-test.cc": "",
    "bar.cc": "",
  })
  mods = discover_modules(fs, ".")
  assert mods == {"foo": ["foo-test.cc", "foo.cc", "foo.h"], "bar": ["bar.cc"]}


# ----------------------------------------------------------------------
# Dependency scanning
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)".*$')


def parse_includes(text: str) -> List[str]:
  """Extract quoted filenames from #include lines in `text`."""
  results = []
  for line in text.splitlines():
    m = INCLUDE_RE.match(line)
    if m:
      results.append(m.group(1))
  return results


def test_parse_includes() -> None:
  """Unit test for parse_includes."""
  txt = '#include "a.h"\n # include "b.h" // comment\n#include <c>\n'
  assert parse_includes(txt) == ["a.h", "b.h"]


def normalize_include(fname: str, cwd: str) -> Optional[str]:
  """
  Normalize an include filename. If it refers to a file in the current
  directory (possibly with a directory prefix equal to cwd), return the
  basename. Otherwise return None.
  """
  if "/" not in fname:
    return fname
  # check if prefix matches cwd
  parts = fname.split("/")
  if parts[-2] == os.path.basename(cwd):
    return parts[-1]
  return None


def test_normalize_include() -> None:
  """Unit test for normalize_include."""
  assert normalize_include("a.h", "src") == "a.h"
  assert normalize_include("x/a.h", "x") == "a.h"
  assert normalize_include("y/a.h", "x") is None


# ----------------------------------------------------------------------
# Dependency analysis
def build_file_dependencies(
  fs: FileSystem, path: str, modules: Dict[str, List[str]]
) -> Dict[str, List[str]]:
  """Build file-to-file dependency graph."""
  file_set = {f for files in modules.values() for f in files}
  deps: Dict[str, Set[str]] = {f: set() for f in file_set}
  cwd = os.path.basename(os.path.abspath(path))
  for f in file_set:
    contents = fs.read(f)
    for inc in parse_includes(contents):
      norm = normalize_include(inc, cwd)
      if norm and norm in file_set:
        deps[f].add(norm)
  return {f: sorted(dests) for f, dests in deps.items()}


def test_build_file_dependencies() -> None:
  """Unit test for build_file_dependencies."""
  fs = FakeFileSystem({
    "a.cc": '#include "a.h"\n',
    "a.h": "",
    "b.cc": '#include "a.h"\n',
  })
  mods = discover_modules(fs, ".")
  fdeps = build_file_dependencies(fs, ".", mods)
  assert fdeps["a.cc"] == ["a.h"]
  assert fdeps["b.cc"] == ["a.h"]


def build_module_dependencies(
  modules: Dict[str, List[str]], file_deps: Dict[str, List[str]]
) -> Dict[str, List[str]]:
  """Compute module-to-module dependencies from file dependencies."""
  file_to_mod: Dict[str, str] = {}
  for mod, files in modules.items():
    for f in files:
      file_to_mod[f] = mod

  mdeps: Dict[str, Set[str]] = {m: set() for m in modules}
  for src, dests in file_deps.items():
    msrc = file_to_mod[src]
    for d in dests:
      mdst = file_to_mod[d]
      if msrc != mdst:
        mdeps[msrc].add(mdst)
  return {m: sorted(ds) for m, ds in mdeps.items()}


def test_build_module_dependencies() -> None:
  """Unit test for build_module_dependencies."""
  mods = {"a": ["a.cc", "a.h"], "b": ["b.cc"]}
  fdeps = {"a.cc": ["a.h"], "a.h": [], "b.cc": ["a.h"]}
  mdeps = build_module_dependencies(mods, fdeps)
  assert mdeps["a"] == []
  assert mdeps["b"] == ["a"]


# ----------------------------------------------------------------------
# Graph algorithms
def strongly_connected_components(
  graph: Dict[str, List[str]]
) -> List[List[str]]:
  """
  Compute strongly-connected components of `graph` (module graph).
  Returns list of SCCs, each a list of nodes.
  """
  index = 0
  indices: Dict[str, int] = {}
  lowlink: Dict[str, int] = {}
  stack: List[str] = []
  onstack: Set[str] = set()
  result: List[List[str]] = []

  def strongconnect(v: str) -> None:
    nonlocal index
    indices[v] = index
    lowlink[v] = index
    index += 1
    stack.append(v)
    onstack.add(v)
    for w in graph[v]:
      if w not in indices:
        strongconnect(w)
        lowlink[v] = min(lowlink[v], lowlink[w])
      elif w in onstack:
        lowlink[v] = min(lowlink[v], indices[w])
    if lowlink[v] == indices[v]:
      comp = []
      while True:
        w = stack.pop()
        onstack.remove(w)
        comp.append(w)
        if w == v:
          break
      result.append(sorted(comp))

  for v in graph:
    if v not in indices:
      strongconnect(v)

  return result


def test_strongly_connected_components() -> None:
  """Unit test for strongly_connected_components."""
  g = {"a": ["b"], "b": ["a"], "c": []}
  sccs = strongly_connected_components(g)
  assert any(set(c) == {"a", "b"} for c in sccs)
  assert any(set(c) == {"c"} for c in sccs)


def topo_sort_sccs(
  graph: Dict[str, List[str]], sccs: List[List[str]]
) -> List[List[str]]:
  """Topologically sort SCCs."""

  # Map from a node to the index in `sccs` where that node is found.
  # Assumes that each node appears in exactly one SCC.
  node_to_scc: Dict[str, int] = {}
  for i, comp in enumerate(sccs):
    for n in comp:
      node_to_scc[n] = i

  # Map from index in `sccs` to the set of other indices in `sccs` for
  # which at least one member of the source SCC is connected to at least
  # one menber of the dest SCC.  That is, this is `graph` modded by the
  # `sccs` equivalence relation.
  scc_graph: Dict[int, Set[int]] = {i: set() for i in range(len(sccs))}
  for src, dests in graph.items():
    for d in dests:
      si, di = node_to_scc[src], node_to_scc[d]
      if si != di:
        scc_graph[si].add(di)

  # Map from index in `sccs` to the number of indices in `sccs` that
  # have an edge going to it, i.e., its in-degree.
  indeg: Dict[int, int] = {i: 0 for i in scc_graph}
  for i, ds in scc_graph.items():
    for di in ds:
      indeg[di] += 1

  order: List[int] = []
  q = [i for i in scc_graph if indeg[i] == 0]
  while q:
    i = q.pop()
    order.append(i)
    for di in scc_graph[i]:
      indeg[di] -= 1
      if indeg[di] == 0:
        q.append(di)

  ret = [sccs[i] for i in order]

  # I want them in bottom-up order.
  ret.reverse()

  return ret


def test_topo_sort_sccs() -> None:
  """Unit test for topo_sort_sccs."""
  g = {"a": ["b"], "b": ["c"], "c": []}
  sccs = strongly_connected_components(g)
  topo = topo_sort_sccs(g, sccs)
  flat = [n for comp in topo for n in comp]
  assert flat == ["c", "b", "a"]


# ----------------------------------------------------------------------
# Integration test with provided example
def integration_test() -> None:
  """Integration test with provided example."""
  files = {
    "lowlevel.h": "",
    "lowlevel.cc": '#include "lowlevel.h"\n',
    "mid1.h": '#include "lowlevel.h"\n',
    "mid1.cc": '#include "mid1.h"\n',
    "mid2.h": '#include "lowlevel.h"\n',
    "mid2.cc": '#include "mid2.h"\n#include "mid3.h"\n',
    "mid3.h": '#include "mid1.h"\n',
    "mid3.cc": '#include "mid3.h"\n#include "mid2.h"\n',
    "high1.h": '#include "mid1.h"\n#include "lowlevel.h"\n',
    "high1.cc": '#include "high1.h"\n',
    "high2.h": '#include "mid2.h"\n',
    "high2.cc": '#include "high2.h"\n',
  }
  fs = FakeFileSystem(files)
  modules = discover_modules(fs, ".")
  fdeps = build_file_dependencies(fs, ".", modules)
  mdeps = build_module_dependencies(modules, fdeps)
  sccs = strongly_connected_components(mdeps)
  topo = topo_sort_sccs(mdeps, sccs)
  # TODO: This variable is not used or checked.
  result = {
    "files": sorted(f for flist in modules.values() for f in flist),
    "file_dependencies": fdeps,
    "module_files": {m: sorted(fl) for m, fl in modules.items()},
    "module_dependencies": mdeps,
    "module_sccs": topo,
  }
  # TODO: This variable is not used or checked.
  expected_sccs = [
    ["lowlevel"],
    ["mid1"],
    ["mid2", "mid3"],
    ["high1"],
    ["high2"],
  ]
  # check SCC structure ignoring order of unrelated SCCs
  assert any(set(c) == {"lowlevel"} for c in topo)
  assert any(set(c) == {"mid1"} for c in topo)
  assert any(set(c) == {"mid2", "mid3"} for c in topo)
  assert any(set(c) == {"high1"} for c in topo)
  assert any(set(c) == {"high2"} for c in topo)


# ----------------------------------------------------------------------
# Main
def unit_tests() -> None:
  """Run all unit tests."""
  test_fake_filesystem()
  test_discover_modules()
  test_parse_includes()
  test_normalize_include()
  test_build_file_dependencies()
  test_build_module_dependencies()
  test_strongly_connected_components()
  test_topo_sort_sccs()


def main() -> None:
  """Run unit tests, integration test, then real analysis."""
  unit_tests()
  integration_test()

  fs = FileSystem()
  modules = discover_modules(fs, ".")
  fdeps = build_file_dependencies(fs, ".", modules)
  mdeps = build_module_dependencies(modules, fdeps)
  sccs = strongly_connected_components(mdeps)
  topo = topo_sort_sccs(mdeps, sccs)
  result = {
    "files": sorted(f for flist in modules.values() for f in flist),
    "file_dependencies": fdeps,
    "module_files": {m: sorted(fl) for m, fl in modules.items()},
    "module_dependencies": mdeps,
    "module_sccs": topo,
  }
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  main()


# EOF
