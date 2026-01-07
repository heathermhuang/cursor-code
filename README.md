# AI 算命網站（八字排盤 + 五行分析）

一個可直接啟動的本機網站：

- **輸入**：生日（陽曆）、出生時間、性別、出生城市（選填）
- **輸出**：八字四柱、基本五行統計
- **互動**：根據八字生成「過去 5 年」是/否驗證題
- **生成**：依回答匹配度生成「未來 5 年」趨勢與建議

## 需求

- Python 3.12+

## 安裝

```bash
python3 -m pip install -r requirements.txt
```

## 啟動

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

然後打開瀏覽器進入：

- `http://localhost:8000`

## 專案結構

- `app/main.py`: FastAPI 入口、API 與靜態頁面
- `app/bazi.py`: 八字四柱排盤（使用 `lunar_python`）與五行統計
- `app/fortune.py`: 驗證題生成與未來 5 年趨勢生成（簡化推演）
- `static/`: 前端頁面（HTML/CSS/JS）

## 注意

- **目前版本不做真太陽時/時區校正**；城市主要用於展示與後續擴充。
- 本工具提供的是「八字/五行簡化推演」與自我反思框架，**不構成**醫療、法律、投資建議。
