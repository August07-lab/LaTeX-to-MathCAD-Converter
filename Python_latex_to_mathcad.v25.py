#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX to MathCAD Converter
==========================
Usage / Cara pakai:
  1. Run / Jalankan:  python latex_to_mathcad.py
  2. Write or paste LaTeX in the Input box. / Tulis atau tempel LaTeX di kotak Input.
  3. Click "Type into Mathcad" (Mathcad Prime) or "Convert".
  4. Language (English / Bahasa Indonesia) and everything else: see the Settings and
     Help tabs inside the window.

Terminal mode (no GUI) / Mode terminal (tanpa GUI):
  python latex_to_mathcad.py "\\frac{a+b}{c}"
  python latex_to_mathcad.py --sexpr "\\frac{d^2y}{dt^2}"   # Prime (@) text format
  python latex_to_mathcad.py --plan  "\\frac{d^2y}{dt^2}"   # key sequence for auto-typing
  python latex_to_mathcad.py --lang en "..."                  # message language

Conversion engine: pure Python standard library (re, json).

Supported LaTeX (besides the basics): fractions (\\frac \\dfrac {a \\over b}), roots, powers/subscripts,
\\sum \\prod \\int (incl. \\iint \\iiint \\oint, \\limits) \\lim, derivatives (ordinary/partial/n-th),
matrices & arrays (p/b/B/v/V/small), piecewise \\begin{cases} -> if(...), aligned/align/gather
(one line per formula), |x| and \\|x\\| norms, \\bmod, \\binom, \\operatorname/\\mathrm names
and units (kN, argmax), \\not, set/logic/relation symbols (∈ ∪ ∧ ¬ ⇒ ≪ ∝ ...), \\xrightarrow,
\\overset/\\underbrace labels, comments (%), \\tag/\\label, spacing commands. Anything Mathcad cannot
represent is dropped or kept as a plain name WITH a warning in the Notes box, never silently
turned into a product of letters.
GUI: PySide6 (pip install PySide6).
"""

import json
import os
import re
import sys

# ----------------------------------------------------------------------------
# BAHASA / LANGUAGE  (satu sistem untuk seluruh teks antarmuka & pesan)
#   - Tambah bahasa baru: tambahkan kode di LANGS + satu blok di I18N.
#   - Rumus/sintaks LaTeX & format keluaran Mathcad TIDAK diterjemahkan.
#   - Pesan dari mesin konversi berupa objek Msg(kunci, **param): diterjemahkan
#     saat ditampilkan, jadi ikut berganti ketika bahasa diubah.
# ----------------------------------------------------------------------------
APP_TITLE = "LaTeX to MathCAD Converter"
LANGS = {"en": "English", "id": "Bahasa Indonesia"}
_LANG = {"code": "id"}

I18N = {
    "en": {
        # ---- tabs / header
        "tab_convert": "Convert", "tab_rules": "Replace rules", "tab_calibrate": "Calibration",
        "tab_settings": "Settings", "tab_help": "Help",
        "btn_theme": "Light / Dark",
        "tip_lang": "Interface language",
        "tip_theme": "Switch between light and dark theme",
        # ---- convert tab: toolbar
        "btn_paste_convert": "Paste & Convert", "btn_convert": "Convert",
        "btn_clear": "Clear", "btn_find": "Find & Replace",
        "btn_undo": "Undo", "btn_redo": "Redo", "btn_prev": "◀ Previous", "btn_next": "Next ▶",
        "tip_paste_convert": "Take the LaTeX from the clipboard, convert it and copy the result",
        "tip_convert": "Convert the input (Ctrl+Enter)",
        "tip_clear": "Clear input, result and notes",
        "tip_find": "Show or hide the Find & Replace bar (Ctrl+H)",
        "tip_undo": "Undo (Ctrl+Z)", "tip_redo": "Redo (Ctrl+Y)",
        "tip_prev": "Previous conversion (Alt+←)", "tip_next": "Next conversion (Alt+→)",
        "lbl_input": "Input (LaTeX)", "lbl_output": "Result", "lbl_notes": "Notes",
        "btn_copy_result": "Copy result", "btn_prime_fmt": "Prime format (@)",
        "tip_copy_result": "Copy the result to the clipboard",
        "tip_prime_fmt": "Convert to Mathcad Prime's internal text format and copy it",
        # ---- sidebar
        "card_prime": "Send to Mathcad Prime",
        "txt_prime_intro": ("Prime cannot read formulas from the clipboard, so the formula is "
                            "typed through the keyboard. Click the button, then click an EMPTY "
                            "area of the Prime worksheet before the countdown ends. Do not "
                            "touch the keyboard or mouse until it finishes."),
        "btn_type": "Type into Mathcad", "btn_stop": "Stop",
        "tip_type": "Type the formula into Mathcad Prime by simulating key presses (Windows)",
        "tip_stop": "Cancel typing",
        "lbl_start_in": "Start in", "lbl_seconds": "seconds",
        "lbl_key_delay": "Key delay",
        "tip_key_delay": "0-400 ms (below 1 ms, several keys are sent per tick; 0 = as fast as possible). Increase (80-120 ms) if Prime lags or drops characters",
        "txt_sexpr_intro": ("Alternative: copy the formula in Prime's text format, then paste "
                            "(Ctrl+V) into an EMPTY math region in Prime."),
        "btn_sexpr": "Copy as Prime format (@)",
        "tip_sexpr": "Convert to (@EQ …) text and copy it",
        "card_options": "Conversion options",
        "lbl_subscript": "Subscript (x₁):",
        "opt_sub_underscore": "x_1 (variable name)", "opt_sub_literal": "x.1 (literal subscript)",
        "opt_sub_drop": "drop",
        "lbl_logbase": "Log with base (log_b x):",
        "opt_log_comma": "log(x,b)", "opt_log_ln": "ln(x)/ln(b)",
        "tip_logbase": "Use ln(x)/ln(b) if Mathcad drops the base typed as log(x,b)",
        "opt_define": "Turn '=' into ':=' (definition)",
        "opt_mul": "Insert '*' between variables (ab → a*b)",
        "opt_watch": "Watch clipboard automatically",
        "opt_rules": "Apply automatic replace rules",
        "tip_define": "Only the first '=' of each line is changed",
        "tip_mul": "Names of 2+ letters that are not functions are split into products",
        "tip_watch": "Convert automatically whenever LaTeX is copied anywhere",
        "tip_rules": "Apply the rules from the 'Replace rules' tab before converting",
        # ---- find & replace bar
        "card_find": "Find & Replace", "lbl_find": "Find", "lbl_replace": "Replace with",
        "opt_case": "Match case", "opt_whole": "Whole word", "opt_regex": "Regex",
        "lbl_apply_to": "Apply to:", "opt_target_in": "Input (LaTeX)",
        "opt_target_out": "Result",
        "btn_find_next": "Find next", "btn_replace": "Replace", "btn_replace_all": "Replace all",
        "btn_make_rule": "Make permanent rule", "btn_close": "Close",
        "tip_make_rule": "Add this pair to the list on the 'Replace rules' tab",
        # ---- rules tab
        "h_rules": "Permanent replace rules",
        "txt_rules_intro": ("One rule per line in the form  old => new.  Start with re: for a "
                            "regular expression, e.g.  re:\\\\alpha_(\\w) => a_\\1.  Lines "
                            "starting with # are ignored. Rules are applied to the input "
                            "BEFORE conversion when 'Apply automatic replace rules' is ticked."),
        "btn_save_rules": "Save rules",
        # ---- calibration tab
        "h_calibrate": "Calibrate Prime format",
        "txt_cal_intro": ("Syntax marked as unverified can be tested here. Quick way: 1) In "
                          "Prime create an empty math region. 2) Click 'Next candidate' (copies "
                          "a sample). 3) Press Ctrl+V in the region. 4) If it shows correctly "
                          "(e.g. the root appears with the √ symbol), stop; the chosen entry is "
                          "used. Otherwise repeat with the next candidate."),
        "cal_define": "Definition   a := b", "cal_sub": "Subtraction   a - b",
        "cal_div": "Division   a / b", "cal_neg": "Unary minus   -a",
        "cal_sqrt": "Square root (√ notation)", "cal_nroot": "n-th root (notation)", "cal_abs": "Absolute value   |x|", "cal_nderiv": "n-th derivative   d^n/dx^n", "cal_index": "Array index   x[n]",
        "cal_rel_lt": "Less than   x < y", "cal_rel_gt": "Greater than   x > y",
        "cal_rel_le": "Less or equal   x ≤ y", "cal_rel_ge": "Greater or equal   x ≥ y",
        "cal_rel_ne": "Not equal   x ≠ y",
        "btn_copy_sample": "Copy sample", "btn_next_candidate": "Next candidate ▶",
        "h_learn": "Learn from Prime",
        "txt_learn_intro": ("The surest shortcut: build the example in Prime (hint below), "
                            "select its region, Ctrl+C, then paste (Ctrl+V) into the box. If "
                            "formatted (@…) text appears, the template is built automatically. "
                            "(If you only get an image or plain text, use 'Next candidate'.)"),
        "lbl_type_in_prime": "Type in Prime: {example}",
        "hint_define": "x := y",
        "hint_sub": "x - y",
        "hint_div": "x / y  (fraction, x over y)",
        "hint_neg": "-x",
        "hint_sqrt": "square root of x  (press \\ then x)",
        "hint_nroot": "y-th root of x  (Ctrl+\\ ; index y, radicand x)",
        "hint_index": "x[y]  (type x then [ then y: array index)",
        "hint_nderiv": "d^y/dx^y of z  (Ctrl+Shift+/ ; order y, variable x, expression z)",
        "hint_abs": "|x|  (press the | key, then x: absolute value bars)",
        "hint_rel_lt": "x < y  (Boolean comparison; type x, <, y)",
        "hint_rel_gt": "x > y  (Boolean comparison; type x, >, y)",
        "hint_rel_le": "x ≤ y  (type x, Ctrl+9, y)",
        "hint_rel_ge": "x ≥ y  (type x, Ctrl+0, y)",
        "hint_rel_ne": "x ≠ y  (type x, Ctrl+3, y)",
        "btn_learn": "Learn & use",
        # ---- settings tab
        "card_appearance": "General", "lbl_language": "Language", "lbl_theme": "Theme",
        "opt_theme_dark": "Dark", "opt_theme_light": "Light",
        "opt_topmost": "Keep window on top",
        "card_typing": "Auto-typing",
        "opt_greek": "Greek letters via Ctrl+G", "opt_real_keys": "Real keyboard keys (not Unicode)",
        "tip_greek": "Types the Latin letter, then Ctrl+G turns it into the Greek letter",
        "tip_real_keys": "Sends real key codes, which Prime handles best",
        "card_data": "Settings file",
        "txt_settings_file": ("Settings are saved automatically next to the program file "
                              "(latex_to_mathcad_settings.json)."),
        "btn_reset_settings": "Reset to defaults",
        # ---- status bar messages
        "s_ready": "Ready. Write or paste LaTeX, then click Convert or Type into Mathcad.",
        "s_empty": "Input is empty.",
        "s_converted": "✔ Converted and copied. In Mathcad Prime use 'Type into Mathcad' "
                       "(a plain paste only becomes a string).",
        "s_clip_empty": "Clipboard is empty or not text.",
        "s_copied": "Result copied to the clipboard.",
        "s_cleared": "Cleared. (Ctrl+Z restores text in a box.)",
        "s_history": "History {i}/{n} (result copied to the clipboard).",
        "s_nothing_undo": "Nothing left to undo.", "s_nothing_redo": "Nothing left to redo.",
        "s_unsupported_sexpr": "The formula contains Σ/∫/lim; it cannot be converted to Prime "
                               "format yet.",
        "s_sexpr_failed": "Could not convert to Prime format. See Notes.",
        "s_sexpr_copied": "✔ Prime format copied. In Prime: empty math region → Ctrl+V.",
        "s_unsupported_type": "The formula contains Σ/∫/lim; type that part manually in Prime.",
        "s_plan_failed": "Could not build the typing plan. See Notes.",
        "s_type_cancelled": "■ Cancelled.",
        "s_type_done": "✔ Finished typing. Check the result in Mathcad.",
        "s_type_focus_back": "Focus returned to this program, typing stopped.",
        "s_type_failed": "Failed to send key: {err}",
        "s_typing": "Typing {i}/{n} …  (click Stop to cancel)",
        "s_type_not_clicked": "The Mathcad window was not clicked. Try again, then click an "
                              "empty area of the Prime worksheet before the countdown ends.",
        "s_type_windows_only": "Auto-typing is only available on Windows. {err}",
        "s_countdown": "Click an EMPTY area of the Mathcad Prime worksheet … starting in {n} s",
        "s_fill_find": "Fill in the 'Find' field first.",
        "s_bad_regex": "Invalid regex: {err}",
        "s_bad_replacement": "Invalid replacement pattern: {err}",
        "s_not_found": "Not found.", "s_found_at": "Found at position {pos}.",
        "s_replaced": "{n} replacements.",
        "s_rule_added": "Added to the permanent rules (remember to click 'Save rules').",
        "s_rules_saved": "Rules saved ({path}).",
        "s_rules_save_failed": "Rules are in use but could not be saved to file: {err}",
        "s_sample_copied": "Sample copied: {sample}",
        "s_candidate_copied": "Candidate {n}/{total} copied: {sample}",
        "s_learned": "✔ Template '{item}' learned: {tpl}",
        "s_template_updated": "Template {item} updated from Prime text.",
        "s_settings_reset": "Settings restored to defaults.",
        "dlg_sym_title": "Symbols need fixing",
        "dlg_sym_body": ("These symbols were found in the LaTeX input:\n\n{items}\n\n"
                         "Fix them automatically now?\n(, becomes .   [ becomes (   ] becomes ) )"),
        "s_sym_fixed": "✔ {n} symbol(s) fixed in the input.",
        # ---- notes
        "n_none": "No warnings.",
        "n_rules_applied": "Replace rules applied: {n} replacement(s).",
        "n_plan": "Typing plan ([→] = right arrow key):\n{plan}",
        "n_cannot_type": "Cannot be typed automatically: {err}",
        "n_cannot_convert": "Cannot be converted: {err}",
        "n_unverified": "⚠ Not verified in Prime (guesses): {items}. If the pasted result is "
                        "wrong, open the Calibration tab.",
        "n_all_verified": "✔ Every part uses syntax verified in Prime.",
        "n_eq_hint": "A '=' becomes (@EQ …) (an equation). Tick ':=' for a definition.",
        # ---- unverified construct names
        "u_div": "division", "u_sub": "subtraction", "u_define": "definition :=",
        "u_neg": "unary minus", "u_rel": "relation {op}", "u_sqrt": "square root",
        "u_nroot": "n-th root", "u_abs": "absolute value |x|", "u_index": "array index x[n] (use Calibration > index)", "u_nderiv": "higher-order derivative (nested)", "u_deg": "degree sign (30 deg)", "u_fact": "factorial n!", "u_pdiff": "partial derivative (copied as an ordinary d/dx)",
        # ---- converter messages
        "end_of_text": "end of text",
        "w_deriv_order": "Derivative order in the numerator ({num}) differs from the "
                         "denominator ({den}); the denominator was used.",
        "w_deriv_symbolic": "Symbolic derivative order (e.g. n) was kept as diff(f,x,n); "
                            "Mathcad needs a numeric order, edit it manually.",
        "w_binom": "\\binom was converted to combin(n,k).",
        "w_accent": "Accent \\{name} was dropped (Mathcad cannot take it through text paste).",
        "w_bigop": "\\{name} (sum/integral) cannot be pasted as plain text; retype the "
                   "operator in Mathcad (Ctrl+Shift+4 / & / Ctrl+I).",
        "w_lim": "\\lim is not supported as text; retype it in Mathcad.",
        "w_unknown_cmd": "Command \\{name} is unknown and was kept as '{name}'.",
        "w_prime": "The prime/apostrophe (') was replaced by 'prime' (e.g. x' → xprime) "
                   "because an apostrophe is not valid in a Mathcad variable name. Use Find & "
                   "Replace for another name.",
        "w_dots": "The ellipsis \\{name} was removed; Mathcad cannot type '…' inside a formula.",
        "w_symbol_unicode": "Symbols such as ∈ ∪ ∧ ¬ ⇒ → are typed as Unicode characters. Prime does \
not treat every one of them as an operator, so check the result.",
        "w_op_limits": "The subscript under \\{name} (e.g. 'min over x') was dropped; Mathcad has no \
such notation.",
        "w_sum_cond": "The index condition of \\{name} is not supported; only the variable was \
kept. Fill in the limits manually in Mathcad.",
        "w_cases_default": "The last case has a condition; 0 was used as the 'otherwise' value of \
if(...).",
        "w_brace_label": "The label/annotation of \\{name} was dropped (only the expression is kept).",
        "w_sup_inf": "\\{name} was converted to {to}(...); check that this is what you mean.",
        "w_opname_kept": "\\{name} has no Mathcad equivalent and was kept as a function name.",
        "w_substack": "\\substack was flattened into a comma-separated list.",
        "w_oint": "\\{name} was converted to an ordinary integral (Mathcad has no contour integral).",
        "w_norm": "The norm ‖x‖ was converted to norm2(x).",
        "e_sym_sexpr": "The symbol '{sym}' cannot be converted to Prime (@) text format; use \
'Type into Mathcad'.",
        "w_tuple": "A comma list in parentheses, e.g. a set {a, b}, is typed as written; Mathcad \
has no set notation.",
        "w_pm": "Mathcad has no ± operator; split it into two formulas (+ and -).",
        "w_def_fallback": "':=' was replaced by '=' because the left side is not a simple "
                          "variable/function name (Mathcad rejects such a definition). It is "
                          "treated as an equation/identity.",
        "w_multiline_type": "There are several lines; only the first one is typed. Run again "
                            "for the next line.",
        "w_multiline_conv": "There are several lines; only the first one is converted "
                            "(one formula per paste).",
        "w_nderiv_type": "Higher-order derivatives are typed as nested derivative operators; "
                         "the key for the operator is KEY_DERIV in the key map (unverified).",
        "w_nderiv_native": "Higher-order derivatives are typed with Prime's nth-derivative "
                           "operator (Ctrl+Shift+/, then order, Tab, variable, Tab, expression). "
                           "Unverified: adjust NDERIV_CHORD / NDERIV_NAV in the key map if needed.",
        "w_vmatrix": "vmatrix / Vmatrix (bars around a matrix) was converted to det(matrix) / "
                     "norm2(matrix), i.e. |A| in Prime.",
        "w_matrix_keys": "Matrix typing: Ctrl+M (1x1), first row filled while adding columns with "
                         "Shift+Space, next rows added with Shift+Enter (lands in the same column) "
                         "then filled in zig-zag order (right to left, left to right, ...). Going back "
                         "from a filled cell uses Left arrows = content length + MAT_LEFT_EXTRA "
                         "(unverified); adjust the MAT_* constants if your Prime differs.",
        "w_bigop_keys": "Sigma/Pi/Integral/Limit typing: the shortcut opens the operator, then the plain "
                        "Right arrow moves between its blue blocks (Sigma/Pi: lower, 2x Right, upper, "
                        "Right, body; Integral: lower, upper, function, dx; Limit: variable, value, "
                        "direction, function). Adjust the SUM_/INT_/LIM_ constants in the key map if "
                        "your Prime differs. The body may be written without braces; it ends at =, a comma, a closing bracket, + or - (sum/prod/lim) or at dx (integral).",
        "w_sub_keys": "Literal subscripts are typed with Ctrl+- (toggle): name, Ctrl+-, subscript, "
                      "Ctrl+- (back to baseline). A plain '.' only gives a name like x.i (no lowered "
                      "subscript). Set SUB_MODE = \"dot\" in the key map for the old behaviour.",
        "e_bigop_sexpr": "Sigma/Pi/Integral/Limit cannot be converted to Prime (@) text format yet; "
                         "use 'Type into Mathcad'.",
        "e_matrix_size": "The number of matrix cells does not match rows x columns.",
        "e_matrix_sexpr": "Matrices cannot be converted to Prime (@) text format yet (its form is "
                          "unknown); use 'Type into Mathcad'.",
        "n_mat_paste": "⚠ A matrix mat(r,c,...) is only an intermediate form for auto-typing. "
                       "Pasting it into Prime gives a plain string. Use 'Type into Mathcad'.",
        "e_char": "Character '{ch}' (position {pos}) cannot be typed automatically.",
        "e_expected": "Expected '{val}' but found '{found}'.",
        "e_leftover": "Unexpected leftover text: '{text}'.",
        "e_incomplete": "Incomplete formula / unexpected character: '{found}'.",
        "e_node": "Unknown node: {kind}",
        "e_no_text_type": "There is no text to type.",
        "e_no_text_conv": "There is no text to convert.",
        "e_deriv_order": "The derivative order must be a positive whole number.",
        "e_learn_format": "The text is not in (@…) / (…) format: it must start with an "
                          "opening parenthesis.",
        "e_learn_var": "Example variable '{name}' was not found in the text. Make sure the "
                       "example in Prime is exactly: {example}",
        # ---- help
        "help_text": """\
## What this program does
It converts LaTeX formulas (for example copied from an AI chat, a paper or Word) into a form Mathcad Prime understands. Everything happens in this one window.

## Why a plain paste does not work in Prime
Prime does not understand ordinary math text (V.c, a/b, ...). Pasted text becomes a quoted string. Prime does understand its own internal text format (Lisp-like: (@EQ …), (@APPLY …)), and it understands keystrokes.

## Method 1: Type into Mathcad (Convert tab, right panel)
1. Write or paste the LaTeX in the Input box.
2. Click "Type into Mathcad".
3. Before the countdown ends, click an EMPTY area of the Prime worksheet.
4. Do not touch the keyboard or mouse until it finishes. "Stop" cancels.
The program presses keys as if you typed: Ctrl+- = subscript, / = fraction, ^ = power, \\ = root, : = :=, ? = derivative operator, and the → key to leave a subscript, power, denominator, root or derivative.

## Method 2: Prime format (@) text
1. Click "Copy as Prime format (@)".
2. In Prime create an EMPTY math region, then press Ctrl+V.
Parts that are still guesses (e.g. root, unary minus) are listed in the Notes; test them in the Calibration tab if the result is wrong.

## Derivatives
Any order, ordinary or partial, are recognised from the structure of the fraction:
    \\frac{dy}{dt}                    first derivative
    \\frac{d^2y}{dt^2}                second derivative
    \\frac{d^3 y}{dx^3}               third derivative (and so on)
    \\frac{\\partial^2 u}{\\partial x^2}      partial derivative
    \\frac{\\partial^2 u}{\\partial x \\partial y}   mixed partial derivative
    \\frac{d^2}{dt^2} f(t)             operator followed by an expression
    \\frac{\\mathrm{d}^2 y}{\\mathrm{d}t^2}   upright d is accepted too
Higher orders are written as nested first derivatives, which is the syntax verified in Prime. A symbolic order such as d^n y / dx^n is kept as diff(y,x,n) and needs manual editing.

## If the result is wrong
• Read the Notes box: it lists warnings and the typing plan (the keys that were pressed).
• Increase "Key delay" (80-120 ms) if Prime lags or drops characters.
• Fractions show a parenthesis in the numerator; that is normal.
• If your Prime uses other keys, change the KEY_* constants in the "MATHCAD PRIME KEY MAP" part of the .py file.
• ≤ ≥ ≠ use Ctrl+9 / Ctrl+0 / Ctrl+3; change CHORDS if needed.

## Limits
• ± cannot be typed automatically; enter it manually in Prime. Σ, ∏, ∫ and lim are typed with their shortcuts and the Right arrow; braces around the body are optional, e.g. \\sum_{i=1}^{n}{i^2}, \\int_{0}^{1}{x^2}\\,dx, \\lim_{x \\to 0^+}{\\frac{\\sin x}{x}}.
• Auto-typing is Windows only. Only the first line is typed per run.
• Prime notation y', \\dot{y} (derivative without a variable) is not converted; use \\frac{dy}{dt}.

## Find & Replace (Ctrl+H)
Replace letters/symbols in the input or the result (whole word, regex, Undo). "Make permanent rule" adds the pair to the Replace rules tab, where rules (old => new) can be saved and applied automatically before every conversion.

## About ':='
Mathcad accepts definitions only for a name or f(x). For tan(2θ) = ..., identities, or a derivative on the left, the program automatically uses '=' (@EQ).

## Shortcuts
Ctrl+Enter convert · Ctrl+H find & replace · Alt+← / Alt+→ history · Ctrl+Z / Ctrl+Y undo / redo · F1 this help · Esc close the find bar

