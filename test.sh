#!/bin/sh
# test 'sh' shell syntax

# ordinary sequential execution: each command goes on a line, and the
# newline separates commands (unless a backslash escapes the newline)
echo "command 1"
echo "command 2"
echo "command" \
     "3"

# In general, commands are components of "lists", which are commands
# separated by ; & <newline && ||, and terminated by ; & <newline>
# So the above 3 commands are part of a list, separated by the
# newlines.

# variables: set simply by variable=value, with no whitespace
# before or after the '='
a=5
foo="a string"
bar="another string"    # quotes are necessary!

# without the quotes, i.e.
#   bar=another string
# would appear as setting 'bar' to "another", then *executing*
# the command "string" (which generally fails)

# variable values are retrieved via interpolation
echo "the value of foo is $foo"
echo "the value of bar is $bar"

# arithmetic can be performed, and the results stored in variables
# the $[ introduces an arithmetic expression, and ] terminates it
echo "a is $a"
a=$[ $a + 2]
echo "a is now $a"

# if-then: syntax is
#   if list then list [ elif list then list ... ] [ else list ] fi
# each of these lists may be terminated by either ; or <newline>
if true             # lists terminated by newline
then echo "yep"
fi

if true
then                # any whitespace can follow the 'then'

echo "yep"
fi

if true; then echo "yep"; fi
 

# what do relational operators return?
x=$[ 0 > 1 ]
echo "0 > 1 yields $x"
x=$[ 2 > 1 ]
echo "2 > 1 yields $x"


# can do relational tests
if [ $[ $a > 0 ] = 1 ] ; then echo "yep to arithmetic"; fi
if [ $[ $a < 0 ] = 1 ] ; then echo "arithmetic failed!"; fi


# while loop syntax:
#   while list do list done
a=1
while [ $[ $a < 5 ] = 1 ]; do
  echo "a is $a"
  a=$[ $a + 1 ]
done


