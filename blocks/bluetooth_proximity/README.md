# Bluetooth Proximity Block

בלוק עצמאי להמרת סדרת מדידות RSSI למצב יציב: `NEAR`, `FAR` או `UNKNOWN`.
הוא אינו מחובר ל־VibeBar ואינו משנה התקני שמע או הגדרות Windows.

## הרצה ראשונית

```powershell
python -m bluetooth_proximity.cli
```

הזן בכל שורה RSSI, לדוגמה `-55`. הזן `missing` לדגימה חסרה ו־`quit` לסיום.

האלגוריתם משתמש בחציון, ספים נפרדים ליציאה ולחזרה, ואישור במספר דגימות רצופות.
מקור האות הוא שקע נפרד: בשלב הבא ניתן לחבר קורא Windows Classic, קורא BLE או סימולטור
בלי לשנות את מנוע ההחלטה.

## מקור Windows Classic

`native/ClassicRssiReader.cs` קורא RSSI חי מ־BTHPORT ומוציא מספר אחד בכל שורה.
בונים אותו באמצעות `native/build.ps1`. המתאם `WindowsClassicRssiSource` עוטף אותו
כשקע Python. זהו ממשק Windows פנימי, ולכן כשל בו מחזיר דגימה חסרה ולא משנה דבר במערכת.

במתאם MediaTek שנבדק, BTHPORT מסמן את הערך כמוחלט אך מחזיר את עוצמת ה־dBm כחיובית;
הקורא מנרמל אותה לערך dBm שלילי לפני שהיא מגיעה למנוע.

`WindowsClassicRssiSource` משתמש כברירת־מחדל במצב היחסי שמתאים למתאם MediaTek:
קרוב מתקבל כ־`0`, והיחלשות מעבר לטווח התקין מתקבלת כמספר שלילי. אפשר להעביר
`absolute=True` עבור מתאם שתומך ב־RSSI מוחלט אמין.