## Language
Choose English or Bahasa Indonesia with EN / ID in the header or in Settings. Math syntax, LaTeX and Mathcad output are never translated.
""",
    },
    "id": {
        # ---- tabs / header
        "tab_convert": "Konversi", "tab_rules": "Aturan ganti", "tab_calibrate": "Kalibrasi",
        "tab_settings": "Pengaturan", "tab_help": "Bantuan",
        "btn_theme": "Terang / Gelap",
        "tip_lang": "Bahasa antarmuka",
        "tip_theme": "Ganti antara tema terang dan gelap",
        # ---- convert tab: toolbar
        "btn_paste_convert": "Tempel & Konversi", "btn_convert": "Konversi",
        "btn_clear": "Bersihkan", "btn_find": "Cari & Ganti",
        "btn_undo": "Urungkan", "btn_redo": "Ulangi", "btn_prev": "◀ Sebelumnya",
        "btn_next": "Berikutnya ▶",
        "tip_paste_convert": "Ambil LaTeX dari clipboard, konversi, lalu salin hasilnya",
        "tip_convert": "Konversi isi kotak input (Ctrl+Enter)",
        "tip_clear": "Kosongkan input, hasil, dan catatan",
        "tip_find": "Tampilkan atau sembunyikan panel Cari & Ganti (Ctrl+H)",
        "tip_undo": "Urungkan (Ctrl+Z)", "tip_redo": "Ulangi (Ctrl+Y)",
        "tip_prev": "Konversi sebelumnya (Alt+←)", "tip_next": "Konversi berikutnya (Alt+→)",
        "lbl_input": "Input (LaTeX)", "lbl_output": "Hasil", "lbl_notes": "Catatan",
        "btn_copy_result": "Salin hasil", "btn_prime_fmt": "Format Prime (@)",
        "tip_copy_result": "Salin hasil ke clipboard",
        "tip_prime_fmt": "Konversi ke format teks internal Mathcad Prime lalu salin",
        # ---- sidebar
        "card_prime": "Kirim ke Mathcad Prime",
        "txt_prime_intro": ("Prime tidak bisa membaca rumus dari clipboard, jadi rumus diketik "
                            "lewat keyboard. Klik tombol, lalu klik area KOSONG di worksheet "
                            "Prime sebelum hitungan mundur habis. Jangan sentuh keyboard/mouse "
                            "sampai selesai."),
        "btn_type": "Ketik ke Mathcad", "btn_stop": "Stop",
        "tip_type": "Ketik rumus ke Mathcad Prime dengan mensimulasikan tombol keyboard "
                    "(Windows)",
        "tip_stop": "Batalkan pengetikan",
        "lbl_start_in": "Mulai dalam", "lbl_seconds": "detik",
        "lbl_key_delay": "Jeda tombol",
        "tip_key_delay": "0-400 ms (di bawah 1 ms, beberapa tombol dikirim per tik; 0 = secepat mungkin). Naikkan (80-120 ms) kalau Prime tertinggal atau karakter hilang",
        "txt_sexpr_intro": ("Alternatif: salin rumus dalam format teks Prime, lalu tempel "
                            "(Ctrl+V) di math region KOSONG di Prime."),
        "btn_sexpr": "Salin format Prime (@)",
        "tip_sexpr": "Konversi ke teks (@EQ …) lalu salin",
        "card_options": "Opsi konversi",
        "lbl_subscript": "Subskrip (x₁):",
        "opt_sub_underscore": "x_1 (nama variabel)", "opt_sub_literal": "x.1 (subskrip literal)",
        "opt_sub_drop": "buang",
        "lbl_logbase": "Log berbasis (log_b x):",
        "opt_log_comma": "log(x,b)", "opt_log_ln": "ln(x)/ln(b)",
        "tip_logbase": "Pakai ln(x)/ln(b) bila Mathcad menghilangkan basis yang diketik sebagai log(x,b)",
        "opt_define": "Ubah '=' menjadi ':=' (definisi)",
        "opt_mul": "Sisipkan '*' antar variabel (ab → a*b)",
        "opt_watch": "Pantau clipboard otomatis",
        "opt_rules": "Terapkan aturan ganti otomatis",
        "tip_define": "Hanya '=' pertama pada tiap baris yang diubah",
        "tip_mul": "Nama 2+ huruf yang bukan fungsi dipecah menjadi perkalian",
        "tip_watch": "Konversi otomatis setiap kali LaTeX disalin dari mana pun",
        "tip_rules": "Terapkan aturan dari tab 'Aturan ganti' sebelum konversi",
        # ---- find & replace bar
        "card_find": "Cari & Ganti", "lbl_find": "Cari", "lbl_replace": "Ganti dengan",
        "opt_case": "Cocok huruf besar/kecil", "opt_whole": "Kata utuh", "opt_regex": "Regex",
        "lbl_apply_to": "Terapkan ke:", "opt_target_in": "Input (LaTeX)",
        "opt_target_out": "Hasil",
        "btn_find_next": "Cari berikutnya", "btn_replace": "Ganti", "btn_replace_all": "Ganti semua",
        "btn_make_rule": "Jadikan aturan tetap", "btn_close": "Tutup",
        "tip_make_rule": "Tambahkan pasangan ini ke daftar di tab 'Aturan ganti'",
        # ---- rules tab
        "h_rules": "Aturan ganti tetap",
        "txt_rules_intro": ("Satu aturan per baris, format  lama => baru.  Awali dengan re: "
                            "untuk regex, mis.  re:\\\\alpha_(\\w) => a_\\1.  Baris berawalan # "
                            "diabaikan. Aturan diterapkan ke input SEBELUM konversi bila "
                            "'Terapkan aturan ganti otomatis' dicentang."),
        "btn_save_rules": "Simpan aturan",
        # ---- calibration tab
        "h_calibrate": "Kalibrasi format Prime",
        "txt_cal_intro": ("Sintaks yang belum terverifikasi bisa diuji di sini. Cara cepat: "
                          "1) Di Prime buat math region kosong. 2) Klik 'Kandidat berikut' "
                          "(menyalin contoh). 3) Tekan Ctrl+V di region. 4) Kalau tampil benar "
                          "(mis. akar muncul dengan simbol √), berhenti; pilihan itulah yang "
                          "dipakai. Kalau tidak, ulangi dengan kandidat berikutnya."),
        "cal_define": "Definisi   a := b", "cal_sub": "Pengurangan   a - b",
        "cal_div": "Pembagian   a / b", "cal_neg": "Minus unary   -a",
        "cal_sqrt": "Akar kuadrat (notasi √)", "cal_nroot": "Akar pangkat n (notasi)", "cal_abs": "Nilai mutlak   |x|", "cal_nderiv": "Turunan ke-n   d^n/dx^n", "cal_index": "Indeks array   x[n]",
        "cal_rel_lt": "Lebih kecil   x < y", "cal_rel_gt": "Lebih besar   x > y",
        "cal_rel_le": "Lebih kecil sama dengan   x ≤ y", "cal_rel_ge": "Lebih besar sama dengan   x ≥ y",
        "cal_rel_ne": "Tidak sama dengan   x ≠ y",
        "btn_copy_sample": "Salin contoh", "btn_next_candidate": "Kandidat berikut ▶",
        "h_learn": "Pelajari dari Prime",
        "txt_learn_intro": ("Jalan pintas paling pasti: buat contoh di Prime (petunjuk di "
                            "bawah), pilih regionnya, Ctrl+C, lalu tempel (Ctrl+V) ke kotak. "
                            "Kalau muncul teks berformat (@…), template dibuat otomatis. "
                            "(Kalau yang muncul hanya gambar/teks biasa, pakai 'Kandidat "
                            "berikut'.)"),
        "lbl_type_in_prime": "Ketik di Prime: {example}",
        "hint_define": "x := y",
        "hint_sub": "x - y",
        "hint_div": "x / y  (pecahan x di atas y)",
        "hint_neg": "-x",
        "hint_sqrt": "akar kuadrat dari x  (tekan \\ lalu x)",
        "hint_nroot": "akar pangkat y dari x  (Ctrl+\\ ; indeks y, isi x)",
        "hint_index": "x[y]  (ketik x, tombol [ , lalu y: indeks array)",
        "hint_nderiv": "d^y/dx^y dari z  (Ctrl+Shift+/ ; tingkat y, variabel x, ekspresi z)",
        "hint_abs": "|x|  (tekan tombol | , lalu x: tanda mutlak)",
        "hint_rel_lt": "x < y  (perbandingan Boolean; ketik x, <, y)",
        "hint_rel_gt": "x > y  (perbandingan Boolean; ketik x, >, y)",
        "hint_rel_le": "x ≤ y  (ketik x, Ctrl+9, y)",
        "hint_rel_ge": "x ≥ y  (ketik x, Ctrl+0, y)",
        "hint_rel_ne": "x ≠ y  (ketik x, Ctrl+3, y)",
        "btn_learn": "Pelajari & pakai",
        # ---- settings tab
        "card_appearance": "Umum", "lbl_language": "Bahasa", "lbl_theme": "Tema",
        "opt_theme_dark": "Gelap", "opt_theme_light": "Terang",
        "opt_topmost": "Selalu di depan",
        "card_typing": "Auto-ketik",
        "opt_greek": "Huruf Yunani via Ctrl+G", "opt_real_keys": "Tombol keyboard asli (bukan Unicode)",
        "tip_greek": "Mengetik huruf Latin, lalu Ctrl+G mengubahnya menjadi huruf Yunani",
        "tip_real_keys": "Mengirim kode tombol asli, yang paling cocok untuk Prime",
        "card_data": "Berkas pengaturan",
        "txt_settings_file": ("Pengaturan disimpan otomatis di samping berkas program "
                              "(latex_to_mathcad_settings.json)."),
        "btn_reset_settings": "Kembalikan ke bawaan",
        # ---- status bar messages
        "s_ready": "Siap. Tulis atau tempel LaTeX, lalu klik Konversi atau Ketik ke Mathcad.",
        "s_empty": "Input kosong.",
        "s_converted": "✔ Dikonversi & disalin. Untuk Mathcad Prime gunakan 'Ketik ke Mathcad' "
                       "(paste biasa hanya jadi string).",
        "s_clip_empty": "Clipboard kosong / bukan teks.",
        "s_copied": "Hasil disalin ke clipboard.",
        "s_cleared": "Dibersihkan. (Ctrl+Z mengembalikan teks di sebuah kotak.)",
        "s_history": "Riwayat {i}/{n} (hasil disalin ke clipboard).",
        "s_nothing_undo": "Tidak ada lagi yang bisa diurungkan.",
        "s_nothing_redo": "Tidak ada lagi yang bisa diulangi.",
        "s_unsupported_sexpr": "Rumus berisi Σ/∫/lim; belum bisa dikonversi ke format Prime.",
        "s_sexpr_failed": "Gagal mengonversi ke format Prime. Lihat Catatan.",
        "s_sexpr_copied": "✔ Format Prime disalin. Di Prime: math region kosong → Ctrl+V.",
        "s_unsupported_type": "Rumus berisi Σ/∫/lim; ketik bagian itu manual di Prime.",
        "s_plan_failed": "Gagal menyusun rencana ketikan. Lihat Catatan.",
        "s_type_cancelled": "■ Dibatalkan.",
        "s_type_done": "✔ Selesai diketik. Cek hasilnya di Mathcad.",
        "s_type_focus_back": "Fokus kembali ke program ini, pengetikan dihentikan.",
        "s_type_failed": "Gagal mengirim tombol: {err}",
        "s_typing": "Mengetik {i}/{n} …  (klik Stop untuk membatalkan)",
        "s_type_not_clicked": "Jendela Mathcad belum diklik. Ulangi, lalu klik area kosong di "
                              "worksheet Prime sebelum hitungan habis.",
        "s_type_windows_only": "Auto-ketik hanya tersedia di Windows. {err}",
        "s_countdown": "Klik area KOSONG di worksheet Mathcad Prime … mulai dalam {n} detik",
        "s_fill_find": "Isi kolom 'Cari' dulu.",
        "s_bad_regex": "Regex tidak valid: {err}",
        "s_bad_replacement": "Pola ganti tidak valid: {err}",
        "s_not_found": "Tidak ditemukan.", "s_found_at": "Ditemukan di posisi {pos}.",
        "s_replaced": "{n} penggantian.",
        "s_rule_added": "Ditambahkan ke aturan tetap (jangan lupa klik 'Simpan aturan').",
        "s_rules_saved": "Aturan disimpan ({path}).",
        "s_rules_save_failed": "Aturan dipakai tetapi gagal disimpan ke file: {err}",
        "s_sample_copied": "Contoh disalin: {sample}",
        "s_candidate_copied": "Kandidat {n}/{total} disalin: {sample}",
        "s_learned": "✔ Template '{item}' dipelajari: {tpl}",
        "s_template_updated": "Template {item} diperbarui dari teks Prime.",
        "s_settings_reset": "Pengaturan dikembalikan ke bawaan.",
        "dlg_sym_title": "Ada simbol yang perlu diperbaiki",
        "dlg_sym_body": ("Ditemukan simbol berikut di input LaTeX:\n\n{items}\n\n"
                         "Perbaiki otomatis sekarang?\n(, jadi .   [ jadi (   ] jadi ) )"),
        "s_sym_fixed": "✔ {n} simbol diperbaiki di input.",
        # ---- notes
        "n_none": "Tidak ada peringatan.",
        "n_rules_applied": "Aturan ganti diterapkan: {n} penggantian.",
        "n_plan": "Rencana ketikan ([→] = tombol panah kanan):\n{plan}",
        "n_cannot_type": "Tidak bisa diketik otomatis: {err}",
        "n_cannot_convert": "Tidak bisa dikonversi: {err}",
        "n_unverified": "⚠ Belum terverifikasi di Prime (tebakan): {items}. Kalau hasil paste "
                        "salah, buka tab Kalibrasi.",
        "n_all_verified": "✔ Seluruh bagian memakai sintaks yang sudah terverifikasi di Prime.",
        "n_eq_hint": "Tanda '=' menjadi (@EQ …) (persamaan). Centang ':=' untuk definisi.",
        # ---- unverified construct names
        "u_div": "pembagian", "u_sub": "pengurangan", "u_define": "definisi :=",
        "u_neg": "minus unary", "u_rel": "relasi {op}", "u_sqrt": "akar kuadrat",
        "u_nroot": "akar pangkat n", "u_abs": "nilai mutlak |x|", "u_index": "indeks array x[n] (pakai Kalibrasi > index)", "u_nderiv": "turunan tingkat tinggi (bersarang)", "u_deg": "tanda derajat (30 deg)", "u_fact": "faktorial n!", "u_pdiff": "turunan parsial (disalin sebagai d/dx biasa)",
        # ---- converter messages
        "end_of_text": "akhir teks",
        "w_deriv_order": "Tingkat turunan di pembilang ({num}) berbeda dari penyebut ({den}); "
                         "yang dipakai tingkat dari penyebut.",
        "w_deriv_symbolic": "Tingkat turunan simbolik (mis. n) dibiarkan sebagai diff(f,x,n); "
                            "Mathcad membutuhkan tingkat berupa angka, ubah manual.",
        "w_binom": "\\binom diubah ke combin(n,k).",
        "w_accent": "Aksen \\{name} dibuang (Mathcad tidak bisa lewat paste teks).",
        "w_bigop": "\\{name} (jumlah/integral) tidak bisa di-paste sebagai teks biasa; ketik "
                   "ulang operatornya di Mathcad (Ctrl+Shift+4 / & / Ctrl+I).",
        "w_lim": "\\lim tidak didukung sebagai teks; ketik ulang di Mathcad.",
        "w_unknown_cmd": "Perintah \\{name} tidak dikenal, dibiarkan sebagai '{name}'.",
        "w_prime": "Tanda prime/apostrof (') diganti 'prime' (mis. x' → xprime) karena "
                   "apostrof tidak valid di nama variabel Mathcad. Ubah lewat Cari & Ganti "
                   "bila ingin nama lain.",
        "w_dots": "Titik-titik \\{name} dihapus; Mathcad tidak bisa mengetik '…' di dalam rumus.",
        "w_symbol_unicode": "Simbol seperti ∈ ∪ ∧ ¬ ⇒ → diketik sebagai karakter Unicode. Prime tidak \
selalu menganggapnya operator, jadi periksa hasilnya.",
        "w_op_limits": "Subskrip di bawah \\{name} (mis. 'min terhadap x') dibuang; Mathcad tidak \
punya notasi itu.",
        "w_sum_cond": "Syarat indeks pada \\{name} tidak didukung; hanya variabelnya yang dipakai. \
Isi batasnya manual di Mathcad.",
        "w_cases_default": "Kasus terakhir punya syarat; nilai 0 dipakai sebagai 'selain itu' pada \
if(...).",
        "w_brace_label": "Keterangan/label dari \\{name} dibuang (hanya ekspresinya yang dipakai).",
        "w_sup_inf": "\\{name} diubah menjadi {to}(...); pastikan sesuai maksud Anda.",
        "w_opname_kept": "\\{name} tidak punya padanan di Mathcad dan dibiarkan sebagai nama fungsi.",
        "w_substack": "\\substack diratakan menjadi daftar dipisah koma.",
        "w_oint": "\\{name} diubah menjadi integral biasa (Mathcad tidak punya integral kontur).",
        "w_norm": "Norma ‖x‖ diubah menjadi norm2(x).",
        "e_sym_sexpr": "Simbol '{sym}' belum bisa dikonversi ke format teks Prime (@); gunakan \
'Type into Mathcad'.",
        "w_tuple": "Daftar berkoma di dalam kurung, mis. himpunan {a, b}, diketik apa adanya; \
Mathcad tidak punya notasi himpunan.",
        "w_pm": "Mathcad tidak punya operator ±; pecah menjadi dua rumus (+ dan -).",
        "w_def_fallback": "':=' diganti '=' karena sisi kiri bukan nama variabel/fungsi "
                          "sederhana (Mathcad menolak definisi seperti itu). Ini dianggap "
                          "persamaan/identitas.",
        "w_multiline_type": "Ada beberapa baris; hanya baris pertama yang diketik. Ketik baris "
                            "berikutnya dengan menjalankan ulang.",
        "w_multiline_conv": "Ada beberapa baris; hanya baris pertama yang dikonversi (satu "
                            "rumus per paste).",
        "w_nderiv_type": "Turunan tingkat tinggi diketik sebagai operator turunan bersarang; "
                         "tombol operator adalah KEY_DERIV di peta tombol (belum terverifikasi).",
        "w_nderiv_native": "Turunan tingkat tinggi diketik dengan operator nth-derivative Prime "
                           "(Ctrl+Shift+D, lalu variabel, tingkat, fungsi). Navigasi antar kotak belum "
                           "terverifikasi: ubah NDERIV_NAV (RIGHT atau TAB) di peta tombol bila perlu.",
        "w_vmatrix": "vmatrix / Vmatrix (garis tegak di sekitar matriks) diubah menjadi "
                     "det(matriks) / norm2(matriks), yaitu |A| di Prime.",
        "w_matrix_keys": "Pengetikan matriks: Ctrl+M (1x1), baris pertama diisi sambil menambah "
                         "kolom dengan Shift+Spasi, baris berikutnya ditambah dengan Shift+Enter "
                         "(mendarat di kolom yang sama) lalu diisi zig-zag: kanan->kiri, "
                         "kiri->kanan, dst. Mundur dari sel terisi memakai panah Kiri sebanyak "
                         "isi + MAT_LEFT_EXTRA (belum terverifikasi); ubah konstanta MAT_* bila "
                         "Prime-mu beda. Mode MAT_ORDER=\"column\": matriks kosong dibangun dulu, "
                         "lalu diisi zig-zag per kolom dengan panah Bawah/Atas/Kanan.",
        "w_bigop_keys": "Pengetikan Sigma/Pi/Integral/Limit: shortcut membuka operator, lalu panah "
                        "Kanan biasa berpindah antar blok biru (Sigma/Pi: bawah, 2x Kanan, atas, "
                        "Kanan, isi; Integral: bawah, atas, fungsi, dx; Limit: variabel, nilai, "
                        "arah, fungsi). Ubah konstanta SUM_/INT_/LIM_ di peta tombol bila Prime-mu "
                        "beda. Isi boleh tanpa kurung kurawal; berakhir di =, koma, kurung penutup, + atau - (sum/prod/lim) atau di dx (integral).",
        "w_sub_keys": "Subskrip literal diketik dengan Ctrl+- (toggle): nama, Ctrl+-, subskrip, "
                      "Ctrl+- (kembali ke baseline). Titik '.' biasa hanya menghasilkan nama x.i "
                      "(tidak turun). Set SUB_MODE = \"dot\" di peta tombol untuk cara lama.",
        "e_bigop_sexpr": "Sigma/Pi/Integral/Limit belum bisa dikonversi ke format teks Prime (@); "
                         "pakai 'Ketik ke Mathcad'.",
        "e_matrix_size": "Jumlah sel matriks tidak cocok dengan baris x kolom.",
        "e_matrix_sexpr": "Matriks belum bisa dikonversi ke format teks Prime (@) (bentuk aslinya "
                          "belum diketahui); pakai 'Ketik ke Mathcad'.",
        "n_mat_paste": "⚠ Matriks mat(r,c,...) hanya bentuk perantara untuk auto-ketik. Kalau "
                       "di-paste ke Prime hasilnya cuma string. Pakai 'Ketik ke Mathcad'.",
        "e_char": "Karakter '{ch}' (posisi {pos}) tidak bisa diketik otomatis.",
        "e_expected": "Diharapkan '{val}' tetapi ditemukan '{found}'.",
        "e_leftover": "Sisa teks tak terduga: '{text}'.",
        "e_incomplete": "Rumus tidak lengkap / karakter tak terduga: '{found}'.",
        "e_node": "Node tidak dikenal: {kind}",
        "e_no_text_type": "Tidak ada teks untuk diketik.",
        "e_no_text_conv": "Tidak ada teks untuk dikonversi.",
        "e_deriv_order": "Tingkat turunan harus berupa bilangan bulat positif.",
        "e_learn_format": "Teks bukan format (@…) / (…): harus diawali tanda kurung buka.",
        "e_learn_var": "Variabel contoh '{name}' tidak ditemukan di teks. Pastikan contoh di "
                       "Prime persis: {example}",
        # ---- help
        "help_text": """\
## Fungsi program
Mengubah rumus LaTeX (misalnya hasil salinan dari AI, makalah, atau Word) menjadi bentuk yang dipahami Mathcad Prime. Semua fitur ada di satu jendela ini.

## Kenapa paste biasa tidak jalan di Prime
Prime tidak mengerti teks matematika biasa (V.c, a/b, dst). Teks itu masuk sebagai string bertanda kutip. Prime justru mengerti format teks internalnya sendiri (mirip Lisp: (@EQ …), (@APPLY …)) dan mengerti ketikan keyboard.

## Cara 1: Ketik ke Mathcad (tab Konversi, panel kanan)
1. Tulis atau tempel LaTeX di kotak Input.
2. Klik "Ketik ke Mathcad".
3. Sebelum hitungan mundur habis, klik area KOSONG di worksheet Prime.
4. Jangan sentuh keyboard/mouse sampai selesai. "Stop" membatalkan.
Program menekan tombol seperti kamu mengetik sendiri: Ctrl+- = subskrip, / = pecahan, ^ = pangkat, \\ = akar, : = :=, ? = operator turunan, dan tombol → untuk keluar dari subskrip, pangkat, penyebut, akar, atau turunan.

## Cara 2: Teks format Prime (@)
1. Klik "Salin format Prime (@)".
2. Di Prime buat math region KOSONG, lalu tekan Ctrl+V.
Bagian yang masih tebakan (mis. akar, minus unary) ditandai di Catatan; uji di tab Kalibrasi bila hasilnya salah.

## Turunan
Tingkat berapa pun, biasa maupun parsial, dikenali dari struktur pecahannya:
    \\frac{dy}{dt}                    turunan pertama
    \\frac{d^2y}{dt^2}                turunan kedua
    \\frac{d^3 y}{dx^3}               turunan ketiga (dan seterusnya)
    \\frac{\\partial^2 u}{\\partial x^2}      turunan parsial
    \\frac{\\partial^2 u}{\\partial x \\partial y}   turunan parsial campuran
    \\frac{d^2}{dt^2} f(t)             operator diikuti ekspresi
    \\frac{\\mathrm{d}^2 y}{\\mathrm{d}t^2}   huruf d tegak juga dikenali
Tingkat tinggi ditulis sebagai turunan pertama yang bersarang, sintaks yang sudah terverifikasi di Prime. Tingkat simbolik seperti d^n y / dx^n dibiarkan sebagai diff(y,x,n) dan perlu diedit manual.

## Kalau hasilnya salah
• Baca kotak Catatan: berisi peringatan dan rencana ketikan (tombol yang ditekan).
• Naikkan "Jeda tombol" (80-120 ms) kalau Prime tertinggal / karakter hilang.
• Pecahan tampil dengan kurung di pembilang; itu normal.
• Kalau tombol di Prime kamu beda, ubah konstanta KEY_* di bagian "PETA TOMBOL MATHCAD PRIME" pada file .py.
• ≤ ≥ ≠ memakai Ctrl+9 / Ctrl+0 / Ctrl+3; ubah di CHORDS jika perlu.

## Batasan
• ± tidak bisa diketik otomatis; ketik manual di Prime. Σ, ∏, ∫, dan lim diketik lewat shortcut + panah Kanan; kurung kurawal di sekitar isinya opsional, mis. \\sum_{i=1}^{n}{i^2}, \\int_{0}^{1}{x^2}\\,dx, \\lim_{x \\to 0^+}{\\frac{\\sin x}{x}}.
• Auto-ketik hanya Windows. Hanya baris pertama yang diketik per proses.
• Notasi y', \\dot{y} (turunan tanpa variabel) tidak dikonversi; pakai \\frac{dy}{dt}.

## Cari & Ganti (Ctrl+H)
Ganti huruf/simbol di input atau hasil (kata utuh, regex, Undo). "Jadikan aturan tetap" menambahkan pasangan ke tab Aturan ganti, tempat aturan (lama => baru) disimpan dan diterapkan otomatis sebelum setiap konversi.

## Soal ':='
Mathcad hanya menerima definisi untuk nama atau f(x). Untuk tan(2θ) = ..., identitas, atau turunan di kiri, program otomatis memakai '=' (@EQ).

## Pintasan
Ctrl+Enter konversi · Ctrl+H cari & ganti · Alt+← / Alt+→ riwayat · Ctrl+Z / Ctrl+Y urungkan / ulangi · F1 bantuan ini · Esc tutup panel cari

## Bahasa
Pilih English atau Bahasa Indonesia lewat EN / ID di header atau di Pengaturan. Sintaks matematika, LaTeX, dan keluaran Mathcad tidak pernah diterjemahkan.
""",
    },
}


def set_language(code):
    _LANG["code"] = code if code in I18N else "en"


def get_language():
    return _LANG["code"]


def tr(key, **kw):
    """Teks terjemahan untuk 'key' pada bahasa aktif (cadangan: English, lalu kuncinya)."""
    text = I18N.get(_LANG["code"], {}).get(key) or I18N["en"].get(key) or key
    if not kw:
        return text
    return text.format(**{k: _fmt(v) for k, v in kw.items()})


def _fmt(v):
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x) for x in v)
    return str(v)


class Msg:
    """Pesan yang diterjemahkan saat ditampilkan (bukan saat dibuat)."""
    __slots__ = ("key", "params")

    def __init__(self, key, **params):
        self.key, self.params = key, params

    def __str__(self):
        return tr(self.key, **self.params)

    __repr__ = __str__

    def _sig(self):
        def norm(v):
            if isinstance(v, Msg):
                return v._sig()
            if isinstance(v, (list, tuple)):
                return tuple(norm(x) for x in v)
            return str(v)
        return (self.key, tuple(sorted((k, norm(v)) for k, v in self.params.items())))

    def __eq__(self, other):
        return isinstance(other, Msg) and self._sig() == other._sig()

    def __hash__(self):
        return hash(self._sig())


# ----------------------------------------------------------------------------
# Tabel simbol
# ----------------------------------------------------------------------------
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "θ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "varpi": "π", "rho": "ρ", "varrho": "ρ", "sigma": "σ",
    "varsigma": "ς", "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ",
    "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ",
    "Omega": "Ω",
}

SYMBOLS = {
    "cdot": "*", "times": "*", "ast": "*", "div": "/",
    "pm": "±", "mp": "∓",
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠",
    "approx": "≈", "equiv": "≡", "infty": "∞", "partial": "∂",
    "degree": "°", "circ": "°", "prime": "'", "ldots": "...", "cdots": "...",
    "to": "→", "rightarrow": "→", "leftarrow": "←",
    "sum": "Σ", "prod": "∏", "int": "∫", "nabla": "∇",
    "lbrace": "(", "rbrace": ")", "lbrack": "[", "rbrack": "]",
    "langle": "(", "rangle": ")", "lvert": "|", "rvert": "|",
    "lfloor": "floor(", "rfloor": ")", "lceil": "ceil(", "rceil": ")",
}

FUNCTIONS = {
    "sin": "sin", "cos": "cos", "tan": "tan", "cot": "cot", "sec": "sec",
    "csc": "csc", "arcsin": "asin", "arccos": "acos", "arctan": "atan",
    "sinh": "sinh", "cosh": "cosh", "tanh": "tanh", "ln": "ln", "log": "log",
    "exp": "exp", "min": "min", "max": "max", "lg": "log", "det": "det",
}

# Variabel untuk ∇² (Laplace). Tambahkan "z" untuk 3D; "z" otomatis ikut bila rumus memakai z.
NABLA_VARS = ("x", "y")
# ^T (T kapital sebagai pangkat) dianggap transpose matriks; ditulis Ctrl+1 di Prime. False: pangkat biasa.
TRANSPOSE_T = True
TRANSPOSE_CHORD = ("c", "1")

KNOWN_FUNC_NAMES = {
    "sin", "cos", "tan", "cot", "sec", "csc", "asin", "acos", "atan", "sinh",
    "cosh", "tanh", "ln", "log", "exp", "min", "max", "abs", "sqrt", "root",
    "floor", "ceil", "mod", "if", "sum", "det", "tr", "mat",
}

# Perintah yang dibuang begitu saja (spasi, ukuran, gaya)
DROP_COMMANDS = {
    "displaystyle", "textstyle", "scriptstyle", "scriptscriptstyle", "limits", "nolimits",
    "enspace", "thinspace", "medspace", "thickspace", "negthinspace", "negmedspace",
    "negthickspace", "mathstrut", "strut", "relax", "allowbreak", "leavevmode", "protect",
    "middle", "bigm", "Bigm", "biggm", "Biggm", "ensuremath", "normalsize", "small",
    "footnotesize", "large", "Large",
    "quad", "qquad", "left", "right", "big", "Big", "bigg", "Bigg",
    "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr", "hfill", "nonumber",
    "noindent", "centering",
}

# Perintah yang hanya mengambil isi dalam kurung kurawal
PASS_ARG_COMMANDS = {
    "mathrm", "mathbf", "mathit", "mathsf", "mathtt", "mathcal", "mathbb",
    "boldsymbol", "bm", "textbf", "textit", "textrm", "operatorname",
    "vec", "hat", "tilde", "bar", "overline", "underline", "dot", "ddot",
    "overrightarrow", "mbox", "boxed", "cancel", "bcancel", "xcancel", "sout", "mathop",
    "mathrel", "mathbin", "mathord", "mathpunct", "mathclose", "mathopen", "widehat",
    "widetilde", "overleftarrow", "overleftrightarrow", "underrightarrow", "underleftarrow",
    "overbracket", "underbracket", "mathscr", "mathfrak", "pmb", "unit", "si", "SI_",
}
# Perintah yang isinya adalah KATA/NAMA utuh (kN, argmax, ...): jangan dipecah jadi a*b*c
WORD_COMMANDS = {"mathrm", "mathit", "mathsf", "mathtt", "textrm", "textit", "textbf",
                 "operatorname", "mbox", "text", "textnormal"}

# Tambahan agar SEMUA bentuk LaTeX umum terbaca (lihat juga Converter.command)
GREEK.update({"varkappa": "κ"})

SYMBOLS.update({
    # relasi
    "ll": "≪", "gg": "≫", "sim": "∼", "simeq": "≃", "cong": "≅", "propto": "∝",
    "varpropto": "∝", "parallel": "∥", "perp": "⊥", "bot": "⊥",
    "approxeq": "≈", "thickapprox": "≈", "asymp": "≍", "doteq": "≐", "triangleq": "≜",
    "prec": "≺", "succ": "≻", "preceq": "⪯", "succeq": "⪰",
    "leqslant": "≤", "geqslant": "≥", "leqq": "≤", "geqq": "≥",
    "nless": "≮", "ngtr": "≯", "nleq": "≰", "ngeq": "≱", "nleqslant": "≰", "ngeqslant": "≱",
    "nequiv": "≢", "nsim": "≁", "napprox": "≉", "ncong": "≇", "nmid": "∤", "nparallel": "∦",
    # himpunan
    "in": "∈", "notin": "∉", "ni": "∋", "owns": "∋",
    "subset": "⊂", "supset": "⊃", "subseteq": "⊆", "supseteq": "⊇",
    "subsetneq": "⊊", "supsetneq": "⊋", "nsubseteq": "⊈", "varsubsetneq": "⊊",
    "cup": "∪", "cap": "∩", "setminus": "∖", "smallsetminus": "∖",
    "bigcup": "∪", "bigcap": "∩", "emptyset": "∅", "varnothing": "∅",
    # logika
    "forall": "∀", "exists": "∃", "nexists": "∄", "neg": "¬", "lnot": "¬",
    "land": "∧", "wedge": "∧", "bigwedge": "∧", "lor": "∨", "vee": "∨", "bigvee": "∨",
    "therefore": "∴", "because": "∵",
    "Rightarrow": "⇒", "Longrightarrow": "⇒", "implies": "⇒", "Leftarrow": "⇐",
    "impliedby": "⇐", "Leftrightarrow": "⇔", "iff": "⇔",
    "leftrightarrow": "↔", "longleftrightarrow": "↔", "mapsto": "↦", "longmapsto": "↦",
    "longrightarrow": "→", "longleftarrow": "←", "hookrightarrow": "→",
    # operator & simbol lain
    "oplus": "⊕", "bigoplus": "⊕", "ominus": "⊖", "otimes": "⊗", "bigotimes": "⊗", "odot": "⊙",
    "star": "⋆", "dagger": "†", "dag": "†", "ddagger": "‡", "ddag": "‡", "bullet": "•",
    "centerdot": "*", "cdotp": "*", "angle": "∠",
    "hbar": "ℏ", "hslash": "ℏ", "ell": "ℓ", "aleph": "ℵ", "wp": "℘",
    "imath": "i", "jmath": "j",
    "top": "T", "intercal": "T",            # A^\top  ->  A^T  ->  transpose
})

# Titik-titik: tidak bisa diketik di dalam rumus Mathcad -> dibuang + peringatan
DOTS_COMMANDS = {"ldots", "cdots", "dots", "dotsc", "dotsb", "dotsm", "dotsi", "hdots",
                 "vdots", "ddots", "mathellipsis"}
for _k in ("ldots", "cdots"):
    SYMBOLS.pop(_k, None)

FUNCTIONS.update({
    "coth": "coth", "sech": "sech", "csch": "csch", "arg": "arg", "gcd": "gcd", "lcm": "lcm",
    "Re": "Re", "Im": "Im", "sgn": "sign", "arccot": "acot", "arcsec": "asec", "arccsc": "acsc",
    "sup": "max", "inf": "min",
    "ker": "ker", "dim": "dim", "hom": "hom", "Pr": "Pr", "limsup": "limsup", "liminf": "liminf",
})
SUPINF_MAP = {"sup": "max", "inf": "min"}
OPNAMES_KEPT = {"ker", "dim", "hom", "Pr", "limsup", "liminf"}
LIMIT_SUB_FUNCS = {"min", "max", "sup", "inf", "limsup", "liminf"}
KNOWN_FUNC_NAMES.update({
    "coth", "sech", "csch", "acot", "asec", "acsc", "asinh", "acosh", "atanh", "arg", "gcd",
    "lcm", "sign", "erf", "combin", "permut", "round", "trunc", "norm2", "diff", "pdiff",
    "limit", "integral", "norm1", "normi", "normf", "normp",
})
# Nama operator di \operatorname{..}/\mathrm{..} yang punya nama lain di Mathcad
OPNAME_ALIASES = {"sgn": "sign", "arcsinh": "asinh", "arccosh": "acosh", "arctanh": "atanh",
                  "arsinh": "asinh", "arcosh": "acosh", "artanh": "atanh", "arccot": "acot",
                  "arcsec": "asec", "arccsc": "acsc", "tg": "tan", "ctg": "cot", "sh": "sinh",
                  "ch": "cosh", "th": "tanh", "arcsin": "asin", "arccos": "acos",
                  "arctan": "atan"}

# Simbol Unicode non-ASCII yang boleh masuk ke parser (diketik lewat karakter Unicode).
SYM_REL = set("≪≫∼≃≅∝∥⊥∈∉∋∌⊂⊃⊆⊇⊊⊋⊄⊈≮≯≰≱≺≻⪯⪰≜≍≐≢≁≉≇∤∦→←↔⇒⇐⇔↦∴∵⊕⊖⊗⊙∧∨")
SYM_ADD = set("∪∩∖")
SYM_PREFIX = set("¬∀∃∄∠∪∩∧∨⊕⊗")      # ∪∩∧∨⊕⊗ juga muncul sebagai \\bigcup dst. (awalan)
SYM_ATOM = set("∅ℏℓℵ⋆†‡•∇∂℘")
SYM_ALL = SYM_REL | SYM_ADD | SYM_PREFIX | SYM_ATOM
# Negasi: \not=  \not\in  ...
NOT_MAP = {"=": "≠", "<": "≮", ">": "≯", "in": "∉", "ni": "∌", "subset": "⊄", "subseteq": "⊈",
           "equiv": "≢", "leq": "≰", "le": "≰", "geq": "≱", "ge": "≱", "sim": "≁",
           "approx": "≉", "exists": "∄", "mid": "∤", "parallel": "∦", "cong": "≇",
           "∈": "∉", "≤": "≰", "≥": "≱", "≡": "≢"}

TEXT_COMMANDS = {"text", "mbox", "textnormal"}
SKIP_ARG_COMMANDS = {"label", "tag", "hspace", "vspace", "qedhere", "color", "phantom",
                     "hphantom", "vphantom", "smash", "hspace*", "vspace*", "textcolor_",
                     "tag*", "ref", "eqref", "cite"}

# Pemisah tak terlihat (U+2063) di antara huruf nama multi-huruf (kN, argmax, dim, ...)
# supaya add_implicit_mult TIDAK memecahnya menjadi k*N / a*r*g*m*a*x. Dibuang di akhir postprocess().
MARK = "\u2063"

# "Atom" = satu angka atau satu nama variabel (BUKAN campuran seperti 2a)
ATOM_RE = re.compile(r"^(\d+(\.\d+)?|[A-Za-zα-ωΑ-Ω∞][\w.α-ωΑ-Ω\u2063]*)$")


# ----------------------------------------------------------------------------
# Helper parser
# ----------------------------------------------------------------------------
def read_group(s, i):
    """s[i] == '{' -> (isi, indeks_setelah_penutup)"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    return s[i + 1:], len(s)


