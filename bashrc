# .bashrc

export PATH="$HOME/scripts:$HOME/bin:$PATH"
export VISUAL=nano

# Use my editor for git!
#export GIT_EDITOR=run-editor

#PS1='\n\w\$ '
alias ls="ls -F"

# this will print either nothing or "[<branch>]" or "[<branch>](merge pending)"
print_git_branch() {
  if [ -f .git/HEAD ]; then
    # The HEAD file is usually "ref: refs/heads/<branch>", although
    # in a "detached HEAD" state, it is a raw SHA1 hash.
    sed -e 's,^ref: refs/heads/,,' -e 's/^/[/' -e 's/$/]/' .git/HEAD | tr -d '\r
\n'
  fi
  if [ -f .git/MERGE_HEAD ]; then
    echo -n '(merge pending)'
  fi
}

PS1="\n$PS1PREFIX"'\w`print_git_branch`\$ '

# This function will be run before every prompt.  Since it is
# encapsulated in a function, upon returning, $? is restored.
# However, during the function, we have to save it since otherwise the
# '[' ('test') will overwrite it.
function exitstatus {
  EXITSTATUS="$?"
  if [ "$EXITSTATUS" -ne 0 ]; then
    echo "Exit $EXITSTATUS"
  fi
}

# establish it as the prompt command
PROMPT_COMMAND=exitstatus

# Do not exit the shell on Ctrl+D!
export IGNOREEOF=10

# Put a directory at the beginning of PATH.  This works even with an
# argument that is not absolute.  Credit to Michael Marks.
prepath() {
  if [ "x$1" = "x" ]; then
    echo "usage: prepath <directory>"
    return 2
  fi
  newpath=`readlink -e --verbose "$1"`
  code="$?"
  if [ "$code" -eq 0 ]; then
    PATH="$newpath:$PATH"
    echo "PATH is now $PATH"
  else
    return "$code"
  fi
}

# Do not beep during tab completion.
bind 'set bell-style none'

if [ -e ~/.bashrc-site ]; then
  . ~/.bashrc-site
fi

# EOF
