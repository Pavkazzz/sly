#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import re
import math
import sys
import random
import time
import os
import unicodedata

try:
    # pylint: disable=F0401
    from colorama import Fore, Style
    has_colorama = True

except ImportError:
    has_colorama = False


if sys.version_info[:2] >= (3, 0):
    # pylint: disable=E0611,F0401
    # import pickle
    # from urllib.parse import urlencode
    uni, byt, xinput = str, bytes, input
    xinput = input

else:
    pass
    # Python 2
    # import cPickle as pickle
    # uni, byt, xinput = unicode, str, raw_input


utf8_encode = lambda x: x.encode("utf8") if type(x) == uni else x
utf8_decode = lambda x: x.decode("utf8") if type(x) == byt else x
mswin = os.name == "nt"
not_utf8_environment = "UTF-8" not in os.environ.get("LANG", "") or mswin
member_var = lambda x: not(x.startswith("__") or callable(x))


class g(object):

    """ Class for holding globals that are needed throught the module. """
    last_opened = message = content = ""
    blank_text = "\n" * 200
    last_volume = None


class Config(object):

    """ Holds various configuration values. """

    PLAYER = "mplayer"
    PLAYERARGS = "-nolirc -prefer-ipv4"
    COLOURS = False if mswin and not has_colorama else True
    CHECKUPDATE = True
    SHOW_MPLAYER_KEYS = True


class c(object):

    """ Class for holding colour code values. """

    if mswin and has_colorama:
        white = Style.RESET_ALL
        ul = Style.DIM + Fore.YELLOW
        red, green, yellow = Fore.RED, Fore.GREEN, Fore.YELLOW
        blue, pink = Fore.CYAN, Fore.MAGENTA

    elif mswin:
        Config.COLOURS = False

    else:
        white = "\x1b[%sm" % 0
        ul = "\x1b[%sm" * 3 % (2, 4, 33)
        cols = ["\x1b[%sm" % n for n in range(91, 96)]
        red, green, yellow, blue, pink = cols

    if not Config.COLOURS:
        ul = red = green = yellow = blue = pink = white = ""

    r, g, y, b, p, w = red, green, yellow, blue, pink, white


def play_range(songlist, shuffle=True, repeat=False):
    """ Play a range of songs, exit cleanly on keyboard interrupt. """

    if shuffle:
        random.shuffle(songlist)

    if not repeat:

        for n, song in enumerate(songlist):
            g.content = playback_progress(n, songlist, repeat=False)
            screen_update()

            try:
                playsong(song)

            except KeyboardInterrupt:
                print("Stopping...")
                time.sleep(1)
                g.message = c.y + "Playback halted" + c.w
                break

    elif repeat:

        while True:
            try:
                for n, song in enumerate(songlist):
                    g.content = playback_progress(n, songlist, repeat=True)
                    screen_update()
                    playsong(song['url'])
                    g.content = generate_songlist_display()

            except KeyboardInterrupt:
                print("Stopping...")
                time.sleep(2)
                g.message = c.y + "Playback halted" + c.w
                break


def playsong(song, failcount=0):
    """ Play song using config.PLAYER called with args config.PLAYERARGS."""

    # pylint: disable = R0912

    song['track_url'] = song['url']

    pargs = Config.PLAYERARGS.split()

    if "mplayer" in Config.PLAYER:

        if "-really-quiet" in pargs:
            pargs.remove("-really-quiet")

        if g.last_volume and "-volume" not in pargs:
            pargs += ["-volume", g.last_volume]

    cmd = [Config.PLAYER] + pargs + [song['track_url']]

    # fix for github issue 59 of mps-youtube
    if "mplayer" in Config.PLAYER and mswin and sys.version_info[:2] < (3, 0):
        cmd = [x.encode("utf8", errors="replace") for x in cmd]

    stdout = stderr = None

    try:
        with open(os.devnull, "w") as fnull:

            if "mpv" in Config.PLAYER:
                stderr = fnull

            if mswin:
                stdout = stderr = fnull

            if "mplayer" in Config.PLAYER:
                p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, bufsize=1)
                mplayer_status(p, "", song['duration'])

            else:
                subprocess.call(cmd, stdout=stdout, stderr=stderr)

    except OSError:
        g.message = F('no player') % Config.PLAYER

    finally:
        try:
            p.terminate()  # make sure to kill mplayer if mps crashes

        except (OSError, AttributeError, UnboundLocalError):
            pass


