"""Generate model outputs for eval cases.

The mock mode is useful before downloading models.
"""

from __future__ import annotations

import argparse

from finpref.data.synthetic_generator import build_answer
from finpref.utils.io import read_jsonl, write_jsonl
from finpref.train.common import load_causal_lm, load_tokenizer


def mock_outputs(eval_rows: list[dict]) -> list[dict]:
    rows = []
    for row in eval_rows:
        base = {
            "query_type": row.get("meta", {}).get("query_type", "suitability"),
            "query": row["messages"][-1]["content"],
            "user_profile": {"risk_tolerance": row.get("meta", {}).get("risk_tolerance", "medium"), "investment_horizon": "medium_term", "liquidity_need": "medium"},
            "product_info": {"risk_level": row.get("meta", {}).get("risk_level", "R3"), "product_type": "fund", "volatility": "medium", "liquidity": "T+1"},
            "meta": row.get("meta", {}),
        }
        rows.append({"id": row.get("id"), "response": build_answer(base), "meta": row.get("meta", {}), "messages": row.get("messages", [])})
    return rows


def model_outputs(
    eval_rows: list[dict],
    model_name_or_path: str,
    adapter_path: str | None,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    limit: int | None,
) -> list[dict]:
    import torch
    from peft import PeftModel

    config = {"bf16": torch.cuda.is_available(), "gradient_checkpointing": False}
    tokenizer = load_tokenizer(model_name_or_path)
    tokenizer.padding_side = "left"
    model = load_causal_lm(model_name_or_path, config)
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path, is_trainable=False)
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")

    rows = []
    selected_rows = eval_rows[:limit] if limit else eval_rows
    for row in selected_rows:
        prompt = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        do_sample = temperature > 0
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = temperature
            generation_kwargs["top_p"] = top_p
        with torch.no_grad():
            output_ids = model.generate(**inputs, **generation_kwargs)
        completion_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
        response = tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
        rows.append({"id": row.get("id"), "response": response, "meta": row.get("meta", {}), "messages": row.get("messages", [])})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval_file", default="data/processed/eval_finpref.jsonl")
    parser.add_argument("--output_file", default="outputs/eval/mock_outputs.jsonl")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model_name_or_path", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--adapter_path", default=None)
    parser.add_argument("--max_new_tokens", type=int, default=384)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    eval_rows = read_jsonl(args.eval_file)
    if args.mock:
        rows = mock_outputs(eval_rows)
    else:
        rows = model_outputs(
            eval_rows,
            args.model_name_or_path,
            args.adapter_path,
            args.max_new_tokens,
            args.temperature,
            args.top_p,
            args.limit,
        )
    write_jsonl(args.output_file, rows)


if __name__ == "__main__":
    main()
