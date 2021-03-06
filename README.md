# Git-Fortunes

`git` + `fortune` = `???`

Finds a fitting fortune to your git state. At least it is supposed to. Combining
the power of regex and counting the program determines a piece of text in which
most of the words of another text appear, by default matching against the commit
message of the checked out git commit.

## Usage

```
usage: git-fortunes.py [-h] [--debug] [--stdin] [--words] [--word-lengths]
                       [--no-word-lengths]
                       [files [files ...]]

Find a fortune cookie matching some text

positional arguments:
  files              Fortune files in the freebsd format, with separating '%'
                     lines

optional arguments:
  -h, --help         show this help message and exit
  --debug            Enable performance and partial result debugging
  --stdin            Read match text from stdin instead of analyzing the git
                     HEAD
  --words            Best matching fortune is selected based on word counts
  --word-lengths     Matches of longer words are more influential
  --no-word-lengths  Matches of longer words are NOT more influential
```

## Additional information

You can use this command directly as a git subcommand by making it available as
an executable on your PATH.  
    
```bash
$ export PATH="$PATH:~/bin/"
$ ln -s "$(realpath ./git-fortune.py)" ~/bin/git-fortune
$ git fortune
```

