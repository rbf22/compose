
"Test all WinAnsi encoding (1252) charter set for standard predefined font"

#PyFPDF-cover-test:format=PDF
#PyFPDF-cover-test:fn=e1252.pdf
#PyFPDF-cover-test:hash=e84f193be84c1162538d64e28ee054b6

#
# Please note: with current PyFPDF state four codepoints:
# breve, dotaccent, hungarumlaut and ogonek will not shown in Helveltica.
#

import os
import os.path

import common  # test utilities

from fpdf import FPDF

if common.PY3K:
    unichr = chr

# PDF 1.7, annex D.1, pages 997-1000
SYMBOLS = [
    # page 997, left
    ["A", "A", 0o101],
    ["Æ", "AE", 0o306],
    ["Á", "Aacute", 0o301],
    ["Â", "Acircumflex", 0o302],
    ["Ä", "Adieresis", 0o304],
    ["À", "Agrave", 0o300],
    ["Å", "Aring", 0o305],
    ["Ã", "Atilde", 0o303],
    ["B", "B", 0o102],
    ["C", "C", 0o103],
    ["Ç", "Ccedilla", 0o307],
    ["D", "D", 0o104],
    ["E", "E", 0o105],
    ["É", "Eacute", 0o311],
    ["Ê", "Ecircumflex", 0o312],
    ["Ë", "Edieresis", 0o313],
    ["È", "Egrave", 0o310],
    ["Ð", "Eth", 0o320],
    ["€", "Euro", 0o200],
    ["F", "F", 0o106],
    ["G", "G", 0o107],
    ["H", "H", 0o110],
    ["I", "I", 0o111],
    ["Í", "Iacute", 0o315],
    ["Î", "Icircumflex", 0o316],
    ["Ï", "Idieresis", 0o317],
    ["Ì", "Igrave", 0o314],
    ["J", "J", 0o112],
    ["K", "K", 0o113],
    ["L", "L", 0o114],
    ["Ł", "Lslash", None], # No WinAnsi code
    ["M", "M", 0o115],
    ["N", "N", 0o116],
    ["Ñ", "Ntilde", 0o321],
    ["O", "O", 0o117],
    # page 997, right
    ["Œ", "OE", 0o214],
    ["Ó", "Oacute", 0o323],
    ["Ô", "Ocircumflex", 0o324],
    ["Ö", "Odieresis", 0o326],
    ["Ò", "Ograve", 0o322],
    ["Ø", "Oslash", 0o330],
    ["Õ", "Otilde", 0o325],
    ["P", "P", 0o120],
    ["Q", "Q", 0o121],
    ["R", "R", 0o122],
    ["S", "S", 0o123],
    ["Š", "Scaron", 0o212],
    ["T", "T", 0o124],
    ["Þ", "Thorn", 0o336],
    ["U", "U", 0o125],
    ["Ú", "Uacute", 0o332],
    ["Û", "Ucircumflex", 0o333],
    ["Ü", "Udieresis", 0o334],
    ["Ù", "Ugrave", 0o331],
    ["V", "V", 0o126],
    ["W", "W", 0o127],
    ["X", "X", 0o130],
    ["Y", "Y", 0o131],
    ["Ý", "Yacute", 0o335],
    ["Ÿ", "Ydieresis", 0o237],
    ["Z", "Z", 0o132],
    ["Ž", "Zcaron", 0o216],
    ["a", "a", 0o141],
    ["á", "aacute", 0o341],
    ["â", "acircumflex", 0o342],
    ["\xb4", "acute", 0o264],
    ["ä", "adieresis", 0o344],
    ["æ", "ae", 0o346],
    ["à", "agrave", 0o340],
    ["&", "ampersand", 0o46],
    # page 998, left
    ["å", "aring", 0o345],
    ["^", "asciicircum", 0o136],
    ["~", "asciitilde", 0o176],
    ["*", "asterisk", 0o52],
    ["@", "at", 0o100],
    ["ã", "atilde", 0o343],
    ["b", "b", 0o142],
    ["\\", "backslash", 0o134],
    ["|", "bar", 0o174],
    ["{", "braceleft", 0o173],
    ["}", "braceright", 0o175],
    ["[", "bracketleft", 0o133],
    ["]", "bracketright", 0o135],
    [" ̆", "breve", None],
    ["¦", "brokenbar", 0o246],
    ["•", "bullet", 0o225],
    ["c", "c", 0o143],
    ["ˇ", "caron", None],
    ["ç", "ccedilla", 0o347],
    ["\xb8", "cedilla", 0o270],
    ["¢", "cent", 0o242],
    ["ˆ", "circumflex", 0o210],
    [":", "colon", 0o72],
    [",", "comma", 0o54],
    ["©", "copyright", 0o251],
    ["¤", "currency", 0o244],
    ["d", "d", 0o144],
    ["†", "dagger", 0o206],
    ["‡", "daggerdbl", 0o207],
    ["°", "degree", 0o260],
    ["\xa8", "dieresis", 0o250],
    ["÷", "divide", 0o367],
    ["$", "dollar", 0o44],
    [" ̇", "dotaccent", None],
    ["ı", "dotlessi", None],
    ["e", "e", 0o145],
    ["é", "eacute", 0o351],
    # page 998, right
    ["ê", "ecircumflex", 0o352],
    ["ë", "edieresis", 0o353],
    ["è", "egrave", 0o350],
    ["8", "eight", 0o70],
    ["\u2026", "ellipsis", 0o205], # ...
    ["—", "emdash", 0o227],
    ["–", "endash", 0o226],
    ["=", "equal", 0o75],
    ["ð", "eth", 0o360],
    ["!", "exclam", 0o41],
    ["¡", "exclamdown", 0o241],
    ["f", "f", 0o146],
    ["\ufb01", "fi", None], # fi
    ["5", "five", 0o65],
    ["\ufb02", "fl", None], # fl
    ["ƒ", "florin", 0o203],
    ["4", "four", 0o64],
    ["⁄", "fraction", None],
    ["g", "g", 0o147],
    ["ß", "germandbls", 0o337],
    ["`", "grave", 0o140],
    [">", "greater", 0o76],
    ["«", "guillemotleft", 0o253],
    ["»", "guillemotright", 0o273],
    ["‹", "guilsinglleft", 0o213],
    ["›", "guilsinglright", 0o233],
    ["h", "h", 0o150],
    [" ̋", "hungarumlaut", None],
    ["-", "hyphen", 0o55],
    ["i", "i", 0o151],
    ["í", "iacute", 0o355],
    ["î", "icircumflex", 0o356],
    ["ï", "idieresis", 0o357],
    ["ì", "igrave", 0o354],
    ["j", "j", 0o152],
    ["k", "k", 0o153],
    ["l", "l", 0o154],
    # page 999, left
    ["<", "less", 0o74],
    ["¬", "logicalnot", 0o254],
    ["ł", "lslash", None],
    ["m", "m", 0o155],
    ["\xaf", "macron", 0o257],
    ["−", "minus", None],
    ["\xb5", "mu", 0o265],
    ["×", "multiply", 0o327],
    ["n", "n", 0o156],
    ["9", "nine", 0o71],
    ["ñ", "ntilde", 0o361],
    ["#", "numbersign", 0o43],
    ["o", "o", 0o157],
    ["ó", "oacute", 0o363],
    ["ô", "ocircumflex", 0o364],
    ["ö", "odieresis", 0o366],
    ["œ", "oe", 0o234],
    [" ̨", "ogonek", None],
    ["ò", "ograve", 0o362],
    ["1", "one", 0o61],
    ["\xbd", "onehalf", 0o275], # 1/2
    ["\xbc", "onequarter", 0o274], # 1/4
    ["\xb9", "onesuperior", 0o271],
    ["\xaa", "ordfeminine", 0o252],
    ["\xba", "ordmasculine", 0o272],
    ["ø", "oslash", 0o370],
    ["õ", "otilde", 0o365],
    ["p", "p", 0o160],
    ["¶", "paragraph", 0o266],
    ["(", "parenleft", 0o50],
    [")", "parenright", 0o51],
    ["%", "percent", 0o45],
    [".", "period", 0o56],
    ["·", "periodcentered", 0o267],
    ["‰", "perthousand", 0o211],
    ["+", "plus", 0o53],
    ["±", "plusminus", 0o261],
    # page 999, right
    ["q", "q", 0o161],
    ["?", "question", 0o77],
    ["¿", "questiondown", 0o277],
    ["\"", "quotedbl", 0o42],
    ["„", "quotedblbase", 0o204],
    ["“", "quotedblleft", 0o223],
    ["”", "quotedblright", 0o224],
    ["‘", "quoteleft", 0o221],
    ["’", "quoteright", 0o222],
    ["‚", "quotesinglbase", 0o202],
    ["'", "quotesingle", 0o47],
    ["r", "r", 0o162],
    ["®", "registered", 0o256],
    [" ̊", "ring", None],
    ["s", "s", 0o163],
    ["š", "scaron", 0o232],
    ["§", "section", 0o247],
    [";", "semicolon", 0o73],
    ["7", "seven", 0o67],
    ["6", "six", 0o66],
    ["/", "slash", 0o57],
    [" ", "space", 0o40],
    ["£", "sterling", 0o243],
    ["t", "t", 0o164],
    ["þ", "thorn", 0o376],
    ["3", "three", 0o63],
    ["\xbe", "threequarters", 0o276], # 3/4
    ["\xb3", "threesuperior", 0o263],
    ["˜", "tilde", 0o230],
    ["\u2122", "trademark", 0o231], # TM
    ["2", "two", 0o62],
    ["\xb2", "twosuperior", 0o262],
    ["u", "u", 0o165],
    ["ú", "uacute", 0o372],
    ["û", "ucircumflex", 0o373],
    ["ü", "udieresis", 0o374],
    ["ù", "ugrave", 0o371],
    # page 1000, left
    ["_", "underscore", 0o137],
    ["v", "v", 0o166],
    ["w", "w", 0o167],
    ["x", "x", 0o170],
    ["y", "y", 0o171],
    ["ý", "yacute", 0o375],
    # page 1000, right
    ["ÿ", "ydieresis", 0o377],
    ["¥", "yen", 0o245],
    ["z", "z", 0o172],
    ["ž", "zcaron", 0o236],
    ["0", "zero", 0o60],
]