def mplayer_status(popen_object, prefix="", songlength=0):
    """ Capture time progress from player output. Write status line. """

    # A: 175.6
    re_mplayer = re.compile(r"A:\s*(?P<elapsed_s>\d+)\.\d\s*")
    # Volume: 88 %
    re_mplayer_volume = re.compile(r"Volume:\s*(?P<volume>\d+)\s*%")

    last_displayed_line = None
    buff = ''
    volume_level = None

    while popen_object.poll() is None:
        char = popen_object.stdout.read(1).decode('utf-8', errors="ignore")

        if char in '\r\n':
            mv = re_mplayer_volume.search(buff)
            if mv:
                volume_level = int(mv.group("volume"))

            m = re_mplayer.match(buff)
            if m:
                line = make_status_line(m, songlength, volume=volume_level)

                if line != last_displayed_line:
                    writestatus(prefix + (" " if prefix else "") + line)
                    last_displayed_line = line

            buff = ''

        else:
            buff += char


def make_status_line(match_object, songlength=0, volume=None,
                     progress_bar_size=60):
    """ Format progress line output.  """

    try:
        elapsed_s = int(match_object.group('elapsed_s') or '0')

    except ValueError:
        return ""

    display_s = elapsed_s
    display_m = 0

    if elapsed_s >= 60:
        display_m = display_s // 60
        display_s %= 60

    pct = (float(elapsed_s) / songlength * 100) if songlength else 0

    status_line = "%02i:%02i %s" % (display_m, display_s,
                                    ("[%.0f%%]" % pct).ljust(6))

    if volume:
        progress_bar_size -= 10
        vol_suffix = " vol: %d%%  " % volume

    else:
        vol_suffix = ""

    progress = int(math.ceil(pct / 100 * progress_bar_size))
    status_line += " [%s]" % ("=" * (progress - 1) +
                              ">").ljust(progress_bar_size)
    status_line += vol_suffix
    return status_line


def writestatus(text):
    """ Update status line. """

    spaces = 75 - len(text)
    sys.stdout.write(" " + text + (" " * spaces) + "\r")
    sys.stdout.flush()


def screen_update():
    """ Display content, show message, blank screen."""

    print(g.blank_text)

    if g.content:
        xprint(g.content)

    if g.message:
        xprint(g.message)

    g.message = g.content = ""


def playback_progress(idx, allsongs, repeat=False):
    """ Generate string to show selected tracks, indicate current track. """

    # pylint: disable=R0914
    # too many local variables
    out = "  %s%-32s  %-33s %s   %s\n" % (c.ul, "Artist", "Title", "Time", c.w)
    show_key_help = (Config.PLAYER == "mplayer" or Config.PLAYER == "mpv"
                     and Config.SHOW_MPLAYER_KEYS)
    multi = len(allsongs) > 1

    for n, song in enumerate(allsongs):
        i = song['artist'][:31], song['title'][:32], song['duration']
        fmt = (c.w, "  ", c.b, i[0], c.w, c.b, i[1], c.w, c.y, i[2], c.w)

        if n == idx:
            fmt = (c.y, "> ", c.p, i[0], c.w, c.p, i[1], c.w, c.p, i[2], c.w)
            cur = i

        out += "%s%s%s%-32s%s  %s%-33s%s [%s%s%s]\n" % fmt

    out += "\n" * (3 - len(allsongs))
    pos = 8 * " ", c.y, idx + 1, c.w, c.y, len(allsongs), c.w
    playing = "{}{}{}{} of {}{}{}\n\n".format(*pos) if multi else "\n\n"
    keys = mplayer_help(short=(not multi and not repeat))
    out = out if multi else generate_songlist_display(song=allsongs[0])

    if show_key_help:
        out += "\n" + keys

    else:
        playing = "{}{}{}{} of {}{}{}\n".format(*pos) if multi else "\n"
        out += "\n" + " " * 58 if multi else ""

    fmt = playing, c.r, cur[1], c.w, c.r, cur[0], c.w
    out += "%s    %s%s%s by %s%s%s" % fmt
    out += "    REPEAT MODE" if repeat else ""
    return out


def mplayer_help(short=True):
    """ Mplayer help.  """

    volume = "[{0}9{1}] volume [{0}0{1}]"
    volume = volume if short else volume + "      [{0}ctrl-c{1}] return"
    seek = u"[{0}\u2190{1}] seek [{0}\u2192{1}]"
    pause = u"[{0}\u2193{1}] SEEK [{0}\u2191{1}]       [{0}space{1}] pause"

    if not_utf8_environment:
        seek = "[{0}<-{1}] seek [{0}->{1}]"
        pause = "[{0}DN{1}] SEEK [{0}UP{1}]       [{0}space{1}] pause"

    ret = "[{0}q{1}] %s" % ("return" if short else "next track")
    fmt = "    %-20s       %-20s"
    lines = fmt % (seek, volume) + "\n" + fmt % (pause, ret)
    return lines.format(c.g, c.w)


