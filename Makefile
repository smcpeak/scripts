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


# Python scripts to pass to mypy, in alphabetical order.
MYPY_SRCS :=
MYPY_SRCS += center-header.py
MYPY_SRCS += mygcov
MYPY_SRCS += trim-path

out/%.mypy.ok: %
	$(CREATE_OUTPUT_DIRECTORY)
	mypy --strict $<
	touch $@

out/all-mypy.ok: $(patsubst %,out/%.mypy.ok,$(MYPY_SRCS))

all: out/all-mypy.ok


# EOF
