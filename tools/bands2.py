# -*- coding: utf-8 -*-
"""Faixas decorativas completas — mapeamento final por página."""
from bands import BAND_NOITE, BAND_BANHO, BAND_VARAL

BAND_JORNADA = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M15 78 C58 54 91 84 129 68 S187 48 222 69 S284 88 321 69 S379 46 416 64 S475 86 514 65 S561 48 590 58" stroke="#b5aa9c" stroke-dasharray="2 6"/>
    <path d="M17 78 Q25 69 32 67 Q29 75 35 80 Q27 80 17 78Z" fill="#f2e3d2" opacity=".75"/>
    <path d="M32 67 Q43 58 51 53 M38 61 Q47 62 52 68"/>
    <path d="M98 70 L98 51 L113 55 L98 60Z" fill="#c0763b" opacity=".68"/>
    <path d="M202 69 L202 48 L217 53 L202 58Z" fill="#e9efe7" opacity=".82"/>
    <path d="M310 72 L310 51 L325 56 L310 61Z" fill="#f6e9e5" opacity=".76"/>
    <path d="M410 65 L410 44 L425 49 L410 54Z" fill="#7a9678" opacity=".7"/>
    <path d="M516 66 L516 45 L531 50 L516 55Z" fill="#f2e3d2" opacity=".78"/>
    <path d="M72 83 Q75 71 81 83 M77 83 Q85 76 89 74 M77 83 Q69 78 65 76" stroke="#7a9678"/>
    <path d="M155 76 Q158 63 164 76 M160 76 Q168 69 173 68 M160 76 Q153 70 149 69" stroke="#c0763b"/>
    <path d="M257 80 Q260 67 266 80 M263 80 Q271 73 275 72 M263 80 Q256 74 251 73" stroke="#7a9678"/>
    <path d="M359 75 Q362 62 368 75 M365 75 Q373 69 378 68 M365 75 Q358 69 354 68" stroke="#c0763b"/>
    <path d="M468 78 Q471 65 477 78 M474 78 Q482 71 487 70 M474 78 Q467 72 463 71" stroke="#7a9678"/>
    <path d="M554 31 L569 15 L584 31 L569 43Z" fill="#e8eef5" opacity=".72"/>
    <path d="M569 43 Q570 53 565 59 M554 31 L544 25 M584 31 L593 25"/>
    <path d="M65 23 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#f2e3d2" opacity=".78"/>
    <path d="M163 22 l2 4 4 2-4 2-2 4-2-4-4-2 4-2Z" fill="#e9efe7" opacity=".82"/>
    <path d="M278 28 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#f6e9e5" opacity=".8"/>
    <path d="M456 23 l2 4 4 2-4 2-2 4-2-4-4-2 4-2Z" fill="#f2e3d2" opacity=".78"/>
    <circle cx="126" cy="28" r="1.5" fill="#c0763b" opacity=".7" stroke="none"/>
    <circle cx="239" cy="22" r="1.8" fill="#7a9678" opacity=".7" stroke="none"/>
    <circle cx="345" cy="29" r="1.4" fill="#c0763b" opacity=".65" stroke="none"/>
    <circle cx="500" cy="27" r="1.7" fill="#7a9678" opacity=".68" stroke="none"/>
  </g>
