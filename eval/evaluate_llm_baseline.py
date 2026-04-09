"""
Foundation-model baseline comparison.
Submits the same labelled titles to ChatGPT-4o-mini and compares precision,
coverage, latency, cost and consistency against the rule-based pipeline.

(requires OPENAI_API_KEY environment variable)
"""

import os
import sys
import json
import csv
import time
 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
 
try:
    from openai import OpenAI
except ImportError:
    print("pip install openai")
    sys.exit(1)
 
LABELLED_PATH = os.path.join(PROJECT_ROOT, "eval", "labelled_titles.csv")
LLM_RESULTS_PATH = os.path.join(PROJECT_ROOT, "eval", "llm_results.json")
CONSISTENCY_SAMPLE_SIZE = 50
CONSISTENCY_RUNS = 3
 
client = OpenAI()
 
EXTRACTION_PROMPT = """Extract vehicle compatibility from this eBay listing title.
Return ONLY a JSON object with these fields:
- make (string, lowercase)
- model (string, lowercase)  
- year_start (integer)
- year_end (integer)
 
If the title does not contain enough information to determine compatibility, return: {{"make": null, "model": null, "year_start": null, "year_end": null}}
 
Title: {title}"""


# submit a single title to GPT-4o-mini and parse the response
def query_llm(title):
    start = time.perf_counter()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(title=title)}],
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        
        return result, elapsed_ms
    
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"make": None, "model": None, "year_start": None, "year_end": None, "error": str(e)}, elapsed_ms
    

# check if the LLM returned a non-null extraction
def has_extraction(result):
    return (result.get("make") is not None and 
            result.get("model") is not None and
            result.get("year_start") is not None)


def load_labelled_dataset(path):
    titles = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            titles.append(row)
    return titles


# run LLM extraction on all titles and compute metrics
def evaluate_llm(titles):
    counts = {"correct": 0, "incorrect": 0, "missed": 0, "justified": 0}
    false_positives = []
    latencies = []
    all_results = []
    
    for i, row in enumerate(titles):
        title = row["title"]
        label = row["label"].strip().lower()
        
        result, elapsed_ms = query_llm(title)
        latencies.append(elapsed_ms)
        
        extracted = has_extraction(result)
        
        all_results.append({
            "title": title,
            "label": label,
            "llm_output": result,
            "llm_extracted": extracted,
            "latency_ms": round(elapsed_ms, 1)
        })
        
        if label == "correct":
            if extracted:
                counts["correct"] += 1
            else:
                counts["missed"] += 1
                
        elif label == "incorrect":
            counts["incorrect"] += 1
            false_positives.append({"title": title, "llm_output": result})
            
        elif label == "missed":
            if extracted:
                counts["correct"] += 1
            else:
                counts["missed"] += 1
                
        elif label == "justified":
            if extracted:
                counts["incorrect"] += 1
                false_positives.append({"title": title, "llm_output": result})
            else:
                counts["justified"] += 1
        
        if (i + 1) % 25 == 0:
            print(f"  Processed {i + 1}/{len(titles)} titles...")
        
        time.sleep(0.1)
    
    return counts, false_positives, latencies, all_results


# submit a subset of titles multiple times to assess determinism
def evaluate_consistency(titles, sample_size=50, runs=3):    
    sample = titles[:sample_size]
    responses_by_title = {row["title"]: [] for row in sample}
    
    print(f"\nConsistency test: {sample_size} titles x {runs} runs")
    
    for run in range(runs):
        print(f"  Run {run + 1}/{runs}...")
        for row in sample:
            result, _ = query_llm(row["title"])
            responses_by_title[row["title"]].append(json.dumps(result, sort_keys=True))
            time.sleep(0.1)
    
    inconsistent = 0
    for title, responses in responses_by_title.items():
        if len(set(responses)) > 1:
            inconsistent += 1
    
    return {
        "sample_size": sample_size,
        "runs": runs,
        "inconsistent_titles": inconsistent,
        "inconsistency_rate": round(inconsistent / sample_size * 100, 1)
    }


def compute_metrics(counts):
    total = sum(counts.values())
    extractable = counts["correct"] + counts["incorrect"] + counts["missed"]
    extracted = counts["correct"] + counts["incorrect"]
    
    precision = counts["correct"] / extracted if extracted > 0 else 0
    coverage = extracted / extractable if extractable > 0 else 0
    
    return {
        "total_titles": total,
        "precision": round(precision * 100, 1),
        "coverage": round(coverage * 100, 1),
        "correct": counts["correct"],
        "incorrect": counts["incorrect"],
        "missed": counts["missed"],
        "justified": counts["justified"],
    }


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    print("Loading labelled dataset...")
    titles = load_labelled_dataset(LABELLED_PATH)
    print(f"Loaded {len(titles)} titles")
    
    print("\nRunning LLM extraction...")
    counts, false_positives, latencies, all_results = evaluate_llm(titles)
    
    metrics = compute_metrics(counts)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    print("\n" + "=" * 60)
    print("LLM BASELINE RESULTS (GPT-4o-mini)")
    print("=" * 60)
    print(f"Precision:       {metrics['precision']}%")
    print(f"Coverage:        {metrics['coverage']}%")
    print(f"False positives: {metrics['incorrect']}")
    print(f"Mean latency:    {avg_latency:.1f} ms per title")
    print()
    
    # consistency test
    consistency = evaluate_consistency(titles, CONSISTENCY_SAMPLE_SIZE, CONSISTENCY_RUNS)
    print(f"Consistency:     {consistency['inconsistent_titles']}/{consistency['sample_size']} "
          f"({consistency['inconsistency_rate']}%) inconsistent across {consistency['runs']} runs")
    
    # save results
    output = {
        "metrics": metrics,
        "mean_latency_ms": round(avg_latency, 1),
        "consistency": consistency,
        "false_positives": false_positives[:20],
        "all_results": all_results,
    }
    
    with open(LLM_RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {LLM_RESULTS_PATH}")