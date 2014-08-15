This contains various psychophysics experiments as individual directories.

The following is a minimal implementation guildline for each experiment:
  * Subdirectory "web/" contains all the files that are to be web-published.
  * Implement Makefile so that: "make production" or
    "python some-driver-script.py" publishes HITs for real.

Optional Makefile sections can include:
  * "make prep" prepares all necessary stuffs prior to publishing.
  * "make sandbox" publishes HITs into the sandbox.
  * "make remove" removes all the published HITs.
