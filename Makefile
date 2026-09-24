# scripts/Makefile
# This is used to run static checkers on some scripts.

# Default target.
all:
.PHONY: all


# Ensure the directory meant to hold the output file of a recipe exists.
CREATE_OUTPUT_DIRECTORY = @mkdir -p $(dir $@)


# Eliminate all implicit rules.
.SUFFIXES:

# Delete a target when its recipe fails.
.DELETE_ON_ERROR:

# Do not remove "intermediate" targets.
.SECONDARY:


PYTHON = python
MYPY = $(PYTHON) -m mypy
MYPY_OPTS = --strict


# Python scripts to pass to mypy, in alphabetical order.
MYPY_SRCS :=
MYPY_SRCS += convert-comment-syntax.py
MYPY_SRCS += count-header-lines.py
MYPY_SRCS += center-header.py
MYPY_SRCS += mygcov
# TODO: Fix mypy errors.
#MYPY_SRCS += replace-across-files
MYPY_SRCS += trim-path
MYPY_SRCS += windows-restart-monitor.py

out/%.mypy.ok: %
	$(CREATE_OUTPUT_DIRECTORY)
	$(MYPY) $(MYPY_OPTS) $<
	touch $@

out/all-mypy.ok: $(patsubst %,out/%.mypy.ok,$(MYPY_SRCS))

all: out/all-mypy.ok


clean:
	$(RM) -r out .mypy_cache


# EOF
