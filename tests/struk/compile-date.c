/* Reproduce СТРУК's header date 11.11.86 without changing generated words.
 * Calendar conversion is fixed; emulator CPU accounting and host timeouts run normally.
 */
#include <time.h>

struct tm *localtime(const time_t *value)
{
    static _Thread_local struct tm date;
    (void)value;
    date = (struct tm){ .tm_year = 86, .tm_mon = 10, .tm_mday = 11,
                        .tm_wday = 2, .tm_yday = 314, .tm_isdst = 0 };
    return &date;
}
