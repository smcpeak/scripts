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


MYPY = mypy
MYPY_OPTS = --strict


# How to run native Windows Python, if we are on Windows.
WINDOWS_PYTHON = windows-python
WINDOWS_MYPY = $(WINDOWS_PYTHON) -m mypy


# Python scripts to pass to mypy, in alphabetical order.
MYPY_SRCS :=
MYPY_SRCS += convert-comment-syntax.py
MYPY_SRCS += count-header-lines.py
MYPY_SRCS += center-header.py
MYPY_SRCS += mygcov
MYPY_SRCS += replace-across-files
MYPY_SRCS += trim-path


out/%.mypy.ok: %
	$(CREATE_OUTPUT_DIRECTORY)
	$(MYPY) $(MYPY_OPTS) $<
	touch $@

out/all-mypy.ok: $(patsubst %,out/%.mypy.ok,$(MYPY_SRCS))

all: out/all-mypy.ok


ifneq ($(shell which $(WINDOWS_PYTHON) 2>/dev/null),"")

WINDOWS_MYPY_SRCS += windows-restart-monitor.py

out/%.windows-mypy.ok: %
	$(CREATE_OUTPUT_DIRECTORY)
	$(WINDOWS_MYPY) $(MYPY_OPTS) $<
	touch $@

out/all-windows-mypy.ok: $(patsubst %,out/%.windows-mypy.ok,$(WINDOWS_MYPY_SRCS))

all: out/all-windows-mypy.ok

endif


clean:
	$(RM) -r out .mypy_cache


# EOF
