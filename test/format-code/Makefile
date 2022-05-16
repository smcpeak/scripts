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
FORMAT_CODE := ../../format-code.py

# Ensure the directory meant to hold the output file of a recipe exists.
CREATE_OUTPUT_DIRECTORY = @mkdir -p $(dir $@)

# Script to run a program and compare its output to expectation.
RUN_COMPARE_EXPECT = $(HOME)/wrk/verifier/cplr/smbase/run-compare-expect.py

# Create empty expect file if needed.
in/%.expect:
	touch $@

# Run the script on a particular input and compare to expected output.
out/%.ok: in/%.txt in/%.expect $(FORMAT_CODE)
	$(CREATE_OUTPUT_DIRECTORY)
	$(FORMAT_CODE) < $< > out/$*.actual
	$(RUN_COMPARE_EXPECT) \
	  --expect in/$*.expect \
	  cat out/$*.actual
	touch $@

# Tests to run.
check: out/simple.ok
check: out/doc-example.ok
check: out/two-tables.ok
check: out/adjacent-tables.ok
check: out/small-min-column.ok
check: out/escaped-re-space.ok
check: out/escaped-at.ok
check: out/nonmatch-line.ok
check: out/nonmatch-entry.ok

clean:
	rm -rf out

# EOF
