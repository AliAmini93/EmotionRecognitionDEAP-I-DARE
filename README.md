# Cross-Subject EEG–EMG Emotion Recognition with Trial-Aware Temporal Modeling
## A Controlled Study on DEAP and I-DARE

> **نسخه فعلی این پروپوزال عمداً محدود و مرحله‌ای است.** در این مرحله، هدف ما ساختن یک مدل نهایی شلوغ نیست؛ هدف این است که یک مسیر تجربی تمیز بسازیم تا بفهمیم کدام inductive biasها واقعاً روی مسئله ما جواب می‌دهند.

---

## 1. انگیزه و مسئله پژوهش

مسئله اصلی پژوهش، تشخیص احساسات از سیگنال‌های فیزیولوژیک در حالت **cross-subject** است. در این تنظیم، مدل روی تعدادی subject آموزش می‌بیند و باید روی subject کاملاً نادیده تعمیم پیدا کند. این مسئله در EEG دشوار است، چون سیگنال EEG بین افراد به‌شدت متفاوت است و علاوه بر نویز، به تفاوت‌های عصبی، آناتومیک، توجه، خستگی و سبک پاسخ‌دهی هر فرد وابسته است.

دلیل انتخاب اولیه‌ی **DEAP** و **I-DARE** این است که هر دو دیتاست به‌صورت همزمان EEG و EMG دارند. بنابراین، یکی از سؤال‌های اصلی مقاله این است:

> آیا اضافه‌کردن EMG به EEG می‌تواند در cross-subject emotion recognition بهبود معنادار ایجاد کند؟

سؤال دوم از ساختار DEAP می‌آید. در DEAP هر trial حدود 60 ثانیه است، اما label در سطح کل trial داده شده است. اگر trial را به segmentهای کوتاه‌تر بشکنیم و هر segment را مستقل فرض کنیم، label هر segment در واقع یک weak label است. بنابراین سؤال دوم این است:

> آیا مدل‌کردن رابطه‌ی temporal بین segmentهای یک trial باعث بهبود تشخیص احساس در DEAP می‌شود؟

در نسخه فعلی، **cross-dataset transfer** بین DEAP و I-DARE بررسی نمی‌شود. تمرکز فقط روی cross-subject داخل هر دیتاست است.

---

## 2. سؤال‌های پژوهشی

### RQ1 — نقش EMG

آیا EMG به‌عنوان modality کمکی در کنار EEG باعث بهبود performance در cross-subject emotion recognition می‌شود؟

### RQ2 — نقش temporal sequence encoding

آیا در DEAP، مدل‌کردن sequence دوازده segment پنج‌ثانیه‌ای داخل هر trial بهتر از طبقه‌بندی مستقل segmentهاست؟

### RQ3 — تعامل EMG و sequence modeling

اگر temporal sequence encoding اضافه شود، آیا EMG هنوز ارزش افزوده دارد؟

### RQ4 — نقش contrastive learning (ablation بعدی)

آیا یک contrastive loss طراحی‌شده بر اساس affective response، نه صرفاً stimulus identity، می‌تواند generalization را بهتر کند؟

> این سؤال چهارم فعلاً در هسته مدل نیست و بعد از تثبیت baselineها بررسی می‌شود.

---

## 3. تصمیم‌های فعلی و قفل‌شده

### دیتاست‌ها

| Item | Value |
|------|-------|
| Main datasets | **DEAP** و **I-DARE** |
| تمرکز فعلی | cross-subject within-dataset |
| cross-dataset transfer | ❌ فعلاً انجام نمی‌شود |

### تسک‌ها

- Binary valence
- Binary arousal

**Label harmonization:**

```python
label = 1 if score > 5 else 0
# score == 5 -> discard (کاهش label noise)
```

<!-- PROJECT_STATUS_LABEL_POLICY_NOTE_START -->
> **Current implementation note:** the original label harmonization rule above is a proposal-stage default, not a locked final decision. Recent smoke runs keep all three policies available and mostly use `midpoint_as_high` for early stability/comparability. Final paper claims should treat label policy as a serious ablation across `discard_midpoint`, `midpoint_as_low`, and `midpoint_as_high`.
<!-- PROJECT_STATUS_LABEL_POLICY_NOTE_END -->

### Windowing فعلی

**Main protocol:**

| Dataset | Windowing |
|---------|-----------|
| DEAP | `60s trial → 12 windows × 5s` |
| I-DARE | `5s stimulus block → 1 window` |

- Overlap در main protocol استفاده نمی‌شود.

**Ablation بعدی:**
- `4s / 5s / 6s` window
- در صورت نیاز، `50%` overlap فقط به‌عنوان ablation

---

## 4. مسیر کلی آزمایش‌ها

### Phase 0 — Data Protocol

- استفاده از DEAP preprocessed
- استفاده از I-DARE processed EEG/EMG
- Resample به `128Hz` در صورت نیاز
- Normalization فقط با آمار train subjects در هر fold
- Strict LOSO

### Phase 1 — EEG-only Baselines

> هدف: ساختن baseline قابل‌اعتماد

| # | مدل | هدف |
|---|------|------|
| 1 | OldEncoder + classifier | مقایسه با نسخه قبلی |
| 2 | EEGSegmentClassifier-v1 | مدل جدید |
| 3 | EEGNet / ShallowConvNet | sanity check |

