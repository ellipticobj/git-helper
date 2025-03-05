PHDRS {
    text PT_LOAD FILEHDR PHDRS FLAGS(5); /* R-X */
    data PT_LOAD FLAGS(6); /* RW- */
    dynamic PT_DYNAMIC FLAGS(6);
}

SECTIONS {
    . = SIZEOF_HEADERS;
    .text : { *(.text .text.*) } :text
    .rodata : { *(.rodata .rodata.*) } :text
    .data : { 
        *(.data .data.*)
        *(.got.plt) *(.got)
    } :data
    .dynamic : { *(.dynamic) } :data :dynamic
    .bss : { *(.bss .bss.*) } :data
    /DISCARD/ : {
        *(.note*)
        *(.gnu*)
        *(.comment*)
        *(.eh_frame*)
    }
}