def generate_songlist_display(song=False):
    """ Generate list of choices from a song list."""

    songs = g.model.songs or []

    if not songs:
        return logo(c.g) + "\n\n"

    fmtrow = "%s%-6s %-7s %-21s %-22s %-8s %-7s%s\n"
    head = (c.ul, "Item", "Size", "Artist", "Track", "Length", "Bitrate", c.w)
    out = "\n" + fmtrow % head

    for n, x in enumerate(songs):
        col = (c.r if n % 2 == 0 else c.p) if not song else c.b
        size = x.get('size') or 0
        title = x.get('song') or "unknown title"
        artist = x.get('singer') or "unknown artist"
        bitrate = x.get('listrate') or "unknown"
        duration = x.get('duration') or "unknown length"
        art, tit = uea_trunc(20, artist), uea_trunc(21, title)
        art, tit = uea_rpad(21, art), uea_rpad(22, tit)
        fmtrow = "%s%-6s %-7s %s %s %-8s %-7s%s\n"
        size = uni(size)[:3]
        size = size[0:2] + " " if size[2] == "." else size

        if not song or song != songs[n]:
            out += (fmtrow % (col, uni(n + 1), size + " Mb",
                              art, tit, duration[:8], bitrate[:6], c.w))
        else:
            out += (fmtrow % (c.p, uni(n + 1), size + " Mb",
                              art, tit, duration[:8], bitrate[:6], c.w))

    return out + "\n" * (5 - len(songs)) if not song else out


def logo(col=None, version=""):
    """ Return         text logo. """

    col = col if col else random.choice((c.g, c.r, c.y, c.b, c.p, c.w))
    LOGO = col + """\
       SSSSSSSSSSSSSSS lllllll
     SS:::::::::::::::Sl:::::l
    S:::::SSSSSS::::::Sl:::::l
    S:::::S     SSSSSSSl:::::l
    S:::::S             l::::lyyyyyyy           yyyyyyy
    S:::::S             l::::l y:::::y         y:::::y
     S::::SSSS          l::::l  y:::::y       y:::::y
      SS::::::SSSSS     l::::l   y:::::y     y:::::y
        SSS::::::::SS   l::::l    y:::::y   y:::::y
           SSSSSS::::S  l::::l     y:::::y y:::::y
                S:::::S l::::l      y:::::y:::::y
                S:::::S l::::l       y:::::::::y
    SSSSSSS     S:::::Sl::::::l       y:::::::y
    S::::::SSSSSS:::::Sl::::::l        y:::::y
    S:::::::::::::::SS l::::::l       y:::::y
     SSSSSSSSSSSSSSS   llllllll      y:::::y
                                    y:::::y
                                   y:::::y
                                  y:::::y
                                 y:::::y
                                yyyyyyy
      """ % (c.w + "v" + version if version else "", col, c.w)
    return LOGO + c.w if not g.debug_mode else ""


def real_len(u):
    """ Try to determine width of strings displayed with monospace font. """

    u = utf8_decode(u)
    ueaw = unicodedata.east_asian_width
    widths = dict(W=2, F=2, A=1, N=0.75, H=0.5)
    return int(round(sum(widths.get(ueaw(char), 1) for char in u)))


def uea_trunc(num, t):
    """ Truncate to num chars taking into account East Asian width chars. """

    while real_len(t) > num:
        t = t[:-1]

    return t


def uea_rpad(num, t):
    """ Right pad with spaces taking into account East Asian width chars. """

    t = uea_trunc(num, t)

    if real_len(t) < num:
        t = t + (" " * (num - real_len(t)))

    return t


def xprint(stuff, end=None):
    """ Compatible print. """

    print(xenc(stuff))


def xenc(stuff, end=None):
    """ Replace unsupported characters. """
    stuff = utf8_replace(stuff) if not_utf8_environment else stuff
    return stuff


def utf8_replace(txt):
    """ Replace unsupported characters in unicode string, returns unicode. """

    sse = sys.stdout.encoding
    txt = txt.encode(sse, "replace").decode("utf8", "ignore")
    return txt


def F(key, nb=0, na=0, percent=r"\*", nums=r"\*\*", textlib=None):
    """Format text.
    nb, na indicate newlines before and after to return
    percent is the delimter for %s
    nums is the delimiter for the str.format command (**1 will become {1})
    textlib is the dictionary to use (defaults to g.        text if not given)
    """

    textlib = textlib or g.text

    assert key in textlib
    text = textlib[key]
    percent_fmt = textlib.get(key + "_")
    number_fmt = textlib.get("_" + key)

    if number_fmt:
        text = re.sub(r"(%s(\d))" % nums, "{\\2}", text)
        text = text.format(*number_fmt)

    if percent_fmt:
        text = re.sub(r"%s" % percent, r"%s", text)
        text = text % percent_fmt

        text = re.sub(r"&&", r"%s", text)

    return "\n" * nb + text + c.w + "\n" * na
