# test/format-code/Makefile

# Default target.
check:

# Eliminate all implicit rules.
.SUFFIXES:

# Delete a target when its recipe fails.
.DELETE_ON_ERROR:

# Do not remove "intermediate" targets.
.SECONDARY:

# Script to test.
FORMAT_MACRO := ../../format-macro.py

# Ensure the directory meant to hold the output file of a recipe exists.
CREATE_OUTPUT_DIRECTORY = @mkdir -p $(dir $@)

# Script to run a program and compare its output to expectation.
RUN_COMPARE_EXPECT = $(HOME)/wrk/verifier/cplr/smbase/run-compare-expect.py

# Create empty expect file if needed.
in/%.expect:
	touch $@

# Run the script on a particular input and compare to expected output.
out/%.ok: in/%.txt in/%.expect in/%.strip.expect $(FORMAT_MACRO)
	$(CREATE_OUTPUT_DIRECTORY)
	$(FORMAT_MACRO) < $< > out/$*.actual
	$(RUN_COMPARE_EXPECT) \
	  --expect in/$*.expect \
	  cat out/$*.actual
	$(FORMAT_MACRO) --strip < $< > out/$*.strip.actual
	$(RUN_COMPARE_EXPECT) \
	  --expect in/$*.strip.expect \
	  cat out/$*.strip.actual
	touch $@

# Tests to run.
check: out/fm1.ok

clean:
	rm -rf out

# EOF
