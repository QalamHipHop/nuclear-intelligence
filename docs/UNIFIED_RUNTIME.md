# Unified Runtime Architecture

## هدف

پروژه از این پس یک مسیر مرجع برای ساخت runtime دارد. CLI، API، GitHub Actions و headless Hugging Face Space باید از `core.runtime` استفاده کنند. `hf_deploy/app.py` فقط لایه نمایش Gradio است و نباید هسته پژوهش مستقل دیگری ایجاد کند.

## اجزای مرجع

| جزء | مسیر مرجع | مسئولیت |
|---|---|---|
| تنظیمات runtime | `core/runtime.py` | خواندن environment، اعتبارسنجی مقدارها، مسیرهای state و thresholdها |
| هسته پژوهش | `core/nuclear_intelligence_v4.py` | تولید پرسش، پژوهش، ارزیابی و کنترل کیفیت |
| چرخه عملیاتی | `core/operation_loop_v4.py` | اجرای cycle، تصمیم mint و ثبت report |
| ledger | `blockchain/virtual_ledger.py` | ثبت زنجیره NES و اعتبارسنجی آن |
| مدیریت credential | `core/runtime_config.py` | خواندن secret فقط از environment و diagnostics غیرحساس |
| همگام‌سازی | `scripts/sync_huggingface.py` | یک مسیر مشترک برای HF Dataset و GitHub |
| adapter فضای HF | `core_hf.py` | adapter headless روی همان core و loop مرجع |

## قرارداد اجرای یک cycle

هر cycle باید با `build_runtime()` ساخته شود. نتیجه باید `OperationCycleResult` باشد و با `to_dict()` برای API، artifact یا Dataset serialise شود. providerهای `fallback`، `demo` و `unknown` و همچنین evaluator ناموجود هرگز اجازه mint ندارند.

## تنظیمات اصلی

مقادیر secret مانند `HF_TOKEN` و `GITHUB_TOKEN` فقط از environment خوانده می‌شوند و نباید در کد، README، commit یا log نوشته شوند. تنظیمات غیرحساس مهم عبارت‌اند از `LLM_PROVIDER_CHAIN`، `MIN_ACCURACY`، `MIN_NOVELTY`، `MIN_USEFULNESS`، `MIN_OVERALL`، `MIN_COMPLETENESS`، `DEVELOPER_MODE`، `WEB_SEARCH_ENABLED`، `SYNC_TO_HF`، `SYNC_TO_GITHUB` و `NI_PROJECT_ROOT`.

## رفتار بدون credential

در local/demo، نبود credential باعث توقف import یا crash نمی‌شود. اتصال خارجی فقط در صورت وجود credential معتبر فعال می‌شود. در workflowهایی که `REQUIRE_HF_SYNC=true` یا `REQUIRE_GH_SYNC=true` دارند، نبودن credential یا شکست کامل upload باید exit code غیرصفر تولید کند تا وضعیت سبز کاذب ایجاد نشود.

## بررسی سلامت

حداقل کنترل‌های release شامل `python -m compileall -q core scripts api tests`، اجرای unittestها، `python scripts/health_check.py`، `git diff --check` و اسکن secret patternها است. health endpoint باید علاوه بر alive بودن process، وضعیت core، ledger، loop و providerهای قابل‌دسترس را گزارش کند.
