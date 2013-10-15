"""Command line interface stuffs"""
import os
import cPickle as pk
from . import utils as ut


def make_backup(full_argv):
    """Download and make a backup of HITs"""
    args, opts = parse_opts2(full_argv[1:])

    if len(args) < 2:
        usage = """\
Make a local backup of assignment results of the given HITs.  Use of this
utility should be TEMPORARY BACKUP PURPOSES ONLY; this stores raw boto objects
into pickle files, and hence old backups might not be recoverable under some
rare cases, especially if there are substantial changes in boto or mturkutils.
Therefore, one MUST save the human data into the central mongodb and run the
ananlysis by using the database if possible.

Usage:
$EXEC [options] <HIT_ID_list.pkl> <output path prefix>
$EXEC [options] <HIT_ID 1> [HIT ID 2] ... <output path prefix>

Options:
--sandbox       Operate in the sandbox
"""
        usage = usage.replace('$EXEC', os.path.basename(full_argv[0]))
        print usage
        return 1

    # -- do work
    outp = args[-1]
    hitids = args[:-1]
    sandbox = False

    print '* Using HIT IDs in:', hitids
    if 'sandbox' in opts:
        print '* Sandbox mode.'
        sandbox = True

    if len(hitids) == 1 and os.path.exists(hitids[0]):
        hitids = pk.load(open(hitids[0]))
    print '* Total %d hits' % len(hitids)

    _, n_hits, n_assgns = ut.download_results(hitids, dstprefix=outp,
            sandbox=sandbox, verbose=True, full=True)

    print '* Done: %d assignments in %d hits saved.' % (n_assgns, n_hits)
    return 0


# -- helper funcs
def parse_opts(opts0):
    """Parse the options in the command line.  This somewhat
    archaic function mainly exists for backward-compatability."""
    opts = {}
    # parse the stuff in "opts"
    for opt in opts0:
        parsed = opt.split('=')
        key = parsed[0].strip()
        if len(parsed) > 1:
            # OLD: cmd = parsed[1].strip()
            cmd = '='.join(parsed[1:]).strip()
        else:
            cmd = ''
        opts[key] = cmd

    return opts


def parse_opts2(tokens, optpx='--', argparam=False):
    """A newer option parser."""
    opts0 = []
    args = []
    n = len(optpx)

    for token in tokens:
        if token.startswith(optpx):
            opts0.append(token[n:])
        else:
            if argparam:
                token = token.split('=')
            args.append(token)

    opts = parse_opts(opts0)

    return args, opts