</svg>'''

BAND_FRALDAS = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="83" cy="35" rx="43" ry="18" fill="#e9efe7" opacity=".58" stroke="none"/>
    <path d="M33 48 Q42 36 55 41 Q63 25 78 37 Q92 26 105 40 Q119 37 128 49 Q86 53 33 48Z" fill="#e9efe7" opacity=".68"/>
    <path d="M33 48 Q42 36 55 41 Q63 25 78 37 Q92 26 105 40 Q119 37 128 49" stroke="#b5aa9c"/>
    <ellipse cx="500" cy="34" rx="49" ry="18" fill="#f2e3d2" opacity=".57" stroke="none"/>
    <path d="M450 48 Q459 36 473 41 Q481 24 498 37 Q512 25 526 40 Q540 37 548 49 Q504 54 450 48Z" fill="#f2e3d2" opacity=".68"/>
    <path d="M450 48 Q459 36 473 41 Q481 24 498 37 Q512 25 526 40 Q540 37 548 49" stroke="#b5aa9c"/>
    <path d="M157 77 Q155 68 163 64 L219 64 Q226 68 224 77 Q189 82 157 77Z" fill="#e9efe7" opacity=".78"/>
    <path d="M161 65 Q190 69 220 64 M157 77 Q189 73 224 77"/>
    <path d="M165 64 Q162 56 170 53 L213 53 Q220 57 217 65 Q190 69 165 64Z" fill="#f2e3d2" opacity=".76"/>
    <path d="M169 54 Q191 58 214 53"/>
    <path d="M173 53 Q170 45 178 42 L207 42 Q214 46 212 54 Q191 57 173 53Z" fill="#e9efe7" opacity=".78"/>
    <path d="M178 43 Q192 47 207 42"/>
    <path d="M338 82 Q336 71 345 67 L402 67 Q410 72 408 82 Q371 87 338 82Z" fill="#f2e3d2" opacity=".77"/>
    <path d="M342 68 Q371 73 404 67 M338 82 Q371 78 408 82"/>
    <path d="M345 67 Q342 58 351 55 L396 55 Q404 59 401 68 Q371 72 345 67Z" fill="#e9efe7" opacity=".78"/>
    <path d="M350 56 Q373 61 397 55"/>
    <path d="M99 80 C105 65 117 55 126 59 C136 64 129 75 112 83 C101 88 94 87 99 80Z" fill="#f6e9e5" opacity=".72"/>
    <path d="M104 80 C112 71 120 65 125 66"/>
    <circle cx="106" cy="81" r="4.5" fill="#e8eef5" opacity=".78"/>
    <circle cx="126" cy="62" r="4.5" fill="#e8eef5" opacity=".78"/>
    <path d="M458 83 C464 68 476 58 485 62 C495 67 488 78 471 86 C460 91 453 90 458 83Z" fill="#f6e9e5" opacity=".72"/>
    <path d="M463 83 C471 74 479 68 484 69"/>
    <circle cx="465" cy="84" r="4.5" fill="#e8eef5" opacity=".78"/>
    <circle cx="485" cy="65" r="4.5" fill="#e8eef5" opacity=".78"/>
    <circle cx="34" cy="73" r="1.7" fill="#c0763b" opacity=".7" stroke="none"/>
    <circle cx="60" cy="83" r="1.3" fill="#7a9678" opacity=".68" stroke="none"/>
    <circle cx="278" cy="61" r="1.6" fill="#b5aa9c" opacity=".75" stroke="none"/>
    <circle cx="301" cy="79" r="2" fill="#c0763b" opacity=".6" stroke="none"/>
    <circle cx="541" cy="73" r="1.6" fill="#7a9678" opacity=".7" stroke="none"/>
    <circle cx="566" cy="82" r="1.3" fill="#b5aa9c" opacity=".76" stroke="none"/>
  </g>
</svg>'''

