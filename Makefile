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
MYPY_SRCS += trim-path

out/mypy.ok: $(MYPY_SRCS)
	$(CREATE_OUTPUT_DIRECTORY)
	mypy --strict $(MYPY_SRCS)
	touch $@

all: out/mypy.ok


# EOF
