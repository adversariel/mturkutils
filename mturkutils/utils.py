"""Various utilities for manipulating psychophysics experiments"""
import os
import json
import shutil as sh
import cPickle as pk
from boto import __version__ as boto_version
from . import base

# -- example rules for prep_web_simple()
PREP_RULE_SIMPLE_RSVP_SANDBOX = [
        {
            'old': 'imgFiles = [];',
            'new': 'imgFiles = ${CHUNK};',
            'n': 1
        },
        {
            'old': 'https://www.mturk.com/mturk/externalSubmit',
            'new': 'https://workersandbox.mturk.com/mturk/externalSubmit',
            'n': 1
        },
    ]

PREP_RULE_SIMPLE_RSVP_PRODUCTION = [
        {
            'old': 'imgFiles = [];',
            'new': 'imgFiles = ${CHUNK};',
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

BACKUP_ALGO_VER = 1


def prep_web_simple(trials, src, dstdir, dstpatt='output_n%04d.html',
        rules=PREP_RULE_SIMPLE_RSVP_SANDBOX, auxfns=None,
        n_per_file=100, verbose=False):
    """Prepare web files for publishing.

    This function does the following things:
    * Do simple string manipulations and prepare html files for publishing.
    * Copy associated web files (e.g., javascripts, images, etc.).

    Parameters
    ----------
    * trials: list of trials to be distributed across multiple (html) files.
      Note that no randomization is done in this function.
    * src: path to the source html file
    * dstdir: dirname for the output web files
    * dstpatt: output file name pattern.  Should contain a formating string
      (e.g., %d) for numbering
    * rules: a list of dictionaries that specifies string manipulations needed.
      Each element dictionary should have keys "old" and "new", which
      mean the old string to be replaced and the new string, respectively.
      If "n" is in the dictionary, the number will be used to assert
      the number of occurances of "old".  "${CHUNK}" in "new" will be
      replaced with the actual trials for the file.  See
      `PREP_RULE_SIMPLE_RSVP_SANDBOX` for example.
    * auxfns: list of aux file names to be copied into `dstdir`
    * n_per_file: the number of presentations per one final html file
    """
    # process html first
    dst_fns = []
    mkdirs(dstdir)
    html_src = open(src, 'rt').read()   # entire file content
    for rule in rules:
        if 'n' not in rule:
            continue
        assert html_src.count(rule['old']) == rule['n']

    for i_chunk, chunk in enumerate(chunker(trials, n_per_file)):
        if verbose and i_chunk % n_per_file == 0:
            print '    At:', i_chunk

        html_dst = html_src
        for rule in rules:
            sold = rule['old']
            snew = rule['new']
            if '${CHUNK}' in snew:
                snew = snew.replace('${CHUNK}', json.dumps(chunk))
            html_dst = html_dst.replace(sold, snew)

        dst_fn = dstpatt % i_chunk
        dst_fn = os.path.join(dstdir, dst_fn)
        open(dst_fn, 'wt').write(html_dst)
        dst_fns.append(dst_fn)

    # -- done main work: copy all aux files
    if auxfns is not None:
        for fn in auxfns:
            sh.copy(fn, dstdir)

    return dst_fns


def validate_html_files(filenames, rules=PREP_RULE_SIMPLE_RSVP_SANDBOX,
        trials_org=None):
    """Validates `filenames` by running simple tests

    Parameters
    ----------
    * filenames: list of target file names (useually html files)
    * rules: list of testing rules.  See prep_web_simple() for the element
      structure.  Only the keys "new" and "n" are used.  If "new" contains
      "${CHUNK}", the portion in all `filenames` will be concatenated and
      compared against `trials_org` (if given).
    * trials_org: the original entire trials.
    """
    trials = []
    sep_begin = None
    sep_end = None
    n_occ = 0

    for rule in rules:
        if '${CHUNK}' not in rule['new']:
            continue
        seps = rule['new'].split('${CHUNK}')
        sep_begin, sep_end = seps[0], seps[1]
        n_occ = rule['n']
        break

    for fn in filenames:
        # pass 1
        html = open(fn).read()
        for rule in rules:
            if 'n' not in rule or '${CHUNK}' in rule['new']:
                continue
            assert html.count(rule['new']) == rule['n']

        # pass 2
        if trials_org is None or sep_begin is None:
            continue
        html = open(fn).readlines()
        html = [e for e in html if sep_begin in e]
        assert len(html) == n_occ
        html = html[0]
        trials0 = html.split(sep_begin)[-1].split(sep_end)[0]
        trials0 = json.loads(trials0)
        trials.extend(trials0)

    if trials_org is not None:
        assert trials_org == trials


def download_results(hitids, dstprefix=None, sandbox=True,
        replstr='${HIT_ID}', verbose=False, full=False):
    """Download all assignment results in `hittids` and save one pickle file
    per HIT with `dstprefix` if it is not `None`.  If `dstprefix` is `None`,
    the downloaded info will be returned without saving files."""
    exp = base.Experiment(sandbox=sandbox,
        max_assignments=base.MTURK_PAGE_SIZE_LIMIT,
        reward=0.,
        collection_name=None,   # disables db connection
        meta=None,
        )

    res = []
    n_total = len(hitids)
    n_hits = 0
    n_assgns = 0
    meta = {'boto_version': boto_version,
            'backup_algo_version': BACKUP_ALGO_VER}

    for hitid in hitids:
        if verbose:
            print 'At (%d/%d):' % (n_hits + 1, n_total), hitid

        assignments, HITdata = exp.getHITdataraw(hitid)
        n_hits += 1
        n_assgns += len(assignments)

        if dstprefix is None:
            res.append((assignments, HITdata))
            continue

        # save files otherwise
        if replstr in dstprefix:
            dst = dstprefix.replace(replstr, str(hitid))
        else:
            dst = dstprefix + str(hitid) + '.pkl'
        pk.dump((assignments, HITdata, meta), open(dst, 'wb'))

    if full:
        return res, n_hits, n_assgns
    if dstprefix is None:
        return res


def mkdirs(pth):
    """Make the directory recursively"""
    if not os.path.exists(pth):
        os.makedirs(pth)


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))
