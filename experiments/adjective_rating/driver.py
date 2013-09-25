import mturkutils as mt
import cPickle as pk
import numpy as np
import sys
import os
import dldata.human_data.roschlib as rl
import json
import shutil as sh
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
REPLSRC = 'imgFiles = [];'
REPLDST = 'imgFiles = %s;'
TESTPATT = 'imgFiles = '
OTHERSRC = ['web/adj_dict.js']
SUBMITURL = 'https://www.mturk.com/mturk/externalSubmit'
SANDBOXURL = 'https://workersandbox.mturk.com/mturk/externalSubmit'

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

    # -- prep trias
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

    # -- main work
    print '* Writing files...'
    rng = np.random.RandomState(rseed + 1)
    rng.shuffle(trials)

    # process html first
    mkdirs(TMPDIR_PRODUCTION)
    mkdirs(TMPDIR_SANDBOX)

    html_src = open(HTMLSRC, 'rt').read()   # entire file content
    assert html_src.count(REPLSRC) == 1
    assert html_src.count(SUBMITURL) == 1

    for i_chunk, chunk in enumerate(chunker(trials, n_trials_per_chunk)):
        if i_chunk % 100 == 0:
            print '    At:', i_chunk

        html_dst = html_src.replace(REPLSRC, REPLDST % json.dumps(chunk))
        dst_fn = HTMLDST % i_chunk
        open(os.path.join(TMPDIR_PRODUCTION, dst_fn), 'wt').write(html_dst)
        html_dst = html_dst.replace(SUBMITURL, SANDBOXURL)
        open(os.path.join(TMPDIR_SANDBOX, dst_fn), 'wt').write(html_dst)

    # -- done main work
    # copy all necessary files
    for fn in OTHERSRC:
        sh.copy(fn, TMPDIR_PRODUCTION)
        sh.copy(fn, TMPDIR_SANDBOX)

    # save the trials and put the timestamp
    pk.dump(trials, open(os.path.join(TMPDIR, TRIALS), 'wb'))
    timestamp()


def test():
    """Test and validates the written html files"""
    trials_org = pk.load(open(os.path.join(TMPDIR, TRIALS)))

    def test_core(pth, assert_occurances=None):
        trials = []
        for fn in sorted(glob.glob(os.path.join(pth, '*.html'))):
            # pass 1
            html = open(fn).read()
            if assert_occurances is not None:
                for patt in assert_occurances:
                    assert html.count(patt) == assert_occurances[patt]
            # pass 2
            html = open(fn).readlines()
            html = [e for e in html if TESTPATT in e]
            assert len(html) == 1
            html = html[0]
            trials0 = html.split(TESTPATT)[-1].split(';')[0]
            trials0 = json.loads(trials0)
            trials.extend(trials0)
        assert trials_org == trials

    print '* Testing sandbox...'
    test_core(TMPDIR_SANDBOX, {SANDBOXURL: 1})
    print '* Testing production...'
    test_core(TMPDIR_PRODUCTION, {SUBMITURL: 1})
    timestamp()


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
    timestamp()


# -- helper funcs
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


def timestamp(tsvar=TSTAMP):
    if tsvar is not None:
        open(os.path.join(TMPDIR, tsvar), 'wt').write(str(time.time()))


def mkdirs(pth):
    if not os.path.exists(pth):
        os.makedirs(pth)


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
    else:
        print 'Bad arguments'
        return 1

    print '* Done.'
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
