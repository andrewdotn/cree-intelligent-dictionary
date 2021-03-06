Paradigm layouts
================

In `CreeDictionary/res/layouts` you will find files like these:

    .
    ├── na-basic.layout.tsv
    ├── na-linguistic.layout.tsv
    ├── na-full.layout.tsv
    ├── nad-basic.layout.tsv
    ├── nad-linguistic.layout.tsv
    ├── nad-full.layout.tsv
    ├── ni-basic.layout.tsv
    ├── ni-linguistic.layout.tsv
    ├── ni-full.layout.tsv
    ├── nid-basic.layout.tsv
    ├── nid-linguistic.layout.tsv
    ├── nid-full.layout.tsv
    ├── vai-basic.layout.tsv
    ├── vai-linguistic.layout.tsv
    ├── vai-full.layout.tsv
    ├── vii-basic.layout.tsv
    ├── vii-linguistic.layout.tsv
    ├── vii-full.layout.tsv
    ├── vta-basic.layout.tsv
    ├── vta-linguistic.layout.tsv
    ├── vta-full.layout.tsv
    ├── vti-basic.layout.tsv
    ├── vti-linguistic.layout.tsv
    └── vti-full.layout.tsv

The file names are in this format:

    {word class}-{name}.layout.{file type}

### Word class

The set of words this layout applies to. The lemma class starts with
either `n` or `v` for "noun" or "verb", respectively. Then a subtype is
provided (e.g., "nad" is noun, animate, dependent; "vta" is **verb**,
**transitive**, **animate**).

When a word form is analyzed, use its tags (e.g., `+V`, `+N`, `+TA`,
`+A`, `+D`, etc.) to match it to a layout.

### Name

This is a label for the layout. The current layouts are named in order
of detail, in ascending order of detail from "basic" to "linguistic" to
"full".

### File type

`.tsv` file is the layout as a tab-separated values file.

Layouts
-------

The layouts are stored in a tab-separated-values format, as exported by
Excel or LibreOffice.

Each cell in the TSV file is a cell in the displayed paradigm.

That is, the following TSV file defines a table that is 2 columns wide,
by 7 rows high (Note, tabs are visualized as a `␉` character, but are
a single U+0009 HORIZONTAL TABLATURE character):

    "1s poss (sg)"␉     =N+A+D+Px1Sg+Sg
    "2s poss (sg)"␉     =N+A+D+Px2Sg+Sg
    "3s poss (obv)"␉    =N+A+D+Px3Sg+Obv
    ␉                   : "Unspecified possessor"
    "X poss (sg)"␉      =N+A+D+PxX+Sg
    "X poss (pl)"␉      =N+A+D+PxX+Pl
    "X poss (obv)"␉     =N+A+D+PxX+Obv

Cell types
----------

Cells can either be **titles**, **word form templates**, or **empty**.

### Titles

Title cells are surrounded in double quotes, optionally preceded by
a `:` colon and whitespace, or followed by some whitespace and a colon.

For example:

 - `"1s poss (sg)"` is a title cell.
 - `: "Unspecified possessor"` is also a title cell.

It is recommended that title cells are converted into a `<th>` if
generating an HTML table.

If a colon is present, it signifies that the cell's contents should be
left-aligned or right-aligned, depending on where the colon is.

### Word form templates

Word form templates are requests to generate a word form from the FST.

| Example                           | Example lookup string              |
|-----------------------------------|------------------------------------|
| `${lemma}+N+I+D+PxX+Sg`           | mitêh+N+I+D+PxX+Sg                 |
| `PV/e+${lemma}+V+TA+Cnj+1Sg+2SgO` | PV/e+wâpamêw+V+TA+Cnj+1Sg+2SgO     |

Word form templates **MUST** contain `${lemma}`, which will be replaced
with the appropriate lemma to form the lookup string.

The general steps are the same:

 1. Apply the lemma to the pattern to create the **lookup string**.
 2. Call `FST.generate()` on the lookup string.
 3. Generate one or more `<td>` cell containing a generated word form.

### Empty cells

Empty cells are those that either contain no content, or whose only
content is whitespace. When generating an HTML table, these empty cells
**MAY** be output as an empty `<td></td>` element. This allows the rest
of the table to maintain its spacing.