CTRL = {
    0x00: "NUL",
    0x01: "SOH",
    0x02: "STX",
    0x03: "ETX",
    0x04: "EOT",
    0x05: "ENQ",
    0x06: "ACK",
    0x07: "BEL",
    0x08: "BS",
    0x09: "HT",
    0x0a: "LF",
    0x0b: "VT",
    0x0c: "FF",
    0x0d: "CR",
    0x0e: "SO",
    0x0f: "SI",
    0x10: "DLE",
    0x11: "DC1",
    0x12: "DC2",
    0x13: "DC3",
    0x14: "DC4",
    0x15: "NAK",
    0x16: "SYN",
    0x17: "ETB",
    0x18: "CAN",
    0x19: "EM",
    0x1a: "SUB",
    0x1b: "ESC",
    0x1c: "FS",
    0x1d: "GS",
    0x1e: "RS",
    0x1f: "US",
    0x20: "SP",
    0x7F: "DEL",
    0xA0: "NBSP",
    0xAD: "SHY"
}

class MyPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.write(10, self.p_hdr1)
        self.ln(10)
        self.set_font('Arial', '', 14)
        self.write(10, self.p_hdr2)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page %s / {nb}' % self.page_no(), 0, 0, 'C')

@common.add_unittest
def dotest(outputname, nostamp):
    pdf = MyPDF()
    pdf.p_hdr1 = "Latin Character Set and WinAnsiEncoding (1252)"
    pdf.p_hdr2 = "PDF 1.7, annex D.1, pages 997-1000"
    pdf.alias_nb_pages()
    pdf.compress = False
    use_exfont = False
    if nostamp:
        pdf._putinfo = lambda: common.test_putinfo(pdf)
    else:
        # This font used if:
        # 1. It exists
        # 2. In user mode
        fp = os.path.join(common.basepath, 'font/DejaVuSans.ttf')
        if os.path.exists(fp):
            use_exfont = True
            pdf.add_font('DejaVu', '', fp, uni = True)
    pdf.set_fill_color(150)
    pdf.add_page()

    def tabletop():
        pdf.set_font('Arial', 'B', 8)
        if use_exfont:
            pdf.cell(12, 8, txt = "DejaVu", border = 1, align = "C")
        pdf.cell(12, 8, txt = "Type 1", border = 1, align = "C")
        pdf.cell(12, 8, txt = "Code", border = 1, align = "C")
        pdf.cell(12, 8, txt = "1252", border = 1, align = "C")
        pdf.cell(35, 8, txt = "Name", border = 1, align = "C")
        pdf.cell(20, 8, txt = "WinAnsi", border = 1, align = "C")
        pdf.cell(20, 8, txt = "Unicode", border = 1, align = "C")
        pdf.ln()

    pdf.table_cnt = 0
    def print_char(char, name, code):
        if pdf.table_cnt > 28:
            pdf.add_page()
            pdf.table_cnt = 0
        if pdf.table_cnt == 0:
            tabletop()
        pdf.table_cnt += 1

        # transform char for displaying
        if len(char) != 1:
            if len(char) == 2 and char[:1] == " ":
                ocode = ord(char[1])
                if code is not None:
                    pchar = unichr(code)
                else:
                    pchar = "O" + char[1:]
            else:
                raise Exception("bad charter for \"" + name + "\" " + repr(char))
        else:
            ocode = ord(char)
            pchar = char


        # external
        if use_exfont:
            pdf.set_font('DejaVu', '', 14)
            pdf.cell(12, 8, txt = pchar, border = 1, align = "R")

        pdf.set_font('Arial', '', 14)

        # as latin-1 charter
        bg = False
        txt = pchar
        try:
            pchar.encode("latin1")
        except UnicodeEncodeError:
            txt = ""
            bg = True
        pdf.cell(12, 8, txt = txt, border = 1, align = "R", fill = bg)

        # as winansi code
        if code is not None:
            txt = chr(code)
        else:
            txt = ""
        pdf.cell(12, 8, txt = txt, border = 1, align = "R")

        # as 1252
        bg = False
        try:
            txt = pchar.encode("windows-1252").decode("latin-1")
        except:
            txt = ""
            bg = True
        pdf.cell(12, 8, txt = txt, border = 1, align = "R", fill = bg)

        # char name
        pdf.cell(35, 8, txt = name, border = 1, align = "L")
        # hex codes
        hcode = ""
        alt = ""
        if code is not None:
            hcode = "0x%02X" % code
            if ocode != code:
                alt = "0x%02X" % ocode
        else:
            alt = "0x%02X" % ocode
        pdf.cell(20, 8, txt = hcode, border = 1, align = "L")
        pdf.cell(20, 8, txt = alt, border = 1, align = "L")

        pdf.ln()


    used = {}
    for char, name, code in SYMBOLS:
        print_char(char, name, code)
        used[code] = (char, name)

    for i in range(32, 256):
        if i not in used:
            print_char(unichr(i), "Code 0x%02X" % i, i)

    # wiki-like table
    pdf.p_hdr1 = "Windows-1252"
    pdf.p_hdr2 = "https://en.wikipedia.org/wiki/Windows-1252"
    pdf.add_page()
    # without this setting we should use
    #  txt.encode("windows-1252").decode("latin-1") for every output
    pdf.set_doc_option("core_fonts_encoding", "windows-1252")
    cc = {}
    codec = {}
    for x in range(256):
        bgr, bgg, bgb = (0xFF, 0xFF, 0xFF)
        pdf.set_font('Arial', '', 14)
        if x in used:
            txt = used[x][0]
            if len(txt) > 1:
                code = ord(used[x][0][1])
            else:
                code = ord(used[x][0])
            if code < 256:
                code = "%02X" % code
            else:
                code = "U+%04X" % code
        else:
            txt = ""
            code = ""
        if x in CTRL:
            # control
            txt = CTRL[x]
            pdf.set_font('Arial', '', 10)
        # colors
        if (x <= 0x1F) or (x == 0x7F):
            bgr, bgg, bgb = (0xFF, 0xFF, 0xEF)
        elif (x >= 0x20 and x <= 0x2F) or \
             (x >= 0x3A and x <= 0x40) or \
             (x >= 0x5B and x <= 0x60) or \
             (x >= 0x7B and x <= 0x7E):
            bgr, bgg, bgb = (0xDF, 0xF7, 0xFF)
            # punctuation
        elif (x >= 0x30 and x <= 0x39) or (x in [0xB2, 0xB3, 0xB9]):
            # numeric digit
            bgr, bgg, bgb = (0xF7, 0xE7, 0xFF)
        elif x >= 0x41 and x <= 0x7A:
            # alphabetic
            bgr, bgg, bgb = (0xE7, 0xFF, 0xE7)
        elif x in [0x81, 0x8D, 0x8F, 0x90, 0x9D]:
            # unused
            bgr, bgg, bgb = (0xD0, 0xD0, 0xD0)
        elif (x in [0x83, 0x8A, 0x8C, 0x8E, 0x9A, 0x9C, 0x9E, 0x9F,
            0xAA, 0xBA]) or (x >= 0xC0 and x <= 0xD6) or \
            (x >= 0xD8 and x <= 0xF6) or (x >= 0xF8 and x <= 0xFF):
            # international
            bgr, bgg, bgb = (0xFF, 0xEF, 0xDF)
        else:
            # extended punctuation
            bgr, bgg, bgb = (0xDF, 0xDF, 0xE7)

        pdf.set_fill_color(bgr, bgg, bgb)
        cc[x % 16] = (bgr, bgg, bgb)
        codec[x % 16] = code
        pdf.cell(12, 8, txt = txt, border = "LRT", align = "C", fill = True)
        if x % 16 == 15:
            pdf.ln()
            pdf.set_font('Arial', '', 6)
            for i in range(16):
                pdf.set_fill_color(*cc[i])
                pdf.cell(12, 3, txt = codec[i],
                    border = "LR", align = "C", fill = True)
            pdf.ln()
            pdf.set_font('Arial', '', 6)
            for i in range(16):
                pdf.set_fill_color(*cc[i])
                pdf.cell(12, 3, txt = "0x%02X" % (x - 15 + i),
                    border = "LRB", align = "C", fill = True)
            pdf.ln()

    pdf.output(outputname, 'F')

if __name__ == "__main__":
    common.testmain(__file__, dotest)

