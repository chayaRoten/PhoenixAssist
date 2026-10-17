# PhoenixAssist

עוזר דיגיטלי בעברית שמחפש מידע באתר הציבורי של הפניקס ומציג קישורים לעמודים שעליהם מבוסס המענה. כשלא נמצא מידע מתאים, הבוט מציין זאת ולא מנחש.

## הרצה מקומית

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/ui.py
```

## פרסום כאתר ציבורי

אפשר לפרסם את האפליקציה דרך [Streamlit Community Cloud](https://share.streamlit.io/) לאחר שהקוד זמין ב-GitHub:

1. להיכנס ל-Streamlit Community Cloud באמצעות חשבון GitHub ולאשר את החיבור.
2. לבחור **Create app** ולבחור במאגר `chayaRoten/PhoenixAssist` ובענף `main`.
3. להגדיר את קובץ האפליקציה כ-`app/ui.py` וללחוץ **Deploy**.
4. לאחר פריסה מוצלחת, השירות יפיק כתובת `*.streamlit.app` שאפשר לשתף.

הפריסה דורשת הרשאה לחשבון Streamlit/GitHub של בעלת המאגר. אין בקוד מפתח API או סוד שצריך להזין. בזמן ריצה האפליקציה אוספת תוכן חי מהאתר הציבורי של הפניקס; זמינות ועדכניות התוכן תלויות בנגישות האתר.

## בדיקות

```powershell
python -m pytest -q
```
