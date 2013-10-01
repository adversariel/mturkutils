import mturkutils as mt
import mturkutils.utils as ut
import cPickle as pk
import sys
import os
import time
import glob
import readline   # noqa
from boto import mturk
from boto.s3.key import Key
from boto.mturk.price import Price

# various
PRODUCTIONPATH = 'html'          # make sure there's no trailing /
SANDBOXPATH = 'html_sandbox'     # same: no trailing /
DATAPATH = 'data'                # same: no trailing /
STATES = 'states.pkl'
TSTAMP = os.environ.get('DRIVER_TSTAMP')        # timestamp
TMPDIR = os.environ.get('DRIVER_TMPDIR', 'tmp')
EXTKWD = os.environ.get('DRIVER_EXTKWD', '')    # comma-sep extra keywords
BONUST0 = os.environ.get('DRIVER_BONUST0')      # t0 for bonus
TMPDIR_PRODUCTION = os.path.join(TMPDIR, PRODUCTIONPATH)
TMPDIR_SANDBOX = os.path.join(TMPDIR, SANDBOXPATH)
DATAFNPREFIX = DATAPATH + '/t0_%s__'

# patterns for string manipulation
HTMLSRC = 'web/compensate.html'
OTHERSRC = []

# other constants
DEF_COMPENSATION = 0.                           # 0 USD
DEF_TITLE = 'INVITATION ONLY - Compensation'    # title of HITs
MAX_PAGE_SIZE = 100          # set by amazon
S3BUCKET = 'dlcompensation'
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
def prep(l_wid_min=11):
    """Prepare web files for publishing"""
    workers = []
    bonuses = {}
    t0 = int(time.time())

    def get_alnumspc(inp):
        inp = [e for e in inp.strip() if e.isalnum() or e.isspace()]
        return ''.join(inp)

    def get_float(inp):
        inp = [e for e in inp.strip() if e.isdigit() or e == '.']
        return ''.join(inp)

    def isyes(inp):
        return inp.strip().lower() in ['', 'y', 'yes']

    # -- fill out info
    print
    print '* Fill out the followings:'

    # compensation level
    print
    print 'NOTE: The default reward/HIT is $0 to avoid unneeded attraction'
    print 'of uninvited workers.  HOWEVER, BY DOING SO, YOU MUST GRANT BONUS'
    print 'TO THE INVITED WORKERS ONCE THEY FINISH THE HITS. Otherwise, they'
    print 'will only receive $0 --- and be upset.'
    inp = raw_input('HIT reward in USD? [default=%f] ' % DEF_COMPENSATION)
    inp = get_float(inp)
    compamt = DEF_COMPENSATION
    if inp != '':
        compamt = float(inp)

    # worker ids / bonus amount
    print
    print 'NOTE: If you decide to grant bonus later (probably you would),'
    print 'you must specify the bonus amount for individual workers now.'
    inp = raw_input('Will you grant bonuses? [default=y] ')

    print
    print 'NOTE: the # of workers cannot exceed %d.' % MAX_PAGE_SIZE
    if isyes(inp):
        # worker ids + specify bonus amount
        print 'Enter bonus amount and corresponding worker ids separted by space.'   # noqa
        print 'Enter -- to finish.'
        print 'Example:'
        print '2.5 ABCDEFGHIJKLM1 ABCDEFGHIJKLM2 ABCDEFGHIJKLM3'
        print '1.5 ABCDEFGHIJKLM4 ABCDEFGHIJKLM5 ABCDEFGHIJKLM6'
        print '--'
        print
        while True:
            # traditional worker id input
            inp = raw_input('>>> ').strip()
            if inp == '--':
                break
            if inp == '':
                continue
            b = float(inp.split()[0])
            inp = get_alnumspc(inp)
            for w in inp.split()[1:]:
                if l_wid_min > 0 and len(w) < l_wid_min:
                    print '* Bad worker id:', w
                    continue
                workers.append(w)
                bonuses[w] = b
    else:
        # only worker ids
        inp = raw_input('Enter space-separated worker ids: ')
        inp = get_alnumspc(inp)
        bad = False
        for w in inp.split():
            if l_wid_min > 0 and len(w) < l_wid_min:
                print '* Bad worker id:', w
                bad = True
                continue
            workers.append(w)
        if bad:
            print '* Bad worker id(s). Aborting...'
            return False

    if len(workers) <= 0:
        print '* No valid workers. Aborting...'
        return False
    elif len(workers) > MAX_PAGE_SIZE:
        print '* Too many workers. Aborting...'
        return False

    # how many HITs?
    n_assignments = len(workers) * 30  # x30 for stupid uninvited ones' accept
    inp = raw_input('The # of total assignments? [default=%d] ' %
            n_assignments)
    inp = get_float(inp)
    if inp != '':
        n_assignments = int(float(inp))
    n_assignments = min(MAX_PAGE_SIZE, n_assignments)

    # title?
    inp = raw_input('Title? [default=%s] ' % DEF_TITLE).strip()
    title = DEF_TITLE if inp == '' else inp

    print '* Summary:'
    print '  - workers:', workers
    print '  - n_assignments:', n_assignments
    print '  - title:', title
    print '  - compensation:', compamt
    print '  - bonuses:'
    for k in bonuses:
        print '              %s -> $%4.2f' % (k, bonuses[k])
    print

    inp = raw_input('Proceed? [default=y] ')
    if not isyes(inp):
        print '* Aborting...'
        return False

    # -- do the work
    print '* Writing files...'
    dstfns_production = []
    dstfns_sandbox = []
    htmldst = 'compensate_' + str(t0) + '_n%d.html'

    for label, rules, dstdir, dstfns in [
            ('sandbox', PREP_RULE_SIMPLE_SANDBOX,
                TMPDIR_SANDBOX, dstfns_sandbox),
            ('production', PREP_RULE_SIMPLE_PRODUCTION,
                TMPDIR_PRODUCTION, dstfns_production)]:
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
        'title': title,
        'dstfns_production': dstfns_production,
        'dstfns_sandbox': dstfns_sandbox,
        'bonuses': bonuses,
        },
            open(os.path.join(TMPDIR, STATES), 'wb'))
    return True