BAND_FARMACINHA = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="164" cy="45" rx="108" ry="30" fill="#f6e9e5" opacity=".48" stroke="none"/>
    <ellipse cx="428" cy="49" rx="118" ry="31" fill="#e9efe7" opacity=".5" stroke="none"/>
    <path d="M33 78 Q146 73 254 78 T460 78 T576 77" stroke="#453c33"/>
    <path d="M35 81 Q146 76 254 81 T460 81 T576 80" stroke="#b5aa9c" opacity=".5"/>
    <path d="M49 78 L51 90 L76 90 L79 78Z" fill="#f6e9e5" opacity=".72"/>
    <path d="M53 76 Q55 63 64 68 Q68 58 74 68 Q81 64 82 76 Q67 79 53 76Z" fill="#e9efe7" opacity=".78"/>
    <path d="M63 76 Q62 63 55 58 M68 76 Q73 65 80 61"/>
    <path d="M113 77 L116 49 Q130 44 144 49 L147 77Z" fill="#f6e9e5" opacity=".76"/>
    <path d="M117 49 L119 43 L141 43 L143 49 M118 60 Q130 64 144 60"/>
    <path d="M171 77 L174 56 Q188 52 201 56 L204 77Z" fill="#e9efe7" opacity=".8"/>
    <path d="M176 56 L178 51 L197 51 L199 56 M175 66 Q188 69 202 66"/>
    <path d="M231 77 L233 52 L256 52 L259 77Z" fill="#f6e9e5" opacity=".76"/>
    <path d="M233 52 Q245 46 256 52 M234 62 Q245 66 258 62"/>
    <path d="M288 77 L293 57 Q310 53 320 59 L316 77Z" fill="#e9efe7" opacity=".78"/>
    <path d="M293 57 L295 51 L313 53 L320 59 M292 67 Q304 70 318 67"/>
    <path d="M347 61 Q362 55 375 61 L375 77 L347 77Z" fill="#f6e9e5" opacity=".75"/>
    <path d="M351 61 Q361 67 371 61 M353 57 Q361 50 369 57"/>
    <path d="M402 59 L443 68 L439 80 L398 71Z" fill="#e9efe7" opacity=".78"/>
    <path d="M402 59 L407 51 L448 60 L443 68 M408 66 L440 75"/>
    <path d="M473 69 Q486 59 497 66 L495 77 L474 77Z" fill="#f6e9e5" opacity=".78"/>
    <path d="M478 67 Q485 73 492 67"/>
    <path d="M520 78 L522 90 L548 90 L551 78Z" fill="#e9efe7" opacity=".8"/>
    <path d="M525 76 Q526 63 535 69 Q540 58 545 69 Q552 65 555 76 Q540 80 525 76Z" fill="#f6e9e5" opacity=".75"/>
    <path d="M535 76 Q533 64 527 59 M541 76 Q547 66 553 62"/>
    <path d="M273 34 L280 38 L276 44 L269 40Z" fill="#f2e3d2" opacity=".78"/>
    <path d="M274 34 Q282 29 288 34 L291 40 L284 45 L276 44"/>
    <path d="M272 37 L288 42"/>
    <circle cx="92" cy="35" r="1.4" fill="#c2857b" opacity=".7" stroke="none"/>
    <circle cx="153" cy="28" r="1.7" fill="#7a9678" opacity=".68" stroke="none"/>
    <circle cx="213" cy="35" r="1.4" fill="#c2857b" opacity=".7" stroke="none"/>
    <circle cx="374" cy="30" r="1.7" fill="#7a9678" opacity=".68" stroke="none"/>
    <circle cx="448" cy="36" r="1.4" fill="#c2857b" opacity=".7" stroke="none"/>
  </g>
</svg>'''

BAND_AMAMENTACAO = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="136" cy="57" rx="91" ry="33" fill="#f2e3d2" opacity=".5" stroke="none"/>
    <ellipse cx="431" cy="59" rx="103" ry="34" fill="#f6e9e5" opacity=".52" stroke="none"/>
    <path d="M76 80 L79 38 Q94 32 109 38 L112 80Z" fill="#e8eef5" opacity=".74"/>
    <path d="M80 38 L82 28 L106 28 L108 38 M85 28 L85 23 L103 23 L103 28"/>
    <path d="M79 52 Q94 56 110 52 M78 65 Q94 69 111 65"/>
    <path d="M85 77 Q94 70 104 77" stroke="#c0763b" opacity=".72"/>
    <path d="M184 81 L187 52 Q198 48 209 52 L212 81Z" fill="#f6e9e5" opacity=".77"/>
    <path d="M188 52 L190 44 L207 44 L209 52 M192 44 L192 40 L205 40 L205 44"/>
    <path d="M187 63 Q198 67 210 63"/>
    <path d="M319 64 Q328 52 338 64 Q348 52 357 64 Q355 76 338 83 Q321 76 319 64Z" fill="#f2e3d2" opacity=".76"/>
    <path d="M323 64 Q338 70 353 64 M325 72 Q338 78 351 72"/>
    <path d="M384 78 Q387 61 403 63 L444 69 Q452 73 449 82 Q418 88 384 78Z" fill="#f6e9e5" opacity=".78"/>
    <path d="M390 73 Q417 78 447 75 M395 68 Q418 73 442 70"/>
    <path d="M468 61 Q465 67 469 72 Q473 67 472 61Z" fill="#c0763b" opacity=".66"/>
    <path d="M499 48 Q496 54 500 59 Q504 54 503 48Z" fill="#c2857b" opacity=".66"/>
    <path d="M540 69 Q537 75 541 80 Q545 75 544 69Z" fill="#c0763b" opacity=".66"/>
    <path d="M142 35 C137 28 126 32 130 40 C134 47 142 50 142 50 C142 50 151 43 154 36 C157 29 147 28 142 35Z" fill="#f6e9e5" opacity=".84"/>
    <path d="M258 31 C254 25 245 28 248 35 C251 41 258 44 258 44 C258 44 266 38 268 32 C271 26 263 25 258 31Z" fill="#f2e3d2" opacity=".84"/>
    <path d="M558 38 C554 32 545 35 548 42 C551 48 558 51 558 51 C558 51 566 45 568 39 C571 33 563 32 558 38Z" fill="#f6e9e5" opacity=".84"/>
    <circle cx="42" cy="48" r="2" fill="#c2857b" opacity=".62" stroke="none"/>
    <circle cx="52" cy="67" r="1.4" fill="#c0763b" opacity=".68" stroke="none"/>
    <circle cx="158" cy="72" r="1.5" fill="#c2857b" opacity=".67" stroke="none"/>
    <circle cx="235" cy="75" r="1.8" fill="#c0763b" opacity=".63" stroke="none"/>
    <circle cx="286" cy="49" r="1.5" fill="#c2857b" opacity=".65" stroke="none"/>
    <circle cx="475" cy="32" r="1.7" fill="#c0763b" opacity=".67" stroke="none"/>
    <path d="M13 91 Q83 87 155 91 T304 91 T455 91 T591 90" stroke="#b5aa9c" opacity=".48"/>
  </g>
</svg>'''