def read_bracket(s, i):
    """s[i] == '[' -> (isi, indeks_setelah_penutup)"""
    j = s.find("]", i)
    if j == -1:
        return s[i + 1:], len(s)
    return s[i + 1:j], j + 1


def read_arg(s, i):
    """Baca satu argumen LaTeX: {..}, \\perintah, atau satu karakter."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        return read_group(s, i)
    if s[i] == "\\":
        m = re.match(r"\\[A-Za-z]+|\\.", s[i:])
        return m.group(0), i + len(m.group(0))
    return s[i], i + 1


def is_wrapped(t):
    """True jika t sudah dibungkus satu pasang kurung terluar."""
    if not (t.startswith("(") and t.endswith(")")):
        return False
    depth = 0
    for k, ch in enumerate(t):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and k != len(t) - 1:
                return False
    return True


# Nama polos >=2 huruf (mis. "dx", "ab") nanti dipecah menjadi perkalian (d*x) oleh
# add_implicit_mult, sehingga HARUS dibungkus kurung agar pembagi/pangkat tidak bergeser:
#   x/dx -> x/d*x (salah)    x/(dx) -> x/(d*x) (benar)
PLAIN_MULTI_RE = re.compile(r"^[A-Za-zα-ωΑ-Ω]{2,}$")
# Pangkat tanpa kurung hanya aman untuk satu token: angka, satu huruf, atau nama bersubskrip.
BARE_EXP_RE = re.compile(r"^(?:\d+(?:\.\d+)?|[A-Za-zα-ωΑ-Ω](?:[_.][A-Za-z0-9α-ωΑ-Ω]+)?)$")


def wrap(t):
    t = t.strip()
    if (ATOM_RE.match(t) and not PLAIN_MULTI_RE.match(t)) or is_wrapped(t):
        return t
    return "(" + t + ")"


# ----------------------------------------------------------------------------
# Konverter utama
# ----------------------------------------------------------------------------
class Converter:
    def __init__(self, subscript="underscore", define=False,
                 implicit_mult=True, unicode_greek=True, log_base="ln"):
        self.log_base = log_base            # 'ln' (ln(x)/ln(b)) | 'comma' log(x,b)
        self.subscript = subscript          # 'underscore' | 'literal' | 'drop'
        self.define = define                # '=' -> ':='
        self.implicit_mult = implicit_mult  # ab -> a*b
        self.unicode_greek = unicode_greek
        self.warnings = []

    # ---- matriks: \begin{pmatrix} a & b \\ c & d \end{pmatrix} -> \mat{2}{2}{a}{b}{c}{d} ----
    _MAT_RE = re.compile(r"\\begin\{([pbBvV]?)(?:small)?matrix\*?\}(?:\[[^\]]*\])?(.*?)"
                         r"\\end\{[pbBvV]?(?:small)?matrix\*?\}", re.S)
    _ARR_RE = re.compile(r"\\begin\{(?:array|subarray)\}\s*(?:\[[a-z]\])?\s*\{[^{}]*\}(.*?)"
                         r"\\end\{(?:array|subarray)\}", re.S)
    _CASES_RE = re.compile(r"\\begin\{(?:d|r)?cases\*?\}(.*?)\\end\{(?:d|r)?cases\*?\}", re.S)

    def _grid_to_mat(self, body):
        body = body.replace("\\hline", " ")
        rows = [r for r in re.split(r"\\\\", body) if r.strip()]
        grid = [[c.strip() for c in r.split("&")] for r in rows]
        if not grid:
            return None
        ncol = max(len(r) for r in grid)
        for r in grid:
            r += ["0"] * (ncol - len(r))
        return "\\mat{%d}{%d}%s" % (len(grid), ncol,
                                    "".join("{" + (c or "0") + "}" for r in grid for c in r))

    def matrix_envs(self, s):
        def repl(m):
            kind, body = m.group(1), m.group(2)
            mat = self._grid_to_mat(body)
            if mat is None:
                return " "
            if kind in ("v", "V"):
                # |A| = determinan, ||A|| = norma: bungkus dengan fungsi yang diketik Prime sebagai |..|
                self.warnings.append(Msg("w_vmatrix"))
                return ("\\det{%s}" if kind == "v" else "\\norm{%s}") % mat
            return mat
        s = self._MAT_RE.sub(repl, s)
        return self._ARR_RE.sub(lambda m: self._grid_to_mat(m.group(1)) or " ", s)

    # ---- fungsi bersyarat: \begin{cases} a & x>0 \\ b & \text{otherwise} \end{cases}
    #      ->  if(x>0, a, b)   (bersarang untuk >2 kasus)
    _COND_LEAD = re.compile(r"^\s*(?:\\(?:text|mbox|textrm|mathrm)\s*\{\s*(?:if|for|when|jika|untuk)\s*\}"
                            r"|(?:if|for|when|jika|untuk)\b)[\s,:]*", re.I)
    _OTHERWISE = re.compile(r"^\s*(?:\\(?:text|mbox|textrm|mathrm)\s*\{\s*(?:otherwise|else|lainnya|"
                            r"selainnya|selain itu)\s*\}|otherwise|else|lainnya|selainnya)\s*[.,]?\s*$", re.I)

    def cases_envs(self, s):
        def repl(m):
            items = []
            for r in re.split(r"\\\\", m.group(1)):
                r = r.replace("\\hline", " ")
                if not r.strip():
                    continue
                parts = r.split("&", 1)
                val = parts[0].strip()
                cond = re.sub(r"[\s,.;]+$", "", parts[1].strip()) if len(parts) > 1 else ""
                if cond and self._OTHERWISE.match(cond):
                    cond = ""
                else:
                    cond = self._COND_LEAD.sub("", cond).strip()
                items.append((val, cond))
            if not items:
                return " "
            val, cond = items[-1]
            if cond:
                self.warnings.append(Msg("w_cases_default"))
                expr = "\\ifelse{%s}{%s}{0}" % (cond, val)
            else:
                expr = "{%s}" % val
            for val, cond in reversed(items[:-1]):
                expr = "\\ifelse{%s}{%s}{%s}" % (cond, val, expr) if cond else "{%s}" % val
            return expr
        return self._CASES_RE.sub(repl, s)

    # ---- {a \over b}  {n \choose k}  (gaya TeX lama) -> \frac / \binom ----
    _OVER_RE = re.compile(r"\{([^{}]*?)\\(over|choose)(?![A-Za-z])([^{}]*?)\}")

    def over_choose(self, s):
        def sub(m):
            cmd = "frac" if m.group(2) == "over" else "binom"
            return "\\%s{%s}{%s}" % (cmd, m.group(1), m.group(3))
        for _ in range(30):
            t = self._OVER_RE.sub(sub, s)
            if t == s:
                break
            s = t
        # bentuk tingkat-atas tanpa kurung kurawal:  a \over b
        depth, k = 0, 0
        while k < len(s):
            c = s[k]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif depth == 0 and c == "\\":
                m = re.match(r"\\(over|choose)(?![A-Za-z])", s[k:])
                if m:
                    cmd = "frac" if m.group(1) == "over" else "binom"
                    return "\\%s{%s}{%s}" % (cmd, s[:k], s[k + m.end():])
            k += 1
        return s

    # ---- norma: \|x\|, \Vert x \Vert, \lVert x \rVert, \left\| .. \right\| -> \norm{..} ----
    _NORM_RE = re.compile(r"\\left\s*(?:\\Vert(?![A-Za-z])|\\lVert(?![A-Za-z])|\\\|)"
                          r"|\\right\s*(?:\\Vert(?![A-Za-z])|\\rVert(?![A-Za-z])|\\\|)"
                          r"|\\lVert(?![A-Za-z])|\\rVert(?![A-Za-z])|\\Vert(?![A-Za-z])|\\\|")

    def norm_bars(self, s):
        out, stack, pos = [], [], 0
        for m in self._NORM_RE.finditer(s):
            tok = m.group(0)
            out.append(s[pos:m.start()])
            pos = m.end()
            if tok.startswith("\\left") or tok == "\\lVert":
                kind = "open"
            elif tok.startswith("\\right") or tok == "\\rVert":
                kind = "close"
            else:
                kind = "close" if stack and stack[-1] == "amb" else "open"
            if kind == "open":
                stack.append("amb" if tok in ("\\|", "\\Vert") else "exp")
                out.append("\\norm{")
            else:
                if not stack:
                    return s
                stack.pop()
                out.append("}")
        out.append(s[pos:])
        return s if stack else "".join(out)

    _OPERAND = (r"(?:\{[^{}]*\}|\([^()]*\)|\\[A-Za-z]+|[A-Za-z0-9α-ωΑ-Ω.]+)"
                r"(?:_(?:\{[^{}]*\}|[A-Za-z0-9]))?(?:\^(?:\{[^{}]*\}|[A-Za-z0-9]))?")
    _BMOD_RE = re.compile(r"(" + _OPERAND + r")\s*\\bmod(?![A-Za-z])\s*(" + _OPERAND + r")")

    @staticmethod
    def _strip_outer(t):
        t = t.strip()
        if (t.startswith("{") and t.endswith("}")) or (t.startswith("(") and t.endswith(")")):
            return t[1:-1]
        return t

    def bmod(self, s):
        if "\\bmod" not in s:
            return s
        return self._BMOD_RE.sub(
            lambda m: "mod(%s,%s)" % (self._strip_outer(m.group(1)), self._strip_outer(m.group(2))), s)

    # ---- pembersihan awal ------------------------------------------------
    def preclean(self, s):
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = s.replace("\u00a0", " ")
        s = re.sub(r"(?<![\\0-9])%[^\n]*", "", s)               # komentar LaTeX (% ... akhir baris)
        s = re.sub(r"\\(?:no)?limits(?![A-Za-z])", " ", s)       # \sum\limits_{..}
        s = re.sub(r"\\\\\s*\[[^\]]*\]", r"\\\\", s)           # \\[2pt] (jarak antarbaris)
        if re.search(r"\{\}\s*[\^_]", s):                       # {}^{14}C : pra-skrip dibuang
            s = re.sub(r"\{\}\s*(?:[\^_](?:\{[^{}]*\}|[A-Za-z0-9])\s*)+", " ", s)
            self.warnings.append(Msg("w_brace_label", name="prescript"))
        s = self.over_choose(s)
        s = self.matrix_envs(s)
        s = self.cases_envs(s)
        if re.search(r"\\o+i*nt(?![A-Za-z])|\\oiiint|\\ointctrclockwise", s):
            self.warnings.append(Msg("w_oint", name="oint"))
        s = re.sub(r"\\oiiint(?![A-Za-z])|\\oiint(?![A-Za-z])|\\ointctrclockwise(?![A-Za-z])"
                   r"|\\ointclockwise(?![A-Za-z])|\\oint(?![A-Za-z])", r"\\int", s)
        s = re.sub(r"\\iiint(?![A-Za-z])", r"\\int\\int\\int", s)
        s = re.sub(r"\\iint(?![A-Za-z])", r"\\int\\int", s)
        s = self.bmod(s)
        s = re.sub(r"\\left\s*\[", r"\\left(", s)      # \left[ ... \right]  ->  kurung biasa
        s = re.sub(r"\\right\s*\]", r"\\right)", s)
        # delimiter display math
        s = re.sub(r"\$\$|\$", "", s)
        s = s.replace("\\[", "").replace("\\]", "")
        s = s.replace("\\(", "").replace("\\)", "")
        s = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", s)
        # perintah spasi: \, \; \: \! \<spasi>   (tapi BUKAN \\ + spasi = baris baru)
        s = re.sub(r"(?<!\\)\\[,;:! ]", " ", s)
        # bersihkan karakter unicode "aneh" dari Word/Gemini
        s = (s.replace("−", "-").replace("–", "-").replace("—", "-")
              .replace("×", "*").replace("·", "*").replace("⋅", "*")
              .replace("÷", "/"))
        s = self.norm_bars(s)
        s = self.abs_bars(s)
        return s.strip()

    # ---- nilai mutlak: \left\vert..\right\vert, \lvert..\rvert, |..| -> \abs{..} ----
    _BAR_RE = re.compile(r"\\left\s*(?:\\vert(?![A-Za-z])|\\lvert(?![A-Za-z])|\|)"
                         r"|\\right\s*(?:\\vert(?![A-Za-z])|\\rvert(?![A-Za-z])|\|)"
                         r"|\\lvert(?![A-Za-z])|\\rvert(?![A-Za-z])|\\vert(?![A-Za-z])"
                         r"|(?<!\\)\|")

    def abs_bars(self, s):
        out, stack, pos = [], [], 0
        for m in self._BAR_RE.finditer(s):
            tok = m.group(0)
            out.append(s[pos:m.start()])
            pos = m.end()
            if tok.startswith("\\left") or tok == "\\lvert":
                kind = "open"
            elif tok.startswith("\\right") or tok == "\\rvert":
                kind = "close"
            else:                                   # '|' atau \vert: buka/tutup bergantian
                kind = "close" if stack and stack[-1] == "amb" else "open"
            if kind == "open":
                stack.append("amb" if tok in ("|", "\\vert") else "exp")
                out.append("\\abs{")
            else:
                if not stack:
                    return s                        # tidak berpasangan: biarkan apa adanya
                stack.pop()
                out.append("}")
        out.append(s[pos:])
        return s if stack else "".join(out)

    # ---- kata/nama utuh: kN, argmax, dim ... jangan dipecah menjadi k*N ----
    _WORD_RE = re.compile(r"[A-Za-zα-ωΑ-Ω]{2,}")

    @staticmethod
    def _known_word(w):
        return w.lower() in KNOWN_FUNC_NAMES      # sama dengan yang dihormati add_implicit_mult

    def _protect_words(self, t, alias=False):
        def one(m):
            w = m.group(0)
            if alias and w in OPNAME_ALIASES:
                return OPNAME_ALIASES[w]
            if self._known_word(w):
                return w
            return MARK.join(w)
        return self._WORD_RE.sub(one, t)

    _FRAC_NEXT_CMDS = {"frac", "dfrac", "tfrac", "cfrac", "sqrt", "left", "binom", "mathrm",
                       "operatorname", "abs", "mat", "norm"}

    def _frac_context(self, s, i, left):
        """(awalan, bungkus) untuk \\frac biasa. Pecahan yang menempel pada operan lain harus
        dikurung: a\\frac{1}{2} -> a*(1/2)  (bukan a1/2),  \\frac{1}{2}\\pi -> (1/2)π  (bukan 1/2π,
        yang di Mathcad terbaca 1/(2π))."""
        pre = "*" if left and (left.isalnum() or left in ")]") else ""
        post = False
        j = self._skip_spaces(s, i)
        if j < len(s):
            c = s[j]
            if c.isalnum() or c in "({":
                post = True
            elif c == "\\":
                m = re.match(r"\\([A-Za-z]+)", s[j:])
                if m and (m.group(1) in GREEK or m.group(1) in FUNCTIONS
                          or m.group(1) in self._FRAC_NEXT_CMDS):
                    post = True
        return pre, bool(pre) or post

    # ---- konversi rekursif -------------------------------------------------
    def conv(self, s):
        out = []
        i = 0
        n = len(s)
        while i < n:
            ch = s[i]

            if ch == "\\":
                m = re.match(r"\\([A-Za-z]+)", s[i:])
                if m:
                    name = m.group(1)
                    i += len(m.group(0))
                    self._left_tail = next((o.rstrip()[-1] for o in reversed(out) if o.strip()), "")
                    res, i = self.command(name, s, i)
                    out.append(res)
                else:
                    nxt = s[i + 1] if i + 1 < n else ""
                    i += 2
                    if nxt == "\\":
                        out.append("\n")
                    elif nxt in "{}":
                        out.append("(" if nxt == "{" else ")")
                    elif nxt == "%":
                        out.append("%")
                    elif nxt == "|":
                        out.append("‖")
                    elif nxt == "&" or nxt == "_" or nxt == "#":
                        out.append(nxt)
                    else:
                        pass
                continue

            if ch == "{":
                inner, i = read_group(s, i)
                out.append(self.conv(inner))
                continue

            if ch == "}":
                i += 1
                continue

            if ch == "^":
                arg, i = read_arg(s, i + 1)
                c = self.conv(arg).strip()
                if c in ("'", "′"):
                    out.append("'")
                elif c == "°":
                    out.append("°")
                elif BARE_EXP_RE.match(c):
                    out.append("^" + c)
                else:
                    out.append("^" + wrap(c))
                continue

            if ch == "_":
                arg, i = read_arg(s, i + 1)
                c = self.conv(arg).strip()
                c_clean = re.sub(r"[\s{}()*\u2063]", "", c)
                if self.subscript != "drop" and not re.fullmatch(r"[A-Za-z0-9α-ωΑ-Ω.]+", c_clean):
                    # x_{n+1}: subskrip berupa ekspresi -> indeks array  x[n+1]
                    out.append("[" + re.sub(r"[\s{}]", "", c) + "]")
                elif self.subscript == "drop":
                    pass
                elif self.subscript == "literal":
                    out.append("." + c_clean)
                else:
                    out.append("_" + c_clean.replace(".", ""))
                continue

            if ch == "&":
                out.append(" ")
                i += 1
                continue

            if ch == "~":
                out.append(" ")
                i += 1
                continue

            out.append(ch)
            i += 1
        return "".join(out)

    # ---- fungsi: \sin^2(x), \tan 2\theta_p, \sin x, \log_{10}(x) -----------
    ARC_OK = {"sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh", "tanh"}

    @staticmethod
    def _skip_spaces(s, k):
        while k < len(s) and s[k] == " ":
            k += 1
        return k

    @staticmethod
    def _match_paren(s, k):
        """s[k] == '(' (atau \\left( ) -> (isi, indeks setelah penutup)."""
        left = s.startswith("\\left(", k)
        k0 = k + (6 if left else 1)
        depth = 1
        j = k0
        while j < len(s):
            if s.startswith("\\left(", j):
                depth += 1
                j += 6
            elif s.startswith("\\right)", j):
                depth -= 1
                if depth == 0:
                    return s[k0:j], j + 7
                j += 7
            elif s[j] == "(":
                depth += 1
                j += 1
            elif s[j] == ")":
                depth -= 1
                if depth == 0:
                    return s[k0:j], j + 1
                j += 1
            else:
                j += 1
        return s[k0:], len(s)

    @staticmethod
    def _read_term(s, k):
        """Argumen tanpa kurung: angka/huruf/\\yunani yang menempel (2\\theta_p, x)."""
        start, n = k, len(s)
        while k < n:
            m = re.match(r"\d+(?:\.\d+)?|[A-Za-z]|\\([A-Za-z]+)", s[k:])
            if not m:
                break
            if m.group(1) == "mat":                      # \det\mat{2}{2}{a}{b}{c}{d}
                k += m.end()
                r_, k = read_arg(s, k)
                c_, k = read_arg(s, k)
                try:
                    cnt = int(r_) * int(c_)
                except ValueError:
                    cnt = 0
                for _ in range(cnt):
                    _x, k = read_arg(s, k)
                continue
            if m.group(1) in ("abs", "sqrt", "frac", "dfrac", "tfrac"):
                k += m.end()               # \ln\abs{x}, \sin\sqrt{x}, \ln\frac{1}{x}
                if m.group(1) == "sqrt" and k < n and s[k] == "[":
                    _o, k = read_bracket(s, k)
                _a, k = read_arg(s, k)
                if m.group(1) != "abs" and m.group(1) != "sqrt":
                    _b, k = read_arg(s, k)
                continue
            if m.group(1) is not None and m.group(1) not in GREEK:
                break                      # \cos, \cdot, \leq ... berhenti
            k += m.end()
            while k < n and s[k] in "_^":
                _arg, k = read_arg(s, k + 1)
        return (s[start:k], k) if k > start else (None, k)

    def function(self, name, s, i):
        fname = FUNCTIONS[name]
        j = self._skip_spaces(s, i)
        power = None
        base = None
        call_ok = False
        if j < len(s) and s[j] == "^":                      # \sin^2  /  \sin^{-1}
            pw, j = read_arg(s, j + 1)
            power = self.conv(pw).strip()
            if power == "-1" and name in self.ARC_OK:
                fname, power = "a" + fname, None
            j = self._skip_spaces(s, j)
        elif j < len(s) and s[j] == "_" and name in ("log", "lg"):   # \log_{10}
            bs, j = read_arg(s, j + 1)
            base = self.conv(bs).strip()
            j = self._skip_spaces(s, j)
        elif j < len(s) and s[j] == "_" and name in LIMIT_SUB_FUNCS:  # \min_{x \in S} f(x)
            _bs, j = read_arg(s, j + 1)
            self.warnings.append(Msg("w_op_limits", name=name))
            j = self._skip_spaces(s, j)
            call_ok = True

        if j < len(s) and (s[j] == "(" or s.startswith("\\left(", j)):
            raw, k = self._match_paren(s, j)
        elif j < len(s) and s[j] == "{":
            raw, k = read_group(s, j)
        else:
            raw, k = self._read_term(s, j)
            if call_ok and raw is not None and (s[k:k + 1] == "(" or s.startswith("\\left(", k)):
                _p, k = self._match_paren(s, k)              # \min_x f(x): f(x) satu argumen
                raw = s[j:k]
        if raw is None:                                      # fungsi tanpa argumen
            return self._protect_words(fname) + ("^" + wrap(power) if power else ""), i

        arg = self.conv(raw).strip()
        if not base:
            out = f"{fname}({arg})"
        elif base == "10":                  # log(x) di Mathcad sudah basis 10
            out = f"{fname}({arg})"
        elif base in ("e", "ℯ"):
            out = f"ln({arg})"
        elif self.log_base == "ln":         # perubahan basis: aman di semua jalur
            out = f"(ln({arg})/ln({base}))"
        else:
            out = f"{fname}({arg},{base})"
        if power:
            out += "^" + (power if BARE_EXP_RE.match(power) else wrap(power))
        return out, k

    # ---- turunan (biasa & parsial, tingkat berapa pun) ------------------------
    # Akar masalah lama: turunan hanya dikenali lewat satu regex untuk d/dt tingkat 1
    # ("dy"/"dt"), sehingga d^2y / dt^2 jatuh ke pecahan biasa (d^2*y)/(d*t^2).
    # Sekarang pembilang & penyebut diurai terstruktur:
    #   pembilang  : (d|∂)[^n] [ekspresi]
    #   penyebut   : (d|∂) var[^k]  (d|∂) var[^k] ...   (turunan campuran)
    # lalu dikeluarkan sebagai pemanggilan  diff(ekspresi, var[, tingkat]).
    _TEXARG = r"(?:\{[^{}]*\}|\\[A-Za-z]+|[^\s\\{}])"
    _D_WRAP = re.compile(r"\\(?:mathrm|operatorname|text|textrm|mathit|rm)\s*\{\s*([dD∂])\s*\}"
                         r"|\{\s*\\rm\s+([dD])\s*\}")
    _D_NUM = re.compile(r"([d∂])\s*(?:\^\s*(" + _TEXARG + r"))?\s*(.*)", re.S)
    _D_FAC = re.compile(r"\s*([d∂])\s*(\{[^{}]+\}|\\[A-Za-z]+|[A-Za-z])"
                        r"((?:_(?:\{[^{}]*\}|[A-Za-z0-9]))?)\s*(?:\^\s*(" + _TEXARG + r"))?")
    MAX_ORDER = 12

    @staticmethod
    def _dnorm(x):
        x = Converter._D_WRAP.sub(lambda m: "d" if (m.group(1) or m.group(2)) in ("d", "D")
                                  else "∂", x)
        x = re.sub(r"\\partial(?![A-Za-z])", "∂", x)
        x = re.sub(r"\\(?:displaystyle|,|;|:|!)", " ", x)
        return x.strip()

    def _dorder(self, raw):
        """None -> 1; '2'/'{2}' -> 2; selain itu (mis. n) -> teks."""
        if raw is None:
            return 1
        t = self.conv(raw).strip()
        return int(t) if re.fullmatch(r"\d+", t) else t

    def _read_operand(self, s, i):
        """Operan setelah operator turunan:  (..)  [..]  f(t)  y_1  x^2  \\theta  \\sin(t)."""
        j = self._skip_spaces(s, i)
        if j >= len(s):
            return None, i
        k = j + 5 if s.startswith("\\left", j) else j
        if k < len(s) and s[k] in "([":
            o, c = s[k], ")" if s[k] == "(" else "]"
            depth, p = 1, k + 1
            while p < len(s) and depth:
                depth += (s[p] == o) - (s[p] == c)
                p += 1
            inner = s[k + 1:p - 1] if depth == 0 else s[k + 1:]
            return re.sub(r"\\right\s*$", "", inner), p
        m = re.match(r"\\([A-Za-z]+)|[A-Za-z]", s[j:])
        if not m or (m.group(1) and m.group(1) not in GREEK and m.group(1) not in FUNCTIONS):
            return None, i
        p = j + m.end()
        while p < len(s) and s[p] in "_^":
            _a, p = read_arg(s, p + 1)
        if p < len(s) and (s[p] == "(" or s.startswith("\\left(", p)):
            _raw, p = self._match_paren(s, p)
        return s[j:p], p

    def _derivative(self, a, b, s, i):
        """Kembalikan (teks, indeks) bila \\frac{a}{b} adalah turunan; selain itu None."""
        na, nb = self._dnorm(a), self._dnorm(b)
        mn = self._D_NUM.fullmatch(na)
        if not mn or re.fullmatch(r"d[A-Za-z]{3,}", na):
            return None
        facs, pos = [], 0
        while pos < len(nb):
            m = self._D_FAC.match(nb, pos)
            if not m:
                return None
            facs.append(m)
            pos = m.end()
        if not facs or any(f.group(1) != mn.group(1) for f in facs):
            return None
        rest = mn.group(3).strip()
        num_order = self._dorder(mn.group(2))
        parts = [(self.conv(f.group(2) + f.group(3)).strip(), self._dorder(f.group(4)))
                 for f in facs]
        if any(v == "" for v, _o in parts):
            return None
        if len(parts) > 1 and any(not isinstance(o, int) for _v, o in parts):
            return None                       # tingkat simbolik hanya untuk satu variabel
        total = sum(o for _v, o in parts) if all(isinstance(o, int) for _v, o in parts) else None
        if total is not None and total > self.MAX_ORDER:
            return None
        if total is not None and num_order != total:
            self.warnings.append(Msg("w_deriv_order", num=num_order, den=total))
        if not rest:
            rest, i = self._read_operand(s, i)
            if rest is None:                  # operator murni: d/dt, d^2/dt^2
                if len(parts) == 1 and parts[0][1] == 1:
                    return "d/d" + parts[0][0], i
                return None
        expr = self.conv(rest).strip()
        fn = "pdiff" if mn.group(1) == "∂" else "diff"      # ∂ -> turunan parsial (Ctrl+D)
        for var, order in reversed(parts):    # ∂²u/∂x∂y = ∂/∂x(∂u/∂y)
            expr = f"\x02{fn}({expr},{var}" + ("" if order == 1 else f",{order}") + ")"
        if any(not isinstance(o, int) for _v, o in parts):
            self.warnings.append(Msg("w_deriv_symbolic"))
        return expr, i

    _DIFF_RE = re.compile(r"(?:\\mathrm\s*\{\s*d\s*\}|\\text\s*\{\s*d\s*\}|d)\s*"
                          r"(\\[A-Za-z]+|[A-Za-z\u03b1-\u03c9\u0391-\u03a9])")
    _REL_CMDS = {"leq", "le", "geq", "ge", "neq", "ne", "approx", "equiv", "to", "rightarrow",
                 "leftarrow", "newline", "cr", "quad", "qquad"}

    @staticmethod
    def _skip_delim(s, j):
        """Lewati delimiter setelah \\left / \\right (mis. '(' , '[' , '.', '\\{', '\\vert')."""
        while j < len(s) and s[j] == " ":
            j += 1
        if j < len(s):
            if s[j] == "\\":
                m = re.match(r"\\[A-Za-z]+|\\.", s[j:])
                return j + len(m.group(0))
            return j + 1
        return j

    def _scan_body(self, s, i, is_int=False):
        """Baca isi operator besar TANPA wajib kurung kurawal.
        Berhenti di tingkat terluar pada: relasi (=, <, >, \\leq ..), koma, penutup yang
        tak berpasangan, \\right, dan (untuk sum/prod/lim) + atau -. Untuk \\int berhenti
        tepat sebelum diferensial dx / \\mathrm{d}x.  -> (isi, indeks, variabel_diferensial)"""
        n = len(s)
        j = self._skip_spaces(s, i)
        start, depth, pending, prev, dvar = j, 0, 0, "", None
        stop_end = j
        while j < n:
            c = s[j]
            if is_int and depth == 0 and (c == "d" or s.startswith("\\mathrm", j)
                                          or s.startswith("\\text", j)):
                before = s[j - 1] if j > start else " "
                md = self._DIFF_RE.match(s, j)
                if md and not before.isalpha() and before != "\\":
                    after = s[md.end():md.end() + 1]
                    if md.group(1).startswith("\\") or not after.isalpha():
                        if pending > 0:
                            pending -= 1
                            j, prev = md.end(), "x"
                            continue
                        dvar = md.group(1)
                        stop_end = md.end()
                        break
            if c == "\\":
                m = re.match(r"\\([A-Za-z]+)", s[j:])
                if m:
                    name = m.group(1)
                    if name == "left":
                        depth += 1
                        j = self._skip_delim(s, j + m.end())
                        prev = "x"
                        continue
                    if name == "right":
                        if depth == 0:
                            break
                        depth -= 1
                        j = self._skip_delim(s, j + m.end())
                        prev = "x"
                        continue
                    if depth == 0 and name in self._REL_CMDS:
                        break
                    if depth == 0 and is_int and name in ("int", "iint", "iiint"):
                        pending += {"int": 1, "iint": 2, "iiint": 3}[name]
                    j += m.end()
                    prev = "x"
                    continue
                if s[j + 1:j + 2] == "\\" and depth == 0:
                    break
                j += 2                                   # \\, \; \: \! \{ \} dst
                continue
            if c in "{([":
                depth += 1
            elif c in "})]":
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0:
                if c in "=<>,&;":
                    break
                if c in "+-" and not is_int and j > start and prev not in ("^", "_"):
                    break
            prev = c if c in "^_" else "x"
            j += 1
        if dvar is None:
            stop_end = j
        return s[start:j].strip(), stop_end, dvar

    def _read_subsup(self, s, i):
        """Baca _{..} dan ^{..} (urutan bebas) -> (sub, sup, indeks)."""
        sub = sup = None
        while True:
            j = self._skip_spaces(s, i)
            if j < len(s) and s[j] == "_" and sub is None:
                sub, i = read_arg(s, j + 1)
            elif j < len(s) and s[j] == "^" and sup is None:
                sup, i = read_arg(s, j + 1)
            else:
                return sub, sup, i

    # ---- perintah \xxx -----------------------------------------------------
    def command(self, name, s, i):
        left_tail = getattr(self, "_left_tail", "")       # simpan SEBELUM konversi rekursif menimpanya
        if name == "operatorname" and i < len(s) and s[i] == "*":
            i += 1                                        # \\operatorname*{argmax}

        if name == "ifelse":                              # dari \\begin{cases}
            c, i = read_arg(s, i)
            a, i = read_arg(s, i)
            b, i = read_arg(s, i)
            return "if(%s,%s,%s)" % (self.conv(c).strip(), self.conv(a).strip(),
                                     self.conv(b).strip()), i

        if name == "norm":                                # \\|x\\|  ->  norm2(x)
            a, i = read_arg(s, i)
            body = self.conv(a).strip()
            j = self._skip_spaces(s, i)
            fn, p = "norm2", None
            if j < len(s) and s[j] == "_":                # ||x||_p
                ps, i = read_arg(s, j + 1)
                pc = self.conv(ps).strip()
                if pc in ("1",):
                    fn = "norm1"
                elif pc in ("∞", "inf"):
                    fn = "normi"
                elif pc in ("F", "f"):
                    fn = "normf"
                elif pc != "2":
                    fn, p = "normp", pc
            self.warnings.append(Msg("w_norm"))
            return fn + "(" + body + ("," + p if p else "") + ")", i

        if name in ("bigcup", "bigcap", "bigoplus", "bigotimes", "bigvee", "bigwedge"):
            sub, sup, i = self._read_subsup(s, i)
            if sub or sup:
                self.warnings.append(Msg("w_op_limits", name=name))
            return SYMBOLS[name] + " ", i

        if name in DOTS_COMMANDS:
            self.warnings.append(Msg("w_dots", name=name))
            return "", i

        if name in ("overset", "underset", "stackrel"):   # simbol di atas/bawah: ambil yang utama
            _a, i = read_arg(s, i)
            b, i = read_arg(s, i)
            self.warnings.append(Msg("w_brace_label", name=name))
            return self.conv(b), i

        if name in ("underbrace", "overbrace"):
            a, i = read_arg(s, i)
            j = self._skip_spaces(s, i)
            if j < len(s) and s[j] == ("_" if name == "underbrace" else "^"):
                _lab, i = read_arg(s, j + 1)
            self.warnings.append(Msg("w_brace_label", name=name))
            return self.conv(a), i

        if name in ("xrightarrow", "xleftarrow", "xlongequal", "xRightarrow", "xLeftarrow",
                    "xleftrightarrow", "xhookrightarrow", "xmapsto"):
            if i < len(s) and s[i] == "[":
                _o, i = read_bracket(s, i)
            _a, i = read_arg(s, i)
            self.warnings.append(Msg("w_brace_label", name=name))
            return {"xleftarrow": "←", "xLeftarrow": "⇐", "xlongequal": "=",
                    "xRightarrow": "⇒", "xleftrightarrow": "↔", "xmapsto": "↦"}.get(name, "→"), i

        if name == "substack":
            a, i = read_arg(s, i)
            self.warnings.append(Msg("w_substack"))
            return self.conv(a.replace("\\\\", ",")), i

        if name == "not":                                 # \\not=  \\not\\in  \\not\\subset ...
            t, i = read_arg(s, i)
            key = t[1:] if t.startswith("\\") else t
            if key in NOT_MAP:
                return NOT_MAP[key], i
            return "¬" + self.conv(t), i

        if name in ("frac", "dfrac", "tfrac", "cfrac"):
            a, i = read_arg(s, i)
            b, i = read_arg(s, i)
            # turunan tingkat berapa pun (biasa & parsial), lihat _derivative()
            res = self._derivative(a, b, s, i)
            if res is not None:
                return res
            core = wrap(self.conv(a)) + "/" + wrap(self.conv(b))
            pre, boxed = self._frac_context(s, i, left_tail)
            if boxed:
                core = pre + "(" + core + ")"
            return core, i

        if name == "mat":
            r, i = read_arg(s, i)
            c, i = read_arg(s, i)
            try:
                nr, nc = int(r), int(c)
            except ValueError:
                nr = nc = 0
            cells = []
            for _ in range(nr * nc):
                a, i = read_arg(s, i)
                cells.append(self.conv(a).strip() or "0")
            return "mat(%d,%d,%s)" % (nr, nc, ",".join(cells)), i

        if name in ("binom", "dbinom", "tbinom"):
            a, i = read_arg(s, i)
            b, i = read_arg(s, i)
            self.warnings.append(Msg("w_binom"))
            return "combin(" + self.conv(a) + "," + self.conv(b) + ")", i

        if name == "sqrt":
            idx = None
            if i < len(s) and s[i] == "[":
                idx, i = read_bracket(s, i)
            a, i = read_arg(s, i)
            body = self.conv(a).strip()
            if idx is not None:
                return "root(" + body + "," + self.conv(idx).strip() + ")", i
            return "sqrt(" + body + ")", i

        if name == "abs":
            a, i = read_arg(s, i)
            return "abs(" + self.conv(a).strip() + ")", i

        if name in ("sum", "prod"):
            # \sum_{i=1}^{n}{body}  atau  \sum^{n}_{i=1}{body}  (urutan ^/_ bebas).
            # body HARUS dibungkus {..} kalau lebih dari satu token (sama kayak \sqrt/\frac).
            sub, sup, i = self._read_subsup(s, i)
            body, i, _dv = self._scan_body(s, i)
            var, lower = "i", ""
            upper = sup or ""
            if sub:
                m = re.match(r"\s*([A-Za-z\u03b1-\u03c9\u0391-\u03a9][\w]*)\s*=\s*(.*)$", sub, re.S)
                m_rng = re.match(r"\s*([^<\\]+?)\s*(?:\\leq?|\\leqslant|<|\\le)\s*"
                                 r"([A-Za-z\u03b1-\u03c9\u0391-\u03a9][\w]*)\s*"
                                 r"(?:\\leq?|\\leqslant|<|\\le)\s*(.+)$", sub, re.S)
                m_var = re.match(r"\s*([A-Za-z\u03b1-\u03c9\u0391-\u03a9][\w]*)\s*$", sub)
                if m:
                    var, lower = m.group(1), m.group(2)
                elif m_rng:                                   # \\sum_{1 \\le i \\le n}
                    lower, var = m_rng.group(1), m_rng.group(2)
                    upper = upper or m_rng.group(3)
                elif m_var:                                   # \\sum_i a_i  (tanpa batas)
                    var = m_var.group(1)
                else:                                         # \\sum_{i<j}, \\sum_{i \\in S}
                    m_first = re.match(r"\s*([A-Za-z\u03b1-\u03c9\u0391-\u03a9][\w]*)", sub)
                    var = m_first.group(1) if m_first else "i"
                    self.warnings.append(Msg("w_sum_cond", name=name))
            fname = "sum" if name == "sum" else "prod"
            return ("%s(%s,%s,%s,%s)" % (fname, var, self.conv(lower).strip(),
                                         self.conv(upper).strip(), self.conv(body).strip())), i

        if name == "int":
            # \int_{a}^{b}{integran} dx   atau   \int_{a}^{b}{integran} \, dx
            # integran HARUS dibungkus {..} kalau lebih dari satu token.
            sub, sup, i = self._read_subsup(s, i)
            i = self._skip_spaces(s, i)
            integrand, i, dv = self._scan_body(s, i, is_int=True)
            var = self.conv(dv).strip() if dv else "x"
            lower = self.conv(sub).strip() if sub else ""
            upper = self.conv(sup).strip() if sup else ""
            return ("integral(%s,%s,%s,%s)" % (lower, upper, self.conv(integrand).strip(), var)), i

        if name == "lim":
            # \lim_{x \to a}{body}  atau  \lim_{x \to a^+}{body} (limit sepihak)
            j = self._skip_spaces(s, i)
            sub = None
            if j < len(s) and s[j] == "_":
                sub, i = read_arg(s, j + 1)
            else:
                i = j
            body, i, _dv = self._scan_body(s, i)
            var, point, direction = "x", "", ""
            if sub:
                m = re.match(r"\s*([A-Za-z\u03b1-\u03c9\u0391-\u03a9][\w]*)\s*"
                             r"\\(?:to|rightarrow)\s*(.+?)\s*$", sub, re.S)
                if m:
                    var, pointraw = m.group(1), m.group(2)
                else:
                    pointraw = sub
                dm = re.match(r"^(.*?)\^\{?\s*([+-])\s*\}?$", pointraw, re.S)
                if dm:
                    point, direction = dm.group(1).strip(), dm.group(2)
                else:
                    point = pointraw
            out = "limit(%s,%s,%s" % (var, self.conv(point).strip(), self.conv(body).strip())
            out += (",%s1)" % ("-" if direction == "-" else "")) if direction else ")"
            return out, i

        if name in TEXT_COMMANDS:
            while i < len(s) and s[i] == " ":
                i += 1
            if i < len(s) and s[i] == "{":
                a, i = read_group(s, i)
                return self._protect_words(a), i
            return "", i

        if name in SKIP_ARG_COMMANDS:
            a, i = read_arg(s, i)
            return "", i

        if name in PASS_ARG_COMMANDS:
            a, i = read_arg(s, i)
            if name in ("vec", "hat", "tilde", "bar", "overline", "dot",
                        "ddot", "overrightarrow"):
                self.warnings.append(Msg("w_accent", name=name))
            if name in WORD_COMMANDS:
                return self._protect_words(self.conv(a), alias=(name == "operatorname")), i
            return self.conv(a), i

        if name in DROP_COMMANDS:
            # \left. / \right.  -> hilangkan titik
            if name in ("left", "right") and i < len(s) and s[i] == ".":
                i += 1
            return "", i

        if name in GREEK:
            return GREEK[name] if self.unicode_greek else name, i

        if name in SYMBOLS:
            if name in ("sum", "prod", "int"):
                self.warnings.append(Msg("w_bigop", name=name))
            return SYMBOLS[name], i

        if name in FUNCTIONS:
            if name in SUPINF_MAP:
                self.warnings.append(Msg("w_sup_inf", name=name, to=SUPINF_MAP[name]))
            elif name in OPNAMES_KEPT:
                self.warnings.append(Msg("w_opname_kept", name=name))
            return self.function(name, s, i)

        if name in ("mid", "vert"):
            return "|", i
        if name in ("lim",):
            self.warnings.append(Msg("w_lim"))
            return "lim", i
        if name in ("newline", "cr"):
            return "\n", i

        # tidak dikenal: tetap SATU nama (bukan perkalian huruf), plus peringatan
        self.warnings.append(Msg("w_unknown_cmd", name=name))
        return self._protect_words(name), i

    # ---- pasca-proses ---------------------------------------------------------
    def postprocess(self, t):
        lines = [ln.strip() for ln in t.split("\n")]
        lines = [re.sub(r"[ \t]+", " ", ln) for ln in lines if ln.strip()]
        res = []
        for ln in lines:
            # a\frac{dy}{dx} -> a*diff(..): penanda \x02 dari _derivative() jadi "*" bila menempel
            ln = re.sub(r"(?<=[A-Za-z0-9α-ωΑ-Ω)\]])\x02", "*", ln).replace("\x02", "")
            ln = self.expand_laplacian(ln)
            ln = self.space_to_mult(ln)
            if self.implicit_mult:
                ln = self.add_implicit_mult(ln)
            if self.define and not re.search(r"[Σ∏∫]", ln):
                ln = self.make_definition(ln)
            if "'" in ln or "′" in ln:
                ln = ln.replace("'", "prime").replace("′", "prime")
                self.warnings.append(Msg("w_prime"))
            res.append(ln.replace(MARK, ""))
        return "\n".join(res)

    def expand_laplacian(self, ln):
        """∇²u  ->  (pdiff(u,x,2) + pdiff(u,y,2))  (Prime tidak punya ketikan untuk ∇²)."""
        out, i = "", 0
        while True:
            k = ln.find("∇^2", i)
            if k < 0:
                out += ln[i:]
                break
            out += ln[i:k]
            j = k + 3
            while j < len(ln) and ln[j] in " *":
                j += 1
            m = j
            if m < len(ln) and ln[m] == "(":
                depth = 0
                while m < len(ln):
                    depth += (ln[m] == "(") - (ln[m] == ")")
                    m += 1
                    if depth == 0:
                        break
            else:
                mm = re.match(r"[A-Za-zα-ωΑ-Ω][A-Za-z0-9α-ωΑ-Ω]*(\.[A-Za-z0-9]+)?(\[[^\]]*\])?", ln[j:])
                m = j + (mm.end() if mm else 0)
            operand = ln[j:m]
            if not operand:
                out += "∇^2"                      # tanpa operan: biarkan, nanti ditolak dengan pesan
                i = k + 3
                continue
            names = list(NABLA_VARS) + (["z"] if re.search(r"(?<![A-Za-z0-9_.])z(?![A-Za-z0-9_.(])", ln) and "z" not in NABLA_VARS else [])
            out += "(" + " + ".join(f"pdiff({operand},{v},2)" for v in names) + ")"
            msg = f"∇² diperluas menjadi turunan parsial kedua terhadap {', '.join(names)} (ubah NABLA_VARS bila dimensinya beda)."
            if msg not in self.warnings:
                self.warnings.append(msg)
            i = m
        return out

    def space_to_mult(self, ln):
        # rapikan spasi di dalam kurung
        ln = re.sub(r"\(\s+", "(", ln)
        ln = re.sub(r"\s+\)", ")", ln)

        # spasi antar operand di LaTeX berarti perkalian: "E I" -> "E*I"
        def repl(m):
            prev_word = re.search(r"[A-Za-zα-ωΑ-Ω]+$", m.string[:m.end(1)])
            if prev_word and prev_word.group(0) in KNOWN_FUNC_NAMES:
                return m.group(0)       # "sin x" dibiarkan
            return m.group(1) + "*" + m.group(2)

        pat = re.compile(r"([\w)\]°'])\s+([\w(α-ωΑ-Ω])")
        prev = None
        while prev != ln:               # ulangi utk "a b c"
            prev = ln
            ln = pat.sub(repl, ln)
        return ln

    def add_implicit_mult(self, ln):
        # ab -> a*b  (hanya nama >=2 huruf yang bukan fungsi & bukan subskrip)
        def split_name(m):
            tok = m.group(0)
            if tok.lower() in KNOWN_FUNC_NAMES:
                return tok
            return "*".join(tok)

        # lindungi notasi turunan d/dt agar 'dt' tidak dipecah menjadi d*t
        ln = re.sub(r"\bd/d([A-Za-z])(?![A-Za-z0-9_.])", "d/\x00\\1", ln)

        name_pat = re.compile(
            r"(?<![A-Za-z_.α-ωΑ-Ω])[A-Za-zα-ωΑ-Ω]{2,}(?![A-Za-z0-9_(.α-ωΑ-Ω])")
        # xy.ijin (LaTeX: x y_{ijin}) -> x*y.ijin : subskrip hanya milik huruf terakhir
        sub_pat = re.compile(
            r"(?<![A-Za-z_.α-ωΑ-Ω])([A-Za-zα-ωΑ-Ω]{2,})(?=[._][A-Za-z0-9])")

        def split_before_sub(m):
            tok = m.group(1)
            if tok.lower() in KNOWN_FUNC_NAMES:
                return tok
            return "*".join(tok[:-1]) + "*" + tok[-1]

        def process(seg):
            seg = sub_pat.sub(split_before_sub, seg)
            return name_pat.sub(split_name, seg)

        # isi indeks array x[kritis,i+1] adalah nama variabel utuh: JANGAN dipecah k*r*i*t*i*s
        parts = re.split(r"(\[[^\[\]]*\])", ln)
        ln = "".join(p if k % 2 else process(p) for k, p in enumerate(parts))
        # )( -> )*(
        ln = re.sub(r"\)\s*\(", ")*(", ln)
        # huruf Yunani/variabel diikuti '(' tidak diubah (bisa fungsi)
        # angka diikuti variabel dibiarkan (Mathcad paham 2x)
        # kurung tutup diikuti variabel/angka: )x -> )*x
        ln = re.sub(r"\)\s*([A-Za-zα-ωΑ-Ω0-9])", r")*\1", ln)
        # variabel/angka tunggal diikuti ( setelah ")" sudah ditangani
        ln = re.sub(r"\*\s*\*", "*", ln)
        ln = ln.replace("\x00", "d")
        return ln

    def make_definition(self, ln):
        # '=' pertama (bukan <=,>=,!=,:=,==) -> ':='
        return re.sub(r"(?<![:<>!=≤≥≠])=(?!=)", ":=", ln, count=1)

    # ---- API ---------------------------------------------------------------
    def convert(self, latex):
        self.warnings = []
        s = self.preclean(latex)
        t = self.conv(s)
        t = self.postprocess(t)
        return t


def convert(latex, **kw):
    c = Converter(**kw)
    result = c.convert(latex)
    return result, list(dict.fromkeys(c.warnings))


# ----------------------------------------------------------------------------
# AUTO-KETIK UNTUK MATHCAD PRIME
# teks linear  ->  pohon rumus (AST)  ->  urutan tombol keyboard
#
# Alasan: Mathcad Prime TIDAK bisa membaca rumus dari clipboard (paste hanya
# menghasilkan string bertanda kutip). Maka rumus "diketik" lewat keyboard,
# persis seperti kalau kamu mengetik sendiri di Prime.
# ----------------------------------------------------------------------------

# --- PETA TOMBOL MATHCAD PRIME ----------------------------------------------
# Kalau di versi Prime kamu ada yang beda, cukup ubah nilai di bawah ini.
KEY_SQRT = "\\"        # akar kuadrat
KEY_DEF = ":"          # definisi  (:=)
KEY_SUBSCRIPT = "."    # (dipakai hanya bila SUB_MODE = "dot")
# Subskrip literal di Prime = tombol Ctrl+- (toggle baseline): ketik nama, Ctrl+-, subskrip, Ctrl+-.
# Tanda titik "." di Prime hanya karakter biasa dalam nama (tampil x.input, tidak turun).
SUB_MODE = "chord"     # "chord" (Ctrl+-, benar-benar subskrip) | "dot" (cara lama: x.i)
SUB_CHORD = "-"        # Ctrl+- 
KEY_POWER = "^"        # pangkat
KEY_FRAC = "/"         # pecahan (pembilang = operand tepat di kiri)
KEY_ABS = "|"          # nilai mutlak |x| (kosongkan "" untuk mengetik abs(x) biasa)
# abs(x) diketik sebagai fungsi abs(...) (aman). True: diketik dengan tombol "|" (bar), tapi
# "|" tepat setelah akar/kurung pernah membuat Prime crash. det(A) tetap memakai bar |A|.
ABS_USE_BARS = True
ABS_WAIT_OPEN = 150     # ms jeda sesudah "|" supaya Prime sempat membuat tanda mutlak
KEY_DERIV = "?"        # operator turunan d/dx (Shift+/ ; tombol "?")
KEY_DEG = "deg"        # derajat: 30° diketik sebagai 30deg (unit bawaan Prime)
# Turunan tingkat n (d^n/dx^n f) memakai operator "nth derivative" Prime (bentuk d^2/dx^2 y),
# BUKAN d/dx bersarang. Urutan ketikan (sesuai pemakaian di Prime):
#   Ctrl+Shift+D -> VARIABEL -> NDERIV_NAV[0] -> TINGKAT -> NDERIV_NAV[1] -> FUNGSI -> keluar
# Tingkat boleh angka (2) atau simbol (n). Antar kotak dipindah dengan NDERIV_NAV; default panah
# KANAN (sama seperti Sigma yang sudah terverifikasi). Kalau di Prime-mu harus Tab, ganti
# menjadi ("TAB", "TAB"). NDERIV_NATIVE = False -> kembali ke turunan bersarang.
NDERIV_NATIVE = True
NDERIV_CHORD = ("cs", "D")      # Ctrl+Shift+D
NDERIV_NAV = ("RIGHT", "RIGHT")
# Turunan PERTAMA (d/dx): tombol "?" (KEY_DERIV) ternyata tidak menjadi operator di Prime-mu
# (muncul "?x" biasa). Jadi default-nya turunan pertama diketik dengan operator yang sama
# (Ctrl+Shift+D, variabel, tingkat 1, fungsi) yang sudah terbukti jalan. Set False untuk
# kembali memakai tombol KEY_DERIV.
FIRST_DERIV_USE_NTH = True
FIRST_DERIV_SHOW_ORDER = False   # False: turunan pertama tanpa mengetik angka 1 (kotak dibiarkan kosong)
# Turunan PARSIAL (∂): Ctrl+D, lalu variabel -> tingkat -> fungsi (sama seperti turunan biasa).
PDERIV_CHORD = ("c", "D")        # Ctrl+D
NDERIV_WAIT_DIALOG = 500        # ms jeda setelah Ctrl+Shift+D
NDERIV_WAIT_STEP = 250          # ms jeda setelah tiap pindah kotak
NDERIV_WAIT_EXIT = 700          # ms jeda setelah operator turunan selesai (keluar dari operator)
# Jeda setelah Ctrl+= : Prime perlu waktu memasang "=" dan memindah kursor ke sisi kanan.
# Tanpa jeda, ketikan sesudahnya bisa mendarat di sisi kiri dan "=" tertinggal di ujung.
EQ_WAIT_AFTER = 600
# Pangkat pada fungsi: sin(x*y)^3 di Prime jadi sin((x*y)^3) (pangkat menempel ke argumen).
# True: diketik (sin(x*y))^3 supaya pangkat berlaku ke seluruh fungsi. False: cara lama.
POW_WRAP_CALL = True
POW_WRAP_FUNCS = {"sin", "cos", "tan", "cot", "sec", "csc", "asin", "acos", "atan",
                  "sinh", "cosh", "tanh", "ln", "log", "exp"}
# Matriks di Prime - TERVERIFIKASI lewat tes manual langsung (bukan dokumentasi PTC):
#   Ctrl+M            -> matriks 1x1 (satu kotak, kursor di situ)
#   Shift+Spasi       -> tambah kolom BARU DI SEBELAH KANAN, kursor pindah ke kotak baru itu
#   Shift+Enter       -> tambah baris baru DI BAWAH, kursor mendarat di baris baru TAPI DI
#                        KOLOM YANG SAMA dengan posisi sebelumnya (bukan balik ke kolom 1!)
#   Panah kiri/kanan biasa (TANPA Ctrl, TANPA Tab) -> pindah satu kotak ke kiri/kanan
#   Ctrl+Kiri TIDAK melompat ke kotak pertama - dia mundur satu kotak demi satu kotak lalu
#   akhirnya malah KELUAR dari matriks. Makanya navigasi di bawah ini sama sekali tidak
#   memakai Ctrl+Kiri lagi: baris pertama diisi sambil membesarkan kolom (Shift+Spasi),
#   baris berikutnya diisi dengan Shift+Enter lalu panah KIRI biasa sebanyak (kolom-1) kali
#   untuk balik ke kolom 1, baru lanjut isi ke kanan dengan panah kanan biasa.
MAT_CHORD = "M"
MAT_ADD_COL = "SPACE"        # Shift+Spasi: tambah kolom (baris pertama saja)
MAT_ADD_ROW = "ENTER"        # Shift+Enter: tambah baris (kolom kursor tidak berubah)
MAT_LEFT = "LEFT"            # panah kiri biasa: mundur satu kotak
MAT_NEXT = "RIGHT"           # panah kanan biasa: maju satu kotak
MAT_WAIT_DIALOG = 300        # ms jeda setelah Ctrl+M
# Urutan isi matriks "zig-zag" (ular): baris 1 kiri->kanan, baris 2 kanan->kiri, baris 3
# kiri->kanan, dst. Shift+Enter mendarat di kolom yang sama, jadi tidak perlu lagi balik
# ke kolom 1 tiap baris. Hasil matriks tetap sama. Set False untuk urutan lama.
MAT_SERPENTINE = True
# Mundur dari kotak yang SUDAH terisi: panah kiri sebanyak (jumlah atom isi) + MAT_LEFT_EXTRA.
# Kalau di Prime-mu kursor kurang/lebih mundur, ubah MAT_LEFT_EXTRA (default 1).
MAT_LEFT_EXTRA = 1
# Urutan isi matriks:
#   "column" : (DISARANKAN) isi zig-zag PER KOLOM sambil membangun matriks: kolom 1 turun
#              (Shift+Enter tambah baris), Shift+Spasi tambah kolom, kolom 2 naik (panah Atas),
#              kolom 3 turun (panah Bawah), dst. Tanpa balik ke awal, tanpa hitung panah kiri,
#              TIDAK bergantung bentuk isi sel (subskrip, pecahan, dll aman).
#   "row"    : per baris (zig-zag kanan-kiri), butuh hitungan panah kiri lewat sel terisi.
MAT_ORDER = "column"
MAT_UP = "UP"                # panah atas biasa: pindah satu kotak ke atas
MAT_DOWN = "DOWN"            # panah bawah biasa: pindah satu kotak ke bawah
# Sel dengan subskrip (a[1,1] atau a.1.1): dari posisi sesudah subskrip, panah kiri perlu
# 1x untuk masuk ke subskrip dan 1x untuk keluar lagi dari subskrip, jadi
#   langkah kiri = len(nama) + len(isi subskrip) + MAT_SUB_EXTRA + MAT_LEFT_EXTRA.
# Kalau mundurnya meleset di sel bersubskrip, ubah MAT_SUB_EXTRA (default 2).
MAT_SUB_EXTRA = 2
# Tanda "=" (bukan ':=') diketik dengan Ctrl+= (Boolean/persamaan) bukan "=" biasa
# (di Prime, "=" biasa = evaluasi). Set False untuk kembali ke "=" biasa.
EQ_USE_CTRL = True
# Jeda tambahan setelah tiap Shift+Spasi / Shift+Enter / pindah kotak, supaya Prime sempat
# memproses tiap langkah. Naikkan (mis. 250-400 / 150) kalau masih sering meleset.
MAT_WAIT_STEP = 180          # ms jeda setelah tiap Shift+Spasi / Shift+Enter
MAT_WAIT_CELL = 90           # ms jeda setelah tiap panah kiri/kanan antar kotak
# Sigma/Product/Integral/Limit - TERVERIFIKASI manual untuk Sigma (B->A->K, panah KANAN
# biasa 2x lalu 1x). Integral & Limit memakai pola navigasi yang sama (dikonfirmasi lewat
# deskripsi, belum lewat screenshot B/A/K seperti Sigma) - sesuaikan *_NAV di bawah kalau
# ternyata beda di Prime kamu. Product (Pi) diasumsikan identik strukturnya dengan Sigma.
BIGOP_NAV = "RIGHT"          # panah kanan biasa: pindah antar kotak operator besar
BIGOP_WAIT_DIALOG = 300      # ms jeda setelah chord pembuka (Ctrl+Shift+4 / # / I, Ctrl+L)
BIGOP_WAIT_STEP = 150        # ms jeda setelah tiap panah kanan antar kotak
SUM_CHORD = ("cs", "4")      # Ctrl+Shift+4 -> Σ: [bawah,var=lower] ->(2x)-> [atas,upper] ->(1x)-> [kanan,body]
PROD_CHORD = ("cs", "3")     # Ctrl+Shift+3 (tombol #) -> ∏: diasumsikan sama struktur dengan Sigma
SUM_NAV = (2, 1)             # jumlah panah-kanan: bawah->atas, atas->kanan(body)
INT_CHORD = ("cs", "i")      # Ctrl+Shift+I -> ∫: [bawah,lower] ->(2x)-> [atas,upper] ->(1x)-> [fungsi] ->(1x)-> [dx]
INT_VAR_FIRST = True         # ketik variabel dx DULU (isi masih kosong), lalu kembali (Left) & isi integran
INT_EXIT_PRESSES = 1         # panah kanan setelah melewati isi kotak dx, untuk keluar dari integral
INT_NAV = (2, 1, 2)          # bawah->atas, atas->isi, isi->dx (huruf 'd' tetap = 1 kotak yang dilewati, jadi 2x)
LIM_CHORD = ("c", "l")       # Ctrl+L -> lim: [variabel] ->(2x)-> [nilai didekati] ->(1x)-> [arah] ->(1x)-> [fungsi]
LIM_NAV = (2, 1, 1)          # variabel->nilai, nilai->arah, arah->fungsi
INF_CHORD = ("cs", "z")      # Ctrl+Shift+Z -> simbol tak hingga
BIGOP_EXIT_PRESSES = 1       # tebakan awal: berapa kali EXIT_KEY dari kotak terakhir buat keluar operator
EXIT_KEY = "RIGHT"     # tombol keluar dari pangkat / penyebut / subskrip / akar
GREEK_CHORD = "G"      # Ctrl+G: huruf latin sebelumnya -> huruf Yunani
CHORDS = {"≤": "9", "≥": "0", "≠": "3"}   # Ctrl + tombol

GREEK_TO_LATIN = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "h",
    "θ": "q", "ϑ": "q", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n",
    "ξ": "x", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "u",
    "φ": "f", "χ": "c", "ψ": "y", "ω": "w",
    "Γ": "G", "Δ": "D", "Θ": "Q", "Λ": "L", "Ξ": "X", "Π": "P", "Σ": "S",
    "Υ": "U", "Φ": "F", "Ψ": "Y", "Ω": "W",
}


class ParseError(Exception):
    pass


_ID = r"[A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9]*(?:(?:\.[A-Za-z0-9α-ωΑ-Ω]+)|(?:_[A-Za-z0-9α-ωΑ-Ω]+))*"
TOKEN_RE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)"
    r"|(?P<id>" + _ID + r")"
    r"|(?P<op>:=|<=|>=|!=|[≤≥≠≈±∓°∞!%+\-*/^(),=<>\[\]])"
    r"|(?P<sym>[" + re.escape("".join(sorted(SYM_ALL))) + r"])"
    r"|(?P<ws>\s+)"
)


def tokenize(text):
    toks, i = [], 0
    while i < len(text):
        m = TOKEN_RE.match(text, i)
        if not m:
            raise ParseError(Msg("e_char", ch=text[i], pos=i + 1))
        i = m.end()
        kind = m.lastgroup
        if kind != "ws":
            toks.append((kind, m.group(kind)))
    return toks


class Parser:
    REL = {":=", "=", "<", ">", "<=", ">=", "!=", "≤", "≥", "≠", "≈"}

    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect(self, val):
        k, v = self.next()
        if v != val:
            raise ParseError(Msg("e_expected", val=val, found=v or Msg("end_of_text")))

    def parse(self):
        n = self.rel()
        if self.i != len(self.t):
            raise ParseError(Msg("e_leftover", text=self.peek()[1]))
        return n

    def _is_rel(self):
        k, v = self.peek()
        return (k == "op" and v in self.REL) or (k == "sym" and v in SYM_REL)

    def rel(self):
        n = self.add()
        while self._is_rel():
            op = self.next()[1]
            if op == "=" and self.peek() == (None, None):
                n = ("rel", op, n, ("empty",))     # "... =" di ujung: evaluasi hasil
            else:
                n = ("rel", op, n, self.add())
        return n

    def add(self):
        n = self.mul()
        while (self.peek()[0] == "op" and self.peek()[1] in ("+", "-", "±", "∓")) \
                or (self.peek()[0] == "sym" and self.peek()[1] in SYM_ADD):
            op = self.next()[1]
            n = ("add", op, n, self.mul())
        return n

    def mul(self):
        n = self.unary()
        while True:
            k, v = self.peek()
            if k == "op" and v == "*":
                self.next()
                n = ("mul", n, self.unary())
            elif k == "op" and v == "/":
                self.next()
                n = ("div", n, self.unary())
            elif k in ("num", "id") or (k == "op" and v == "(") \
                    or (k == "sym" and v in SYM_ATOM):
                n = ("mul", n, self.unary())          # perkalian implisit
            else:
                return n

    def unary(self):
        k, v = self.peek()
        if k == "op" and v == "-":
            self.next()
            return ("neg", self.unary())
        if k == "op" and v == "+":
            self.next()
            return self.unary()
        if k == "sym" and v in SYM_PREFIX:                 # ¬p  ∀x  ∃y  ∠A
            self.next()
            return ("usym", v, self.unary())
        return self.pow()

    def pow(self):
        base = self.atom()
        while self.peek() in (("op", "°"), ("op", "!"), ("op", "%")):
            op_ = self.next()[1]
            if op_ == "°":                         # 30° -> 30 deg
                base = ("deg", base)
            elif op_ == "%":                       # 5% -> persen
                base = ("pct", base)
            else:                                  # n! / (2n)! -> faktorial
                base = ("fact", base)
        if self.peek() == ("op", "^"):
            self.next()
            return ("pow", base, self.pow_operand())
        return base

    def pow_operand(self):
        if self.peek() == ("op", "-"):
            self.next()
            return ("neg", self.pow_operand())
        return self.pow()

    def atom(self):
        k, v = self.next()
        if k == "num":
            return ("num", v)
        if k == "id":
            if self.peek() == ("op", "("):
                self.next()
                args = []
                while True:
                    if self.peek() in (("op", ","), ("op", ")")):
                        args.append(("empty",))        # blok kosong, mis. integral tak tentu
                    else:
                        args.append(self.rel())
                    if self.peek() == ("op", ","):
                        self.next()
                        continue
                    break
                self.expect(")")
                return ("call", v, args)
            if self.peek() == ("op", "["):
                self.next()
                args = [self.add()]
                while self.peek() == ("op", ","):
                    self.next()
                    args.append(self.add())
                self.expect("]")
                return ("index", v, args)
            return ("id", v)
        if (k, v) == ("op", "∞"):
            return ("inf",)
        if k == "sym" and v in SYM_ATOM:
            return ("sym", v)
        if (k, v) == ("op", "("):
            inner = self.rel()
            if self.peek() == ("op", ","):                 # (a, b)  /  himpunan {a, b}
                items = [inner]
                while self.peek() == ("op", ","):
                    self.next()
                    items.append(self.rel())
                self.expect(")")
                return ("tuple", items)
            self.expect(")")
            return ("paren", inner)
        raise ParseError(Msg("e_incomplete", found=v or Msg("end_of_text")))


def valid_definition_lhs(n):
    """Sisi kiri ':=' yang sah di Mathcad: variabel, atau f(a,b) dengan argumen
    berupa nama dan f BUKAN fungsi bawaan (tan(2θ) := ... ditolak Prime)."""
    if n[0] in ("id", "index"):
        return True
    if n[0] == "call":
        base = re.match(r"[A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9]*", n[1]).group(0)
        if base.lower() in KNOWN_FUNC_NAMES or base in ("diff", "deriv", "pdiff"):
            return False
        return all(a[0] == "id" for a in n[2])
    return False


DEF_FALLBACK_NOTE = Msg("w_def_fallback")


BIGOP_NAMES = ("sum", "prod", "integral", "limit")


def ends_with_bigop(n):
    """True bila ujung kanan ekspresi adalah Σ/∏/∫/lim (isi operator menelan ketikan berikutnya)."""
    k = n[0]
    if k == "call":
        return n[1] in BIGOP_NAMES
    if k in ("add", "rel"):
        return ends_with_bigop(n[3])
    if k == "mul":
        return ends_with_bigop(n[2])
    if k == "neg":
        return ends_with_bigop(n[1])
    return False


class Emitter:
    """Menghasilkan token: ('t', char, slow) | ('k', nama_tombol, slow) | ('c', tombol, slow)=Ctrl+tombol"""

    def __init__(self, greek_ctrlg=True):
        self.out = []
        self.greek = greek_ctrlg
        self.notes = []

    def T(self, ch, slow=False):
        self.out.append(("t", ch, slow))

    def K(self, name):
        self.out.append(("k", name, True))

    def C(self, key):
        self.out.append(("c", key, True))

    def S(self, key):
        self.out.append(("s", key, True))

    def W(self, ms):
        self.out.append(("w", ms, False))

    def CS(self, key):
        self.out.append(("cs", key, True))

    def text(self, s):
        for ch in s:
            if self.greek and ch in GREEK_TO_LATIN:
                self.T(GREEK_TO_LATIN[ch])
                self.C(GREEK_CHORD)
            elif ch in CHORDS:
                self.C(CHORDS[ch])
            else:
                self.T(ch)

    # -- pembantu ---
    def note_once(self, msg):
        if msg not in self.notes:
            self.notes.append(msg)

    def sym_note(self):
        self.note_once(Msg("w_symbol_unicode"))

    def ident(self, name):
        m = re.match(r"([A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9]*)(.*)$", name)
        self.text(m.group(1))
        subs = re.findall(r"([._])([A-Za-z0-9α-ωΑ-Ω]+)", m.group(2))
        k = 0
        while k < len(subs):
            sep, sub = subs[k]
            if sep == "." and SUB_MODE == "chord":
                parts = [sub]                       # t.i.j -> satu subskrip "i.j"
                while k + 1 < len(subs) and subs[k + 1][0] == ".":
                    k += 1
                    parts.append(subs[k][1])
                self.note_once(Msg("w_sub_keys"))
                self.C(SUB_CHORD)                   # masuk subskrip
                self.text(".".join(parts))
                self.C(SUB_CHORD)                   # kembali ke baseline
            elif sep == ".":
                self.T(KEY_SUBSCRIPT, True)
                self.text(sub)
                self.K(EXIT_KEY)
            else:
                self.T("_")
                self.text(sub)
            k += 1

    def cell_width(self, n):
        """Jumlah 'atom' (langkah panah kiri) untuk melewati isi sel sederhana, atau None
        bila isinya terstruktur (pecahan, pangkat, akar, dst) sehingga hitungannya tak pasti."""
        k = n[0]
        if k == "empty":
            return 0
        if k == "num":
            return len(n[1])
        if k == "id":
            m = re.fullmatch(r"([A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9]*)(.*)", n[1])
            if not m:
                return None
            subs = re.findall(r"([._])([A-Za-z0-9α-ωΑ-Ω]+)", m.group(2))
            if "".join(a + b for a, b in subs) != m.group(2):
                return None
            w = len(m.group(1))
            k2 = 0
            while k2 < len(subs):
                sep, sub = subs[k2]
                if sep == "_":
                    w += 1 + len(sub)                    # '_' diketik sebagai karakter biasa
                elif SUB_MODE == "chord":
                    parts = [sub]
                    while k2 + 1 < len(subs) and subs[k2 + 1][0] == ".":
                        k2 += 1
                        parts.append(subs[k2][1])
                    w += len(".".join(parts)) + MAT_SUB_EXTRA
                else:
                    w += 1 + len(sub) + MAT_SUB_EXTRA
                k2 += 1
            return w
        if k == "index":
            w = self.cell_width(("id", n[1]))
            if w is None:
                return None
            for q, a in enumerate(n[2]):
                wa = self.cell_width(a)
                if wa is None:
                    return None
                w += wa + (1 if q else 0)               # koma antar indeks
            return w + MAT_SUB_EXTRA
        if k == "neg":
            w = self.cell_width(n[1])
            return None if w is None else w + 1
        if k in ("add", "mul"):
            a, b = (n[2], n[3]) if k == "add" else (n[1], n[2])
            wa, wb = self.cell_width(a), self.cell_width(b)
            if wa is None or wb is None:
                return None
            return wa + wb + 1
        return None

    def matrix_column_snake(self, grid, nr, nc):
        """Isi zig-zag per kolom sambil MEMBANGUN matriks (tanpa bangun-dulu, tanpa balik ke
        kiri-atas): kolom 1 atas->bawah (Shift+Enter tambah baris), lalu Shift+Spasi tambah
        kolom baru di kanan (kursor ikut ke baris yang sama), kolom 2 bawah->atas (panah
        Atas), kolom 3 atas->bawah (panah Bawah), dst. Nol perjalanan sia-sia."""
        for r in range(nr):                      # kolom 1: turun, baris ditambah sambil jalan
            self.node(self.unparen(grid[r][0]))
            if r < nr - 1:
                self.S(MAT_ADD_ROW)
                self.W(MAT_WAIT_STEP)
        for c in range(1, nc):                   # kursor sekarang di baris terakhir kolom c-1
            self.S(MAT_ADD_COL)                  # kolom baru di kanan, kursor di baris yang sama
            self.W(MAT_WAIT_STEP)
            going_up = (c % 2 == 1)              # kolom ganjil (indeks 1,3,..) diisi dari bawah
            rows = range(nr - 1, -1, -1) if going_up else range(nr)
            for i, r in enumerate(rows):
                if i:
                    self.K(MAT_UP if going_up else MAT_DOWN)
                    self.W(MAT_WAIT_CELL)
                self.node(self.unparen(grid[r][c]))

    def wrapped(self, n):
        self.T("(")
        self.node(n)
        self.T(")")

    def unparen(self, n):
        return n[1] if n[0] == "paren" else n

    # -- operator besar (Sigma, Pi, Integral, Limit) ---
    def bigop_open(self, chord):
        if chord[0] == "cs":
            self.CS(chord[1])
        else:
            self.C(chord[1])
        self.W(BIGOP_WAIT_DIALOG)

    def bigop_right(self, times):
        for _ in range(times):
            self.K(BIGOP_NAV)
            self.W(BIGOP_WAIT_STEP)

    def bigop_fill(self, n):
        if n[0] != "empty":
            self.node(self.unparen(n))

    def bigop_exit(self, presses=None):
        for _ in range(BIGOP_EXIT_PRESSES if presses is None else presses):
            self.K(EXIT_KEY)

    # -- node ---
    def node(self, n):
        kind = n[0]
        if kind == "num":
            self.text(n[1])
        elif kind == "id":
            self.ident(n[1])
        elif kind == "empty":
            pass
        elif kind == "inf":
            self.CS(INF_CHORD[1])
        elif kind == "tuple":                    # (a, b)
            self.note_once(Msg("w_tuple"))
            self.T("(")
            for q, a in enumerate(n[1]):
                if q:
                    self.T(",")
                self.node(a)
            self.T(")")
        elif kind == "sym":                      # ∅ ℏ ∇ ... : karakter Unicode
            self.sym_note()
            self.T(n[1])
        elif kind == "usym":                     # ¬p ∀x ∃y ∠A
            self.sym_note()
            self.T(n[1])
            self.node(n[2])
        elif kind == "pct":                      # 5%  /  (a+b)%
            base = n[1]
            if base[0] in ("neg", "add", "mul", "div", "rel", "pow", "deg", "fact", "pct") \
                    or ends_with_bigop(base):
                self.wrapped(base)
            else:
                self.node(base)
            self.T("%")
        elif kind == "index":
            self.ident(n[1])
            self.T("[", True)                 # indeks array: x[n+1]
            for k, a in enumerate(n[2]):
                if k:
                    self.T(",")
                self.node(a)
            self.K(EXIT_KEY)
        elif kind == "deg":
            self.node(n[1])
            self.text(KEY_DEG)                # 30deg -> Prime mengenali unit deg
        elif kind == "fact":
            base = n[1]
            if base[0] in ("neg", "add", "mul", "div", "rel", "pow", "deg", "fact") \
                    or ends_with_bigop(base):
                self.wrapped(base)            # (a+b)! : kurung supaya ! berlaku ke semuanya
            else:
                self.node(base)
            self.T("!")                       # faktorial postfix di Prime
        elif kind == "neg":
            self.T("-")
            self.node(n[1])
        elif kind == "paren":
            self.wrapped(n[1])
        elif kind == "add":
            # Σ/∏/∫ yang diikuti "+": dibungkus kurung supaya operan kiri "+" jelas
            # (tanpa kurung, Prime menganggap "+" tidak punya operan kiri).
            if ends_with_bigop(n[2]) or (n[2][0] == "call" and n[2][1] in ("diff", "deriv", "pdiff")):
                self.wrapped(n[2])
            else:
                self.node(n[2])
            if n[1] in SYM_ADD:
                self.sym_note()
            self.text(n[1])
            if n[3][0] == "call" and n[3][1] in ("diff", "deriv", "pdiff"):
                self.wrapped(n[3])
            else:
                self.node(n[3])
        elif kind == "mul":
            left = n[1]
            if left[0] == "paren" and left[1][0] == "div":
                left = left[1]                    # (1/2)*x : pecahan sudah tertutup sendiri
            if ends_with_bigop(left):
                self.wrapped(left)
            else:
                self.node(left)
            self.T("*")
            self.node(n[2])
        elif kind == "rel":
            op = {"<=": "≤", ">=": "≥", "!=": "≠"}.get(n[1], n[1])
            if op == ":=" and not valid_definition_lhs(n[2]):
                op = "="
                if DEF_FALLBACK_NOTE not in self.notes:
                    self.notes.append(DEF_FALLBACK_NOTE)
            if (n[2][0] == "call" and n[2][1] in ("diff", "deriv", "pdiff")) \
                    or ends_with_bigop(n[2]):
                self.wrapped(n[2])                  # (∂²u/∂t²) = ... : operan kiri jelas
            else:
                self.node(n[2])
            if n[3][0] == "empty" and op == "=":
                self.T("=")                         # "=" di ujung = evaluasi (bukan Ctrl+=)
                return
            if op in SYM_REL:
                self.sym_note()
            if op == ":=":
                self.T(KEY_DEF, True)
            elif op == "=" and EQ_USE_CTRL:
                self.C("=")                         # Ctrl+= (persamaan/boolean)
                self.W(EQ_WAIT_AFTER)
            else:
                self.text(op)
            self.node(n[3])
        elif kind == "div":
            num = n[1]
            if num[0] in ("neg", "add", "mul", "rel") or ends_with_bigop(num):
                self.wrapped(num)
            else:
                self.node(num)
            self.T(KEY_FRAC, True)
            self.node(self.unparen(n[2]))
            self.K(EXIT_KEY)
        elif kind == "pow":
            base = n[1]
            # (sin(x))^2 : kurung luar dibuang supaya urutan ketikan sama dengan
            # sin(x)^2 (yang benar di Prime). Kalau tidak, Prime menghasilkan sin((x)^2).
            while base[0] == "paren" and base[1][0] in ("call", "id", "num", "index", "paren"):
                base = base[1]
            if base[0] in ("neg", "add", "mul", "div", "rel") or ends_with_bigop(base):
                self.wrapped(base)
            elif POW_WRAP_CALL and base[0] == "call" and base[1] in POW_WRAP_FUNCS:
                self.wrapped(base)          # (sin(xy))^3 : kalau tidak, Prime memangkatkan argumennya
            else:
                self.node(base)
            if TRANSPOSE_T and n[2] == ("id", "T"):
                self.C(TRANSPOSE_CHORD[1])          # B^T : transpose matriks (Ctrl+1)
                self.W(EQ_WAIT_AFTER // 3)
                return
            self.T(KEY_POWER, True)
            self.node(self.unparen(n[2]))
            self.K(EXIT_KEY)
        elif kind == "call":
            name, args = n[1], n[2]
            if name == "sqrt" and len(args) == 1:
                self.T(KEY_SQRT, True)
                self.node(self.unparen(args[0]))
                self.K(EXIT_KEY)
            elif ((name == "det") or (name == "abs" and ABS_USE_BARS)) and len(args) == 1 and KEY_ABS:
                self.T(KEY_ABS, True)               # |x|
                self.W(ABS_WAIT_OPEN)
                self.node(self.unparen(args[0]))
                self.K(EXIT_KEY)
            elif name in ("diff", "deriv", "pdiff") and len(args) in (2, 3) and args[1][0] == "id":
                order, order_node = 1, None
                if len(args) == 3:
                    if args[2][0] == "num" and args[2][1].isdigit() and int(args[2][1]) >= 1:
                        order = int(args[2][1])
                    elif args[2][0] == "id" and NDERIV_NATIVE:
                        order, order_node = 2, args[2]       # tingkat simbolik (n): operator nth
                    else:
                        raise ParseError(Msg("e_deriv_order"))
                if (order > 1 or FIRST_DERIV_USE_NTH) and NDERIV_NATIVE:
                    # d^n/dx^n f : Ctrl+Shift+D -> variabel -> tingkat -> fungsi
                    self.note_once(Msg("w_nderiv_native"))
                    chord = PDERIV_CHORD if name == "pdiff" else NDERIV_CHORD   # ∂ : Ctrl+D
                    if chord[0] == "cs":
                        self.CS(chord[1])
                    else:
                        self.C(chord[1])
                    self.W(NDERIV_WAIT_DIALOG)
                    self.ident(args[1][1])
                    self.K(NDERIV_NAV[0])
                    self.W(NDERIV_WAIT_STEP)
                    if order_node or order > 1 or FIRST_DERIV_SHOW_ORDER:
                        self.node(order_node if order_node else ("num", str(order)))
                    # tingkat 1: kotak tingkat dibiarkan kosong (tampil d/dx), cukup dilewati
                    self.K(NDERIV_NAV[1])
                    self.W(NDERIV_WAIT_STEP)
                    self.node(self.unparen(args[0]))
                    self.K(EXIT_KEY)
                    self.W(NDERIV_WAIT_EXIT)
                else:
                    if order > 1:
                        self.note_once(Msg("w_nderiv_type"))
                    for _ in range(order):
                        self.T(KEY_DERIV, True)
                        self.ident(args[1][1])
                        self.K(EXIT_KEY)
                    self.node(self.unparen(args[0]))
                    for _ in range(order):
                        self.K(EXIT_KEY)
            elif name == "mat" and len(args) >= 3 and args[0][0] == "num" and args[1][0] == "num":
                nr, nc, cells = int(args[0][1]), int(args[1][1]), args[2:]
                if nr * nc != len(cells) or nr < 1 or nc < 1:
                    raise ParseError(Msg("e_matrix_size"))
                self.note_once(Msg("w_matrix_keys"))
                grid = [cells[r * nc:(r + 1) * nc] for r in range(nr)]
                self.C(MAT_CHORD)
                self.W(MAT_WAIT_DIALOG)
                if MAT_ORDER == "column":
                    self.matrix_column_snake(grid, nr, nc)
                else:
                    # Baris pertama: isi kotak 1x1 yang sudah ada, lalu Shift+Spasi untuk tiap
                    # kolom tambahan (kursor otomatis pindah ke kotak baru setelah Shift+Spasi).
                    self.node(self.unparen(grid[0][0]))
                    for c in range(1, nc):
                        self.S(MAT_ADD_COL)
                        self.W(MAT_WAIT_STEP)
                        self.node(self.unparen(grid[0][c]))
                    # Baris berikutnya: Shift+Enter menambah baris baru, kursor mendarat di kolom
                    # yang SAMA dengan posisi sebelumnya. Pola zig-zag:
                    #   - kursor di kolom terakhir -> isi baris ini dari KANAN ke KIRI
                    #   - kursor di kolom pertama  -> isi baris ini dari KIRI ke KANAN
                    # sehingga tidak ada lagi perjalanan panjang balik ke kolom 1.
                    at_right = True                     # baris 1 selesai di kolom terakhir
                    for r in range(1, nr):
                        self.S(MAT_ADD_ROW)
                        self.W(MAT_WAIT_STEP)
                        row = grid[r]
                        cells_u = [self.unparen(x) for x in row]
                        widths = [self.cell_width(x) for x in cells_u]
                        if nc == 1:
                            self.node(cells_u[0])
                        elif at_right and MAT_SERPENTINE and None not in widths:
                            for c in range(nc - 1, -1, -1):          # kanan -> kiri
                                self.node(cells_u[c])
                                if c > 0:
                                    for _ in range(widths[c] + MAT_LEFT_EXTRA):
                                        self.K(MAT_LEFT)
                                    self.W(MAT_WAIT_CELL)
                            at_right = False
                        elif at_right:
                            # isi sel rumit: cara lama (mundur lewat sel kosong, lalu isi ke kanan)
                            for _ in range(nc - 1):
                                self.K(MAT_LEFT)
                                self.W(MAT_WAIT_CELL)
                            for c in range(nc):
                                if c:
                                    self.K(MAT_NEXT)
                                    self.W(MAT_WAIT_CELL)
                                self.node(cells_u[c])
                        else:
                            for c in range(nc):                      # kiri -> kanan
                                if c:
                                    self.K(MAT_NEXT)
                                    self.W(MAT_WAIT_CELL)
                                self.node(cells_u[c])
                            at_right = True
                self.K(EXIT_KEY)
            elif name in ("sum", "prod") and len(args) == 4:
                # Sigma / Pi: [bawah: var=lower] -> [atas] -> [isi]
                self.note_once(Msg("w_bigop_keys"))
                var, lo, up, body = args
                self.bigop_open(SUM_CHORD if name == "sum" else PROD_CHORD)
                self.node(var)
                if lo[0] != "empty":
                    self.T("=")
                    self.node(self.unparen(lo))
                self.bigop_right(SUM_NAV[0])
                self.bigop_fill(up)
                self.bigop_right(SUM_NAV[1])
                self.bigop_fill(body)
                self.bigop_exit()
            elif name == "integral" and len(args) == 4:
                # Integral: [bawah] -> [atas] -> [fungsi] -> [dx]
                self.note_once(Msg("w_bigop_keys"))
                lo, up, body, var = args
                self.bigop_open(INT_CHORD)
                self.bigop_fill(lo)
                self.bigop_right(INT_NAV[0])
                self.bigop_fill(up)
                self.bigop_right(INT_NAV[1])
                if INT_VAR_FIRST:
                    # isi integran masih kosong -> pindah ke dx tidak bergantung pada isi integran
                    self.bigop_right(INT_NAV[2])
                    self.bigop_fill(var)
                    nvar = len(re.match(r"[^._]*", var[1]).group(0)) if var[0] == "id" else 1
                    for _ in range(nvar + INT_NAV[2]):     # kembali: lewati isi dx + kotak
                        self.K("LEFT")
                        self.W(BIGOP_WAIT_STEP)
                    self.bigop_fill(body)
                    # dari akhir isi: ke kotak dx (INT_NAV[2]x), lewati isi dx (nvar x), lalu keluar
                    self.bigop_exit(INT_NAV[2] + nvar + INT_EXIT_PRESSES)
                else:
                    self.bigop_fill(body)
                    self.bigop_right(INT_NAV[2])
                    self.bigop_fill(var)
                    self.bigop_exit()
            elif name == "limit" and len(args) in (3, 4):
                # Limit: [variabel] -> [nilai] -> [arah +/-] -> [fungsi]
                self.note_once(Msg("w_bigop_keys"))
                var, pt, body = args[0], args[1], args[2]
                self.bigop_open(LIM_CHORD)
                self.bigop_fill(var)
                self.bigop_right(LIM_NAV[0])
                self.bigop_fill(pt)
                self.bigop_right(LIM_NAV[1])
                if len(args) == 4:
                    self.T("-" if args[3] == ("neg", ("num", "1")) else "+")
                self.bigop_right(LIM_NAV[2])
                self.bigop_fill(body)
                self.bigop_exit()
            elif name == "root" and len(args) == 2:
                # akar pangkat n  ->  (x)^(1/n)
                x = args[0]
                base = x if x[0] in ("num", "id", "paren", "call") else ("paren", x)
                self.node(("pow", base, ("div", ("num", "1"), args[1])))
            else:
                self.ident(name)
                self.T("(")
                for k, a in enumerate(args):
                    if k:
                        self.T(",")
                    self.node(a)
                self.T(")")
        else:  # pragma: no cover
            raise ParseError(Msg("e_node", kind=kind))


def build_plan(linear_text, greek_ctrlg=True):
    """Teks linear -> (daftar token ketikan, daftar peringatan)."""
    lines = [ln for ln in linear_text.strip().split("\n") if ln.strip()]
    if not lines:
        raise ParseError(Msg("e_no_text_type"))
    warns = []
    if len(lines) > 1:
        warns.append(Msg("w_multiline_type"))
    line = lines[0]
    if "±" in line or "∓" in line:
        warns.append(Msg("w_pm"))
    ast = Parser(tokenize(line)).parse()
    em = Emitter(greek_ctrlg)
    em.node(ast)
    return em.out, warns + em.notes


def describe_plan(plan):
    parts = []
    for kind, val, _slow in plan:
        if kind == "t":
            parts.append(val)
        elif kind == "k":
            parts.append("[→]" if val == "RIGHT" else f"[{val}]")
        elif kind == "w":
            parts.append(f"[wait {val}ms]")
        elif kind == "s":
            parts.append(f"[Shift+{val}]")
        elif kind == "cs":
            parts.append(f"[Ctrl+Shift+{val}]")
        else:
            parts.append(f"[Ctrl+{val}]")
    return " ".join(parts)


# ---------------- pengirim tombol (Windows) ----------------------------------
class WinTyper:
    VK = {"RIGHT": 0x27, "LEFT": 0x25, "UP": 0x26, "DOWN": 0x28,
          "SPACE": 0x20, "ENTER": 0x0D, "TAB": 0x09}
    OEM = {"/": 0xBF, ".": 0xBE, ",": 0xBC, ";": 0xBA, "\\": 0xDC, "-": 0xBD, "=": 0xBB}
    EXTENDED = {"RIGHT", "LEFT", "UP", "DOWN"}

    def __init__(self, real_keys=True):
        import ctypes
        from ctypes import wintypes
        self.ctypes, self.real_keys = ctypes, real_keys
        self.user32 = ctypes.windll.user32
        self.user32.VkKeyScanW.argtypes = [wintypes.WCHAR]
        self.user32.VkKeyScanW.restype = ctypes.c_short

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_void_p)]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.c_void_p)]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                        ("wParamH", wintypes.WORD)]

        class _U(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

        class INPUT(ctypes.Structure):
            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _U)]

        self.INPUT, self.KEYBDINPUT = INPUT, KEYBDINPUT

    def _send(self, vk=0, scan=0, flags=0):
        inp = self.INPUT(type=1)
        inp.ki = self.KEYBDINPUT(vk, scan, flags, 0, None)
        self.user32.SendInput(1, self.ctypes.byref(inp), self.ctypes.sizeof(self.INPUT))

    def _vk(self, vk, mods=(), extended=False):
        ext = 0x1 if extended else 0
        for m in mods:
            self._send(m)
        self._send(vk, 0, ext)
        self._send(vk, 0, ext | 0x2)
        for m in reversed(mods):
            self._send(m, 0, 0x2)

    def _unicode(self, ch):
        data = ch.encode("utf-16-le")
        for k in range(0, len(data), 2):
            code = int.from_bytes(data[k:k + 2], "little")
            self._send(0, code, 0x4)
            self._send(0, code, 0x4 | 0x2)

    def char(self, ch):
        if self.real_keys:
            res = self.user32.VkKeyScanW(ch)
            if res != -1:
                vk, st = res & 0xFF, (res >> 8) & 0xFF
                mods = []
                if st & 1:
                    mods.append(0x10)
                if st & 2:
                    mods.append(0x11)
                if st & 4:
                    mods.append(0x12)
                self._vk(vk, mods)
                return
        self._unicode(ch)

    def send(self, tok):
        kind, val, _slow = tok
        if kind == "t":
            self.char(val)
        elif kind == "k":
            self._vk(self.VK[val], extended=val in self.EXTENDED)
        elif kind in ("c", "cs", "s"):
            vk = self.VK.get(val) or self.OEM.get(val) or ord(val.upper())
            mods = {"c": [0x11], "cs": [0x11, 0x10], "s": [0x10]}[kind]
            self._vk(vk, mods=mods, extended=val in self.EXTENDED)


def own_window_has_focus():
    """True jika jendela di depan milik program ini (bukan Mathcad)."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value == os.getpid()
    except Exception:
        return False


# ----------------------------------------------------------------------------
# FORMAT TEKS INTERNAL MATHCAD PRIME  (mirip Lisp):  (@EQ ...)  (@APPLY ...)
#
# Teks seperti ini bisa di-paste ke "math placeholder" KOSONG di Prime dan
# langsung menjadi rumus (tanpa tanda kutip). Sumber contoh:
#   https://community.ptc.com/t5/Mathcad/Pasting-MathCAD-code-from-Chatgpt-need-to-be-manullay-typed/m-p/1033783
#
# TERVERIFIKASI (ada contoh nyata dari Prime):
#   (@EQ a b)                      persamaan  a = b
#   (+ a b)   (* a b)   (^ a b)    tambah, kali, pangkat (biner, bersarang)
#   (@ID V (@SUB x))               variabel V dengan subskrip x
#   (@APPLY f (@ARGS t))           pemanggilan fungsi f(t)
#   (@DERIV t @PLACEHOLDER expr)   turunan d/dt dari expr
#   D, M, t, 2                     nama variabel / angka ditulis apa adanya
#
# BELUM TERVERIFIKASI (tebakan; bisa diubah lewat menu "Kalibrasi format"):
#   definisi :=, pengurangan, pembagian, minus unary, akar, relasi < > <= >=
# ----------------------------------------------------------------------------
SX_CHOICES = {
    "define": ("cal_define",
               ["(:= {a} {b})", "(@DEFINE {a} {b})", "(@DEF {a} {b})",
                "(@ASSIGN {a} {b})"]),
    "sub": ("cal_sub",
            ["(- {a} {b})", "(@MINUS {a} {b})", "(@SUBTRACT {a} {b})"]),
    "div": ("cal_div",
            ["(/ {a} {b})", "(@DIV {a} {b})", "(@FRAC {a} {b})"]),
    "neg": ("cal_neg",
            ["(-{a})", "(* -1 {a})", "(- 0 {a})", "(@NEG {a})", "(@MINUS {a})"]),
    "sqrt": ("cal_sqrt",
             ["(@NTHROOT @PLACEHOLDER {a})", "POW", "(@NTHROOT {a} 2)", "(@NTHROOT 2 {a})",
              "(@APPLY sqrt (@ARGS {a}))",
              "(√ {a})", "(@RADICAL {a})", "(@SQRT {a})", "(@ROOT {a})",
              "(sqrt {a})",
              "(@ROOT {a} 2)", "(@ROOT 2 {a})", "(@SQUARE_ROOT {a})"]),
    "abs": ("cal_abs",
            ["(@ABS {a})", "(@APPLY abs (@ARGS {a}))", "(@VERT {a})", "(@ABSVAL {a})",
             "(| {a})", "(@BARS {a})", "(@MODULUS {a})", "(@MAG {a})"]),
    "nderiv": ("cal_nderiv",
               ["NEST", "(@DERIV {v} {n} @PLACEHOLDER {a})", "(@NDERIV {v} {n} @PLACEHOLDER {a})",
                "(@DERIV {v} @PLACEHOLDER {a} {n})"]),
    "index": ("cal_index",
              ["(@ID {a} (@SUB {b}))", "(@INDEX {a} {b})", "(@SUBSCRIPT {a} {b})",
               "(@IDX {a} {b})", "(@ELEMENT {a} {b})", "(@ARRAYREF {a} {b})"]),
    "rel_lt": ("cal_rel_lt",
               ["(< {a} {b})", "(@LT {a} {b})", "(@LESS {a} {b})", "(@LESSTHAN {a} {b})",
                "(@LESS_THAN {a} {b})", "(@LSS {a} {b})"]),
    "rel_gt": ("cal_rel_gt",
               ["(> {a} {b})", "(@GT {a} {b})", "(@GREATER {a} {b})", "(@GREATERTHAN {a} {b})",
                "(@GREATER_THAN {a} {b})", "(@GTR {a} {b})"]),
    "rel_le": ("cal_rel_le",
               ["(<= {a} {b})", "(≤ {a} {b})", "(@LE {a} {b})", "(@LTE {a} {b})",
                "(@LEQ {a} {b})", "(@LESSEQ {a} {b})", "(@LESSEQUAL {a} {b})",
                "(@LESS_EQUAL {a} {b})"]),
    "rel_ge": ("cal_rel_ge",
               ["(>= {a} {b})", "(≥ {a} {b})", "(@GE {a} {b})", "(@GTE {a} {b})",
                "(@GEQ {a} {b})", "(@GREATEREQ {a} {b})", "(@GREATEREQUAL {a} {b})",
                "(@GREATER_EQUAL {a} {b})"]),
    "rel_ne": ("cal_rel_ne",
               ["(!= {a} {b})", "(≠ {a} {b})", "(@NE {a} {b})", "(@NEQ {a} {b})",
                "(@NOTEQUAL {a} {b})", "(@NOT_EQUAL {a} {b})"]),
    "nroot": ("cal_nroot",
              ["(@NTHROOT {n} {a})", "POW", "(√ {n} {a})", "(√ {a} {n})",
               "(@NTHROOT {a} {n})", "(@ROOT {n} {a})", "(@ROOT {a} {n})",
               "(@RADICAL {n} {a})"]),
}
# Petunjuk untuk fitur "Pelajari dari teks Prime": apa yang diketik di Prime,
# dan nama variabel contoh yang dipakai untuk menandai {a}, {b}, {n}.
SX_LEARN = {
    "define": ("hint_define", {"a": "x", "b": "y"}),
    "sub": ("hint_sub", {"a": "x", "b": "y"}),
    "div": ("hint_div", {"a": "x", "b": "y"}),
    "neg": ("hint_neg", {"a": "x"}),
    "sqrt": ("hint_sqrt", {"a": "x"}),
    "nroot": ("hint_nroot", {"a": "x", "n": "y"}),
    "index": ("hint_index", {"a": "x", "b": "y"}),
    "abs": ("hint_abs", {"a": "x"}),
    "rel_lt": ("hint_rel_lt", {"a": "x", "b": "y"}),
    "rel_gt": ("hint_rel_gt", {"a": "x", "b": "y"}),
    "rel_le": ("hint_rel_le", {"a": "x", "b": "y"}),
    "rel_ge": ("hint_rel_ge", {"a": "x", "b": "y"}),
    "rel_ne": ("hint_rel_ne", {"a": "x", "b": "y"}),
    "nderiv": ("hint_nderiv", {"v": "x", "n": "y", "a": "z"}),
}
SX_TPL = {k: v[1][0] for k, v in SX_CHOICES.items()}
# Minus unary di depan ekspresi majemuk, mis. -(x^2). "(-(^ x 2))" TIDAK diterima Prime.
# "(* -1 {a})" selalu terbaca (tampil -1·x^2). Alternatif: "(- 0 {a})" (tampil 0 - x^2).
NEG_COMPOUND = "(* -1 {a})"
SX_REL = {"<": "(< {a} {b})", ">": "(> {a} {b})", "<=": "(<= {a} {b})",
          ">=": "(>= {a} {b})", "≤": "(<= {a} {b})", "≥": "(>= {a} {b})",
          "!=": "(!= {a} {b})", "≠": "(!= {a} {b})", "≈": "(≈ {a} {b})"}


SX_REL_KEY = {"<": "rel_lt", ">": "rel_gt", "<=": "rel_le", "≤": "rel_le",
              ">=": "rel_ge", "≥": "rel_ge", "!=": "rel_ne", "≠": "rel_ne"}


def sx_fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("{" + k + "}", v)
    return tpl


def sx_sample(key, tpl=None):
    """Contoh kecil untuk menguji satu konstruksi di Prime."""
    tpl = tpl or SX_TPL
    if key == "define":
        return sx_fill(tpl["define"], a="x", b="2")
    if key == "sub":
        return sx_fill(tpl["sub"], a="5", b="2")
    if key == "div":
        return sx_fill(tpl["div"], a="1", b="2")
    if key == "neg":
        return sx_fill(tpl["neg"], a="x")
    if key == "sqrt":
        if tpl["sqrt"] == "POW":
            return "(^ x " + sx_fill(tpl["div"], a="1", b="2") + ")"
        return sx_fill(tpl["sqrt"], a="x")
    if key == "index":
        return sx_fill(tpl["index"], a="x", b="n")
    if key == "abs":
        return sx_fill(tpl["abs"], a="x")
    if key.startswith("rel_"):
        return sx_fill(tpl[key], a="x", b="y")
    if key == "nderiv":
        if tpl["nderiv"] == "NEST":
            return "(@DERIV x @PLACEHOLDER (@DERIV x @PLACEHOLDER y))"
        return sx_fill(tpl["nderiv"], v="x", n="2", a="y")
    if key == "nroot":
        if tpl["nroot"] == "POW":
            return "(^ x " + sx_fill(tpl["div"], a="1", b="3") + ")"
        return sx_fill(tpl["nroot"], a="x", n="3")
    return ""


class SexprBuilder:
    def __init__(self, tpl=None):
        self.tpl = tpl or SX_TPL
        self.unverified = []
        self.notes = []

    # sudah terbukti jalan di Prime (hasil uji pengguna): definisi, / dan -
    VERIFIED = {"u_div", "u_sub", "u_define"}

    def mark(self, key, **params):
        if key in self.VERIFIED:
            return
        label = Msg(key, **params)
        if label not in self.unverified:
            self.unverified.append(label)

    def ident(self, name):
        m = re.match(r"([A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9]*)(.*)$", name)
        base = m.group(1)
        subs = [s for _sep, s in re.findall(r"([._])([A-Za-z0-9α-ωΑ-Ω]+)", m.group(2))]
        if subs:
            return f"(@ID {base} (@SUB {'.'.join(subs)}))"
        return base

    def infix(self, n):
        """Node -> teks infix biasa (untuk isi subskrip), mis. n+1, 2*n-1."""
        k = n[0]
        if k in ("num", "id"):
            return n[1].replace(".", "").replace("_", "") if k == "id" else n[1]
        if k == "paren":
            return "(" + self.infix(n[1]) + ")"
        if k == "inf":
            return "∞"
        if k == "empty":
            return ""
        if k == "deg":
            return self.infix(n[1]) + "deg"
        if k == "fact":
            return self.infix(n[1]) + "!"
        if k == "neg":
            return "-" + self.infix(n[1])
        if k == "add":
            return self.infix(n[2]) + n[1] + self.infix(n[3])
        if k == "mul":
            return self.infix(n[1]) + "*" + self.infix(n[2])
        if k == "div":
            return self.infix(n[1]) + "/" + self.infix(n[2])
        if k == "pow":
            return self.infix(n[1]) + "^" + self.infix(n[2])
        if k == "call":
            return n[1] + "(" + ",".join(self.infix(a) for a in n[2]) + ")"
        raise ParseError(Msg("e_node", kind=k))

    def deriv(self, var, expr, order=1):
        """Turunan tingkat ke-n = n turunan pertama yang bersarang (sintaks (@DERIV ..)
        terverifikasi). Contoh orde 2: (@DERIV t @PLACEHOLDER (@DERIV t @PLACEHOLDER y))."""
        if not isinstance(order, int) or order < 1:
            raise ParseError(Msg("e_deriv_order"))
        if order > 1:
            self.mark("u_nderiv")
        out = self.node(expr)
        v = self.ident(var)
        if order > 1 and self.tpl.get("nderiv", "NEST") != "NEST":
            return sx_fill(self.tpl["nderiv"], v=v, n=str(order), a=out)
        for _ in range(order):
            out = f"(@DERIV {v} @PLACEHOLDER {out})"
        return out

    def node(self, n):
        kind = n[0]
        if kind == "num":
            return n[1]
        if kind == "id":
            return self.ident(n[1])
        if kind == "paren":
            return self.node(n[1])
        if kind == "inf":
            return "∞"
        if kind == "empty":
            return ""
        if kind in ("sym", "usym", "pct"):
            raise ParseError(Msg("e_sym_sexpr", sym=n[1] if kind != "pct" else "%"))
        if kind == "tuple":
            raise ParseError(Msg("e_sym_sexpr", sym=","))
        if kind == "index":
            base = re.match(r"[A-Za-zα-ωΑ-Ω][A-Za-zα-ωΑ-Ω0-9]*", n[1]).group(0)
            # Hasil uji pengguna: isi @SUB berupa teks infix dalam kurung, mis. (n+1)
            return sx_fill(self.tpl["index"], a=base,
                           b="(" + ",".join(self.infix(a) for a in n[2]) + ")")
        if kind == "deg":
            self.mark("u_deg")
            return f"(* {self.node(n[1])} deg)"
        if kind == "fact":
            self.mark("u_fact")
            return f"(! {self.node(n[1])})"
        if kind == "neg":
            self.mark("u_neg")
            inner = n[1]
            while inner[0] == "paren":
                inner = inner[1]
            if inner[0] == "num":                  # -2 tetap angka negatif, bukan -1*2
                return "-" + inner[1]
            body = self.node(n[1])
            if inner[0] == "id" and "(" not in body and " " not in body:
                return sx_fill(self.tpl["neg"], a=body)      # (-x): terbukti jalan di Prime
            # Minus di depan ekspresi majemuk: "(-(^ x 2))" ditolak Prime (jadi string).
            if inner[0] == "mul":                  # -(a*b) -> (* -a b)
                return f"(* {self.node(('neg', inner[1]))} {self.node(inner[2])})"
            if inner[0] == "div":                  # -(a/b) -> (/ -a b)
                return sx_fill(self.tpl["div"], a=self.node(("neg", inner[1])),
                               b=self.node(inner[2]))
            return sx_fill(NEG_COMPOUND, a=body)
        if kind == "add":
            op = n[1]
            if op in ("±", "∓"):
                raise ParseError(Msg("w_pm"))
            if op not in ("+", "-"):
                raise ParseError(Msg("e_sym_sexpr", sym=op))
            rhs = n[3]
            while rhs[0] == "paren" and rhs[1][0] == "neg":
                rhs = rhs[1]
            if rhs[0] == "neg" and op in ("+", "-"):   # a + -b -> a - b ; a - -b -> a + b
                op = "-" if op == "+" else "+"
                rhs = rhs[1]
            if op == "+" and n[2][0] == "neg":          # -a + b -> b - a (tanpa -1*)
                self.mark("u_sub")
                return sx_fill(self.tpl["sub"], a=self.node(rhs), b=self.node(n[2][1]))
            a, b = self.node(n[2]), self.node(rhs)
            if op == "+":
                return f"(+ {a} {b})"
            self.mark("u_sub")
            return sx_fill(self.tpl["sub"], a=a, b=b)
        if kind == "mul":
            left = n[1]
            # d/dt * expr  ->  turunan
            if (left[0] == "div" and left[1] == ("id", "d")
                    and left[2][0] == "id" and re.match(r"^d[A-Za-z]\w*$", left[2][1])):
                return self.deriv(left[2][1][1:], n[2])
            return f"(* {self.node(n[1])} {self.node(n[2])})"
        if kind == "div":
            num, den = n[1], n[2]
            # d/dt(expr)  ->  turunan (dt(expr) terbaca sebagai pemanggilan fungsi)
            if num == ("id", "d") and den[0] == "call" and re.match(r"^d[A-Za-z]\w*$", den[1]) \
                    and len(den[2]) == 1:
                return self.deriv(den[1][1:], den[2][0])
            self.mark("u_div")
            return sx_fill(self.tpl["div"], a=self.node(num), b=self.node(den))
        if kind == "pow":
            return f"(^ {self.node(n[1])} {self.node(n[2])})"
        if kind == "rel":
            if n[3][0] == "empty":                  # "... =" di ujung: buang, Prime menghitung sendiri
                return self.node(n[2])
            op, a, b = n[1], self.node(n[2]), self.node(n[3])
            if op == "=":
                return f"(@EQ {a} {b})"
            if op == ":=" and not valid_definition_lhs(n[2]):
                if DEF_FALLBACK_NOTE not in self.notes:
                    self.notes.append(DEF_FALLBACK_NOTE)
                return f"(@EQ {a} {b})"
            if op == ":=":
                self.mark("u_define")
                return sx_fill(self.tpl["define"], a=a, b=b)
            if op not in SX_REL:
                raise ParseError(Msg("e_sym_sexpr", sym=op))
            self.mark("u_rel", op=op)
            rkey = SX_REL_KEY.get(op)
            return sx_fill(self.tpl.get(rkey) or SX_REL[op], a=a, b=b)
        if kind == "call":
            name, args = n[1], n[2]
            if name == "mat":
                raise ParseError(Msg("e_matrix_sexpr"))
            if name in ("sum", "prod", "integral", "limit"):
                raise ParseError(Msg("e_bigop_sexpr"))
            if name == "sqrt" and len(args) == 1:
                if self.tpl["sqrt"] == "POW":      # akar kuadrat sebagai pangkat 1/2
                    return f"(^ {self.node(args[0])} " + sx_fill(self.tpl["div"], a="1", b="2") + ")"
                self.mark("u_sqrt")
                return sx_fill(self.tpl["sqrt"], a=self.node(args[0]))
            if name == "abs" and len(args) == 1:
                self.mark("u_abs")
                return sx_fill(self.tpl["abs"], a=self.node(args[0]))
            if name == "root" and len(args) == 2:
                self.mark("u_nroot")
                a, nn = self.node(args[0]), self.node(args[1])
                if self.tpl["nroot"] == "POW":
                    self.mark("u_div")
                    return f"(^ {a} " + sx_fill(self.tpl["div"], a="1", b=nn) + ")"
                return sx_fill(self.tpl["nroot"], a=a, n=nn)
            if name in ("diff", "deriv", "pdiff") and len(args) in (2, 3) and args[1][0] == "id":
                if name == "pdiff":
                    self.mark("u_pdiff")
                order = 1
                if len(args) == 3:
                    order = int(args[2][1]) if args[2][0] == "num" and args[2][1].isdigit() else None
                return self.deriv(args[1][1], args[0], order)
            return (f"(@APPLY {self.ident(name)} (@ARGS "
                    + " ".join(self.node(a) for a in args) + "))")
        raise ParseError(Msg("e_node", kind=kind))


def build_sexpr(linear_text, tpl=None):
    """Teks linear -> (string format Prime '@', daftar bagian belum terverifikasi)."""
    lines = [ln for ln in linear_text.strip().split("\n") if ln.strip()]
    if not lines:
        raise ParseError(Msg("e_no_text_conv"))
    ast = Parser(tokenize(lines[0])).parse()
    b = SexprBuilder(tpl)
    out = b.node(ast)
    notes = list(b.notes)
    if len(lines) > 1:
        notes.append(Msg("w_multiline_conv"))
    return out, b.unverified, notes


# ----------------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------------
# Simbol yang perlu diperbaiki sebelum konversi:  ,  ->  .     [  ->  (     ]  ->  )
# Dilewati: \\sqrt[n]{..} (akar pangkat n), \\[ \\] (delimiter display math),
#           \\, \\; \\: \\! (spasi LaTeX) dan \\\\ (baris baru).
_SYM_RE = re.compile(r"\\sqrt\s*\[[^\]]*\]|\\\\|\\[\[\],;:! ]|([,\[\]])")
_SYM_MAP = {",": ".", "[": "(", "]": ")"}


# Koma di dalam argumen log(...) / \\log_b(...) adalah pemisah argumen log(x,b): dikecualikan.
_LOG_RE = re.compile(r"(?<![A-Za-z])\\?(?:log|lg)(?![A-Za-z])\s*"
                     r"(?:_\s*(?:\{[^{}]*\}|[A-Za-z0-9]))?\s*(?:\\left\s*)?\(")


def _log_spans(text):
    spans = []
    for m in _LOG_RE.finditer(text):
        start, depth = m.end() - 1, 0
        for j in range(start, len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    spans.append((start, j))
                    break
    for m in re.finditer(r"_\s*\{", text):          # t_{i,j}: koma = pemisah indeks
        depth = 0
        for j in range(m.end() - 1, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    spans.append((m.end() - 1, j))
                    break
    return spans


def _skip_comma(m, spans):
    return m.group(1) == "," and any(a < m.start() < b for a, b in spans)


def scan_symbols(text):
    """Hitung kemunculan , [ ] di input LaTeX (di luar bagian yang dilindungi)."""
    counts = {",": 0, "[": 0, "]": 0}
    spans = _log_spans(text)
    for m in _SYM_RE.finditer(text):
        if m.group(1) and not _skip_comma(m, spans):
            counts[m.group(1)] += 1
    return counts


def fix_symbols(text):
    """, -> .   [ -> (   ] -> )   (bagian yang dilindungi & koma dalam log dibiarkan)."""
    spans = _log_spans(text)
    return _SYM_RE.sub(lambda m: _SYM_MAP[m.group(1)]
                       if m.group(1) and not _skip_comma(m, spans) else m.group(0), text)


def apply_rules(text, rules_text):
    """Terapkan aturan 'lama => baru' (awali 're:' untuk regex). -> (teks, jumlah ganti)."""
    total = 0
    for raw in rules_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=>" not in line:
            continue
        left, right = (x.strip() for x in line.split("=>", 1))
        if not left:
            continue
        try:
            if left.startswith("re:"):
                text, n = re.subn(left[3:].strip(), right, text)
            else:
                n = text.count(left)
                text = text.replace(left, right)
        except (re.error, IndexError):
            continue
        total += n
    return text, total


def learn_template(key, prime_text):
    """Ubah teks (@...) yang disalin dari Prime menjadi template, dengan
    mengganti nama variabel contoh (x, y) menjadi {a}, {b}, {n}."""
    _hint, names = SX_LEARN[key]
    t = prime_text.strip()
    if not t.startswith("("):
        raise ValueError(Msg("e_learn_format"))
    for ph, name in names.items():
        pat = r"(?<![\w@])" + re.escape(name) + r"(?![\w])"
        if not re.search(pat, t):
            raise ValueError(Msg("e_learn_var", name=name, example=Msg(SX_LEARN[key][0])))
        t = re.sub(pat, "{" + ph + "}", t)
    return " ".join(t.split())


# ----------------------------------------------------------------------------
# PENGATURAN (disimpan di samping file .py)
# ----------------------------------------------------------------------------
try:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:                                     # pragma: no cover
    APP_DIR = os.getcwd()
SETTINGS_PATH = os.path.join(APP_DIR, "latex_to_mathcad_settings.json")
RULES_PATH = os.path.join(APP_DIR, "latex_to_mathcad_rules.txt")
OLD_RULES_PATH = os.path.join(APP_DIR, "latex_ke_mathcad_aturan.txt")   # versi lama

DEFAULT_SETTINGS = {
    "language": "id", "theme": "dark", "topmost": False,
    "subscript": "underscore", "define": False, "implicit_mult": True,
    "apply_rules": False, "countdown": 4.0, "delay": 50.0,
    "greek": True, "real_keys": True, "log_base": "ln",
}


def load_settings():
    cfg = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        for k, v in data.items():
            if k in cfg and type(v) is type(cfg[k]):
                cfg[k] = v
            elif k in ("delay", "countdown") and isinstance(v, (int, float)) and not isinstance(v, bool):
                cfg[k] = float(v)
    except (OSError, ValueError):
        pass
    if cfg["language"] not in LANGS:
        cfg["language"] = DEFAULT_SETTINGS["language"]
    if cfg["theme"] not in ("dark", "light"):
        cfg["theme"] = DEFAULT_SETTINGS["theme"]
    cfg["delay"] = min(400.0, max(0.0, float(cfg["delay"])))
    cfg["countdown"] = min(15.0, max(0.5, float(cfg["countdown"])))
    if cfg["log_base"] not in ("comma", "ln"):
        cfg["log_base"] = DEFAULT_SETTINGS["log_base"]
    if cfg["subscript"] not in ("underscore", "literal", "drop"):
        cfg["subscript"] = DEFAULT_SETTINGS["subscript"]
    return cfg


def save_settings(cfg):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


try:
    import html
    from string import Template
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import (QColor, QFont, QFontDatabase, QGuiApplication, QKeySequence,
                               QPainter, QPalette, QPen, QShortcut, QSyntaxHighlighter,
                               QTextCharFormat, QTextCursor)
    from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFrame,
                                   QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                                   QMessageBox, QPlainTextEdit, QPushButton, QRadioButton,
                                   QScrollArea, QSizePolicy, QSpinBox, QSplitter, QStatusBar,
                                   QStyle, QStyleOptionButton, QTabWidget, QTextBrowser,
                                   QVBoxLayout, QWidget)
    HAVE_QT = True
except ImportError:                                    # PySide6 belum terpasang
    HAVE_QT = False


if HAVE_QT:
    # ----------------------------------------------------------------------------
    # GUI  (PySide6 / Qt Widgets)
    # Seluruh logika konversi di atas tidak diubah; bagian ini hanya tampilan.
    # ----------------------------------------------------------------------------
    THEMES = {
        "dark": dict(bg="#0d0f13", panel="#14171d", surface="#0e1116", elevated="#1b1f27",
                     out_bg="#0c1218", border="#22272f", border_strong="#2f3642",
                     fg="#cfd4de", fg_strong="#eef1f7", muted="#8a92a3", faint="#566071",
                     accent="#4d8dff", accent_hover="#6ba2ff", accent_fg="#ffffff",
                     accent_soft="rgba(77,141,255,0.16)", hover="#212631",
                     success="#4fcfa3", warn="#e6b869", danger="#ef6b75", sel="#27436f"),
        "light": dict(bg="#eceff4", panel="#ffffff", surface="#f6f8fb", elevated="#f0f2f6",
                      out_bg="#f1f6fb", border="#dfe3ea", border_strong="#c8cfda",
                      fg="#2a303b", fg_strong="#10131a", muted="#66708a", faint="#98a2b5",
                      accent="#2d6df0", accent_hover="#1f5cd9", accent_fg="#ffffff",
                      accent_soft="rgba(45,109,240,0.12)", hover="#e6e9ef",
                      success="#14946b", warn="#a8650b", danger="#d6404c", sel="#c9dcff"),
    }

    QSS = Template("""
    QWidget { color: ${fg}; selection-background-color: ${sel}; selection-color: ${fg_strong}; }
    QMainWindow, QWidget#Root { background: ${bg}; }
    QToolTip { background: ${elevated}; color: ${fg}; border: 1px solid ${border_strong};
               padding: 5px 8px; }

    #Header { background: ${panel}; border-bottom: 1px solid ${border}; }
    #Logo { background: ${accent}; color: ${accent_fg}; border-radius: 9px;
            font-size: 18px; font-weight: 700; }
    #AppTitle { font-size: 15px; font-weight: 600; color: ${fg_strong}; }
    #AppSub { font-size: 11px; color: ${muted}; }
    #SegWrap { background: ${surface}; border: 1px solid ${border}; border-radius: 8px; }

    QTabWidget::pane { border: none; border-top: 1px solid ${border}; background: ${bg}; }
    QTabWidget::tab-bar { left: 14px; }
    QTabBar { background: transparent; }
    QTabBar::tab { background: transparent; color: ${muted}; padding: 11px 16px 10px 16px;
                   margin-right: 2px; border: none; border-bottom: 2px solid transparent; }
    QTabBar::tab:hover { color: ${fg}; }
    QTabBar::tab:selected { color: ${fg_strong}; border-bottom: 2px solid ${accent}; }

    #Card { background: ${panel}; border: 1px solid ${border}; border-radius: 10px; }
    #Section { color: ${muted}; }
    #Heading { font-size: 16px; font-weight: 600; color: ${fg_strong}; }
    #Muted { color: ${muted}; }
    #Accent { color: ${accent}; }
    #NavLabel { color: ${muted}; }
    QFrame#Sep { background: ${border}; border: none; max-height: 1px; min-height: 1px; }

    QPlainTextEdit, QTextBrowser { background: ${surface}; border: 1px solid ${border};
                                   border-radius: 8px; padding: 6px 8px; }
    QPlainTextEdit:focus { border: 1px solid ${accent}; }
    QPlainTextEdit#Out { background: ${out_bg}; }
    QPlainTextEdit#Notes { color: ${warn}; }
    QTextBrowser#Help { background: ${panel}; border: 1px solid ${border}; border-radius: 10px;
                        padding: 14px 18px; }

    QPushButton { background: ${elevated}; border: 1px solid ${border_strong}; border-radius: 7px;
                  padding: 7px 14px; color: ${fg}; }
    QPushButton:hover { background: ${hover}; border-color: ${faint}; }
    QPushButton:pressed { background: ${border}; }
    QPushButton:focus { border: 1px solid ${accent}; }
    QPushButton:disabled { color: ${faint}; background: ${panel}; border-color: ${border}; }
    QPushButton[role="primary"] { background: ${accent}; border: 1px solid ${accent};
                                  color: ${accent_fg}; font-weight: 600; }
    QPushButton[role="primary"]:hover { background: ${accent_hover}; border-color: ${accent_hover}; }
    QPushButton[role="primary"]:disabled { background: ${border}; border-color: ${border};
                                           color: ${faint}; }
    QPushButton[role="ghost"] { background: transparent; border: 1px solid transparent; }
    QPushButton[role="ghost"]:hover { background: ${hover}; }
    QPushButton[role="ghost"]:disabled { color: ${faint}; background: transparent; }
    QPushButton[role="small"] { padding: 4px 10px; font-size: 12px; }
    QPushButton[role="danger"]:hover { color: ${danger}; border-color: ${danger}; }
    QPushButton[role="seg"] { background: transparent; border: none; border-radius: 6px;
                              padding: 5px 13px; color: ${muted}; font-weight: 600; }
    QPushButton[role="seg"]:hover { color: ${fg}; }
    QPushButton[role="seg"]:checked { background: ${accent}; color: ${accent_fg}; }

    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: ${surface}; border: 1px solid ${border_strong};
                                     border-radius: 7px; padding: 5px 9px; min-height: 20px; }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid ${accent}; }
    QSpinBox, QDoubleSpinBox { padding-right: 22px; }
    QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 18px;
                          border: none; background: transparent; margin: 3px 3px 0 0; }
    QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 18px;
                            border: none; background: transparent; margin: 0 3px 3px 0; }
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: none; width: 0px; height: 0px; border-left: 4px solid transparent;
                         border-right: 4px solid transparent; border-bottom: 5px solid ${muted}; }
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: none; width: 0px; height: 0px; border-left: 4px solid transparent;
                           border-right: 4px solid transparent; border-top: 5px solid ${muted}; }
    QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right;
                           width: 24px; border: none; }
    QComboBox::down-arrow { image: none; width: 0px; height: 0px; border-left: 4px solid transparent;
                            border-right: 4px solid transparent; border-top: 5px solid ${muted}; }
    QComboBox QAbstractItemView { background: ${elevated}; border: 1px solid ${border_strong};
                                  selection-background-color: ${accent_soft};
                                  selection-color: ${fg_strong}; outline: 0; padding: 4px; }

    QCheckBox, QRadioButton { spacing: 9px; padding: 3px 0; background: transparent; }
    QCheckBox:hover, QRadioButton:hover { color: ${fg_strong}; }
    QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid ${border_strong};
                           border-radius: 4px; background: ${surface}; }
    QCheckBox::indicator:hover { border-color: ${accent}; }
    QCheckBox::indicator:checked { background: ${accent}; border-color: ${accent}; }
    QRadioButton::indicator { width: 14px; height: 14px; border: 1px solid ${border_strong};
                              border-radius: 8px; background: ${surface}; }
    QRadioButton::indicator:hover { border-color: ${accent}; }
    QRadioButton::indicator:checked { width: 8px; height: 8px; border: 4px solid ${accent};
                                      border-radius: 8px; background: ${accent_fg}; }

    QSplitter::handle { background: transparent; }
    QSplitter::handle:horizontal { width: 12px; }
    QSplitter::handle:vertical { height: 12px; }
    QSplitter::handle:hover { background: ${accent_soft}; }

    QScrollArea { border: none; background: transparent; }
    QScrollArea > QWidget > QWidget { background: transparent; }
    QScrollBar:vertical { background: transparent; width: 11px; margin: 2px; }
    QScrollBar::handle:vertical { background: ${border_strong}; border-radius: 4px; min-height: 30px; }
    QScrollBar::handle:vertical:hover { background: ${faint}; }
    QScrollBar:horizontal { background: transparent; height: 11px; margin: 2px; }
    QScrollBar::handle:horizontal { background: ${border_strong}; border-radius: 4px; min-width: 30px; }
    QScrollBar::handle:horizontal:hover { background: ${faint}; }
    QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

    QStatusBar { background: ${panel}; border-top: 1px solid ${border}; color: ${muted}; }
    QStatusBar::item { border: none; }
    QStatusBar QLabel { color: ${muted}; padding: 3px 8px; }
    QMessageBox { background: ${panel}; }
    """)


    def pick_font(candidates, fallback):
        fams = set(QFontDatabase.families())
        return next((f for f in candidates if f in fams), fallback)


    class Var:
        """Nilai kecil yang bisa diamati (pengganti tk.Variable)."""

        def __init__(self, value):
            self._v, self._cbs = value, []

        def get(self):
            return self._v

        def set(self, v):
            if v == self._v:
                return
            self._v = v
            for cb in list(self._cbs):
                cb(v)

        def trace(self, cb):
            self._cbs.append(cb)


    class CheckBox(QCheckBox):
        """Checkbox yang kotaknya digambar QSS; tanda centang digambar di atasnya."""
        mark = "#ffffff"

        def paintEvent(self, event):
            super().paintEvent(event)
            if not self.isChecked():
                return
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            r = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, opt, self)
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor(CheckBox.mark), 1.9)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            x, y, w, h = r.x(), r.y(), r.width(), r.height()
            p.drawLine(int(x + w * 0.27), int(y + h * 0.53), int(x + w * 0.44), int(y + h * 0.70))
            p.drawLine(int(x + w * 0.44), int(y + h * 0.70), int(x + w * 0.74), int(y + h * 0.33))
            p.end()


    class LatexHighlighter(QSyntaxHighlighter):
        """Pewarnaan ringan untuk kotak input LaTeX (hanya tampilan)."""

        def __init__(self, doc):
            super().__init__(doc)
            self.rules = []

        def set_colors(self, cmd, num, punct):
            def fmt(color, bold=False):
                f = QTextCharFormat()
                f.setForeground(QColor(color))
                if bold:
                    f.setFontWeight(QFont.Weight.DemiBold)
                return f
            self.rules = [(re.compile(r"\\[A-Za-z]+|\\."), fmt(cmd, True)),
                          (re.compile(r"\d+(?:\.\d+)?"), fmt(num)),
                          (re.compile(r"[{}\[\]()^_&=+\-*/<>|]"), fmt(punct))]
            self.rehighlight()

        def highlightBlock(self, text):
            for pat, f in self.rules:
                for m in pat.finditer(text):
                    self.setFormat(m.start(), m.end() - m.start(), f)


    class App(QMainWindow):
        """Jendela utama: tab Konversi / Aturan / Kalibrasi / Pengaturan / Bantuan."""

        def __init__(self, app):
            super().__init__()
            self.app = app
            self.cfg = load_settings()
            set_language(self.cfg["language"])

            self._reg = []            # (setter, kunci i18n, huruf besar?)
            self._tips = []           # (widget, kunci)
            self._tabs = []           # kunci tab
            self._groups = []
            self._status = ("s_ready", {})
            self.history, self.pos, self.cur = [], -1, None
            self.state = {"last_clip": "", "watch_skip": "", "theme": self.cfg["theme"]}
            self.typing = {"running": False, "plan": [], "i": 0, "typer": None}
            self.rules = {"text": "", "last": 0}
            self._loading = True
            self._sym_declined = ""
            self.find_visible = False

            self.ui_font = pick_font(("Inter", "Segoe UI Variable Text", "Segoe UI", "SF Pro Text",
                                      "Helvetica Neue", "Noto Sans", "DejaVu Sans"), "Sans Serif")
            self.mono_font = pick_font(("JetBrains Mono", "Cascadia Mono", "Cascadia Code", "Consolas",
                                        "SF Mono", "DejaVu Sans Mono", "Courier New"), "Monospace")
            app.setStyle("Fusion")
            app.setFont(QFont(self.ui_font, 10))

            self.setWindowTitle(APP_TITLE)
            self.setMinimumSize(960, 660)
            self.resize(1280, 840)
            if self.cfg["topmost"]:
                self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

            self._make_vars()
            self._load_rules()

            root = QWidget()
            root.setObjectName("Root")
            self.setCentralWidget(root)
            outer = QVBoxLayout(root)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
            outer.addWidget(self._build_header())
            self.nb = QTabWidget()
            self.nb.setDocumentMode(True)
            outer.addWidget(self.nb, 1)
            self._build_statusbar()

            self.tab_convert = self._add_tab("tab_convert", self._build_convert())
            self.tab_rules = self._add_tab("tab_rules", self._build_rules())
            self.tab_calib = self._add_tab("tab_calibrate", self._build_calibration())
            self.tab_settings = self._add_tab("tab_settings", self._build_settings())
            self.tab_help = self._add_tab("tab_help", self._build_help())

            self._bind_keys()
            self.apply_theme(self.cfg["theme"])
            self.retext()
            self._loading = False
            self.update_nav()

            self.watch_timer = QTimer(self)
            self.watch_timer.setInterval(600)
            self.watch_timer.timeout.connect(self.watch)
            self.watch_timer.start()

        # ------------------------------------------------------------------ util
        def _make_vars(self):
            c = self.cfg
            self.v_lang = Var(c["language"])
            self.v_theme = Var(c["theme"])
            self.v_top = Var(c["topmost"])
            self.v_sub = Var(c["subscript"])
            self.v_log = Var(c["log_base"])
            self.v_define = Var(c["define"])
            self.v_mul = Var(c["implicit_mult"])
            self.v_rules = Var(c["apply_rules"])
            self.v_watch = Var(False)
            self.v_count = Var(c["countdown"])
            self.v_delay = Var(c["delay"])
            self.v_greek = Var(c["greek"])
            self.v_real = Var(c["real_keys"])
            for v in (self.v_top, self.v_sub, self.v_log, self.v_define, self.v_mul, self.v_rules,
                      self.v_count, self.v_delay, self.v_greek, self.v_real):
                v.trace(lambda _x: self.persist())
            self.v_theme.trace(lambda name: self.apply_theme(name))
            self.v_top.trace(self._apply_topmost)

        def _apply_topmost(self, on):
            was_visible = self.isVisible()
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(on))
            if was_visible:
                self.show()

        def persist(self):
            if self._loading:
                return
            c = self.cfg
            c["language"], c["theme"] = self.v_lang.get(), self.v_theme.get()
            c["topmost"], c["subscript"] = bool(self.v_top.get()), self.v_sub.get()
            c["log_base"] = self.v_log.get()
            c["define"], c["implicit_mult"] = bool(self.v_define.get()), bool(self.v_mul.get())
            c["apply_rules"] = bool(self.v_rules.get())
            c["countdown"], c["delay"] = self._float(self.v_count, 4.0), self._float(self.v_delay, 50.0)
            c["greek"], c["real_keys"] = bool(self.v_greek.get()), bool(self.v_real.get())
            save_settings(c)

        @staticmethod
        def _float(var, default):
            try:
                return float(var.get())
            except Exception:                                  # noqa: BLE001
                return default

        @staticmethod
        def _int(var, default):
            try:
                return int(var.get())
            except Exception:                                  # noqa: BLE001
                return default

        # ---- pembantu widget -------------------------------------------------------
        def T(self, widget, key, upper=False, tip=None):
            """Daftarkan teks widget agar ikut bahasa."""
            setter = widget.setText
            self._reg.append((setter, key, upper))
            setter(tr(key).upper() if upper else tr(key))
            if tip:
                self.tip(widget, tip)
            return widget

        def tip(self, widget, key):
            self._tips.append((widget, key))
            widget.setToolTip(tr(key))

        def label(self, key=None, role=None, wrap=False, upper=False):
            lab = QLabel()
            if role:
                lab.setObjectName(role)
            if wrap:
                lab.setWordWrap(True)
                lab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            if key:
                self.T(lab, key, upper=upper)
            if role == "Section":
                f = lab.font()
                f.setPointSizeF(8.5)
                f.setWeight(QFont.Weight.DemiBold)
                f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.9)
                lab.setFont(f)
            return lab

        def button(self, key, role=None, tip=None, slot=None, focus=True):
            b = QPushButton()
            self.T(b, key)
            if role:
                b.setProperty("role", role)
            if tip:
                self.tip(b, tip)
            if slot:
                b.clicked.connect(lambda _c=False, s=slot: s())
            if not focus:
                b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            return b

        def check(self, key, var, tip=None):
            cb = CheckBox()
            self.T(cb, key, tip=tip)
            cb.setChecked(bool(var.get()))
            cb.toggled.connect(lambda ch: var.set(bool(ch)))
            var.trace(lambda v: cb.setChecked(bool(v)) if cb.isChecked() != bool(v) else None)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            return cb

        def radios(self, items, var):
            """items = [(valor, kunci_i18n)] -> daftar QRadioButton yang terikat ke var."""
            grp = QButtonGroup(self)
            self._groups.append(grp)
            btns = {}
            for val, key in items:
                rb = QRadioButton()
                self.T(rb, key)
                rb.setCursor(Qt.CursorShape.PointingHandCursor)
                grp.addButton(rb)
                btns[val] = rb
                rb.toggled.connect(lambda ch, v=val: var.set(v) if ch else None)
            if var.get() in btns:
                btns[var.get()].setChecked(True)
            var.trace(lambda v: btns[v].setChecked(True) if v in btns else None)
            return list(btns.values())

        def spin(self, var, lo, hi, step=1, width=78):
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setSingleStep(step)
            sp.setFixedWidth(width)
            sp.setValue(self._int(var, lo))
            sp.valueChanged.connect(lambda v: var.set(int(v)))
            var.trace(lambda v: sp.setValue(int(v)) if sp.value() != int(v) else None)
            return sp

        def dspin(self, var, lo, hi, step=1.0, decimals=1, width=88):
            sp = QDoubleSpinBox()
            sp.setDecimals(decimals)
            sp.setRange(lo, hi)
            sp.setSingleStep(step)
            sp.setFixedWidth(width)
            sp.setValue(self._float(var, lo))
            sp.valueChanged.connect(lambda v: var.set(float(v)))
            var.trace(lambda v: sp.setValue(float(v)) if abs(sp.value() - float(v)) > 1e-9 else None)
            return sp

        def card(self, title_key=None):
            fr = QFrame()
            fr.setObjectName("Card")
            lay = QVBoxLayout(fr)
            lay.setContentsMargins(16, 14, 16, 16)
            lay.setSpacing(10)
            if title_key:
                lay.addWidget(self.label(title_key, "Section", upper=True))
            return fr, lay

        @staticmethod
        def sep():
            s = QFrame()
            s.setObjectName("Sep")
            s.setFixedHeight(1)
            return s

        def editor(self, role=None, font=None, wrap=True):
            ed = QPlainTextEdit()
            if role:
                ed.setObjectName(role)
            ed.setFont(font or QFont(self.mono_font, 11))
            ed.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if wrap
                               else QPlainTextEdit.LineWrapMode.NoWrap)
            ed.setTabStopDistance(28)
            return ed

        def panel(self, key, role, font=None, actions=()):
            """Kartu berisi judul bagian, tombol aksi (opsional), dan satu editor."""
            fr, lay = self.card()
            lay.setSpacing(8)
            head = QHBoxLayout()
            head.setSpacing(6)
            head.addWidget(self.label(key, "Section", upper=True))
            head.addStretch(1)
            for w in actions:
                head.addWidget(w)
            lay.addLayout(head)
            ed = self.editor(role, font)
            ed.setMinimumHeight(64)
            lay.addWidget(ed, 1)
            return fr, ed

        def scroll_page(self, inner):
            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setFrameShape(QFrame.Shape.NoFrame)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            sc.setWidget(inner)
            return sc

        def say(self, key, **kw):
            self._status = (key, kw)
            self.lbl_status.setText(tr(key, **kw))

        # ---------------------------------------------------------------- bahasa
        def retext(self):
            for setter, key, upper in self._reg:
                setter(tr(key).upper() if upper else tr(key))
            for widget, key in self._tips:
                widget.setToolTip(tr(key))
            for i, key in enumerate(self._tabs):
                self.nb.setTabText(i, tr(key))
            self.lbl_status.setText(tr(self._status[0], **self._status[1]))
            self.refresh_notes()
            self.render_help()
            self.refresh_learn_hint()
            self.update_nav()
            self.setWindowTitle(APP_TITLE)

        def set_lang(self, code):
            if code not in LANGS:
                return
            set_language(code)
            self.v_lang.set(code)
            for c, b in self.seg_btns.items():
                b.blockSignals(True)
                b.setChecked(c == code)
                b.blockSignals(False)
            self.cb_lang.blockSignals(True)
            self.cb_lang.setCurrentIndex(list(LANGS).index(code))
            self.cb_lang.blockSignals(False)
            self.cfg["language"] = code
            self.persist()
            self.retext()

        # ---------------------------------------------------------------- bangun
        def _build_statusbar(self):
            sb = QStatusBar()
            sb.setSizeGripEnabled(False)
            self.lbl_status = QLabel("")
            sb.addWidget(self.lbl_status, 1)
            self.setStatusBar(sb)

        def _build_header(self):
            head = QFrame()
            head.setObjectName("Header")
            head.setFixedHeight(62)
            lay = QHBoxLayout(head)
            lay.setContentsMargins(22, 0, 20, 0)
            lay.setSpacing(12)
            logo = QLabel("∑")
            logo.setObjectName("Logo")
            logo.setFixedSize(36, 36)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(logo)
            col = QVBoxLayout()
            col.setSpacing(0)
            col.setContentsMargins(0, 0, 0, 0)
            t = QLabel(APP_TITLE)
            t.setObjectName("AppTitle")
            s = QLabel("LaTeX  →  Mathcad Prime")
            s.setObjectName("AppSub")
            col.addStretch(1)
            col.addWidget(t)
            col.addWidget(s)
            col.addStretch(1)
            lay.addLayout(col)
            lay.addStretch(1)

            wrap = QFrame()
            wrap.setObjectName("SegWrap")
            wl = QHBoxLayout(wrap)
            wl.setContentsMargins(3, 3, 3, 3)
            wl.setSpacing(2)
            grp = QButtonGroup(self)
            grp.setExclusive(True)
            self._groups.append(grp)
            self.seg_btns = {}
            for code, text in (("en", "EN"), ("id", "ID")):
                b = QPushButton(text)
                b.setProperty("role", "seg")
                b.setCheckable(True)
                b.setChecked(code == self.cfg["language"])
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                b.clicked.connect(lambda _c=False, c=code: self.set_lang(c))
                self.tip(b, "tip_lang")
                grp.addButton(b)
                wl.addWidget(b)
                self.seg_btns[code] = b
            lay.addWidget(wrap)
            self.btn_theme = self.button("btn_theme", "ghost", "tip_theme", self.toggle_theme)
            lay.addWidget(self.btn_theme)
            return head

        def _add_tab(self, key, page):
            self.nb.addTab(page, tr(key))
            self._tabs.append(key)
            return page

        def goto(self, page):
            self.nb.setCurrentWidget(page)

        # ---- tab Konversi ------------------------------------------------------
        def _build_convert(self):
            page = QWidget()
            pl = QVBoxLayout(page)
            pl.setContentsMargins(16, 16, 16, 12)
            split = QSplitter(Qt.Orientation.Horizontal)
            split.setChildrenCollapsible(False)
            pl.addWidget(split)

            # ---------- kolom kiri: toolbar + editor + cari & ganti
            left = QWidget()
            ll = QVBoxLayout(left)
            ll.setContentsMargins(0, 0, 0, 0)
            ll.setSpacing(12)

            bar = QHBoxLayout()
            bar.setSpacing(8)
            bar.addWidget(self.button("btn_paste_convert", "primary", "tip_paste_convert",
                                      self.paste_convert))
            bar.addWidget(self.button("btn_convert", None, "tip_convert", self.do_convert))
            bar.addWidget(self.button("btn_clear", None, "tip_clear", self.clear_all))
            bar.addWidget(self.button("btn_find", None, "tip_find", self.toggle_find))
            bar.addStretch(1)
            ll.addLayout(bar)

            vsplit = QSplitter(Qt.Orientation.Vertical)
            vsplit.setChildrenCollapsible(False)
            ll.addWidget(vsplit, 1)

            self.btn_undo = self.button("btn_undo", "ghost", "tip_undo", self.do_undo, focus=False)
            self.btn_redo = self.button("btn_redo", "ghost", "tip_redo", self.do_redo, focus=False)
            self.btn_prev = self.button("btn_prev", "ghost", "tip_prev", self.go_prev, focus=False)
            self.btn_next = self.button("btn_next", "ghost", "tip_next", self.go_next, focus=False)
            for b in (self.btn_undo, self.btn_redo, self.btn_prev, self.btn_next):
                b.setProperty("role", "ghost")
            self.nav_label = QLabel("0/0")
            self.nav_label.setObjectName("NavLabel")
            self.nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.nav_label.setMinimumWidth(44)
            in_actions = (self.btn_undo, self.btn_redo, self.btn_prev, self.nav_label, self.btn_next)
            pin, self.txt_in = self.panel("lbl_input", "In", None, in_actions)
            self.hl = LatexHighlighter(self.txt_in.document())

            b_copy = self.button("btn_copy_result", "small", "tip_copy_result", self.copy_out,
                                 focus=False)
            b_prime = self.button("btn_prime_fmt", "small", "tip_prime_fmt", self.convert_sexpr,
                                  focus=False)
            pout, self.txt_out = self.panel("lbl_output", "Out", QFont(self.mono_font, 12),
                                            (b_prime, b_copy))
            pnote, self.txt_warn = self.panel("lbl_notes", "Notes", QFont(self.ui_font, 10))
            self.txt_warn.setReadOnly(True)
            for w in (pin, pout, pnote):
                vsplit.addWidget(w)
            vsplit.setStretchFactor(0, 3)
            vsplit.setStretchFactor(1, 3)
            vsplit.setStretchFactor(2, 2)
            vsplit.setSizes([300, 300, 180])

            ll.addWidget(self._build_findbar())

            # ---------- kolom kanan: sidebar
            inner = QWidget()
            sl = QVBoxLayout(inner)
            sl.setContentsMargins(0, 0, 6, 0)
            sl.setSpacing(14)

            c1, l1 = self.card("card_prime")
            intro = self.label("txt_prime_intro", "Muted", wrap=True)
            l1.addWidget(intro)
            row = QHBoxLayout()
            row.setSpacing(8)
            self.btn_type = self.button("btn_type", "primary", "tip_type", self.start_typing)
            self.btn_type.setMinimumHeight(38)
            self.btn_stop = self.button("btn_stop", "danger", "tip_stop", self.stop_typing)
            self.btn_stop.setMinimumHeight(38)
            row.addWidget(self.btn_type, 1)
            row.addWidget(self.btn_stop)
            l1.addLayout(row)
            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(8)
            grid.addWidget(self.label("lbl_start_in"), 0, 0)
            grid.addWidget(self.dspin(self.v_count, 0.5, 15.0, 0.5, 1), 0, 1)
            grid.addWidget(self.label("lbl_seconds", "Muted"), 0, 2)
            lk = self.label("lbl_key_delay")
            self.tip(lk, "tip_key_delay")
            grid.addWidget(lk, 1, 0)
            grid.addWidget(self.dspin(self.v_delay, 0.0, 400.0, 0.5, 1), 1, 1)
            grid.addWidget(self.label(None, "Muted"), 1, 2)
            grid.itemAtPosition(1, 2).widget().setText("ms")
            grid.setColumnStretch(3, 1)
            l1.addLayout(grid)
            l1.addWidget(self.sep())
            l1.addWidget(self.label("txt_sexpr_intro", "Muted", wrap=True))
            l1.addWidget(self.button("btn_sexpr", None, "tip_sexpr", self.convert_sexpr))
            sl.addWidget(c1)

            c2, l2 = self.card("card_options")
            l2.addWidget(self.label("lbl_subscript"))
            for rb in self.radios((("underscore", "opt_sub_underscore"),
                                   ("literal", "opt_sub_literal"), ("drop", "opt_sub_drop")),
                                  self.v_sub):
                rb.setStyleSheet("margin-left: 6px;")
                l2.addWidget(rb)
            l2.addWidget(self.sep())
            for var, key, tp in ((self.v_define, "opt_define", "tip_define"),
                                 (self.v_mul, "opt_mul", "tip_mul"),
                                 (self.v_watch, "opt_watch", "tip_watch"),
                                 (self.v_rules, "opt_rules", "tip_rules")):
                l2.addWidget(self.check(key, var, tp))
            sl.addWidget(c2)
            sl.addStretch(1)

            side = self.scroll_page(inner)
            side.setMinimumWidth(330)
            side.setMaximumWidth(460)

            split.addWidget(left)
            split.addWidget(side)
            split.setStretchFactor(0, 1)
            split.setStretchFactor(1, 0)
            split.setSizes([820, 380])
            left.setMinimumWidth(460)
            return page

        # ---- panel Cari & Ganti (di dalam tab Konversi) ------------------------------
        def _build_findbar(self):
            self.f_var, self.r_var = QLineEdit(), QLineEdit()
            self.o_case, self.o_whole, self.o_regex = Var(False), Var(False), Var(False)
            self.o_target = Var("in")
            fb, lay = self.card("card_find")
            self.findbar = fb
            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(8)
            grid.addWidget(self.label("lbl_find"), 0, 0)
            grid.addWidget(self.f_var, 0, 1)
            grid.addWidget(self.label("lbl_replace"), 1, 0)
            grid.addWidget(self.r_var, 1, 1)
            grid.setColumnStretch(1, 1)
            lay.addLayout(grid)
            opts = QHBoxLayout()
            opts.setSpacing(14)
            opts.addWidget(self.check("opt_case", self.o_case))
            opts.addWidget(self.check("opt_whole", self.o_whole))
            opts.addWidget(self.check("opt_regex", self.o_regex))
            opts.addStretch(1)
            opts.addWidget(self.label("lbl_apply_to", "Muted"))
            for rb in self.radios((("in", "opt_target_in"), ("out", "opt_target_out")),
                                  self.o_target):
                opts.addWidget(rb)
            lay.addLayout(opts)
            btns = QHBoxLayout()
            btns.setSpacing(8)
            btns.addWidget(self.button("btn_find_next", "primary", None, self.find_next))
            btns.addWidget(self.button("btn_replace", None, None, self.replace_one))
            btns.addWidget(self.button("btn_replace_all", None, None, self.replace_all))
            btns.addWidget(self.button("btn_make_rule", None, "tip_make_rule", self.save_as_rule))
            btns.addStretch(1)
            btns.addWidget(self.button("btn_close", "ghost", None, self.toggle_find))
            lay.addLayout(btns)
            fb.setVisible(False)
            self.f_var.returnPressed.connect(self.find_next)
            return fb

        def toggle_find(self):
            if self.find_visible:
                self.findbar.setVisible(False)
                self.find_visible = False
            else:
                self.goto(self.tab_convert)
                self.findbar.setVisible(True)
                self.find_visible = True
                self.f_var.setFocus()

        # ---- tab Aturan ----------------------------------------------------------
        def _build_rules(self):
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.setContentsMargins(24, 22, 24, 18)
            lay.setSpacing(10)
            lay.addWidget(self.label("h_rules", "Heading"))
            lay.addWidget(self.label("txt_rules_intro", "Muted", wrap=True))
            self.rules_box = self.editor(None, None, wrap=False)
            self.rules_box.setPlainText(self.rules["text"])
            lay.addWidget(self.rules_box, 1)
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addWidget(self.button("btn_save_rules", "primary", None, self.save_rules))
            row.addWidget(self.check("opt_rules", self.v_rules))
            row.addStretch(1)
            lay.addLayout(row)
            return page

        def _load_rules(self):
            for path in (RULES_PATH, OLD_RULES_PATH):
                try:
                    with open(path, encoding="utf-8") as fh:
                        self.rules["text"] = fh.read()
                    return
                except OSError:
                    continue

        def save_rules(self):
            self.rules["text"] = self.rules_box.toPlainText().strip("\n")
            try:
                with open(RULES_PATH, "w", encoding="utf-8") as fh:
                    fh.write(self.rules["text"])
                self.say("s_rules_saved", path=RULES_PATH)
            except OSError as exc:
                self.say("s_rules_save_failed", err=exc)

        # ---- tab Kalibrasi -------------------------------------------------------------
        def _build_calibration(self):
            inner = QWidget()
            lay = QVBoxLayout(inner)
            lay.setContentsMargins(24, 22, 24, 18)
            lay.setSpacing(10)
            lay.addWidget(self.label("h_calibrate", "Heading"))
            lay.addWidget(self.label("txt_cal_intro", "Muted", wrap=True))

            card, cl = self.card()
            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(9)
            grid.setColumnStretch(1, 1)
            cl.addLayout(grid)
            self.cal_boxes, self.cal_extra = {}, {}

            def candidates(key):
                return list(SX_CHOICES[key][1]) + self.cal_extra.get(key, [])

            def copy_sample(key):
                sample = sx_sample(key)
                self.to_clipboard(sample)
                self.say("s_sample_copied", sample=sample)

            def next_candidate(key):
                cands = candidates(key)
                cb = self.cal_boxes[key]
                cur = cb.currentText()
                idx = cands.index(cur) if cur in cands else -1
                nxt = cands[(idx + 1) % len(cands)]
                cb.setCurrentText(nxt)
                SX_TPL[key] = nxt
                sample = sx_sample(key)
                self.to_clipboard(sample)
                self.say("s_candidate_copied", n=(idx + 1) % len(cands) + 1, total=len(cands),
                         sample=sample)

            for r, (key, (label_key, cands)) in enumerate(SX_CHOICES.items()):
                grid.addWidget(self.label(label_key), r, 0)
                cb = QComboBox()
                cb.setEditable(True)
                cb.addItems(cands)
                cb.setCurrentText(SX_TPL[key])
                cb.currentTextChanged.connect(lambda txt, k=key: SX_TPL.__setitem__(k, txt))
                grid.addWidget(cb, r, 1)
                self.cal_boxes[key] = cb
                grid.addWidget(self.button("btn_copy_sample", "small", None,
                                           lambda k=key: copy_sample(k)), r, 2)
                grid.addWidget(self.button("btn_next_candidate", "small", None,
                                           lambda k=key: next_candidate(k)), r, 3)
            lay.addWidget(card)

            lay.addSpacing(6)
            lay.addWidget(self.label("h_learn", "Heading"))
            lay.addWidget(self.label("txt_learn_intro", "Muted", wrap=True))
            c2, l2 = self.card()
            row = QHBoxLayout()
            row.setSpacing(12)
            self.cb_learn = QComboBox()
            self.cb_learn.setMinimumWidth(240)
            self.hint_lbl = self.label(None, "Muted")
            row.addWidget(self.cb_learn)
            row.addWidget(self.hint_lbl, 1)
            l2.addLayout(row)
            self.learn_box = self.editor(None, None)
            self.learn_box.setFixedHeight(96)
            l2.addWidget(self.learn_box)
            row2 = QHBoxLayout()
            row2.setSpacing(12)
            row2.addWidget(self.button("btn_learn", "primary", None, self.do_learn))
            self.learn_msg = self.label(None, "Accent")
            row2.addWidget(self.learn_msg, 1)
            l2.addLayout(row2)
            lay.addWidget(c2)
            lay.addStretch(1)
            self.cal_candidates = candidates
            self._learn_ready = False
            self.refresh_learn_hint(first=True)
            self.cb_learn.currentIndexChanged.connect(lambda _i: self.refresh_learn_hint())
            self._learn_ready = True
            return self.scroll_page(inner)

        def _learn_key(self):
            keys = list(SX_CHOICES)
            idx = self.cb_learn.currentIndex()
            return keys[idx] if 0 <= idx < len(keys) else keys[0]

        def refresh_learn_hint(self, first=False):
            if not hasattr(self, "cb_learn") or getattr(self, "_refreshing", False):
                return
            self._refreshing = True
            try:
                keys = list(SX_CHOICES)
                if first:
                    idx = keys.index("sqrt")
                else:
                    idx = self.cb_learn.currentIndex()
                    idx = idx if 0 <= idx < len(keys) else 0
                self.cb_learn.blockSignals(True)
                self.cb_learn.clear()
                self.cb_learn.addItems([f"{k} - {tr(SX_CHOICES[k][0])}" for k in keys])
                self.cb_learn.setCurrentIndex(idx)
                self.cb_learn.blockSignals(False)
                self.hint_lbl.setText(tr("lbl_type_in_prime", example=tr(SX_LEARN[keys[idx]][0])))
            finally:
                self._refreshing = False

        def do_learn(self):
            key = self._learn_key()
            try:
                tpl = learn_template(key, self.learn_box.toPlainText())
            except ValueError as exc:
                self.learn_msg.setText("✖ " + str(exc))
                return
            self.cal_extra.setdefault(key, []).append(tpl)
            cb = self.cal_boxes[key]
            if cb.findText(tpl) < 0:
                cb.addItem(tpl)
            cb.setCurrentText(tpl)
            SX_TPL[key] = tpl
            self.learn_msg.setText(tr("s_learned", item=key, tpl=tpl))
            self.say("s_template_updated", item=key)

        # ---- tab Pengaturan -------------------------------------------------------------
        def _build_settings(self):
            inner = QWidget()
            grid = QGridLayout(inner)
            grid.setContentsMargins(24, 22, 24, 18)
            grid.setHorizontalSpacing(16)
            grid.setVerticalSpacing(16)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)

            c1, l1 = self.card("card_appearance")
            g1 = QGridLayout()
            g1.setHorizontalSpacing(14)
            g1.setVerticalSpacing(10)
            g1.addWidget(self.label("lbl_language"), 0, 0)
            self.cb_lang = QComboBox()
            self.cb_lang.addItems(list(LANGS.values()))
            self.cb_lang.setCurrentIndex(list(LANGS).index(self.cfg["language"]))
            self.cb_lang.currentIndexChanged.connect(self._on_lang_combo)
            g1.addWidget(self.cb_lang, 0, 1)
            g1.addWidget(self.label("lbl_theme"), 1, 0)
            trow = QHBoxLayout()
            for rb in self.radios((("dark", "opt_theme_dark"), ("light", "opt_theme_light")),
                                  self.v_theme):
                trow.addWidget(rb)
            trow.addStretch(1)
            g1.addLayout(trow, 1, 1)
            g1.setColumnStretch(1, 1)
            l1.addLayout(g1)
            l1.addWidget(self.check("opt_topmost", self.v_top))
            l1.addStretch(1)
            grid.addWidget(c1, 0, 0)

            c2, l2 = self.card("card_typing")
            l2.addWidget(self.check("opt_greek", self.v_greek, "tip_greek"))
            l2.addWidget(self.check("opt_real_keys", self.v_real, "tip_real_keys"))
            lb = self.label("lbl_logbase")
            self.tip(lb, "tip_logbase")
            l2.addWidget(lb)
            for rb in self.radios((("ln", "opt_log_ln"), ("comma", "opt_log_comma")), self.v_log):
                rb.setStyleSheet("margin-left: 6px;")
                l2.addWidget(rb)
            l2.addStretch(1)
            grid.addWidget(c2, 0, 1)

            c3, l3 = self.card("card_data")
            l3.addWidget(self.label("txt_settings_file", "Muted", wrap=True))
            row = QHBoxLayout()
            row.addWidget(self.button("btn_reset_settings", None, None, self.reset_settings))
            row.addStretch(1)
            l3.addLayout(row)
            grid.addWidget(c3, 1, 0, 1, 2)
            grid.setRowStretch(2, 1)
            return self.scroll_page(inner)

        def _on_lang_combo(self, idx):
            codes = list(LANGS)
            if 0 <= idx < len(codes):
                self.set_lang(codes[idx])

        def reset_settings(self):
            d = DEFAULT_SETTINGS
            self._loading = True
            self.v_top.set(d["topmost"])
            self.v_sub.set(d["subscript"])
            self.v_define.set(d["define"])
            self.v_mul.set(d["implicit_mult"])
            self.v_rules.set(d["apply_rules"])
            self.v_count.set(d["countdown"])
            self.v_delay.set(d["delay"])
            self.v_greek.set(d["greek"])
            self.v_real.set(d["real_keys"])
            self.v_log.set(d["log_base"])
            self.v_theme.set(d["theme"])
            self._loading = False
            self.apply_theme(d["theme"])
            self.set_lang(d["language"])
            self.say("s_settings_reset")

        # ---- tab Bantuan -----------------------------------------------------------------
        def _build_help(self):
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.setContentsMargins(24, 20, 24, 16)
            self.help_box = QTextBrowser()
            self.help_box.setObjectName("Help")
            self.help_box.setOpenExternalLinks(False)
            lay.addWidget(self.help_box)
            return page

        def render_help(self):
            t = THEMES[self.state["theme"]]
            parts = []
            for line in tr("help_text").split("\n"):
                if line.startswith("## "):
                    parts.append(f'<h3 style="color:{t["accent"]}; margin:20px 0 6px 0;">'
                                 f'{html.escape(line[3:])}</h3>')
                elif line.startswith("    "):
                    parts.append(f'<div style="font-family:\'{self.mono_font}\'; color:{t["fg_strong"]};'
                                 f' margin-left:18px;">'
                                 f'{html.escape(line).replace(" ", "&nbsp;")}</div>')
                elif not line.strip():
                    parts.append('<div style="height:4px;"></div>')
                else:
                    parts.append(f'<div style="margin:2px 0; color:{t["fg"]};">'
                                 f'{html.escape(line)}</div>')
            self.help_box.setHtml("".join(parts))

        # ---------------------------------------------------------------- tema
        def toggle_theme(self):
            self.v_theme.set("light" if self.state["theme"] == "dark" else "dark")

        def _palette(self, t):
            pal = QPalette()
            roles = {QPalette.ColorRole.Window: t["bg"], QPalette.ColorRole.WindowText: t["fg"],
                     QPalette.ColorRole.Base: t["surface"], QPalette.ColorRole.AlternateBase: t["panel"],
                     QPalette.ColorRole.Text: t["fg"], QPalette.ColorRole.Button: t["elevated"],
                     QPalette.ColorRole.ButtonText: t["fg"], QPalette.ColorRole.ToolTipBase: t["elevated"],
                     QPalette.ColorRole.ToolTipText: t["fg"], QPalette.ColorRole.Highlight: t["accent"],
                     QPalette.ColorRole.HighlightedText: t["accent_fg"],
                     QPalette.ColorRole.PlaceholderText: t["faint"]}
            for role, col in roles.items():
                pal.setColor(role, QColor(col))
            return pal

        def apply_theme(self, name):
            if name not in THEMES:
                return
            self.state["theme"] = name
            self.cfg["theme"] = name
            t = THEMES[name]
            self.app.setPalette(self._palette(t))
            self.app.setStyleSheet(QSS.substitute(t))
            CheckBox.mark = t["accent_fg"]
            self.hl.set_colors(t["accent"], t["warn"], t["faint"])
            if hasattr(self, "help_box"):
                self.render_help()
            self._title_bar(name)
            self.persist()

        def _title_bar(self, name):
            """Title bar gelap/terang di Windows 10/11 (diabaikan di OS lain)."""
            try:
                import ctypes
                hwnd = int(self.winId())
                val = ctypes.c_int(1 if name == "dark" else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val),
                                                           ctypes.sizeof(val))
                h = THEMES[name]["panel"].lstrip("#")
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                cap = ctypes.c_int(r | (g << 8) | (b << 16))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(cap),
                                                           ctypes.sizeof(cap))
            except Exception:                                  # noqa: BLE001
                pass

        def showEvent(self, event):
            super().showEvent(event)
            self._title_bar(self.state["theme"])

        # ---------------------------------------------------------------- teks & riwayat
        def set_text(self, w, s):
            """Ganti seluruh isi tetapi tetap bisa di-Undo (setPlainText menghapus riwayat undo)."""
            c = w.textCursor()
            c.beginEditBlock()
            c.select(QTextCursor.SelectionType.Document)
            if s:
                c.insertText(s)
            else:
                c.removeSelectedText()
            c.endEditBlock()
            c2 = w.textCursor()
            c2.movePosition(QTextCursor.MoveOperation.Start)
            w.setTextCursor(c2)

        def to_clipboard(self, s):
            QGuiApplication.clipboard().setText(s)
            self.state["watch_skip"] = s

        def render_notes(self, entry):
            notes = entry.get("notes") or []
            return "\n".join("• " + str(n) for n in notes) if notes else tr("n_none")

        def refresh_notes(self):
            if self.cur is not None and hasattr(self, "txt_warn"):
                self.set_text(self.txt_warn, self.render_notes(self.cur))

        def commit(self, latex, out, notes, status=None, copy=True):
            entry = {"in": latex, "out": out, "notes": list(notes)}
            self.cur = entry
            self.set_text(self.txt_out, out)
            self.set_text(self.txt_warn, self.render_notes(entry))
            if not self.history or self.history[-1] != entry:
                self.history.append(entry)
            self.pos = len(self.history) - 1
            self.update_nav()
            if copy:
                self.to_clipboard(out)
            if status:
                self.say(status)

        def update_nav(self):
            n = len(self.history)
            self.nav_label.setText(f"{self.pos + 1}/{n}")
            self.btn_prev.setEnabled(self.pos > 0)
            self.btn_next.setEnabled(self.pos < n - 1)

        def show_entry(self, idx):
            e = self.history[idx]
            self.pos, self.cur = idx, e
            self.set_text(self.txt_in, e["in"])
            self.set_text(self.txt_out, e["out"])
            self.set_text(self.txt_warn, self.render_notes(e))
            self.to_clipboard(e["out"])
            self.update_nav()
            self.say("s_history", i=idx + 1, n=len(self.history))

        def go_prev(self):
            if self.pos > 0:
                self.show_entry(self.pos - 1)

        def go_next(self):
            if self.pos < len(self.history) - 1:
                self.show_entry(self.pos + 1)

        def focused_text(self):
            w = QApplication.focusWidget()
            return w if w in (self.txt_in, self.txt_out) else self.txt_in

        def do_undo(self):
            w = self.focused_text()
            if w.document().isUndoAvailable():
                w.undo()
            else:
                self.say("s_nothing_undo")

        def do_redo(self):
            w = self.focused_text()
            if w.document().isRedoAvailable():
                w.redo()
            else:
                self.say("s_nothing_redo")

        # ---------------------------------------------------------------- aturan ganti tetap
        def check_symbols(self, latex):
            """Kalau ada , [ ] di input: tampilkan konfirmasi; OK -> langsung diperbaiki."""
            counts = scan_symbols(latex)
            if not any(counts.values()) or latex == self._sym_declined:
                return latex
            shown = []
            for sym, n in counts.items():
                if n:
                    shown.append(f"    {sym}   ×{n}   →   {_SYM_MAP[sym]}")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle(tr("dlg_sym_title"))
            box.setText(tr("dlg_sym_body", items="\n".join(shown)))
            box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            ok = box.exec() == QMessageBox.StandardButton.Ok
            if not ok:
                self._sym_declined = latex          # jangan tanya lagi untuk teks yang sama
                return latex
            fixed = fix_symbols(latex)
            self.set_text(self.txt_in, fixed)
            self._sym_declined = ""
            self.say("s_sym_fixed", n=sum(counts.values()))
            return fixed

        def read_input(self):
            latex = self.txt_in.toPlainText().strip()
            latex = self.check_symbols(latex)
            self.rules["last"] = 0
            if self.v_rules.get() and self.rules["text"].strip():
                latex, self.rules["last"] = apply_rules(latex, self.rules["text"])
            return latex

        def rules_note(self):
            return [Msg("n_rules_applied", n=self.rules["last"])] if self.rules["last"] else []

        # ---------------------------------------------------------------- aksi utama
        def do_convert(self, copy=True):
            latex = self.read_input()
            if not latex:
                self.say("s_empty")
                return
            res, warns = convert(latex, subscript=self.v_sub.get(), define=self.v_define.get(),
                                 implicit_mult=self.v_mul.get(), log_base=self.v_log.get())
            extra = [Msg("n_mat_paste")] if "mat(" in res else []
            self.commit(latex, res, list(warns) + extra + self.rules_note(),
                        status="s_converted" if copy else None, copy=copy)

        def paste_convert(self):
            data = QGuiApplication.clipboard().text()
            if not data:
                self.say("s_clip_empty")
                return
            self.set_text(self.txt_in, data)
            self.do_convert()

        def copy_out(self):
            self.to_clipboard(self.txt_out.toPlainText().strip())
            self.say("s_copied")

        def clear_all(self):
            for w in (self.txt_in, self.txt_out, self.txt_warn):
                self.set_text(w, "")
            self.cur = None
            self.say("s_cleared")

        @staticmethod
        def _unsupported(warns):
            return any(isinstance(w, Msg) and w.key in ("w_bigop", "w_lim") for w in warns)

        # ---- format teks Prime (@EQ ...) ----
        def convert_sexpr(self):
            latex = self.read_input()
            if not latex:
                self.say("s_empty")
                return
            res, warns = convert(latex, subscript="literal", define=self.v_define.get(),
                                 implicit_mult=True, log_base=self.v_log.get())
            if self._unsupported(warns):
                self.set_text(self.txt_warn, "\n".join("• " + str(w) for w in warns))
                self.say("s_unsupported_sexpr")
                return
            try:
                sx, unverified, notes = build_sexpr(res)
            except ParseError as exc:
                self.set_text(self.txt_out, res)
                self.cur = {"in": latex, "out": res, "notes": [Msg("n_cannot_convert", err=exc)]}
                self.set_text(self.txt_warn, self.render_notes(self.cur))
                self.say("s_sexpr_failed")
                return
            out_notes = list(warns) + list(notes) + self.rules_note()
            out_notes.append(Msg("n_unverified", items=unverified) if unverified
                             else Msg("n_all_verified"))
            if not self.v_define.get():
                out_notes.append(Msg("n_eq_hint"))
            self.commit(latex, sx, out_notes, status="s_sexpr_copied")

        # ---- auto-ketik ke Mathcad Prime ----
        def finish_typing(self, key, **kw):
            self.typing["running"] = False
            self.btn_type.setEnabled(True)
            self.say(key, **kw)

        def stop_typing(self):
            if self.typing["running"]:
                self.finish_typing("s_type_cancelled")

        def type_step(self):
            ty = self.typing
            if not ty["running"]:
                return
            plan = ty["plan"]
            delay = max(0.0, self._float(self.v_delay, 50.0))
            # QTimer hanya presisi 1 ms: untuk jeda < 1 ms, kirim beberapa tombol per tik.
            # 0 ms = 50 tombol per putaran event loop (tombol Stop tetap responsif).
            if delay <= 0:
                batch, wait = 50, 0
            elif delay < 1.0:
                batch, wait = max(1, int(round(1.0 / delay))), 1
            else:
                batch, wait = 1, int(round(delay))
            for _ in range(batch):
                i = ty["i"]
                if i >= len(plan):
                    self.finish_typing("s_type_done")
                    return
                if own_window_has_focus():
                    self.finish_typing("s_type_focus_back")
                    return
                tok = plan[i]
                ty["i"] = i + 1
                if tok[0] == "w":                              # jeda tunggu (dialog / matriks)
                    self.say("s_typing", i=i + 1, n=len(plan))
                    QTimer.singleShot(int(tok[1]), self.type_step)
                    return
                try:
                    ty["typer"].send(tok)
                except Exception as exc:                       # noqa: BLE001
                    self.finish_typing("s_type_failed", err=exc)
                    return
                self.say("s_typing", i=i + 1, n=len(plan))
                if tok[2]:                                     # tombol lambat: beri jeda penuh
                    QTimer.singleShot(int(delay * 2.5) + 40, self.type_step)
                    return
            QTimer.singleShot(wait, self.type_step)

        def begin_typing(self):
            if not self.typing["running"]:
                return
            if own_window_has_focus():
                self.finish_typing("s_type_not_clicked")
                return
            try:
                self.typing["typer"] = WinTyper(real_keys=bool(self.v_real.get()))
            except Exception as exc:                           # noqa: BLE001
                self.finish_typing("s_type_windows_only", err=exc)
                return
            self.typing["i"] = 0
            self.type_step()

        def countdown(self, n):
            if not self.typing["running"]:
                return
            if n > 1e-9:
                self.say("s_countdown", n=("%g" % round(n, 1)))
                step = min(1.0, n)
                QTimer.singleShot(int(step * 1000), lambda: self.countdown(n - step))
            else:
                self.begin_typing()

        def start_typing(self):
            if self.typing["running"]:
                return
            if not sys.platform.startswith("win"):
                self.say("s_type_windows_only", err="")
                return
            latex = self.read_input()
            if not latex:
                self.say("s_empty")
                return
            res, warns = convert(latex, subscript="literal", define=self.v_define.get(),
                                 implicit_mult=True, log_base=self.v_log.get())
            if self._unsupported(warns):
                self.set_text(self.txt_warn, "\n".join("• " + str(w) for w in warns))
                self.say("s_unsupported_type")
                return
            try:
                plan, pw = build_plan(res, greek_ctrlg=bool(self.v_greek.get()))
            except ParseError as exc:
                self.set_text(self.txt_out, res)
                self.cur = {"in": latex, "out": res, "notes": [Msg("n_cannot_type", err=exc)]}
                self.set_text(self.txt_warn, self.render_notes(self.cur))
                self.say("s_plan_failed")
                return
            notes = list(warns) + list(pw) + self.rules_note()
            notes.append(Msg("n_plan", plan=describe_plan(plan)))
            self.commit(latex, res, notes, copy=False)
            self.typing.update(running=True, plan=plan, i=0)
            self.btn_type.setEnabled(False)
            self.countdown(max(0.5, self._float(self.v_count, 4.0)))

        # ---------------------------------------------------------------- cari & ganti
        def _target(self):
            return self.txt_in if self.o_target.get() == "in" else self.txt_out

        def _pattern(self):
            f = self.f_var.text()
            if not f:
                self.say("s_fill_find")
                return None
            pat = f if self.o_regex.get() else re.escape(f)
            if self.o_whole.get():
                pat = r"(?<!\w)(?:" + pat + r")(?!\w)"
            try:
                return re.compile(pat, 0 if self.o_case.get() else re.IGNORECASE)
            except re.error as exc:
                self.say("s_bad_regex", err=exc)
                return None

        def _expand(self, m):
            return m.expand(self.r_var.text()) if self.o_regex.get() else self.r_var.text()

        def find_next(self):
            pat, w = self._pattern(), self._target()
            if not pat:
                return None
            text = w.toPlainText()
            cur = w.textCursor().position()
            m = pat.search(text, cur) or pat.search(text, 0)
            if not m:
                c = w.textCursor()
                c.clearSelection()
                w.setTextCursor(c)
                self.say("s_not_found")
                return None
            c = w.textCursor()
            c.setPosition(m.start())
            c.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            w.setTextCursor(c)
            w.ensureCursorVisible()
            self.say("s_found_at", pos=m.start() + 1)
            return m

        def replace_one(self):
            pat, w = self._pattern(), self._target()
            if not pat:
                return
            c = w.textCursor()
            if not c.hasSelection():
                self.find_next()
                return
            m = pat.fullmatch(c.selectedText().replace(" ", "\n"))
            if not m:
                self.find_next()
                return
            try:
                new = self._expand(m)
            except (re.error, IndexError) as exc:
                self.say("s_bad_replacement", err=exc)
                return
            c.insertText(new)
            w.setTextCursor(c)
            self.find_next()

        def replace_all(self):
            pat, w = self._pattern(), self._target()
            if not pat:
                return
            text = w.toPlainText()
            try:
                new, n = pat.subn(self._expand, text)
            except (re.error, IndexError) as exc:
                self.say("s_bad_replacement", err=exc)
                return
            if n:
                self.set_text(w, new)
            self.say("s_replaced", n=n)

        def save_as_rule(self):
            f, r = self.f_var.text().strip(), self.r_var.text().strip()
            if not f:
                self.say("s_fill_find")
                return
            prefix = "re:" if self.o_regex.get() else ""
            line = f"{prefix}{f} => {r}"
            cur = self.rules_box.toPlainText().strip()
            self.rules_box.moveCursor(QTextCursor.MoveOperation.End)
            self.rules_box.insertPlainText(("\n" if cur else "") + line)
            self.say("s_rule_added")

        # ---------------------------------------------------------------- pintasan & clipboard
        def _bind_keys(self):
            def sc(seq, fn):
                s = QShortcut(QKeySequence(seq), self)
                s.activated.connect(fn)
                return s
            sc("Ctrl+Return", self.do_convert)
            sc("Ctrl+Enter", self.do_convert)
            sc("Ctrl+H", self.toggle_find)
            sc("Esc", lambda: self.toggle_find() if self.find_visible else None)
            sc("Alt+Left", self.go_prev)
            sc("Alt+Right", self.go_next)
            sc("F1", lambda: self.goto(self.tab_help))

        def watch(self):
            if not self.v_watch.get():
                return
            data = QGuiApplication.clipboard().text()
            if data and data != self.state["last_clip"] and data != self.state["watch_skip"]:
                self.state["last_clip"] = data
                if any(c in data for c in ("\\", "^", "_", "$", "{")):
                    self.set_text(self.txt_in, data)
                    self.do_convert()


    def run_gui():
        app = QApplication.instance() or QApplication(sys.argv)
        win = App(app)
        win.show()
        sys.exit(app.exec())


