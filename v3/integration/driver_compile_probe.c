/* Compile/disassemble check only. No claim of execution on E203. */
#include "kwt_driver.h"
uint32_t probe(const volatile kwt_descriptor *descriptor) { return kwt_run(descriptor); }