BAND_PASSEIO = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="548" cy="20" r="19" fill="#f2e3d2" opacity=".76" stroke="none"/>
    <path d="M548 0 L548 7 M528 8 L534 13 M568 8 L562 13 M522 24 L530 24 M574 24 L566 24 M529 39 L535 33 M567 39 L561 33" stroke="#c0763b"/>
    <path d="M8 84 Q78 77 141 83 T273 83 T404 84 T528 82 T593 85" stroke="#b5aa9c"/>
    <path d="M64 82 L64 56 M64 63 Q48 61 43 72 Q54 73 64 68 M64 60 Q76 49 88 58 Q79 66 64 67 M64 56 Q67 44 75 42 Q78 52 70 60" fill="#e9efe7" opacity=".76"/>
    <path d="M478 82 L478 54 M478 64 Q463 60 456 72 Q467 73 478 68 M478 60 Q490 49 502 58 Q493 66 478 68 M478 54 Q481 44 489 41 Q492 52 484 60" fill="#e9efe7" opacity=".76"/>
    <path d="M232 77 Q238 44 269 43 Q300 44 308 75 L232 77Z" fill="#e8eef5" opacity=".7"/>
    <path d="M239 75 Q244 52 269 52 Q294 52 301 75Z"/>
    <path d="M249 48 Q269 38 289 48"/>
    <path d="M255 77 A14 14 0 1 0 255 77 M286 77 A14 14 0 1 0 286 77"/>
    <path d="M259 77 A10 10 0 1 0 259 77 M290 77 A10 10 0 1 0 290 77"/>
    <path d="M225 53 Q211 57 202 67 M202 67 Q196 68 193 64"/>
    <path d="M117 28 Q122 23 127 28 Q132 23 137 28" stroke="#453c33"/>
    <path d="M345 35 Q350 30 355 35 Q360 30 365 35" stroke="#453c33"/>
    <path d="M397 18 L411 7 L425 19 L411 30Z" fill="#f6e9e5" opacity=".74"/>
    <path d="M411 30 Q410 40 405 46 M397 18 L388 15 M425 19 L434 15"/>
    <path d="M154 74 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#f2e3d2" opacity=".78"/>
    <path d="M536 65 l2 4 4 2-4 2-2 4-2-4-4-2 4-2Z" fill="#e8eef5" opacity=".82"/>
    <circle cx="30" cy="52" r="1.6" fill="#7a9678" opacity=".68" stroke="none"/>
    <circle cx="179" cy="41" r="1.4" fill="#c0763b" opacity=".68" stroke="none"/>
    <circle cx="329" cy="67" r="1.7" fill="#6b8fb5" opacity=".66" stroke="none"/>
    <circle cx="442" cy="48" r="1.4" fill="#c0763b" opacity=".68" stroke="none"/>
  </g>
