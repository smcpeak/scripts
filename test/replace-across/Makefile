# test/replace-across/Makefile

# Default target.
check:

# Eliminate all implicit rules.
.SUFFIXES:

# Delete a target when its recipe fails.
.DELETE_ON_ERROR:

# Do not remove "intermediate" targets.
.SECONDARY:

# Script to test.
REPLACE_ACROSS := ../../replace-across-files

# Test with old script.
ifeq ($(USE_PERL),1)
REPLACE_ACROSS := ../../replace-across-files.pl
endif

# Ensure the directory meant to hold the output file of a recipe exists.
CREATE_OUTPUT_DIRECTORY = @mkdir -p $(dir $@)

# Script to run a program and compare its output to expectation.
RUN_COMPARE_EXPECT = $(HOME)/wrk/verifier/cplr/smbase/run-compare-expect.py

# Create empty expect file if needed.
in/%.expect:
	touch $@

# Run the script on a particular input and compare to expected output.
out/%.ok: in/%.txt in/%.expect $(REPLACE_ACROSS)
	$(CREATE_OUTPUT_DIRECTORY)
	cp $< out/
	$(REPLACE_ACROSS) -F $($*_SOURCE) $($*_REPLACE) out/$*.txt
	$(RUN_COMPARE_EXPECT) \
	  --expect in/$*.expect \
	  cat out/$*.txt
	touch $@

# Tests to run.

check: out/simple.ok
simple_SOURCE = 'foo'
simple_REPLACE = 'bar'

check: out/field_to_call.ok
field_to_call_SOURCE = '\bfoo\b(?!\()'
field_to_call_REPLACE = 'foo()'

check: out/method_to_function.ok
method_to_function_SOURCE = 'foo->([a-zA-Z0-9_]+)\('
method_to_function_REPLACE = '\1(foo, '

# The perl script cannot do this one.
check: out/repl_ins_newlines.ok
repl_ins_newlines_SOURCE = 'two'
repl_ins_newlines_REPLACE = 't\nw\n\no'

clean:
	rm -rf out

# EOF
