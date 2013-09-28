import mturkutils as mt
import mturkutils.utils as ut
import cPickle as pk
import sys
import os
import time
import glob
import readline   # noqa

# various
PRODUCTIONPATH = 'html'          # make sure there's no trailing /
SANDBOXPATH = 'html_sandbox'     # same: no trailing /
TSTAMP = os.environ.get('DRIVER_TSTAMP')     # timestamp
STATES = os.environ.get('DRIVER_STATES', 'states.pkl')
TMPDIR = os.environ.get('DRIVER_TMPDIR', 'tmp')
TMPDIR_PRODUCTION = os.path.join(TMPDIR, PRODUCTIONPATH)
TMPDIR_SANDBOX = os.path.join(TMPDIR, SANDBOXPATH)

# patterns for string manipulation
HTMLSRC = 'web/compensate.html'
OTHERSRC = []

# other constants
S3BUCKET = 'dlcompensation'
DEF_COMPENSATION = 2.   # 2 USD
PREP_RULE_SIMPLE_SANDBOX = [
        {
            'old': 'acceptID = [];',
            'new': 'acceptID = ${CHUNK};',
            'n': 1
        },
        {
            'old': 'https://www.mturk.com/mturk/externalSubmit',
            'new': 'https://workersandbox.mturk.com/mturk/externalSubmit',
            'n': 1
        },
    ]
PREP_RULE_SIMPLE_PRODUCTION = [
        {
            'old': 'acceptID = [];',
            'new': 'acceptID = ${CHUNK};',
            'n': 1
        },
        {
            # Do not remove this part: although this doesn't really replace
            # `old` with `new`, this makes sure that there is one `old`.
            # Also, this part is required to check the existance of `new`
            # with the use of validate_html_files().
            'old': 'https://www.mturk.com/mturk/externalSubmit',
            'new': 'https://www.mturk.com/mturk/externalSubmit',
            'n': 1
        },
    ]


# -- main funcs
def prep(n_wid=14):
    """Prepare web files for publishing"""
    # -- fill out info
    print
    print '* Fill out the followings:'
    workers = []
    t0 = int(time.time())
    htmldst = 'compensate_' + str(t0) + '_n%d.html'

    # worker ids
    inp = raw_input('Enter space-separated worker ids: ').strip()
    inp = [e for e in inp if e.isalnum() or e.isspace()]
    inp = ''.join(inp)
    for w in inp.split():
        if n_wid > 0 and len(w) != n_wid:
            print '* Bad worker id:', w
            continue
        workers.append(w)
    if len(workers) <= 0:
        print '* No valid workers. Aborting...'
        return False

    # how many HITs?
    inp = raw_input('The # of total assignments? [default=%d] ' % len(workers))
    inp = [e for e in inp.strip() if e.isdigit()]
    inp = ''.join(inp)
    n_assignments = len(workers)
    if inp != '':
        n_assignments = int(inp)

    # compensation level?
    inp = raw_input('Compensation $ amount? [default=%f] ' % DEF_COMPENSATION)
    inp = [e for e in inp.strip() if e.isdigit() or e == '.']
    inp = ''.join(inp)
    compamt = DEF_COMPENSATION
    if inp != '':
        compamt = float(inp)

    print '* Summary:'
    print '  - workers:', workers
    print '  - n_assignments:', n_assignments
    print '  - compensation:', compamt
    print

    inp = raw_input('Proceed? [default=y] ').strip().lower()
    if inp not in ['', 'y', 'yes']:
        print '* Aborting...'
        return False

    # -- do the work
    print '* Writing files...'
    dstfns_production = []
    dstfns_sandbox = []
    for label, rules, dstdir, dstfns in [
            ('sandbox', PREP_RULE_SIMPLE_SANDBOX,
                TMPDIR_SANDBOX, dstfns_production),
            ('production', PREP_RULE_SIMPLE_PRODUCTION,
                TMPDIR_PRODUCTION, dstfns_sandbox)]:
        print '  ->', label
        ds = ut.prep_web_simple(workers, HTMLSRC, dstdir, dstpatt=htmldst,
                rules=rules, auxfns=OTHERSRC,
                n_per_file=len(workers), verbose=True)
        dstfns.extend(ds)

    # save trials for future reference
    pk.dump({
        'workers': workers,
        'htmldst': htmldst,
        't0': t0,
        'workers': workers,
        'n_assignments': n_assignments,
        'compamt': compamt,
        'dstfns_production': dstfns_production,
        'dstfns_sandbox': dstfns_sandbox,
        },
            open(os.path.join(TMPDIR, STATES), 'wb'))
    return True


def upload():
    """Upload generated web files into S3"""
    print '* Uploading sandbox...'
    fns = glob.glob(os.path.join(TMPDIR_SANDBOX, '*.*'))
    mt.uploader(fns, S3BUCKET, dstprefix=SANDBOXPATH + '/', test=True,
            verbose=10)

    print '* Uploading production...'
    fns = glob.glob(os.path.join(TMPDIR_PRODUCTION, '*.*'))
    mt.uploader(fns, S3BUCKET, dstprefix=PRODUCTIONPATH + '/', test=True,
            verbose=10)


def publish(sandbox=True):
    """Publish to the sandbox"""
    states = pk.load(open(os.path.join(TMPDIR, STATES)))
    s_t0 = str(states['t0'])

    exp = mt.Experiment(sandbox=sandbox,
        keywords=['compensation', 'reimbursement', s_t0],
        max_assignments=states['n_assignments'],
        title='Compensation',
        reward=states['compamt'],
        duration=1500,
        description="***For invited workers only***",
        comment="compensation, reimbursement",
        collection_name=None,   # disables db connection
        meta=None,
        )

    if sandbox:
        fns = sorted(states['dstfns_sandbox'])
    else:
        fns = sorted(states['dstfns_production'])

    hitidslog = os.path.join(TMPDIR, 'hitidslog_' +
            ('sandbox' if sandbox else 'production') + '_' +
            s_t0 + '.pkl')
    exp.URLs = ['http://s3.amazonaws.com/' + S3BUCKET +
            e.split(TMPDIR)[-1] for e in fns]
    exp.createHIT(verbose=True, hitidslog=hitidslog)
    print '* t0 was:', s_t0


# -- helper funcs
def timestamp(tsvar=TSTAMP):
    """Put a time stamp.  Mainly for Makefile support."""
    if tsvar is not None:
        open(os.path.join(TMPDIR, tsvar), 'wt').write(str(time.time()))


def main(argv):
    if len(argv) < 2:
        print 'driver.py <target>'
        return 1

    if argv[1] == 'prep':
        flag = prep()
    elif argv[1] == 'upload':
        flag = upload()
    elif argv[1] == 'sandbox':
        flag = publish(sandbox=True)
    elif argv[1] == 'production':
        flag = publish(sandbox=False)
    else:
        print 'Bad arguments'
        return 1

    if flag is None or flag:
        timestamp()
    print '* Done.'
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
