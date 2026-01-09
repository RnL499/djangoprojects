# 成績系統 (Minimal Django app)

管理者帳號:user

管理者密碼:user_@@@

---

快速啟動

1. 建立並啟用 virtualenv

```powershell
# 成績系統 (Django app)

簡介
-- 此專案是一個簡易的選課與成績管理系統，包含學生、教師與管理者三種角色，支援課程建立、選退課、成績輸入、留言與個人檔案（含頭像）。

主要功能
- 帳號與使用者管理
	- 學生註冊與登入
	- 管理員可建立教師帳號（或透過管理介面建立）
	- 個人資料編輯、上傳頭像
- 課程管理
	- 管理員：可新增/修改/刪除課程，並為課程指派教師
	- 教師：可建立自己任教的課程（教師專區）、查看任課學生名單、輸入期中與期末成績
	- 課程列表、可查詢本學期選課人數（可擴充報表）
- 選課管理
	- 學生可加選/退選課程
	- 教師/管理員可替學生加退選
- 成績管理
	- 學生：查詢期中/期末成績與本學期平均
	- 教師：為所屬課程學生輸入/修改成績
	- 支援成績 CRUD 與簡易驗證
- 留言系統
	- 登入使用者可於課程頁面留言、編輯或刪除自己的留言；管理員可刪除留言

角色行為重點
- 管理員 (is_staff / is_superuser)
	- 使用 Django admin 管理所有資料
	- 前端有專屬管理連結（包括「新增課程（指派教師）」）
- 教師 (加入 Teacher 群組或 Profile.is_teacher=True)
	- 登入後導向「教師專區」(teacher_courses)
	- 僅能管理自己任教之課程與該課程學生成績
- 學生
	- 登入後導向「我的修習課程」(student_courses)

快速啟動
1. 建立並啟用 virtualenv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安裝需求

```powershell
pip install -r requirements.txt
```

3. 建立資料庫遷移並套用

```powershell
python manage.py makemigrations
python manage.py migrate
```

4. 建立 superuser（管理員）

```powershell
python manage.py createsuperuser
```

5. 建立 media 資料夾

```powershell
mkdir media
mkdir media\avatars
```

6. （選用）建立示範資料

```powershell
python manage.py seed_demo
```

7. 啟動開發伺服器

```powershell
python manage.py runserver
```

管理與遷移工具
- 若已用舊版資料標記教師（Profile.is_teacher=True），可執行：

```powershell
python manage.py create_teachers_from_profiles
```

	這會為對應使用者建立 Teacher 物件並把使用者加入 Teacher 群組。
- 管理員可在 Admin 裡的新群組 Teacher 中管理教師成員與權限。

測試
- 建議執行應用內 tests：

```powershell
python manage.py test grades
```

備註
- 登入後的導向行為使用 LOGIN_REDIRECT_URL = 'main'，main 會根據使用者身分把教師導至 teacher_courses、學生導至 student_courses、管理員保留在管理總覽。
- 範本與 view 中的角色檢查優先檢查 Teacher 群組，並向後相容 Profile.is_teacher 標記。
- 若有現有資料庫，更新模型後請先備份 db.sqlite3 再執行 migrate。
