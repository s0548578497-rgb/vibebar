# התאמת VibeBar למערכות הפעלה

הקוד המקורי של מרגולן נשאר מקור האמת של גרסת macOS. המתאמים אינם מעתיקים את
הסקריפטים שלו ואינם משנים את פורמט היומן; הם מחברים אותם לחוזים המשותפים.

## שכבות

1. `vibebar_modular` — חוזים, לוחיות Null, הרכבות וליבת Legacy משותפת.
2. `vibebar_windows` — מימושים של Windows בלבד.
3. `vibebar_macos` — מימושים של macOS בלבד.
4. `blocks` — יכולות עצמאיות שאינן תלויות בממשק המשתמש.

אין import מ־`vibebar_macos` אל `vibebar_windows` או להפך. בחירה במימוש נעשית
רק בנקודת ההרכבה של הפלטפורמה.

## מצב שקעי macOS

| שקע | מימוש | מצב |
|---|---|---|
| יומן, דוחות ולוח העתקה | סקריפטי Legacy המקוריים | מחובר |
| תפריט | SwiftBar וה־URL המקורי לרענון | מחובר |
| פתיחת קבצים | הפקודה `open` | מחובר |
| צליל אישור | `afplay` וצליל מערכת | מחובר |
| קיצור הקלטה | `pynput` והרשאת Accessibility | מחובר |
| שינוי יומן | רענון SwiftBar הקיים | Null בטוח בתהליך Python |
| מצב חיבור Bluetooth | `system_profiler` JSON | שקע גיבוי אופציונלי |
| מרחק Bluetooth RSSI | helper ב־Swift מעל `IOBluetoothDevice.rawRSSI()` | מחובר; דורש כיול חומרה |

שקע Bluetooth של macOS קורא RSSI אמיתי דרך API של Apple. ערך `127`, ש־Apple
מגדירה כלא זמין או מנותק, אינו הופך למרחק מלאכותי. קורא ששותק נעטף באותו
`RestartingSignalSource` של Windows, ומנוע החציון וההפסקות משותף לשניהם.

## בדיקה בלי Mac מקומי

הבדיקות המקומיות מאמתות חוזים, parsing, כיוון בטוח והיעדר תלות ב־Windows.
ה־workflow שב־`.github/workflows/cross-platform.yml` מיועד להריץ ב־Mac אמיתי של
GitHub את בדיקות הליבה, מתאמי macOS ובדיקת התחביר של הסקריפטים. הוא ירוץ רק לאחר
שהענף יועלה ל־GitHub. מיקרופון, הרשאות Accessibility ו־Bluetooth פיזי עדיין
דורשים בדיקת קבלה חד־פעמית על מחשב Mac.
