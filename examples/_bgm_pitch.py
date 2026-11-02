"""Private gen_bgm diagnostic helpers; never changes score or playback timing."""

import math
import re

CLOCK_HZ = 1_789_773
SIZES = (8, 16, 32, 64, 128, 256, 512)
TOKEN = re.compile(r"@(?:ENV|VIB)\d+(?:\{[^{}]*\})?|@\d+|[TLQV]\d+|O\d+|[<>]|[A-GR][#-]?\d*\.*|\[|\]\d*|&(?:\d+\.*)?|\s+")


def score_notes(mmls):
    """Read only gen_bgm's bounded MML subset; reject unknown commands.

    Sound.notes does not expose the notes of MML-mode Sounds. Pyxel resolves
    octaves once while parsing; repeated playback can still change Tone state.
    """
    notes = [set() for _ in range(4)]
    vibrato = 0.0
    for text in mmls:
        if len(text) > 20000:
            raise ValueError("generated MML is too long to diagnose")
        tokens, position = [], 0
        for match in TOKEN.finditer(text.upper()):
            if match.start() != position:
                raise ValueError("unsupported generated MML in pitch diagnosis")
            position = match.end()
            if not match.group().isspace():
                tokens.append(match.group())
        if position != len(text):
            raise ValueError("unsupported generated MML in pitch diagnosis")
        octave, tone, steps = 4, 0, 0
        resolved_notes = {}

        def read(start, depth=0, replay=False):
            nonlocal octave, tone, steps, vibrato
            if depth > 16:
                raise ValueError("MML repeats too deeply nested")
            i = start
            while i < len(tokens):
                steps += 1
                if steps > 100000:
                    raise ValueError("MML repeat expansion exceeds diagnostic limit")
                token = tokens[i]
                if token.startswith("]"):
                    if not depth:
                        raise ValueError("unmatched MML repeat end")
                    return i
                if token == "[":
                    end = read(i+1, depth+1, replay)
                    count = int(tokens[end][1:] or "0")
                    if not 1 <= count <= 1024:
                        raise ValueError("unsupported MML repeat count")
                    for _ in range(count-1):
                        read(i+1, depth+1, True)
                    i = end
                elif token.startswith("@VIB") and "{" in token:
                    params = token.split("{", 1)[1].rstrip("}").split(",")
                    if len(params) != 3:
                        raise ValueError("unsupported Vibrato definition")
                    vibrato = max(vibrato, abs(float(params[2])))
                elif token.startswith("@") and token[1:].isdigit():
                    tone = int(token[1:])
                    if not 0 <= tone < 4:
                        raise ValueError("unexpected gen_bgm Tone index")
                elif token.startswith("O"):
                    if not replay:
                        octave = int(token[1:])
                elif token == ">":
                    if not replay:
                        octave += 1
                elif token == "<":
                    if not replay:
                        octave -= 1
                elif token[0] in "CDEFGAB":
                    if not replay:
                        note = 12*(octave+1) + dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)[token[0]]
                        note += 1 if token[1:2] == "#" else -1 if token[1:2] == "-" else 0
                        resolved_notes[i] = note
                    note = resolved_notes[i]
                    if not 0 <= note <= 127:
                        raise ValueError("generated note outside diagnostic range")
                    notes[tone].add(note)
                i += 1
            if depth:
                raise ValueError("unmatched MML repeat start")
            return i

        read(0)
    return tuple(tuple(sorted(group)) for group in notes), vibrato


def pitch_error(note, size):
    frequency = 440*2**((note-69)/12)
    clocks = max(1, math.floor(CLOCK_HZ/(size*frequency)+.5))
    return 1200*math.log2(CLOCK_HZ/(size*clocks)/frequency)


def error_bound(notes, size, vibrato_cents=0):
    """Conservative clock-quantization bound over all pitches up to the peak.

    A rounded period q differs by at most 0.5 clock. The negative-cent
    boundary is the larger absolute error. Including the highest vibrato
    definition across all parts deliberately overestimates active vibrato.
    """
    if not notes:
        return 0.0
    peak = 440*2**((max(notes)-69)/12 + vibrato_cents/1200)
    clocks = math.floor(CLOCK_HZ/(size*peak)+.5)
    if clocks < 1:
        return math.inf
    return -1200*math.log2(1-.5/clocks)


def choose_sizes(notes, vibrato_cents, target):
    if target not in (10, 25, None):
        raise ValueError("target must be 10, 25 or None (fixed 128)")
    sizes = []
    for group in notes:
        candidates = [size for size in SIZES if error_bound(group, size, vibrato_cents) <= (target or math.inf)]
        if target and group and not candidates:
            raise ValueError("pitch target cannot be met with candidate sizes")
        sizes.append(max(candidates) if target and group else 128)
    return tuple(sizes)
