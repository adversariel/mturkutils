import mturkutils as mt
import mturkutils.utils as ut
import cPickle as pk
import numpy as np
import sys
import os
import dldata.human_data.roschlib as rl
import time
import glob

# various
METAPATH = 'references/meta64_rotonly_graybg.pkl'
PRODUCTIONPATH = 'html'          # make sure there's no trailing /
SANDBOXPATH = 'html_sandbox'     # same: no trailing /
TSTAMP = os.environ.get('DRIVER_TSTAMP')     # timestamp
TRIALS = os.environ.get('DRIVER_TRIALS', 'trials.pkl')
TMPDIR = os.environ.get('DRIVER_TMPDIR', 'tmp')
TMPDIR_PRODUCTION = os.path.join(TMPDIR, PRODUCTIONPATH)
TMPDIR_SANDBOX = os.path.join(TMPDIR, SANDBOXPATH)

# patterns for string manipulation
HTMLSRC = 'web/adjectives_slider.html'
HTMLDST = 'adjectives_slider_n%04d.html'
OTHERSRC = ['web/adj_dict.js']

# other constants
ADJS = ['light', 'bulbous', 'boxy', 'curly', 'globular', 'disc-like',
    'pointy', 'bumpy', 'rectangular', 'striped', 'spotted', 'juicy',
    'cuddly']
S3PREFIX_SUBJSIM = 'http://s3.amazonaws.com/subjsimilarity/'
S3BUCKET = 'objectome_adjectives'


# -- main funcs
def prep(n_reps=50, n_trials_per_chunk=100, with_repl=False, same_across=True,
        rseed=0, nc_objs=64, nc_imgs=100):
    """Prepare web files for publishing"""
    meta = pk.load(open(METAPATH))
    models64 = rl.ps64_models
    assert len(models64) == nc_objs

    # -- make trials
    print '* Creating trials...'
    rng = np.random.RandomState(rseed)
    trials = []
    for obj in models64:
        si_obj = np.nonzero(meta['obj'] == obj)[0]
        assert len(si_obj) == nc_imgs
        si = None

        for adj in ADJS:
            if si is not None and same_across:
                # same images are shown across all adjs
                pass
            else:
                if with_repl:
                    # with replacement
                    n = len(si_obj)
                    si = rng.randint(n, size=n_reps)
                    si = si_obj[si]
                else:
                    # without replacement
                    rng.shuffle(si_obj)
                    si = si_obj[:n_reps]
                assert len(si) == n_reps

            for i in si:
                assert meta[i]['obj'] == obj
                imgurl = S3PREFIX_SUBJSIM + meta[i]['id'] + '.png'
                trials.append([imgurl, adj])
    assert len(trials) % n_trials_per_chunk == 0

    # -- prep files
    print '* Writing files...'
    rng = np.random.RandomState(rseed + 1)
    rng.shuffle(trials)

    for label, rules, dstdir in [
            ('sandbox', ut.PREP_RULE_SIMPLE_RSVP_SANDBOX, TMPDIR_SANDBOX),
            ('production', ut.PREP_RULE_SIMPLE_RSVP_PRODUCTION,
                TMPDIR_PRODUCTION)]:
        print '  ->', label
        ut.prep_web_simple(trials, HTMLSRC, dstdir, dstpatt=HTMLDST,
                rules=rules, auxfns=OTHERSRC,
                n_per_file=100, verbose=True)

    # save trials for future reference
    pk.dump(trials, open(os.path.join(TMPDIR, TRIALS), 'wb'))


def test():
    """Test and validates the written html files"""
    trials_org = pk.load(open(os.path.join(TMPDIR, TRIALS)))

    fns_sandbox = sorted(glob.glob(os.path.join(
        TMPDIR_SANDBOX, '*.html')))
    fns_production = sorted(glob.glob(os.path.join(
        TMPDIR_PRODUCTION, '*.html')))

    print '* Testing sandbox...'
    ut.validate_html_files(fns_sandbox,
            rules=ut.PREP_RULE_SIMPLE_RSVP_SANDBOX,
            trials_org=trials_org)
    print '* Testing production...'
    ut.validate_html_files(fns_production,
            rules=ut.PREP_RULE_SIMPLE_RSVP_PRODUCTION,
            trials_org=trials_org)


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
    exp = mt.experiment(sandbox=sandbox,
        keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
        max_assignments=1,
        title='Visual judgment',
        reward=0.35, duration=1500,
        description="(This requester was previously published as Ethan Solomon.) ***You may complete as many HITs in this group as you want.*** Complete a visual object judgment task where you report the amount of certain properties of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
        comment="objectome_adj_slider task.  For each object (64 total) and selected adjective (13 total), there are 50 reps where subjects report 1 to 100 ratings.",  # noqa
        collection_name=None,   # disables db connection
        meta=None,
        )

    if sandbox:
        fns = sorted(glob.glob(os.path.join(
            TMPDIR_SANDBOX, '*.html')))
    else:
        fns = sorted(glob.glob(os.path.join(
            TMPDIR_PRODUCTION, '*.html')))

    hitidslog = os.path.join(TMPDIR, 'hitidslog_' +
            ('sandbox' if sandbox else 'production') + '_' +
            str(int(time.time())) + '.pkl')
    exp.URLs = ['http://s3.amazonaws.com/' + S3BUCKET +
            e.split(TMPDIR)[-1] for e in fns]
    exp.createHIT(verbose=True, hitidslog=hitidslog)


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
        prep()
    elif argv[1] == 'test':
        test()
    elif argv[1] == 'upload':
        upload()
    elif argv[1] == 'sandbox':
        publish(sandbox=True)
    elif argv[1] == 'production':
        publish(sandbox=False)
    else:
        print 'Bad arguments'
        return 1

    timestamp()
    print '* Done.'
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
