# my_model.py
import re
from collections import Counter

import numpy as np
import pandas as pd

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer

import torch
from transformers import AutoTokenizer, AutoModel
from kmodes.kmodes import KModes

# ---------- GLOBAL SETUP----------

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

stop_words = set(stopwords.words("english"))
stemmer = PorterStemmer()

def safe_split(s):
    if isinstance(s, str):
        return s.split()
    return []

def parse_number(s):
    try:
        return float(str(s).strip())
    except Exception:
        return None

def parse_range(ref_str):
    if ref_str is None or (isinstance(ref_str, float) and np.isnan(ref_str)):
        return (None, None)
    text = str(ref_str)
    m = re.search(r"(-?\d+(\.\d+)?)\s*[-–]\s*(-?\d+(\.\d+)?)", text)
    if m:
        low = float(m.group(1))
        high = float(m.group(3))
        return (low, high)
    return (None, None)

def classify_test_value(result, ref_str):
    res_str = str(result).strip()
    res_lower = res_str.lower()
    ref_str = "" if ref_str is None or (isinstance(ref_str, float) and np.isnan(ref_str)) else str(ref_str)
    ref_clean = " ".join(ref_str.split())

    if any(w in res_lower for w in ["negative", "within normal", "within range",
                                    "normal", "non-reactive", "nil", "absent", "clear"]):
        return "normal", "Text suggests a normal or negative finding."
    if any(w in res_lower for w in ["positive", "reactive", "raised", "increased",
                                    "decreased", "high", "low"]):
        return "abnormal", "Text suggests an abnormal or noteworthy finding."

    val = parse_number(res_str)
    low, high = parse_range(ref_clean)

    if val is not None and low is not None and high is not None:
        if val < low:
            return "low", f"Result {val} is below reference range ({low}–{high})."
        elif val > high:
            return "high", f"Result {val} is above reference range ({low}–{high})."
        else:
            return "normal", f"Result {val} is within reference range ({low}–{high})."

    return "unknown", "Status could not be clearly determined from text."

def compute_severity_score(result, ref_str):
    val = parse_number(result)
    low, high = parse_range(ref_str)
    if val is None or low is None or high is None or high == low:
        return 0.0
    if low <= val <= high:
        return 0.0
    width = max(1e-6, high - low)
    if val > high:
        return (val - high) / width
    else:
        return (low - val) / width

organ_keywords = {
    "cardiac": ["troponin", "ck-mb", "myoglobin", "bnp", "pro-bnp"],
    "renal": ["creatinine", "urea", "bun", "egfr"],
    "electrolytes": ["sodium", "na", "potassium", "k", "chloride", "cl", "calcium", "ca", "magnesium", "mg", "phosphate"],
    "cbc": ["hemoglobin", "hb", "wbc", "neutrophil", "lymphocyte", "platelet", "rbc"],
    "liver": ["alt", "ast", "sgpt", "sgot", "bilirubin", "alkaline phosphatase", "alp", "ggt"],
}
organ_priority = {
    "cardiac": 1,
    "renal": 2,
    "electrolytes": 3,
    "cbc": 4,
    "liver": 5,
    "others": 6,
}

def organ_group(test_name: str) -> str:
    t = str(test_name).lower()
    for grp, keys in organ_keywords.items():
        if any(k in t for k in keys):
            return grp
    return "others"

# ---------- TEXT PREPROCESS ----------

def preprocess_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^a-zA-Z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    tokens = word_tokenize(t)
    tokens = [w for w in tokens if w not in stop_words]
    tokens = [stemmer.stem(w) for w in tokens]
    return " ".join(tokens)

# ---------- BIOBERT   ----------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
biomodel = AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.1").to(device)

def embed_biobert(sent_list, batch_size=16, max_length=128):
    all_embs = []
    biomodel.eval()
    with torch.no_grad():
        for i in range(0, len(sent_list), batch_size):
            batch = sent_list[i:i+batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            ).to(device)
            outputs = biomodel(**enc)
            cls_emb = outputs.last_hidden_state[:, 0, :]
            all_embs.append(cls_emb.cpu().numpy())
    return np.vstack(all_embs) if all_embs else np.zeros((0, biomodel.config.hidden_size))

# ---------- CLUSTERING HELPERS ----------

def euclidean_distance(a, b):
    return np.linalg.norm(a - b)

def manhattan_distance(a, b):
    return np.sum(np.abs(a - b))