### Phase 2 — EMG Contribution

| # | مدل |
|---|------|
| 1 | EMG-only MLP |
| 2 | EEG+EMG concat fusion |
| 3 | EEG+EMG gated fusion |

### Phase 3 — Trial Sequence Modeling (DEAP)

| # | مدل |
|---|------|
| 1 | EEG-only بدون sequence |
| 2 | EEG-only با sequence |
| 3 | EEG+EMG بدون sequence |
| 4 | EEG+EMG با sequence |

### Phase 4 — I-DARE

| # | مدل |
|---|------|
| 1 | EEG-only |
| 2 | EMG-only |
| 3 | EEG+EMG |

> ادعای اصلی sequence modeling روی I-DARE مطرح نمی‌شود، مگر اینکه ساختار eventها اجازه دهد.

### Phase 5 — Contrastive Learning / Regularization

| # | Loss |
|---|------|
| 1 | CE only |
| 2 | CE + affective SupCon |
| 3 | CE + VREx |
| 4 | CE + SupCon + VREx |

---

## 5. تصمیم فعلی درباره Contrastive Learning

ما توافق کردیم که contrastive learning اگر خام طراحی شود، می‌تواند اشتباه باشد. دلیلش این است که یک ویدیو ممکن است برای افراد مختلف احساس متفاوتی ایجاد کند. بنابراین، positive pair نباید صرفاً بر اساس same stimulus تعریف شود.

**طراحی درست‌تر:**

```
positive = same emotion label + different subject
optional: close continuous rating
```

**Hard negative مهم:**

```
same stimulus/video + different reported emotion
```

**محل اعمال contrastive loss:**
- بهتر است روی **trial-level representation** باشد، نه روی segment خام.

> در نسخه فعلی کد، فقط projection head آماده شده است؛ loss در training script فعال یا غیرفعال خواهد شد.

---

## 6. مدل فعلی: EEGSegmentClassifier-v1

> این مدل فقط برای مرحله اول است — فقط EEG، بدون EMG، بدون trial sequence encoder، بدون SupCon/VREx

### هدف مدل

```
EEG window [B, C, T] → embedding → logits
```

برای DEAP/I-DARE در حالت 5 ثانیه:

```
C = 32
T = 640  # 5s × 128Hz
```

---

## 7. تغییرات نسبت به مدل کنفرانسی قبلی

| # | تغییر | جزئیات |
|---|-------|--------|
| 7.1 | Regressor → Classifier | خروجی `logits: [B, n_classes]` |
| 7.2 | Temporal stem ماژولار شد | قابل تنظیم برای 4, 5, 6 ثانیه |
| 7.3 | Multi-branch temporal stem | `~0.125s`, `~0.25s`, `~0.5s` |
| 7.4 | Fusion قابل تنظیم | `concat` (default), `sum`, `attn`, `moe` |
| 7.5 | Channel positional embedding | `learnable` (default), `none`, `coord` |
| 7.6 | Channel mixer قابل تنظیم | `mha` (default), `none`, `graph_bias` |
| 7.7 | Spectral branch اختیاری | `use_spectral_branch=False` (default) |
| 7.8 | GN به‌عنوان norm اصلی | `norm_kind="gn"` (default) |

---

## 8. Default پیشنهادی برای اولین Run

```python
model = EEGSegmentClassifier(
    C=32,
    sampling_rate=128,
    window_sec=5.0,
    n_classes=2,
    modelsize="lite",
    stem_fusion="concat",
    channel_pos_mode="learnable",
    channel_mixer="mha",
    norm_kind="gn",
    use_spectral_branch=False,
)
```

---

## 9. Run‌های اولیه پیشنهادی

| Run | مدل | هدف |
|-----|------|------|
| R0 | OldEncoder + classifier head | بفهمیم تغییرات جدید واقعاً کمک می‌کنند یا نه |
| R1 | EEGSegmentClassifier-v1 default | مدل اصلی |
| R2 | EEGNet / ShallowConvNet | baseline کلاسیک |

---

## 10. Ablation‌های بعدی

> بعد از تثبیت baseline — مرحله‌ای اجرا شوند:

1. `4s` vs `5s` vs `6s`
2. `concat` vs `sum` vs `attn` vs lightweight `MoE`
3. no channel position vs learnable channel position
4. raw-only vs raw+spectral
5. `GN` vs `BN`
6. modelsize `lite` vs `base`

---

## 11. جمع‌بندی فعلی

در این نسخه، تمرکز روی ساختن یک EEG segment encoder قابل‌اعتماد است. مدل هنوز EMG و temporal sequence را وارد نکرده است. این تصمیم آگاهانه است، چون می‌خواهیم ابتدا بفهمیم backbone اصلاح‌شده روی DEAP cross-subject چه رفتاری دارد.

### گام‌های بعدی

1. ✅ آماده‌سازی dataloader برای DEAP 5s windows
2. ⬜ اجرای OldEncoder + classifier
3. ⬜ اجرای EEGSegmentClassifier-v1
4. ⬜ مقایسه با EEGNet
5. ⬜ تصمیم درباره اضافه‌کردن EMG و trial sequence encoder

---

## Appendix A — کد مدل

کد کامل مدل `EEGSegmentClassifier-v1` در فایل [`model_v1.py`](./model_v1.py) قرار دارد.
