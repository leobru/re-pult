/*
 * ADSIS-style scientific conversion, with all real arithmetic in float.
 *
 *   cc -std=c11 -Wall -Wextra -Wpedantic -O2 printfloat.c -lm -o printfloat
 *   ./printfloat 0.0625 14 1
 *
 * The algorithm estimates the decimal exponent from frexpf(), scales by
 * powers of ten, adds a rounding correction, and prints the fractional
 * digits as one integer field. This is an illustration of that algorithm:
 * finite-precision intermediates can give an incorrectly rounded last digit.
 * Precisions 1..10 reproduce the ADSIS parameter range; they do not promise
 * ten accurate fractional digits with a 24-bit float significand.
 *
 * Adaptations: handle zero, infinities and NaNs; keep the exponent sign;
 * scale in steps to cover subnormal floats; use the requested field width.
 * No floating-point printf conversion, log10f() or powf() is used.
 */
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static const float tens[] = {
    1e1f, 1e2f, 1e4f, 1e8f, 1e16f, 1e32f
};

/* Apply 10^exponent by its binary decomposition. A separate 10^45 would
 * overflow float, although multiplying a tiny float by it has a finite result.
 */
static float scale10(float x, int exponent)
{
    unsigned n = (unsigned)(exponent < 0 ? -exponent : exponent);
    for (unsigned i = 0; n != 0; ++i, n >>= 1) {
        if (n & 1u)
            x = exponent < 0 ? x / tens[i] : x * tens[i];
    }
    return x;
}

static void repeat(int ch, int count)
{
    while (count-- > 0)
        putchar(ch);
}

static void integer(uint64_t value, int width)
{
    char digits[32];
    int count = 0;
    do {
        digits[count++] = (char)('0' + value % 10);
        value /= 10;
    } while (value != 0);
    repeat('0', width - count);
    while (count != 0)
        putchar(digits[--count]);
}

void printfloat(float value, int width, int precision)
{
    static const float rounding[] = {
        0.05f, 0.005f, 0.0005f, 0.00005f, 0.000005f,
        0.0000005f, 0.00000005f, 0.000000005f,
        0.0000000005f, 0.00000000005f
    };
    const int negative = signbit(value) != 0;
    int binary_exponent, exponent = 0;
    float y = fabsf(value);

    if (precision < 1)
        precision = 1;
    if (precision > 10)
        precision = 10;
    if (width < 8)
        width = 8;

    if (!isfinite(y)) {
        repeat(' ', width - 4);
        putchar(negative ? '-' : ' ');
        fputs(isnan(y) ? "nan" : "inf", stdout);
        return;
    }

    if (y != 0.0f) {
        (void)frexpf(y, &binary_exponent);
        exponent = (int)floorf((float)binary_exponent * 0.30103f);
        y = scale10(y, -exponent);
        if (y < 1.0f) {
            y *= 10.0f;
            --exponent;
        }
        y += rounding[precision - 1];
        if (y >= 10.0f) {
            y /= 10.0f;
            ++exponent;
        }
    }

    repeat(' ', width - (precision + 7));
    putchar(negative ? '-' : ' ');
    unsigned leading = (unsigned)y;
    putchar((int)('0' + leading));
    putchar('.');

    /* Round first, then truncate: the same fractional-field scheme as ADSIS. */
    float fraction = y - (float)leading;
    uint64_t tail = (uint64_t)scale10(fraction, precision);
    integer(tail, precision);
    putchar('E');
    putchar(exponent < 0 ? '-' : '+');
    integer((uint64_t)(exponent < 0 ? -exponent : exponent), 2);
}

static int field(const char *text, int *result)
{
    char *end;
    errno = 0;
    long n = strtol(text, &end, 10);
    if (end == text || *end != '\0' || errno == ERANGE ||
        n < INT_MIN || n > INT_MAX)
        return 0;
    *result = (int)n;
    return 1;
}

int main(int argc, char **argv)
{
    int width = 14, precision = 4;
    char *end;
    if (argc < 2 || argc > 4) {
        fprintf(stderr, "Usage: %s number [width [precision]]\n", argv[0]);
        return 2;
    }
    float value = strtof(argv[1], &end);
    if (end == argv[1] || *end != '\0' ||
        (argc >= 3 && !field(argv[2], &width)) ||
        (argc >= 4 && !field(argv[3], &precision))) {
        fputs("Invalid number, width or precision\n", stderr);
        return 2;
    }
    printfloat(value, width, precision);
    putchar('\n');
    return ferror(stdout) ? 1 : 0;
}