def upload():
    """Upload generated web files into S3"""
    states = pk.load(open(os.path.join(TMPDIR, STATES)))
    s_t0 = str(states['t0'])

    print '* Uploading sandbox...'
    fns = glob.glob(os.path.join(TMPDIR_SANDBOX, '*.*'))
    mt.uploader(fns, S3BUCKET, dstprefix=SANDBOXPATH + '/', test=True,
            verbose=10)

    print '* Uploading production...'
    fns = glob.glob(os.path.join(TMPDIR_PRODUCTION, '*.*'))
    mt.uploader(fns, S3BUCKET, dstprefix=PRODUCTIONPATH + '/', test=True,
            verbose=10)

    print '* Uploading data...'
    fns = [os.path.join(TMPDIR, STATES)]
    mt.uploader(fns, S3BUCKET, dstprefix=DATAFNPREFIX % s_t0,
            test=True, verbose=10, acl=None)


def publish(sandbox=True):
    """Publish to the sandbox"""
    states = pk.load(open(os.path.join(TMPDIR, STATES)))
    s_t0 = str(states['t0'])
    kwd = ['compensation', 'reimbursement', s_t0]
    extkwd = EXTKWD.split(',')
    if len(extkwd) > 0:
        print '* Extra keywords:', extkwd
        kwd += extkwd

    exp = mt.Experiment(sandbox=sandbox,
        keywords=kwd,
        max_assignments=states['n_assignments'],
        title=states['title'],
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
    exp.URLs = ['https://s3.amazonaws.com/' + S3BUCKET +
            e.split(TMPDIR)[-1] for e in fns]
    exp.createHIT(verbose=True, hitidslog=hitidslog)

    fns = [hitidslog]
    dfns = ['hitidslog_' + 'sandbox.pkl' if sandbox else 'production.pkl']
    mt.uploader(fns, S3BUCKET, dstprefix=DATAFNPREFIX % s_t0,
            test=True, verbose=10, acl=None, dstfiles=dfns)

    print '* t0 was:', s_t0


def bonus(sandbox=True):
    """Publish to the sandbox"""
    bucket = mt.connect_s3().get_bucket(S3BUCKET)
    k = Key(bucket)

    def is_in_sloppy(x, iterable):
        for a in iterable:
            if a in x:
                return a
        return None

    if BONUST0 is None:
        states = pk.load(open(os.path.join(TMPDIR, STATES)))
        s_t0 = str(states['t0'])
        pref = DATAFNPREFIX % s_t0
    else:
        pref = DATAFNPREFIX % BONUST0
        k.key = pref + STATES
        states = pk.loads(k.get_contents_as_string())
        s_t0 = str(states['t0'])
        assert s_t0 == BONUST0

    fn_hs = 'hitidslog_' + 'sandbox.pkl' if sandbox else 'production.pkl'
    k.key = pref + fn_hs
    hitids = pk.loads(k.get_contents_as_string())
    bonuses = states['bonuses']
    unbonused = bonuses.keys()

    exp = mt.Experiment(sandbox=sandbox,
        max_assignments=MAX_PAGE_SIZE,
        reward=0.,
        collection_name=None,   # disables db connection
        meta=None,
        )

    rs = [e for hid in hitids for e in exp.getHITdata(hid)]
    for r in rs:
        w0 = r['WorkerID']
        w = is_in_sloppy(w0, bonuses)
        if w is None:
            print '*** Potential cheater:', r['WorkerID']
            continue

        k.key = pref + w + '.pkl'
        if k.exists():
            unbonused.remove(w)
            continue  # already gave a bonus

        aid = r['AssignmentID']
        try:
            exp.conn.approve_assignment(aid)
        except mturk.connection.MTurkRequestError:
            print 'Already approved?', aid

        b = Price(bonuses[w])
        exp.conn.grant_bonus(w0, aid, b, 'Compensation')

        pkl = pk.dumps(r)
        k.set_contents_from_string(pkl)

        unbonused.remove(w)
        print '* Granting $%4.2f bonus to %s' % (bonuses[w], w0)

    if len(unbonused) > 0:
        print '* Not yet bonused:', unbonused
    else:
        print '* All invited workers got bonuses.'


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
    elif argv[1] == 'bonus-sandbox':
        flag = bonus(sandbox=True)
    elif argv[1] == 'bonus':
        flag = bonus(sandbox=False)
    else:
        print 'Bad arguments'
        return 1

    if flag is None or flag:
        timestamp()
    else:
        return 1
    print '* Done.'
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