if not HAVE_QT:
    def run_gui():
        msg = 'PySide6 is required for the GUI.  Install it with:  pip install PySide6'
        print(msg, file=sys.stderr)
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror(APP_TITLE, msg)
        except Exception:                              # noqa: BLE001
            pass


# ----------------------------------------------------------------------------
def _cli(argv):
    cfg = load_settings()
    set_language(cfg["language"])
    args = list(argv)
    if "--lang" in args:                      # --lang en|id
        k = args.index("--lang")
        if k + 1 < len(args) and args[k + 1] in LANGS:
            set_language(args[k + 1])
            del args[k:k + 2]
    if len(args) > 1 and args[0] == "--sexpr":
        # python latex_to_mathcad.py --sexpr "\frac{a}{b}"  -> format teks Prime (@)
        lin, w = convert(" ".join(args[1:]), subscript="literal", define=False)
        try:
            sx, unv, notes = build_sexpr(lin)
            print(sx)
            for x in w + notes:
                print("# " + str(x), file=sys.stderr)
            if unv:
                print("# " + str(Msg("n_unverified", items=unv)), file=sys.stderr)
        except ParseError as exc:
            print("ERROR:", exc)
    elif len(args) > 1 and args[0] == "--plan":
        # python latex_to_mathcad.py --plan "\frac{a}{b}"   -> tampilkan urutan tombol
        lin, w = convert(" ".join(args[1:]), subscript="literal", define=True)
        print(lin)
        try:
            p, pw = build_plan(lin)
            print(describe_plan(p))
            for x in w + pw:
                print("# " + str(x), file=sys.stderr)
        except ParseError as exc:
            print("ERROR:", exc)
    elif args:
        r, w = convert(" ".join(args))
        print(r)
        for x in w:
            print("# " + str(x), file=sys.stderr)
    else:
        run_gui()


if __name__ == "__main__":
    _cli(sys.argv[1:])