</svg>'''

BAND_MALA = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="285" cy="60" rx="143" ry="34" fill="#e8eef5" opacity=".44" stroke="none"/>
    <path d="M164 78 Q164 52 185 44 Q281 30 378 45 Q398 53 398 78Z" fill="#f2e3d2" opacity=".75"/>
    <path d="M164 78 Q164 52 185 44 Q281 30 378 45 Q398 53 398 78Z"/>
    <path d="M174 77 Q185 53 194 51 Q278 40 369 51 Q382 56 389 77Z" fill="#e8eef5" opacity=".7"/>
    <path d="M174 77 Q185 53 194 51 Q278 40 369 51 Q382 56 389 77"/>
    <path d="M198 54 Q217 50 237 55 L235 68 L199 68Z" fill="#c2857b" opacity=".67"/>
    <path d="M202 56 Q217 60 232 56"/>
    <path d="M247 52 Q266 47 286 53 L284 68 L248 68Z" fill="#e9efe7" opacity=".78"/>
    <path d="M252 54 Q266 59 281 54"/>
    <path d="M297 53 Q317 48 341 54 L339 69 L298 69Z" fill="#f6e9e5" opacity=".78"/>
    <path d="M302 55 Q318 60 337 55"/>
    <path d="M169 79 L173 86 L190 86 L194 79 M369 79 L373 86 L390 86 L394 79"/>
    <path d="M395 54 L425 48 L431 67 L401 73Z" fill="#e8eef5" opacity=".75"/>
    <path d="M425 48 L431 67 L419 69 L413 51Z"/>
    <path d="M92 72 Q95 57 110 55 Q124 55 131 66 Q122 73 108 73Z" fill="#f2e3d2" opacity=".76"/>
    <path d="M96 61 Q109 50 122 61 M105 56 Q103 47 112 44 Q119 48 117 57"/>
    <path d="M454 62 L482 62 L486 86 L450 86Z" fill="#c0763b" opacity=".67"/>
    <path d="M454 62 L468 52 L482 62 M468 52 L486 62"/>
    <path d="M463 70 L473 70 L473 79 L463 79Z" fill="#e8eef5" opacity=".8"/>
    <path d="M523 43 L542 48 L537 69 L518 64Z" fill="#f2e3d2" opacity=".78"/>
    <path d="M523 43 L542 48 L539 55 L520 50Z"/>
    <circle cx="52" cy="32" r="1.5" fill="#6b8fb5" opacity=".68" stroke="none"/>
    <path d="M145 24 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#f2e3d2" opacity=".8"/>
    <path d="M425 26 l2 4 4 2-4 2-2 4-2-4-4-2 4-2Z" fill="#e8eef5" opacity=".82"/>
    <path d="M566 43 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#f2e3d2" opacity=".78"/>
    <circle cx="69" cy="81" r="1.5" fill="#c0763b" opacity=".66" stroke="none"/>
    <circle cx="140" cy="72" r="1.4" fill="#6b8fb5" opacity=".67" stroke="none"/>
    <circle cx="445" cy="39" r="1.6" fill="#c0763b" opacity=".66" stroke="none"/>
  </g>
</svg>'''

