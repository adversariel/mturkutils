"""Various utilities for manipulating psychophysics experiments"""
import os
import json
from bson import json_util
import shutil as sh
from yamutils.mongo import SONify


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


def dictchunker(seqdict, size):
    L = len(seqdict[seqdict.keys()[0]])
    return ({k: seqdict[k][pos:pos + size] for k in seqdict.keys()}
            for pos in xrange(0, L, size))


def prep_web_simple(trials, src, dstdir, rules, dstpatt='output_n%04d.html',
        auxfns=None,
        n_per_file=100, verbose=False,
        chunkerfunc=chunker,
        prefix=None):
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
            # skips the following safety mechanism.
            continue
        if html_src.count(rule['old']) != rule['n']:
            raise ValueError('Mismatch in replace rule "%s": ' +
                    '# expected = %d, # actual = %d' %
                    (rule['old'], rule['n'], html_src.count(rule['old'])))

    for i_chunk, chunk in enumerate(chunkerfunc(trials, n_per_file)):
        if verbose and i_chunk % n_per_file == 0:
            print '    At:', i_chunk

        html_dst = html_src
        for rule in rules:
            sold = rule['old']
            snew = rule['new']
            if '${CHUNK}' in snew:
                snew = snew.replace('${CHUNK}', json.dumps(SONify(chunk), default=json_util.default))
            html_dst = html_dst.replace(sold, snew)

        if prefix is None:
            dst_fn = dstpatt % i_chunk
        else:
            dst_fn = dstpatt % (prefix, i_chunk)
        dst_fn = os.path.join(dstdir, dst_fn)
        open(dst_fn, 'wt').write(html_dst)
        dst_fns.append(dst_fn)

    # -- done main work: copy all aux files
    if auxfns is not None:
        for fn in auxfns:
            sh.copy(fn, dstdir)

    return dst_fns


def validate_html_files(filenames, ruledict,
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
    trials = {}
    sep_begin = None
    sep_end = None
    n_occ = 0

    for rules in ruledict.values():
        for rule in rules:
            if '${CHUNK}' not in rule['new']:
                continue
            seps = rule['new'].split('${CHUNK}')
            sep_begin, sep_end = seps[0], seps[1]
            n_occ = rule['n']
            break

    for fn in filenames:
        # pass 1
        rules = ruledict[fn]
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
        for _k in trials0:
            if _k in trials:
                trials[_k].extend(trials0[_k])
            else:
                trials[_k] = trials0[_k]

    if trials_org is not None:
        assert trials_org.keys() == trials.keys()
        for ind in trials_org:
            assert len(trials[ind]) % len(trials_org[ind]) == 0
            mult = len(trials[ind]) / len(trials_org[ind])
            if mult * trials_org[ind] != trials[ind]:
                assert mult * len(trials_org[ind]) == len(trials[ind]), (len(trials_org[ind]), len(trials[ind]))

                badinds = [_i for _i in range(len(trials_org)) if trials_org[ind][_i] != trials[ind][_i]]
                assert len(badinds) > 0
                badind0 = badinds[0]
                print(badind0, trials[ind][badind0], trials_org[ind][badind0])
                raise Exception


def mkdirs(pth):
    """Make the directory recursively"""
    if not os.path.exists(pth):
        os.makedirs(pth)