def pairwise_distance_matrix(X, centroids, metric="euclidean"):
    n, k = X.shape[0], centroids.shape[0]
    dists = np.zeros((n, k))
    for i in range(n):
        for j in range(k):
            if metric == "euclidean":
                dists[i, j] = euclidean_distance(X[i], centroids[j])
            else:
                dists[i, j] = manhattan_distance(X[i], centroids[j])
    return dists

def k_cluster(X, k, distance="euclidean", centroid_type="mean",
              max_iter=100, tol=1e-4):
    if X.shape[0] == 0:
        raise ValueError("No data points to cluster.")
    n_samples, _ = X.shape
    k = min(k, n_samples)
    indices = np.random.choice(n_samples, k, replace=False)
    centroids = X[indices].copy()

    for _ in range(max_iter):
        dists = pairwise_distance_matrix(X, centroids, metric=distance)
        labels = np.argmin(dists, axis=1)

        new_centroids = np.zeros_like(centroids)
        for j in range(k):
            pts = X[labels == j]
            if len(pts) == 0:
                new_centroids[j] = X[np.random.randint(0, n_samples)]
            else:
                if centroid_type == "mean":
                    new_centroids[j] = np.mean(pts, axis=0)
                elif centroid_type == "median":
                    new_centroids[j] = np.median(pts, axis=0)
                else:
                    raise ValueError("Unsupported centroid_type")

        shift = np.linalg.norm(new_centroids - centroids)
        centroids = new_centroids
        if shift < tol:
            break

    return labels, centroids

# ---------- ROUGE HELPERS ----------

def ngrams(tokens, n):
    return list(zip(*[tokens[i:] for i in range(n)]))

def rouge_n(reference, hypothesis, n=1):
    ref_tokens = word_tokenize(reference.lower())
    hyp_tokens = word_tokenize(hypothesis.lower())

    ref_ngrams = Counter(ngrams(ref_tokens, n))
    hyp_ngrams = Counter(ngrams(hyp_tokens, n))

    overlap = sum((ref_ngrams & hyp_ngrams).values())
    ref_count = max(1, sum(ref_ngrams.values()))
    hyp_count = max(1, sum(hyp_ngrams.values()))

    recall = overlap / ref_count
    precision = overlap / hyp_count
    f1 = 0.0 if (recall + precision) == 0 else 2 * recall * precision / (recall + precision)
    return recall, precision, f1