BAND_CHEGADA = '''<svg viewBox="0 0 600 100" xmlns="http://www.w3.org/2000/svg" fill="none">
  <g stroke="#453c33" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 18 Q91 28 170 18 T329 19 T487 18 T590 21" stroke="#453c33"/>
    <path d="M32 21 L46 42 L60 23Z" fill="#f6e9e5" opacity=".8"/>
    <path d="M76 25 L90 46 L104 24Z" fill="#e9efe7" opacity=".82"/>
    <path d="M122 23 L137 43 L151 21Z" fill="#f2e3d2" opacity=".8"/>
    <path d="M171 19 L185 40 L199 20Z" fill="#e8eef5" opacity=".8"/>
    <path d="M220 21 L235 42 L249 20Z" fill="#f6e9e5" opacity=".8"/>
    <path d="M271 21 L286 41 L300 20Z" fill="#e9efe7" opacity=".82"/>
    <path d="M323 20 L338 41 L352 20Z" fill="#f2e3d2" opacity=".8"/>
    <path d="M376 20 L391 41 L405 20Z" fill="#e8eef5" opacity=".8"/>
    <path d="M428 20 L443 42 L457 20Z" fill="#f6e9e5" opacity=".8"/>
    <path d="M480 20 L495 41 L509 20Z" fill="#e9efe7" opacity=".82"/>
    <path d="M530 20 L545 41 L559 21Z" fill="#f2e3d2" opacity=".8"/>
    <ellipse cx="154" cy="71" rx="58" ry="24" fill="#f6e9e5" opacity=".48" stroke="none"/>
    <path d="M111 65 L154 51 L197 65 L197 88 L111 88Z" fill="#f2e3d2" opacity=".77"/>
    <path d="M111 65 L154 76 L197 65 M154 51 L154 88"/>
    <path d="M145 51 Q154 42 163 51 L163 60 Q154 68 145 60Z" fill="#c2857b" opacity=".72"/>
    <path d="M111 65 L125 56 L154 68 L183 56 L197 65"/>
    <ellipse cx="403" cy="70" rx="64" ry="25" fill="#e9efe7" opacity=".5" stroke="none"/>
    <path d="M350 57 L447 57 L440 84 L357 84Z" fill="#e8eef5" opacity=".76"/>
    <path d="M350 57 L398 77 L447 57 M357 84 L398 66 L440 84"/>
    <circle cx="398" cy="68" r="6" fill="#c2857b" opacity=".78"/>
    <path d="M395 68 Q398 64 401 68"/>
    <path d="M62 66 l3 7 7 3-7 3-3 7-3-7-7-3 7-3Z" fill="#f2e3d2" opacity=".82"/>
    <path d="M247 62 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#e9efe7" opacity=".84"/>
    <path d="M526 69 l3 7 7 3-7 3-3 7-3-7-7-3 7-3Z" fill="#f6e9e5" opacity=".85"/>
    <circle cx="28" cy="70" r="2" fill="#c0763b" opacity=".68" stroke="none"/>
    <circle cx="89" cy="82" r="1.5" fill="#7a9678" opacity=".7" stroke="none"/>
    <circle cx="224" cy="81" r="1.7" fill="#c2857b" opacity=".7" stroke="none"/>
    <g stroke="#453c33" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M251 76 Q263 68 275 76 L272 82 Q263 85 254 82 Z" fill="#f2e3d2" opacity=".9"/>
      <path d="M255 74 Q263 78 271 74 M258 71 L268 76 M268 71 L258 76" stroke="#c0763b" stroke-width="1.1"/>
      <circle cx="260" cy="70" r="1.6" fill="#a8544a" stroke="none"/><circle cx="265" cy="69" r="1.6" fill="#a8544a" stroke="none"/>
      <path d="M290 82 L304 82 L302 72 L292 72 Z" fill="#e8eef5" opacity=".9"/>
      <path d="M304 74 Q309 75 307 79 Q306 81 303 80"/>
      <path d="M294 68 Q296 64 294 61 M299 68 Q301 64 299 61" stroke="#b5aa9c"/>
    </g>
    <circle cx="278" cy="53" r="1.5" fill="#c0763b" opacity=".68" stroke="none"/>
    <circle cx="315" cy="82" r="1.7" fill="#7a9678" opacity=".68" stroke="none"/>
    <circle cx="478" cy="59" r="1.5" fill="#c2857b" opacity=".7" stroke="none"/>
    <circle cx="567" cy="82" r="1.8" fill="#c0763b" opacity=".67" stroke="none"/>
    <path d="M12 92 Q79 88 146 92 T281 92 T419 92 T589 91" stroke="#b5aa9c" opacity=".46"/>
  </g>
</svg>'''

BANDS = {
    'howto': BAND_JORNADA,
    'roupas': BAND_VARAL,
    'sono': BAND_NOITE,
    'banho': BAND_BANHO,
    'fraldas': BAND_FRALDAS,
    'farmacinha': BAND_FARMACINHA,
    'amamentacao': BAND_AMAMENTACAO,
    'passeio': BAND_PASSEIO,
    'mala': BAND_MALA,
    'docs': BAND_CHEGADA,
}
