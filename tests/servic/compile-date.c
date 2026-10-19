/* Reproduce the compilation date stored in word 00002 of СЕРВИС.
 * Override calendar conversion only; wall-clock and timeout functions run normally.
 */
#include <time.h>

struct tm *localtime(const time_t *value)
{
    static _Thread_local struct tm date;
    (void)value;
    date = (struct tm){ .tm_year = 88, .tm_mon = 10, .tm_mday = 21,
                        .tm_wday = 1, .tm_yday = 325, .tm_isdst = 0 };
    return &date;
}