def lcs_length(x, y):
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if x[i] == y[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
    return dp[m][n]

def rouge_l(reference, hypothesis):
    ref_tokens = word_tokenize(reference.lower())
    hyp_tokens = word_tokenize(hypothesis.lower())
    lcs = lcs_length(ref_tokens, hyp_tokens)

    ref_count = max(1, len(ref_tokens))
    hyp_count = max(1, len(hyp_tokens))

    recall = lcs / ref_count
    precision = lcs / hyp_count
    f1 = 0.0 if (recall + precision) == 0 else 2 * recall * precision / (recall + precision)
    return recall, precision, f1

# ---------- BUILD SENTENCES / OVERVIEW / STATUS ----------

def build_sentences_from_report(report_df: pd.DataFrame):
    sentences = []
    row0 = report_df.iloc[0]
    patient = row0.get("Patient_Name", "")
    age = row0.get("Patient_Age_Years", "")
    gender = row0.get("Patient_Gender", "")
    title = row0.get("Report_Title", "")
    lab = row0.get("Lab", "")
    dept = row0.get("Department", "")
    sample_type = row0.get("Sample_Type", "")
    sample_date = row0.get("Sample_Date", "")
    report_date = row0.get("Report_Date", "")

    header = (
        f"This laboratory report ('{title}') is for {patient}, "
        f"{age} years, {gender}, tested at {lab}, department {dept}. "
        f"Sample type: {sample_type}, collected on {sample_date} and reported on {report_date}."
    )
    sentences.append(header)

    for _, row in report_df.iterrows():
        test = str(row["Test_Name"])
        result = row["Result"]
        unit = "" if pd.isna(row.get("Unit")) else str(row["Unit"])
        ref = None if pd.isna(row.get("Reference_Range")) else str(row["Reference_Range"])
        method = "" if pd.isna(row.get("Method")) else str(row["Method"])

        status, expl = classify_test_value(result, ref)

        ref_short = ""
        if ref:
            ref_short = " ".join(str(ref).split())
            if len(ref_short) > 70:
                ref_short = ref_short[:67] + "..."

        base_val = f"{result} {unit}".strip()

        if status in ["normal", "low", "high"]:
            sentence = f"{test}: {base_val}."
            if ref_short:
                sentence += f" Reference: {ref_short}."
            sentence += f" {expl}"
        elif status == "abnormal":
            sentence = f"{test}: {base_val} (text suggests an abnormal or noteworthy finding)."
            if ref_short:
                sentence += f" Reference: {ref_short}."
        else:
            sentence = f"{test}: {base_val}."
            if ref_short:
                sentence += f" Reference: {ref_short}."

        if method.strip():
            sentence += f" Method: {method}."

        sentences.append(sentence)

    return sentences

def build_overview_sentences(report_df: pd.DataFrame):
    overview_sents = []
    n_tests = len(report_df)
    unique_tests = list(report_df["Test_Name"].astype(str).unique())

    if n_tests > 0:
        if len(unique_tests) <= 6:
            tests_str = ", ".join(unique_tests)
        else:
            tests_str = ", ".join(unique_tests[:6]) + ", and others"
        overview_sents.append(
            f"This report contains {n_tests} test measurements, including {tests_str}."
        )

    status_list = []
    for _, row in report_df.iterrows():
        s, _ = classify_test_value(row["Result"], row["Reference_Range"])
        status_list.append(s)

    n_normal = sum(s == "normal" for s in status_list)
    n_abn = sum(s in ["high", "low", "abnormal"] for s in status_list)
    n_unknown = sum(s == "unknown" for s in status_list)

    if n_tests > 0:
        overview_sents.append(
            f"Out of {n_tests} tests, approximately {n_normal} appear clearly within normal or negative limits, "
            f"{n_abn} show possible abnormality (high, low, or flagged), and {n_unknown} have unclear status."
        )

    if n_abn > 0:
        abn_tests = report_df[[s in ["high", "low", "abnormal"] for s in status_list]]["Test_Name"].astype(str).unique().tolist()
        top_abn = ", ".join(abn_tests[:5])
        overview_sents.append(f"Key tests that may require closer review include: {top_abn}.")

    return overview_sents

def add_status_columns(report_df: pd.DataFrame):
    statuses = []
    explanations = []
    severities = []
    for _, row in report_df.iterrows():
        status, expl = classify_test_value(row["Result"], row["Reference_Range"])
        sev = compute_severity_score(row["Result"], row["Reference_Range"])
        statuses.append(status)
        explanations.append(expl)
        severities.append(sev)
    df_out = report_df.copy()
    df_out["Status"] = statuses
    df_out["Status_Explanation"] = explanations
    df_out["SeverityScore"] = severities
    return df_out

# ---------- SUMMARY BUILDERS ----------

def build_summary_by_percentage(sentences, X, labels, centroids,
                                percentage=0.3, distance="euclidean"):
    selected_idx = []
    k = centroids.shape[0]
    for c in range(k):
        idxs = np.where(labels == c)[0]
        if len(idxs) == 0:
            continue
        dists = []
        for idx in idxs:
            if distance == "euclidean":
                d = euclidean_distance(X[idx], centroids[c])
            else:
                d = manhattan_distance(X[idx], centroids[c])
            dists.append((idx, d))
        dists.sort(key=lambda x: x[1])
        n_select = max(1, int(len(idxs) * percentage))
        chosen = [idx for idx, _ in dists[:n_select]]
        selected_idx.extend(chosen)
    selected_idx = sorted(set(selected_idx))
    summary_text = " ".join(sentences[i] for i in selected_idx)
    return summary_text, selected_idx

def build_summary_by_nearest_x(sentences, X, labels, centroids,
                               x=2, distance="euclidean"):
    selected_idx = []
    k = centroids.shape[0]
    for c in range(k):
        idxs = np.where(labels == c)[0]
        if len(idxs) == 0:
            continue
        dists = []
        for idx in idxs:
            if distance == "euclidean":
                d = euclidean_distance(X[idx], centroids[c])
            else:
                d = manhattan_distance(X[idx], centroids[c])
            dists.append((idx, d))
        dists.sort(key=lambda x: x[1])
        n_select = min(x, len(idxs))
        chosen = [idx for idx, _ in dists[:n_select]]
        selected_idx.extend(chosen)
    selected_idx = sorted(set(selected_idx))
    summary_text = " ".join(sentences[i] for i in selected_idx)
    return summary_text, selected_idx

def hamming_distance(a, b):
    return np.sum(a != b)

def build_summary_kmode_by_percentage(sentences, X_cat, labels, modes,
                                      percentage=0.3):
    selected_idx = []
    k = modes.shape[0]
    for c in range(k):
        idxs = np.where(labels == c)[0]
        if len(idxs) == 0:
            continue
        dists = []
        for idx in idxs:
            d = hamming_distance(X_cat[idx], modes[c])
            dists.append((idx, d))
        dists.sort(key=lambda x: x[1])
        n_select = max(1, int(len(idxs) * percentage))
        chosen = [idx for idx, _ in dists[:n_select]]
        selected_idx.extend(chosen)
    selected_idx = sorted(set(selected_idx))
    summary_text = " ".join(sentences[i] for i in selected_idx)
    return summary_text, selected_idx

def build_summary_kmode_by_nearest_x(sentences, X_cat, labels, modes,
                                     x=2):
    selected_idx = []
    k = modes.shape[0]
    for c in range(k):
        idxs = np.where(labels == c)[0]
        if len(idxs) == 0:
            continue
        dists = []
        for idx in idxs:
            d = hamming_distance(X_cat[idx], modes[c])
            dists.append((idx, d))
        dists.sort(key=lambda x: x[1])
        n_select = min(x, len(idxs))
        chosen = [idx for idx, _ in dists[:n_select]]
        selected_idx.extend(chosen)
    selected_idx = sorted(set(selected_idx))
    summary_text = " ".join(sentences[i] for i in selected_idx)
    return summary_text, selected_idx

def dedup_sentences(text):
    sents = [s.strip() for s in sent_tokenize(text) if s.strip()]
    seen = set()
    keep = []
    for s in sents:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        keep.append(s)
    return " ".join(keep)

def build_abnormal_summary(report_df_status, max_items=12):
    abn_mask = report_df_status["Status"].isin(["high", "low", "abnormal"])
    abn_df = report_df_status[abn_mask].copy()

    if abn_df.empty:
        return (
            "Key abnormal or notable test results:\n"
            "- No clearly abnormal results were detected based on the available reference ranges. "
            "Interpretation should still be confirmed in the clinical context."
        )

    abn_df["OrganGroup"] = abn_df["Test_Name"].apply(organ_group)
    abn_df["OrganPriority"] = abn_df["OrganGroup"].map(lambda g: organ_priority.get(g, 999))
    abn_df["SeverityScore"] = abn_df["SeverityScore"].fillna(0.0)
    abn_df["IsCritical"] = abn_df["SeverityScore"] > 2.0

    abn_df = abn_df.sort_values(
        by=["IsCritical", "OrganPriority", "SeverityScore"],
        ascending=[False, True, False]
    )

    lines = []
    n = 0
    for _, row in abn_df.iterrows():
        if n >= max_items:
            break
        test = str(row["Test_Name"])
        result = str(row["Result"])
        unit = "" if pd.isna(row["Unit"]) else f" {row['Unit']}"
        status = row["Status"]
        expl = row["Status_Explanation"]
        sev = row["SeverityScore"]
        grp = row["OrganGroup"]
        critical_flag = row["IsCritical"]

        if status == "high":
            status_text = "elevated"
        elif status == "low":
            status_text = "reduced"
        elif status == "abnormal":
            status_text = "flagged as abnormal"
        else:
            status_text = status

        prefix = "CRITICAL – " if critical_flag else ""
        line = (
            f"- {prefix}{test}: {result}{unit} ({status_text}, severity index {sev:.2f}, {grp.upper()}). "
            f"{expl}"
        )
        lines.append(line)
        n += 1

    if len(abn_df) > max_items:
        lines.append(
            f"- Plus {len(abn_df) - max_items} additional abnormal or flagged results not listed in detail here."
        )

    header = (
        "Key abnormal or urgent findings (ordered by clinical priority and severity):\n"
        + "\n".join(lines)
    )
    return header

# ---------- MAIN PUBLIC FUNCTION ----------

def generate_summary_from_report_df(report_df: pd.DataFrame) -> str:
    """
    Core pipeline:
    - Build sentences
    - Preprocess
    - Embed with BioBERT
    - K-Means, K-Median, K-Modes
    - Build 6 summaries
    - ROUGE evaluation
    - Pick best
    - Build overview + abnormal + narrative final text
    """
    if report_df.empty:
        return "No data found for this report."

    # 1) Sentences, overview, status
    base_sentences = build_sentences_from_report(report_df)
    overview_sents = build_overview_sentences(report_df)
    report_df_status = add_status_columns(report_df)

    sentences_raw = base_sentences
    sentences_clean = [preprocess_text(s) for s in sentences_raw]
    sentences_clean = [c if isinstance(c, str) else "" for c in sentences_clean]

    # 2) Embeddings
    X = embed_biobert(sentences_raw)
    n_sent = X.shape[0]
    if n_sent == 0:
        return "No sentences generated for this report."

    if n_sent <= 5:
        optimal_k = 1
    else:
        optimal_k = min(5, max(2, n_sent // 4))

    # 3) K-Means / K-Median
    labels_kmeans, centroids_kmeans = k_cluster(
        X, optimal_k, distance="euclidean", centroid_type="mean"
    )
    labels_kmedian, centroids_kmedian = k_cluster(
        X, optimal_k, distance="manhattan", centroid_type="median"
    )

    # 4) K-Modes BoW
    bow_tokens = []
    for s in sentences_clean:
        bow_tokens.extend(safe_split(s))

    MAX_VOCAB = 1000
    vocab_counts = Counter(bow_tokens)
    most_common = [w for w, _ in vocab_counts.most_common(MAX_VOCAB)]
    vocab = {w: i for i, w in enumerate(most_common)}
    V = len(vocab)

    X_cat = np.zeros((n_sent, V), dtype=int)
    for i, s in enumerate(sentences_clean):
        for w in safe_split(s):
            if w in vocab:
                X_cat[i, vocab[w]] = 1

    km = KModes(n_clusters=optimal_k, init="Huang", n_init=3, verbose=0)
    labels_kmode = km.fit_predict(X_cat)
    modes_kmode = km.cluster_centroids_

    # 5) Build 6 summaries
    SUMMARY_PERCENT = 0.3
    NEAREST_X = 2

    summary_kmeans_percent, _ = build_summary_by_percentage(
        sentences_raw, X, labels_kmeans, centroids_kmeans,
        percentage=SUMMARY_PERCENT, distance="euclidean"
    )

    summary_kmeans_nearest, _ = build_summary_by_nearest_x(
        sentences_raw, X, labels_kmeans, centroids_kmeans,
        x=NEAREST_X, distance="euclidean"
    )

    summary_kmedian_percent, _ = build_summary_by_percentage(
        sentences_raw, X, labels_kmedian, centroids_kmedian,
        percentage=SUMMARY_PERCENT, distance="manhattan"
    )

    summary_kmedian_nearest, _ = build_summary_by_nearest_x(
        sentences_raw, X, labels_kmedian, centroids_kmedian,
        x=NEAREST_X, distance="manhattan"
    )

    summary_kmode_percent, _ = build_summary_kmode_by_percentage(
        sentences_raw, X_cat, labels_kmode, modes_kmode,
        percentage=SUMMARY_PERCENT
    )

    summary_kmode_nearest, _ = build_summary_kmode_by_nearest_x(
        sentences_raw, X_cat, labels_kmode, modes_kmode,
        x=NEAREST_X
    )

    summary_dict = {
        "kmeans_percent": summary_kmeans_percent,
        "kmeans_nearest": summary_kmeans_nearest,
        "kmedian_percent": summary_kmedian_percent,
        "kmedian_nearest": summary_kmedian_nearest,
        "kmode_percent": summary_kmode_percent,
        "kmode_nearest": summary_kmode_nearest,
    }

    # 6) ROUGE evaluation
    reference_summary = " ".join(sentences_raw)
    results = []
    for name, text in summary_dict.items():
        r1 = rouge_n(reference_summary, text, n=1)
        r2 = rouge_n(reference_summary, text, n=2)
        rl = rouge_l(reference_summary, text)
        results.append({
            "name": name,
            "rouge1_f1": r1[2],
            "rouge2_f1": r2[2],
            "rougeL_f1": rl[2],
        })

    rouge_df = pd.DataFrame(results)
    best_row = rouge_df.sort_values("rouge1_f1", ascending=False).iloc[0]
    best_name = best_row["name"]
    best_summary_raw = summary_dict[best_name]
    best_summary = dedup_sentences(best_summary_raw)

    # 7) Combine overview + abnormal + narrative
    overview_block = ""
    if overview_sents:
        overview_block = dedup_sentences(" ".join(overview_sents))

    abnormal_block = build_abnormal_summary(report_df_status)

    final_pieces = []
    if overview_block:
        final_pieces.append("1. Overall report overview:\n" + overview_block)
    if abnormal_block:
        final_pieces.append("2. Key abnormal or urgent test results:\n" + abnormal_block)
    if best_summary:
        final_pieces.append(
            "3. Detailed narrative summary (BioBERT + clustering, best by ROUGE-1 F1):\n"
            + best_summary
        )

    final_summary_text = "\n\n".join(final_pieces).strip()
    return final_summary_text
